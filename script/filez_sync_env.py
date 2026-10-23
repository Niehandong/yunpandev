"""Filez 企业空间文档同步。

包含获取 token 与文档下载，连接参数从 .env 文件读取（默认与本脚本同目录，可用 --env 指定）。
.env 内容示例（见 .env.example）:
    FILEZ_BASE=https://filez.jptoe.com:5555
    FILEZ_APP_KEY=...
    FILEZ_APP_SECRET=...
    FILEZ_SLUG=jik462374
已在系统环境变量中设置的同名变量优先于 .env。

用法（运行即完成扫描 + 下载）:
    python3 filez_sync_env.py                                   # 扫描 / 并下载到 ./mirror
    python3 filez_sync_env.py --out ./mirror --root /roky       # 指定下载目录和起始目录
    python3 filez_sync_env.py --root /roky/a/b --root /newy/c   # 多个目录
    python3 filez_sync_env.py --limit 5                         # 试跑：最多下载 5 个文件
增量策略: 下载后把本地文件修改时间设为远端 modified；本地已存在且修改时间一致的文件跳过。
"""
import argparse
import base64
import logging
import os
import sys
import threading
import time
from collections import deque
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath

import requests

ENV_KEYS = ("FILEZ_BASE", "FILEZ_APP_KEY", "FILEZ_APP_SECRET", "FILEZ_SLUG")

API_VER = "v2"  # 私有化部署实测：/v3 返回 405，统一用 /v2
PAGE_SIZE = 999

log = logging.getLogger("filez")


class FilezError(Exception):
    pass


class RateLimiter:
    """滑动窗口限速：任意 period 秒内最多 limit 次，线程安全，超出时阻塞等待。"""

    def __init__(self, limit, period=60.0):
        self.limit = limit
        self.period = period
        self._stamps = deque()
        self._lock = threading.Lock()

    def acquire(self):
        while True:
            with self._lock:
                now = time.monotonic()
                while self._stamps and now - self._stamps[0] >= self.period:
                    self._stamps.popleft()
                if len(self._stamps) < self.limit:
                    self._stamps.append(now)
                    return
                wait = self.period - (now - self._stamps[0])
            time.sleep(max(wait, 0.05))


def rate_limit_wait(r):
    """服务端限速响应（403 且 reason.type=rate）返回需等待的秒数，否则返回 None。"""
    if r.status_code not in (403, 429):
        return None
    try:
        reason = r.json().get("reason") or {}
    except ValueError:
        return None
    if reason.get("type") != "rate":
        return None
    return int(reason.get("seconds") or 60)


class FilezClient:
    def __init__(self, base, app_key, app_secret, slug, timeout=60, rate=90):
        self.base = base.rstrip("/")
        self.slug = slug
        self.timeout = timeout
        self._basic = "Basic " + base64.b64encode(f"{app_key}:{app_secret}".encode()).decode()
        self._token = None
        self._token_exp = 0.0
        self._lock = threading.Lock()
        self.session = requests.Session()
        # 服务端按应用、按接口限速：fileList / fileDownload 各自每 60s 100 次，客户端主动留余量
        self.list_limiter = RateLimiter(rate, 60)
        self.download_limiter = RateLimiter(rate, 60)

    # ---------- token ----------
    def _fetch_token(self):
        r = self.session.post(
            f"{self.base}/{API_VER}/oauth/token",
            headers={"Authorization": self._basic},
            data={"grant_type": "client_with_su", "scope": "all", "slug": self.slug},
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise FilezError(f"获取 token 失败: {r.status_code} {r.text[:300]}")
        j = r.json()
        self._token = j["access_token"]
        # 提前 5 分钟过期，避免边界失效
        self._token_exp = time.time() + int(j.get("expires_in", 3600)) - 300
        log.info("已获取 token，有效期 %ss", j.get("expires_in"))

    def token(self, force=False):
        with self._lock:
            if force or not self._token or time.time() >= self._token_exp:
                self._fetch_token()
            return self._token

    # ---------- 通用请求：401/invalid_token 自动刷新，限速等待，5xx/429/网络错误退避重试 ----------
    def request(self, method, path, retries=4, stream=False, limiter=None, rate_retries=10, **kw):
        url = f"{self.base}/{API_VER}/api{path}"
        refreshed = False
        attempt = 0
        while attempt <= retries:
            if limiter:
                limiter.acquire()
            headers = {"Authorization": f"bearer {self.token()}"}
            try:
                r = self.session.request(method, url, headers=headers, timeout=self.timeout,
                                         stream=stream, **kw)
            except requests.RequestException as e:
                if attempt == retries:
                    raise
                wait = 2 ** attempt
                log.warning("%s %s 网络错误 %s，%ss 后重试", method, path, e, wait)
                time.sleep(wait)
                attempt += 1
                continue

            wait = rate_limit_wait(r)
            if wait is not None:
                r.close()
                if rate_retries <= 0:
                    raise FilezError(f"{method} {path} 持续被限速: {r.status_code} {r.text[:300]}")
                rate_retries -= 1
                log.warning("%s %s 被服务端限速，%ss 后重试", method, path, wait)
                time.sleep(wait)
                continue

            if r.status_code == 401 or (r.status_code == 400 and "invalid_token" in r.text[:500]):
                if refreshed:
                    raise FilezError(f"鉴权失败: {r.status_code} {r.text[:300]}")
                log.info("token 失效，重新获取")
                r.close()
                self.token(force=True)
                refreshed = True
                continue
            if r.status_code == 429 or r.status_code >= 500:
                if attempt == retries:
                    raise FilezError(f"{method} {path} 失败: {r.status_code} {r.text[:300]}")
                r.close()
                wait = 2 ** attempt
                log.warning("%s %s -> %s，%ss 后重试", method, path, r.status_code, wait)
                time.sleep(wait)
                attempt += 1
                continue
            return r
        raise FilezError(f"{method} {path} 重试耗尽")

    def api_json(self, method, path, **kw):
        r = self.request(method, path, **kw)
        try:
            j = r.json()
        except ValueError:
            raise FilezError(f"{method} {path} 非 JSON 响应: {r.status_code} {r.text[:300]}")
        if r.status_code != 200 or j.get("errcode") not in (0, "0"):
            raise FilezError(f"{method} {path} 业务错误: {r.status_code} {j}")
        return j

    # ---------- 业务接口 ----------
    def list_dir(self, path, path_type="ent"):
        """分页列出目录下全部条目。"""
        items, page = [], 0
        while True:
            j = self.api_json("POST", "/file", limiter=self.list_limiter, data={
                "path": path, "path_type": path_type, "page_num": page,
                "page_size": PAGE_SIZE, "order_by": "name", "sort": "asc",
            })
            batch = j.get("fileModelList") or []
            items.extend(batch)
            total = int(j.get("total") or 0)
            if not batch or len(items) >= total:
                return items
            page += 1

    def download(self, neid, nsid, dest: Path):
        """按 neid 下载到 dest（先写 .part 再原子重命名）。"""
        r = self.request("GET", "/file/content/download",
                         params={"neid": neid, "nsid": nsid}, stream=True,
                         limiter=self.download_limiter)
        with r:
            ctype = r.headers.get("Content-Type", "")
            if r.status_code != 200 or ctype.startswith("application/json"):
                raise FilezError(f"下载 neid={neid} 失败: {r.status_code} {r.text[:300]}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".part")
            size = 0
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
                    size += len(chunk)
        os.replace(tmp, dest)
        return size


# ---------- .env 配置 ----------
def load_env(path: Path):
    """读取 KEY=VALUE 格式的 .env；忽略空行和 # 注释，去掉值两侧引号；不覆盖已有环境变量。"""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip().removeprefix("export ").strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        os.environ.setdefault(key, val)


def load_config(env_file: Path):
    load_env(env_file)
    cfg = {k: os.environ.get(k, "") for k in ENV_KEYS}
    missing = [k for k, v in cfg.items() if not v]
    if missing:
        sys.exit(f"缺少配置 {', '.join(missing)}，请检查 {env_file}")
    return cfg


# ---------- 本地路径与修改时间 ----------
def safe_local_path(out_dir: Path, remote_path: str) -> Path:
    parts = [p for p in PurePosixPath(remote_path).parts if p not in ("/", "", ".")]
    if any(p == ".." for p in parts):
        raise FilezError(f"非法路径: {remote_path}")
    return out_dir.joinpath(*parts)


def remote_mtime(it):
    """把远端 modified（如 2021-08-13 14:37:51）转成时间戳，解析失败返回 None。"""
    try:
        return datetime.strptime(it.get("modified") or "", "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def is_up_to_date(dest: Path, mtime):
    return mtime is not None and dest.is_file() and int(dest.stat().st_mtime) == int(mtime)


# ---------- 遍历 ----------
ENT_ROOT_LABEL = "/企业空间"  # 网页上显示的根节点名，接口路径里不包含它


def normalize_root(root):
    """去掉末尾 /（根目录除外），并去掉从网页复制路径时带上的 /企业空间 前缀。"""
    root = root.rstrip("/") or "/"
    if root == ENT_ROOT_LABEL or root.startswith(ENT_ROOT_LABEL + "/"):
        root = root[len(ENT_ROOT_LABEL):] or "/"
        log.info("已去掉路径中的 %s 前缀，实际查询 %s", ENT_ROOT_LABEL, root)
    return root


def diagnose_root(client, root):
    """起始目录列不出来时，从 / 逐级往下核对，指出哪一级不存在及该级实际有哪些子目录。"""
    cur = "/"
    for name in PurePosixPath(root).parts[1:]:
        try:
            items = client.list_dir(cur)
        except FilezError as e:
            log.error("诊断：列目录 %s 也失败: %s", cur, e)
            return
        dirs = [PurePosixPath(it["path"]).name for it in items if it.get("dir")]
        if name not in dirs:
            log.error("诊断：%s 下没有目录「%s」，现有子目录（前 50 个）: %s", cur, name, dirs[:50])
            return
        cur = str(PurePosixPath(cur) / name)
    log.error("诊断：逐级核对 %s 均存在，可能是当前账号对该目录没有权限", root)


def scan(client, root):
    """遍历 root 下所有目录，返回文件条目列表。"""
    queue = deque([root])
    files = []
    n_dir = 0
    while queue:
        d = queue.popleft()
        try:
            items = client.list_dir(d)
        except FilezError as e:
            log.error("列目录 %s 失败: %s", d, e)
            if d == root and root != "/":
                diagnose_root(client, root)
            continue
        for it in items:
            if it.get("dir"):
                n_dir += 1
                queue.append(it["path"])
            else:
                files.append(it)
        log.info("已扫描 %s（目录 %d，文件 %d，待扫描 %d）", d, n_dir, len(files), len(queue))
    log.info("扫描完成 %s：目录 %d，文件 %d", root, n_dir, len(files))
    return files


def sync_files(client, files, out_dir: Path, workers, limit):
    todo = []
    for it in files:
        dest = safe_local_path(out_dir, it["path"])
        mtime = remote_mtime(it)
        if not is_up_to_date(dest, mtime):
            todo.append((it, dest, mtime))
    skipped = len(files) - len(todo)
    if limit:
        todo = todo[:limit]
    log.info("共 %d 个文件，跳过未变化 %d 个，待下载 %d 个", len(files), skipped, len(todo))

    def job(it, dest, mtime):
        size = client.download(str(it["neid"]), str(it["nsid"]), dest)
        if mtime is not None:
            os.utime(dest, (mtime, mtime))
        return size

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(job, *t): t[0]["path"] for t in todo}
        for fut in as_completed(futs):
            path = futs[fut]
            try:
                size = fut.result()
            except Exception as e:  # noqa: BLE001 单个文件失败不影响整体
                fail += 1
                log.error("下载失败 %s: %s", path, e)
                continue
            ok += 1
            log.info("[%d/%d] %s (%d bytes)", ok + fail, len(todo), path, size)
    log.info("下载完成：成功 %d，失败 %d", ok, fail)


def main():
    ap = argparse.ArgumentParser(description="Filez 企业空间文档同步（扫描 + 下载）")
    ap.add_argument("--root", action="append", dest="roots",
                    help="企业空间起始路径，可写多次；默认 /")
    ap.add_argument("--out", default="mirror", help="下载目录，默认 ./mirror")
    ap.add_argument("--env", default=str(Path(__file__).resolve().parent / ".env"),
                    help="配置文件路径，默认脚本同目录下的 .env")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="最多下载多少个文件（试跑用）")
    ap.add_argument("--rate", type=int, default=90,
                    help="列目录、下载接口各自每 60 秒最多请求多少次，默认 90（服务端上限 100）")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cfg = load_config(Path(args.env))
    client = FilezClient(cfg["FILEZ_BASE"], cfg["FILEZ_APP_KEY"],
                         cfg["FILEZ_APP_SECRET"], cfg["FILEZ_SLUG"], rate=args.rate)

    # 多个 root 有重叠时按 neid 去重
    roots = [normalize_root(r) for r in (args.roots or ["/"])]
    files = {}
    for root in roots:
        for it in scan(client, root):
            files[str(it["neid"])] = it
    sync_files(client, list(files.values()), Path(args.out), args.workers, args.limit)


if __name__ == "__main__":
    main()
