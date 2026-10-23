# 联想 Filez 开放对接平台 API

> 由《联想Filez开放平台API.pdf》（北京联想协同科技有限公司，2021.03.05，223 页）转换而来。

## 概念介绍

### 1. 应用（app）

一个应用（app）代表一个开放平台API 的调用主体。目前开放平台API 不提供匿名访问机制，因此需要持有应用身份信息（详细信息见令牌解释）才能使用开放平台提供的API。

应用身份信息包含两个字段：

appKey，用于唯一确定一个应用的信息（相当于用户名）appSecret，用于防止应用信息被冒用（相当于密码）这两个字段由开放平台提供，开放平台API 的调用者应该妥善保存。为确保安全性，对于appSecret，应该只在后台调用时传递。

### 2. 用户（user）

用户（user）在本文档若无特殊说明特指filez Box 用户。

### 3. 令牌（token）

令牌（token）是调用所有API 都需要传递的凭证信息。若想调用API 需要携带应用信息和用户信息到指定的端点申请令牌（详见后续部分）。这就意味着一个令牌对应一个应用信息和一个用户信息。若想使用若干不同用户的身份调用API，则需要针对每一个用户申请一次令牌。

### 4. 参数

调用API 需要传递参数。在后续章节中，我们使用方括号来代表需要传递的参数。如token=[token]，就代表需要将[token]替换为需要传递的参数。另外，有些参数需要用某些函数处理，处理函数我们使用斜体表示，如base64([token])，表示将token 参数传递后，再做一次base64 编码处理。

## 获取token

获取token 是调用开放平台API 接口的第一步，几乎所有的业务API 接口都需要依赖于token 来确定调用方（应用，app）和用户（user）身份。

`POST /v3/oauth/token`

**请求示例：**

```bash
curl \
-H "Authorization: Basic YWFhOmJiYg==" \
-d 'grant_type=client_with_su&scope=all&slug=admin' \
https://api.zbox.filez.com/v3/oauth/token
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 |
|---|---|---|---|
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded |
| Authorization | 是 | Header | 格式为Basic base64([appKey]:[appSecret]) |
|  |  |  | 例如，对于appKey=aaa 和appSecret=bbb，你需要先拼接出“aaa:bbb”，然后进行base64 编码，最终的请求头为Authorization: Basic YWFhOmJiYg== |
| grant_type | 是 | Body(form) | 此处需填写固定值client_with_su |
| scope | 是 | Body(form) | 应用能对用户做的操作范围。此处需填写固定值all |
| slug | 是 | Body(form) | 用户登录名。这表示生成token 后能代表哪个用户调用API。 |

**返回示例：**

```json
{
    "access_token":"574a05fd-c99c-4f77-97a4-b6f807cbbade",
    "token_type":"bearer",
    "expires_in":43199,
    "scope":"all"
}
```

获取token 失败：

```json
{
    "timestamp": 1612332489208,
    "status": 401,
    "error": "Unauthorized",
    "message": "",
    "path": "/oauth/token"
}
```

token 过期或者不存在：

```json
{
    "error": "invalid_token",
    "error_description": "Invalid access token: bf64c816-b3fb-4fb4-8d78-2b3954f042f8"
}
```

**返回字段：**

| 参数 | 说明 |
|---|---|
| scope | 应用能对用户做的操作范围。与申请令牌时填写的一致。 |
| token_type | 目前固定为bearer |
| access_token | 获取到的令牌 |
| expires_in | 令牌的有效时间（秒） |

注意事项：

开发者需要缓存access_token，用于后续接口的调用（注意：不能频繁调用此接口，否则会受到频率拦截）。当access_token 失效或过期时，需要重新获取。

access_token 的有效期通过返回的expires_in 来传达，同一应用在有效期内重复针对同一用户获取令牌将返回相同结果，过期后获取会返回新的access_token。

由于运营策略，不保证token 在有效期内持续有效。开发者应实现access_token 失效时重新获取的逻辑。

access_token 至少保留512 字节的存储空间。

## 使用token

获取到token 后，就能使用开放平台提供的API 了。在调用API 时，只需要添加如下所示的Authorization 请求头即可。

`Authorization: bearer [token]`

请将[token]替换为之前已获取的token 内容。

## 1. 文件

### 1.1. 获取文件列表

获取指定路径下的文件列表。

`POST /v3/api/file`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'path=/a' \
-d 'path_type=ent' \
-d 'page_num=0' \
-d 'page_size=1' \
-d 'sort=desc' \
-d 'order_by=mtime' \
'https://api.zbox.filez.com/v3/api/file'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| path | 是 | Body(form) | 要查询的路径 | string |  |
| path_type | 是 | Body(form) | 路径类型: ent:企业空间,self:个人空间 | string |  |
| sort | 否 | Body(form) | 排序方式: asc:正序,desc:倒序 | string | desc |
| order_by | 否 | Body(form) | 排序条件: name:文件名称,size:大小,mtime:更新时间 | string | mtime |
| page_num | 否 | Body(form) | 页码（不可为负数），从第0 页开始 | int32 | 0 |
| page_size | 否 | Body(form) | 每页数量，取值范围（0，999） | int32 | 10 |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "fileModelList":
    [{
        "desc": "",
        "dir": false,
        "modified": "2021-08-13 14:37:51",
        "neid": "1316664166093688899",
        "nsid": "1",
        "path": "/ffff/aa.docx",
        "pathType": "ent",
        "rev": "28dfd82a5aa44e77ae1ed711959afb1f",
        "size": "14.1 KB",
         "creator": "zwpt4",
            "creatorUid": 959,
         "updator": "zwpt4",
            "updatorUid": 959，
         "isTeam":false
        "bookmarkId": 959，
        "supportPreview": true，
      "deliveryCode": "2034f5c3e9ce443da0c7b572f033eb9a"，
      "isBookmark": true
    }],
   "total": 1
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| fileModelList | 文件列表（见单个文件模型） | Array<File> |
| total | 文件数量 | integer (int64) |

单个文件模型（File）结构如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| desc | 文件备注 | string |
| dir | 是否为文件夹 | boolean |
| modified | 最后修改时间 | string |
| neid | 文件id | integer (int64) |
| nsid | 命名空间id | integer (int64) |
| path | 文件路径 | string |
| pathType | 路径类型: ent 企业空间，self 个人空间 | string |
| rev | 文件版本 | string |
| size | 文件大小 | string |
| creator | 创建者 | string |
| creatorUid | 创建者id | string |
| updator | 更新者 | string |
| updatorUid | 更新者id | string |
| isTeam | 是否团队文件夹 | boolean |
| bookmarkId | 收藏id | integer (int64) |
| supportPreview | 是否支持预览 | boolean |
| deliveryCode | 外链码 | string |
| isBookmark | 是否收藏 | boolean |

### 1.2. 查询文件信息

获取指定路径的文件信息。

`POST /v3/api/file/path`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'path=/a' \
-d 'path_type=ent' \
'https://api.zbox.filez.com/v3/api/file/path'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| path | 是 | Body(form) | 路径 | string | / |
| path_type | 是 | Body(form) | 路径类型: ent:企业空间,self:个人空间 | string | self |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "desc": "",
    "dir": false,
    "modified": "2021-08-13 14:37:51",
    "neid": "1316664166093688899",
    "nsid": "1",
    "path": "/ffff/aa.docx",
    "pathType": "ent",
    "rev": "28dfd82a5aa44e77ae1ed711959afb1f",
    "size": "14.1 KB",
    "creator": "zwpt4",
     "creatorUid": 959,
    "updator": "zwpt4",
     "updatorUid": 959,
    "isTeam":false
     "bookmarkId": 959，
     "supportPreview": true，
   "deliveryCode": "2034f5c3e9ce443da0c7b572f033eb9a"，
   "isBookmark": true
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| desc | 文件备注 | string |
| dir | 是否为文件夹 | boolean |
| modified | 最后修改时间 | string |
| neid | 文件id | integer (int64) |
| nsid | 命名空间id | integer (int64) |
| path | 文件路径 | string |
| pathType | 路径类型: ent 企业空间，self 个人空间 | string |
| rev | 文件版本 | string |
| size | 文件大小 | string |
| creator | 创建者 | string |
| creatorUid | 创建者id | string |
| updator | 更新者 | string |
| updatorUid | 更新者id | string |
| isTeam | 是否团队文件夹 | boolean |
| bookmarkId | 收藏id | integer (int64) |
| supportPreview | 是否支持预览 | boolean |
| deliveryCode | 外链码 | string |
| isBookmark | 是否收藏 | boolean |

### 1.3. 通过id 获取文件信息

获取指定Id 的文件信息。

`GET /v3/api/file/{neid}`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
'https://api.zbox.filez.com/v3/api/file/1316664166093688899?nsid=1'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| neid | 是 | Path | 文件id | int64 |  |
| nsid | 是 | Query | 命名空间id | int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "desc": ""
    "dir": false,
    "modified": "2021-08-13 14:37:51",
    "neid": "1316664166093688899",
    "nsid": "1",
    "path": "/ffff/aa.docx",
    "pathType": "ent",
    "rev": "28dfd82a5aa44e77ae1ed711959afb1f",
    "size": "14.1 KB",
    "creator": "zwpt4",
     "creatorUid": 959,
    "updator": "zwpt4",
     "updatorUid": 959，
    "isTeam":false
    "isTeam":false
     "bookmarkId": 959，
     "supportPreview": true，
   "deliveryCode": "2034f5c3e9ce443da0c7b572f033eb9a"，
   "isBookmark": true
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| desc | 文件备注 | string |
| dir | 是否为文件夹 | boolean |
| modified | 最后修改时间 | string |
| neid | 文件id | integer (int64) |
| nsid | 命名空间id | integer (int64) |
| path | 文件路径 | string |
| pathType | 路径类型: ent 企业空间，self 个人空间 | string |
| rev | 文件版本 | string |
| size | 文件大小 | string |
| creator | 创建者 | string |
| creatorUid | 创建者id | string |
| updator | 更新者 | string |
| updatorUid | 更新者id | string |
| isTeam | 是否团队文件夹 | boolean |
| bookmarkId | 收藏id | integer (int64) |
| supportPreview | 是否支持预览 | boolean |
| deliveryCode | 外链码 | string |
| isBookmark | 是否收藏 | boolean |

### 1.4. 查看文件历史版本

查看文件的历史版本。

`GET /v3/api/file/{neid}/revision`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/file/1110024/revision?nsid=1
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| neid | 是 | Path | 文件id | int64 |  |
| nsid | 是 | Query | nsid | int64 |  |

**返回示例：**

```json
{
    "errcode":0,
    "errmsg":"ok",
    "revisionModelList":[
        {
            "op": "create",
            "rev": "8924d086aab24aba93899140e863def9",
            "utime": 1621923054000,
            "version": "v1",
            "isDeleted": false,
            "bytes": 15367,
            "dir": false,
            "modified": "2021-05-25T14:10:54+0800",
            "user": "zwpt44",
            "hash": "5fcf43c58271c18af723f532015891cc",
            "path": "/",
            "root": "databox"
        },
        {
            "op": "update",
            "rev": "ee12a80ff4974869b063b2da40db7455",
            "utime": 1621923077000,
            "version": "v3",
            "isDeleted": false,
            "bytes": 15621,
            "dir": false,
            "modified": "2021-05-25T14:11:18+0800",
            "user": "zwpt44",
            "hash": "f499d9145907cc03fe7b1959ed079610",
            "path": "/",
            "root": "databox"
        },
        {
            "op": "update",
            "rev": "c26a87fd547543db949149819ce7f19d",
            "utime": 1621923798000,
            "version": "v3",
            "isDeleted": false,
            "bytes": 15691,
            "dir": false,
            "modified": "2021-05-25T14:23:18+0800",
            "user": "zwpt44",
            "hash": "eafb20028b274fe0b67a81e8c46426e8"，
            "path": "/",
            "root": "databox"
        }
    ]}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| revisionModelList | 文件历史版本数组。 | Array<Revision> |

单个文件历史版本信息（Revision）结构如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| op | 操作类型。对于一个正常状态的文件，可能的值为"create"或者"delete" | string |
| rev | 历史版本号 | string |
| utime | 历史版本生成的时间戳 | integer (int64) |
| version | 版本名，以v 开头，后面跟随自增的版本号。 | string |
| isDeleted | 是否已被删除 | boolean |
| dir | 是否为文件夹 | boolean |
| bytes | 版本文件的字节大小 | integer (int64) |
| modified | 历史版本生成的时间字符串 | string |
| user | 生成此历史版本的用户名 | string |
| hash | 文件SHA-256 值 | string |
| path | 文件路径 | string |
| root | databox | string |

### 1.5. 上传文件

调用本接口上传文件到指定路径。

`POST /v3/api/file/content`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-F 'filedata=@/tmp/aaa.docx'
-d 'path=/a/b/aaa.docx' \
-d 'path_type=ent' \
'https://api.zbox.filez.com/v3/api/file/content'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为multipart/form-data | string |  |
| path | 是 | Body(form) | 上传路径（全路径，如：/a/b/test.txt） | string |  |
| path_type | 是 | Body(form) | 路径类型: ent:企业空间,self:个人空间 | string | self |
| filedata | 是 | Body(multipart) | 文件本体 | multipartfile |  |

注：path 上传路径为全路径，如路径不存在则自动创建

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "desc": "",
    "dir": false,
    "modified": "2020-10-15T16:56:14+0800",
    "neid": "1316664166093688899",
    "nsid": "1",
    "path": "/ffff/aa.docx",
    "pathType": "ent",
    "rev": "28dfd82a5aa44e77ae1ed711959afb1f",
    "size": "14.1 KB",
    "creator": "zwpt4",
     "creatorUid": 959,
    "updator": "zwpt4",
     "updatorUid": 959
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| desc | 文件备注 | string |
| dir | 是否为文件夹 | boolean |
| modified | 最后修改时间 | string |
| neid | 文件id | integer (int64) |
| nsid | 命名空间id | integer (int64) |
| path | 文件路径 | string |
| pathType | 路径类型: ent 企业空间，self 个人空间 | string |
| rev | 文件版本 | string |
| size | 文件大小 | string |
| creator | 创建者 | string |
| creatorUid | 创建者id | string |
| updator | 更新者 | string |
| updatorUid | 更新者id | string |

### 1.6. 文件分块

为了防止连接意外中断和提供断点续传功能，大文件需要将文件分成若干个小块上传。

一“块”文件大小是4MB。将大文件分块时，应该从头开始，每4MB 数据记录为一个文件块，并计算每一块数据的SHA-256 值作为Hash。最后一块如果不足4MB 也不需要填充。

分块完成后，应该依次调用后续的三个接口。

#### 1.6.1. 获取需上传文件的块Hash 列表

有些文件块可能在网盘中已经存在，那么这些文件块在本次传输中就无需再次传递。

所以文件分块应该将文件块和该块的SHA-256 值的对应关系记录下来，然后调用此接口以获取本次传输需要传递的文件块有哪些。

Hash 在此处特指SHA-256 算法。

`POST /v3/api/file_chunk/need_upload_chunks`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d ' path=/test/a.txt' \
-d ' path_type=ent ' \
-d
'chunk_hashes=%5b%22b2f09e4c62a6e43a2d445759d5f4cf6b16886d9dba68d1be43a
bd6127aeb96d1%22%2c%22d8bf7676c69f0c96d5e15469c70b16bbf696f08670506008
8d138496f7450a51%22%5d' \
https://api.zbox.filez.com/v3/api/file_chunk/need_upload_chunks
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| chunk_hashes | 是 | Body(form) | 块hash 列表，如：["b2f09e4c62a6e43a2d44575 9d5f4cf6b16886d9dba68d1be43abd6127aeb96d1","d8bf 7676c69f0c96d5e15469c70b 16bbf696f086705060088d13 8496f7450a51"] | string (Array< string> ) |  |
| path | 是 | Body(form) | 上传路径（全路径，如：/a/b/test.txt） | string |  |
| path_type | 是 | Body(form) | 路径类型:{ent:企业空间,self:个人空间} | string | self |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "neededBlock":
    [
"b2f09e4c62a6e43a2d445759d5f4cf6b16886d9dba68d1be43abd6127aeb96d1"
    ],
    "uploadId": "f3475aaf68f14b558078cef6e1e2b58e"
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| neededBlock | 需要上传的文件块的SHA-256 值。 | Array<string> |
| uploadId | 上传标记id，相当于文件的“预标识”，在后续上传文件块的操作中会需要用到。 | string |

#### 1.6.2. 上传文件块

该接口用于上传文件块。上传文件块需提供文件块SHA-256 值，文件块本体和之前获取的uploadId。

`POST /v3/api/file_chunk/upload_chunk`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d ' path=/test/a.txt' \
-d ' path_type=ent ' \
-F 'filedata=@/tmp/b2f09e4c.part.1' \
'https://api.zbox.filez.com/v3/api/file_chunk/upload_chunk?chunk_hash=
b2f09e4c62a6e43a2d445759d5f4cf6b16886d9dba68d1be43abd6127aeb96d1&upload
_id= f3475aaf68f14b558078cef6e1e2b58e'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为multipart/form-data | string |  |
| chunk_hash | 是 | Query | 文件块SHA-256 值 | string |  |
| upload_id | 是 | Query | 上传Id,由获取需上传文件的块列表接口返回 | string |  |
| filedata | 是 | Body(multipart ) | 块文件本体 | multipartfile |  |
| path | 是 | Body(form) | 上传路径（全路径，如：/a/b/test.txt） | string |  |
| path_type | 是 | Body(form) | 路径类型:ent:企业空间,self:个人空间 | string | self |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "hash":
"b2f09e4c62a6e43a2d445759d5f4cf6b16886d9dba68d1be43abd6127aeb96d1",
    "status": "success",
    "uploadId": "f3475aaf68f14b558078cef6e1e2b58e",
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| hash | 本次上传的文件块的hash。 | string |
| uploadId | 上传标记id | string |
| status | 状态 | string |

#### 1.6.3. 提交文件上传

该接口用于结束整个分块上传流程。在调用该接口前，请确保所有文件块都已经上传完毕。调用接口需要提供总文件大小，对应文件块的SHA-256 值列表，文件放入网盘的路径以及路径类型。

`POST /v3/api/file_chunk/commit_chunk_upload`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'bytes=9698568'
-d
'chunk_hashes=%5b%22b2f09e4c62a6e43a2d445759d5f4cf6b16886d9dba68d1be43a
bd6127aeb96d1%22%2c%22d8bf7676c69f0c96d5e15469c70b16bbf696f08670506008
8d138496f7450a51%22%5d' \
-d 'path=%2fffff' \
-d 'path_type=ent' \
'https://api.zbox.filez.com/v3/api/file_chunk/commit_chunk_upload'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| bytes | 是 | Body(form) | 整个文件大小 | int64 |  |
| chunk_hashes | 是 | Body(form) | 文件块hash 列表 | stringstring( Array< string> ) |  |
| path | 是 | Body(form) | 上传路径（全路径，如：/a/b/test.txt） | string |  |
| path_type | 是 | Body(form) | 路径类型:{ent:企业空间,self:个人空间} | string | self |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "metadata": {
        "desc": "",
        "dir_type": 8,
        "modified": "2020-12-22T15:31:41+0800",
        "neid": "1341285262826672193",
        "nsid": "1",
        "path": "/test1/filezilla.exe",
        "pathType": "ent",
        "rev": "96b072231724472fb869343dd4515284",
        "size": "9.2 MB"
    },
    "neededBlock": [],
    "uploadId": ""
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| metadata | 上传文件的元数据信息，结构为文件模型 | File |
| uploadId | 上传id | string |
| neededBlock | 需要上传的块 | string |

文件模型（File）的结构如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| desc | 描述 | string |
| dirType | 是否文件夹 | int64 |
| modified | 修改时间 | string(date) |
| neid | 文件id | int64 |
| nsid | 命名空间id | int64 |
| path | 路径 | string |
| pathType | 路径类型 | string |
| rev | 版本号 | string |
| size | 文件大小 | string |

### 1.7. 获取数据中心地址

判断是否能够上传，如果可以上传返回上传数据中心服务器地址。

`POST /v3/api/file/fileops/auth`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d ' path=/a/b' \
-d 'path_type=ent' \
-d 'file_name =a.txt' \
'https://api.zbox.filez.com/v3/api/file/auth_upload'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| path | 是 | Body(form) | 上传路径（全路径，如：/a/b） | string |  |
| path_type | 是 | Body(form) | 路径类型:{ent:企业空间,self:个人空间} | string | self |
| file_name | 是 | Body(form) | 文件名（例如:a.txt） | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "region": "https://qa-t4.vips100.com",
    "session": "74df43417a4c4d3b9f9205b62a4d963a_97_1016_meta",
    "s": "949499DE"
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| region | 数据中心地址 | string |
| session | sessionid | string |
| s | s | string |

### 1.8. 上传文件(调用数据中心方式)

先调用 获取数据中心地址 接口获取到上传地址和session 后，再调用以下接口，需要用获取数据中心地址接口返回的服务器地址作为上传域名（替换请求示例中域名的部分）。

`POST /v2/files/databox/{path}`

**请求示例：**

```bash
curl -X POST "https://qa-
t4.vips100.com/v2/files/databox/123/abcd.txt?overwrite=true&source=file&language
=zh&path_type=ent&S=949499DE" -v -F 'file=@/root/genmd5.sh' -k  --cookie "X-
LENOVO-SESS-ID=3345af0145f44e689aee1fe125d25db6_97_1016_meta"
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 |  | 类型 |  | 默认值 |  |
|---|---|---|---|---|---|---|---|---|
| X-LENOVO-SESS-ID | 是 | Cookie/Query | sessionid |  | string |  |  |  |
| S | 是 | Query | s |  | string |  |  |  |
| Content-Type | 是 | Header | 必须为multipart/form-data |  | string |  |  |  |
| path | 是 | path | 上传路径（全路径，如：/a/b/test.txt） |  | string |  |  |  |
| overwrite | 是 | Query | 是否覆盖原文件 |  | string |  | true |  |
| language | 是 | Query | 语言 |  | string | zh |  |  |
| source | 是 | Query | 来源 |  | string | file |  |  |
| path_type | 是 | Query | 路径类型:{ent:企业空间,self:个人空间} |  | string |  |  |  |
| file | 是 | Body(multipart) | 文件本体 |  | multipartfile |  |  |  |

**返回示例：**

```json
{
 "result": "success",
 "path": "/123/456/abcd.txt",
 "is_dir": false,
 "owner_uid": 1016,
 "modified": "2021-01-20T16:48:59+0800",
 "creator_uid": 1016,
 "neid": 39826,
  "nsid": 1,
 "rev": "f853a6ec52784371a083a9117c4ef500",
 "region_id": 0,
 "path_type": "ent",
 "size": "122.0 bytes",
 "updator_uid": 1016,
 "mime_type": "doc/.txt",
 "bytes": 122,
 "hash": "b55bbca23c3be88174e4d7b193bcbead",
 "desc": ""
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| result | 上传结果 | string |
| path | 上传文件全路径 | string |
| is_dir | 是否是文件夹 | string |
| owner_uid | 归属者用户id | string |
| modified | 上传时间 | string |
| creator_uid | 创建者用户id | string |
| neid | 文件id | string |
| nsid | 命名空间id | string |
| rev | 版本号 | string |
| region_id | 数据中心id | string |
| path_type | 路径类型 | string |
| size | 文件大小 | string |
| updator_uid | 更新者用户id | string |
| mime_type | 文件类型 | string |
| bytes | 字节数 | string |
| hash | 文件hash 值 | string |
| desc | 描述 | string |

### 1.9. 文件分块(调用数据中心方式)

先调用 获取数据中心地址 接口获取数据中心地址，再依次调用以下接口，需要用获取数据中心地址接口返回的服务器地址作为上传域名（替换请求示例中域名的部分）。

#### 1.9.1. 判断文件块

本接口判断用户所上传的文件块是否存在，返回需上传的文件块Hash 信息。

`POST /v2/commit_chunked_upload/commit/databox`

**请求示例：**

```bash
curl -X POST
"https://content.box.lenovo.com/v2/commit_chunked_upload/commit/databox?S=
949499DE" --cookie "X-LENOVO-SESS-ID=5ece72ef009c4abc9df550e17fc8aefc" –
H "Content-Type: application/x-www-form-urlencoded" -d
"hashes[]=2ff71c45f1598223685e34dbae243f5ee294dfe7a1c9b50e4dd4ec887e410
f38&
hashes[]=4ded355d5df7e44eb5e0713cb3fe837834b275af90c8da433f649c9aab64b
411&
hashes[]=41b33dd8cff19718156c74a41d7c278e18e194480681332509e0b297a959
35d3" -vik
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| X-LENOVO-SESS-ID | 是 | Cookie | Sessionid | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| S | 是 | Query | s | string |  |
| hashes[] | 是 | Body(form) | 块hash 列表 | string (Array< string> ) |  |

**返回示例：**

```json
{
    "needed_block":
    [
“2ff71c45f1598223685e34dbae243f5ee294dfe7a1c9b50e4dd4ec887e410f38","41b33dd8cff19718156c74a41d7c278e18e194480681332509e0b297a95935d3"
    ],
    "upload_id": "15c419020e64faf382ae22adfaa82a9b"
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| needed_block | 需要上传的文件块的SHA-256 值。 | Array<string> |
| upload_id | 上传标记id，相当于文件的“预标识”，在后续上传文件块的操作中会需要用到。 | string |

#### 1.9.2. 上传文件块

该接口用于上传文件块。上传数据块需提供文件块SHA-256 值。

`POST /v2/chunked_upload`

**请求示例：**

```bash
curl -X POST
"https://content.box.lenovo.com/v2/chunked_upload?S=949499DE&upload_id=15c41
9020e64faf382ae22adfaa82a9b&hash=2ff71c45f1598223685e34dbae243f5ee294dfe7
a1c9b50e4dd4ec887e410f38&offset=0 " --cookie "X-LENOVO-SESS-
ID=5ece72ef009c4abc9df550e17fc8aefc" -H "Transfer-Encoding: chunked" --data-
binary "@文件全路径" –vi
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| X-LENOVO-SESS-ID | 是 | Cookie | Sessionid | string |  |
| Content-Type | 是 | Header | 必须为multipart/form-data | string |  |
| S | 是 | Query | s | string |  |
| hash | 是 | Query | 文件块SHA-256 值 | string |  |
| upload_id | 是 | Query | 上传Id,由获取需上传文件的块列表接口返回 | string |  |
| offset | 是 | Query | 上传hash 块的偏移量 | string |  |

**返回示例：**

```json
{
    "upload_id":"f83cc28d409ff828d0a25e4de96824b4",
    "status":"success",
"hash":"2ff71c45f1598223685e34dbae243f5ee294dfe7a1c9b50e4dd4ec887e410f38"
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| hash | 本次上传的文件块的hash。 | string |
| upload_id | 上传标记id | string |
| status | 状态 | string |

#### 1.9.3. 提交文件

该接口用于结束整个分块上传流程。在调用该接口前，请确保所有文件块都已经上传完毕。

调用接口需要提供总文件大小，对应文件块的SHA-256 值列表，文件放入网盘的路径以及路径类型。

`POST /v2/commit_chunked_upload/commit/databox/{filepath}`

**请求示例：**

```bash
curl -X POST
"https://content.box.lenovo.com/v2/commit_chunked_upload/commit/databox/a/test.
txt?S=949499DE" --cookie "X-LENOVO-SESS-ID=5ece72ef009c4abc9df550e17fc8aefc"
-H "Content-Type: application/x-www-form-urlencoded"
-d
"path=%2Fa%2Ftest.txt&path_type=self&overwrite=true&parent_rev=&is_file_commit
=true&bytes=9607259&
hashes[]=2ff71c45f1598223685e34dbae243f5ee294dfe7a1c9b50e4dd4ec887e410f3
8&hashes[]=4ded355d5df7e44eb5e0713cb3fe837834b275af90c8da433f649c9aab64b
411&hashes[]=41b33dd8cff19718156c74a41d7c278e18e194480681332509e0b297a95
935d3"
-vi
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| X-LENOVO-SESS-ID | 是 | Cookie | Sessionid | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| filepath | 是 | Path | 上传路径 | string |  |
| S | 是 | Query | s | string |  |
| overwrite | 是 | Body(form) | 是否覆盖 | string |  |
| is_file_commit | 是 | Body(form) | 是否文件提交 | string |  |
| bytes | 是 | Body(form) | 整个文件大小 | int64 |  |
| hashes[] | 是 | Body(form) | 文件块hash 列表 | stringstring( Array< string> ) |  |
| path | 是 | Body(form) | 路径 | string |  |
| path_type | 是 | Body(form) | 路径类型:ent:企业空间,self:个人空间 | string |  |

**返回示例：**

```json
{
    "metadata": {
        "desc": "",
        "dir_type": 8,
        "modified": "2020-12-22T15:31:41+0800",
        "neid": "1341285262826672193",
        "nsid": "1",
        "path": "/test1/filezilla.exe",
        "path_type": "ent",
        "rev": "96b072231724472fb869343dd4515284",
        "size": "9.2 MB"
    },
    "needed_block": [],
    "upload_id": ""
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| metadata | 上传文件的元数据信息，结构为文件模型 | File |
| upload_id | 上传id。 | string |
| needed_block | 需要上传的块。 | string |

文件模型（File）的结构如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| desc | 描述 | string |
| dir_type | 是否文件夹 | int64 |
| modified | 修改时间 | string(date) |
| neid | 文件id | int64 |
| nsid | 命名空间id | int64 |
| path | 路径 | string |
| path_type | 路径类型 | string |
| rev | 版本号 | string |
| size | 文件大小 | string |

### 1.10. 下载文件(文件id)

下载指定id 的文件。

`GET /v3/api/file/content/download`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-O \
'https://api.zbox.filez.com/v3/api/file/content/download?neid=8103&nsid=1'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Range | 否 | Header | 支持byRange 下载格式：bytes=0-4194304 | string |  |
| neid | 是 | Query | 文件id | int64 |  |
| nsid | 是 | Query | 命名空间id | int64 |  |
| rev | 否 | Query | 文件版本，不填则是最新版本 | string |  |

返回为文件流。

### 1.11. 下载文件(文件路径)

下载指定路径的文件。

`POST /v3/api/file/content/download`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'path=%2fffff' \
-d 'path_type = ent' \
'https://api.zbox.filez.com/v3/api/file/content/download'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Range | 否 | Header | 支持byRange 下载格式：bytes=0-4194304 bytes=4194304- | string |  |
| path | 是 | Body(form) | 文件路径（全路径，如：/a/b/test.txt） | string |  |
| path_type | 是 | Body(form) | 路径类型:ent:企业空间,self:个人空间 | string | self |
| rev | 否 | Body(form) | 文件版本，不填则是最新版本 | string |  |

返回为文件流。

### 1.12. 创建文件夹

创建指定路径文件夹。

`POST /v3/api/file/folder`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'path=%2fffff' \
-d 'path_type=ent' \
https://api.zbox.filez.com/v3/api/file/folder
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| path | 是 | Body(form) | 全路径（例如：/a/b/c） | string |  |
| path_type | 是 | Body(form) | 路径类型:ent:企业空间,self:个人空间 | string | self |

注：如果传入的path 的父路径不存在，则系统自动创建

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "desc": "",
   "modified": "2021-08-13 14:37:51",
    "neid": "1316664166093688899",
    "path": "/ffff ",
    "pathType": "ent",
    "rev": "",
    "size": "",
    "creator": "zwpt4",
     "creatorUid": 959,
    "updator": "zwpt4",
     "updatorUid": 959
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| desc | 文件备注 | string |
| modified | 最后修改时间 | string |
| neid | 文件id | integer (int64) |
| path | 文件路径 | string |
| pathType | 路径类型: ent 企业空间，self 个人空间 | string |
| rev | 文件版本 | string |
| size | 文件大小 | string |
| creator | 创建者 | string |
| creatorUid | 创建者id | string |
| updator | 更新者 | string |
| updatorUid | 更新者id | string |

### 1.13. 删除文件

根据文件id 删除文件。

`DELETE /v3/api/file/{neid}`

**请求示例：**

```bash
curl \
-X DELETE \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
'https://api.zbox.filez.com/v3/api/file/1316664166093688899?nsid=1'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| neid | 是 | Path | 文件id | int64 |  |
| nsid | 是 | Query | 命名空间id | int64 |  |
| ignore_share | 否 | Query | 忽略共享删除,为true 时可删除已共享的文件 | boolean | false |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok"
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

### 1.14. 复制文件

将文件复制到指定文件夹下。

`POST /v3/api/file/copy`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'nsid=1' \
-d 'from_neid=1803' \
-d 'to_path=/aaa/' \
-d 'to_path_type=self' \
https://api.zbox.filez.com/v3/api/file/copy
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| nsid | 是 | Body(form) | 命名空间id | int64 |  |
| from_neid | 是 | Body(form) | 文件id | int64 |  |
| to_path | 是 | Body(form) | 复制的目标路径 | string | / |
| to_path_type | 是 | Body(form) | 复制的目录路径类型:ent:企业空间,self:个人空间 | string | self |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "desc": "",
    "dir": false,
    "modified": "2021-08-13 14:37:51",
    "neid": "1316664166093688899",
    "nsid": "1",
    "path": "/ffff/aa.docx",
    "pathType": "ent",
    "rev": "28dfd82a5aa44e77ae1ed711959afb1f",
    "size": "14.1 KB",
    "creator": "zwpt4",
     "creatorUid": 959,
    "updator": "zwpt4",
     "updatorUid": 959,
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| desc | 文件备注 | string |
| modified | 最后修改时间 | string |
| neid | 文件id | integer (int64) |
| path | 文件路径 | string |
| pathType | 路径类型: ent 企业空间，self 个人空间 | string |
| rev | 文件版本 | string |
| size | 文件大小 | string |
| creator | 创建者 | string |
| creatorUid | 创建者id | string |
| updator | 更新者 | string |
| updatorUid | 更新者id | string |
| dir | 是否为文件夹 | boolean |
| nsid | 命名空间id | integer (int64) |

### 1.15. 移动文件

将文件移动到指定文件夹下。

`POST /v3/api/file/move`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'nsid=1' \
-d 'from_neid=1803' \
-d 'to_path=/aaa/' \
-d 'to_path_type=self' \
https://api.zbox.filez.com/v3/api/file/move
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| nsid | 是 | Body(form) | 命名空间id | int64 |  |
| from_neid | 是 | Body(form) | 文件id | int64 |  |
| to_path | 是 | Body(form) | 移动的目标路径 | string | / |
| to_path_type | 是 | Body(form) | 移动的目录路径类型:{ent:企业空间,self:个人空间} | string | self |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok"
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

### 1.16. 重命名文件

重命名文件。

`POST /v3/api/file/rename`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'from_neid=1803' \
-d 'nsid=1' \
-d 'to_file_name=bbb' \
https://api.zbox.filez.com/v3/api/file/rename
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| nsid | 是 | Body(form) | 命名空间id | int64 |  |
| from_neid | 是 | Body(form) | 文件id | int64 |  |
| to_file_name | 是 | Body(form) | 文件名称（需带有文件后缀类型，例如：新名称.txt） | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok"
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

### 1.17. 授权（共享）

#### 1.17.1. 添加修改授权（共享）

将文件或文件夹授权或共享给其他用户或团队，修改对用户或团队的授权或共享。企业空间为授权，个人空间为共享。单次授权的文件不超过20 个，单个文件一次授权的操作不超过20 个。

`POST /v3/api/auth/batch_create`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'nsid=11'＼
-d 'path_type=ent'＼
-d 'file_list=[{\"neid\":159,\"path\":\"/a/d\"},{\"neid\":5632,\"path\":\"/c/b\"}]'＼
-d 'auth_list=
[{\"agentId\":27,\"agentType\":\"team\",\"isSubteamInheritable\":false,\"privilegeType\
":2007}]' \
'https://api.zbox.filez.com/v3/api/auth/batch_create'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| nsid | 是 | Body(form) | 命名空间id | int64 |  |
| path_type | 是 | Body(form) | 文件空间类型（ent 企业空间为授权/self 个人空间为共享） | string |  |
| file_list | 是 | Body(form) | 授权（共享）文件集合，结构详见下方对file_list 的描述 | JSON Array |  |
| auth_list | 是 | Body(form) | 被授权者集合结构详见下方对auth_list 的描述 | JSON Array |  |

file_list：数组。每项结构如下

| neid | 否 | object key | 文件或文件夹id（neid 和path必须传一个） | int64 |  |
|---|---|---|---|---|---|
| path | 否 | object key | 文件或文件夹路径（neid 和path必须传一个） | string |  |

auth_list: 数组。每项结构如下

| agentId | 是 | object key | 被授权（共享）者id（team_id/org_id/user_id），team_id 对应agent_type 为team,org_id 对应的agent_type为org，user_id 对应user，agent_type 为all 时agent_id 不传 | int64 |  |
|---|---|---|---|---|---|
| agentType | 是 | object key | 被授权（共享）者类型（team/org/user/all），all 表示授权（共享）给所有用户 | string |  |
| privilegeType | 是 | object key | 预览: 2009上传: 2007下载: 2005上传/下载: 2003编辑: 2001可见列表: 1011禁止访问: 1000 | int32 |  |
| isSubteamInheritable | 否 | object key | 是否可继承（true 可继承，false不可继承，agent_type 为all 时一定为false） | Boolean | false |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
     authModelList:[]
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| authModelList | 创建授权列表 | List<> |

#### 1.17.2. 取消授权（共享）

取消文件或文件夹给其他用户或团队的授权或共享。企业空间为授权，个人空间为共享。

`DELETE /v3/api/auth/batch_delete`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'nsid=11'＼
-d 'path_type=ent'＼
-d 'file_list=[{\"neid\":159,\"path\":\"/a/d\"},{\"neid\":5632,\"path\":\"/c/b\"}]'＼
-d 'delete_list=
[{\"agentId\":27,\"agentType\":\"team\"},{\"agentId\":58,\"agentType\":\"user\"}]' \
'https://api.zbox.filez.com/v3/api/auth/batch_delete'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| nsid | 是 | Body(form) | 命名空间id | int64 |  |
| path_type | 是 | Body(form) | 文件空间类型（ent 企业空间为授权/self 个人空间为共享） | string |  |
| file_list | 是 | Body(form) | 授权（共享）文件集合 | JSONArray |  |
| delete_list | 否 | Body(form) | 被取消授权者集合 | JSONArray |  |
| delete_all_auth | 否 | Body(form) | 取消所有授权或共享(为true时，delete_list 无效) | boolean | false |

file_list：数组。每项结构如下

| neid | 否 | object key | 文件或文件夹id（neid 和path必须传一个） | int64 |  |
|---|---|---|---|---|---|
| path | 否 | object key | 文件或文件夹路径（neid 和path必须传一个） | string |  |

delete_list：数组。每项结构如下

| agentId | 是 | object key | 被取消授权（共享）者id（team_id/org_id/user_id），team_id 对应agent_type 为team,org_id 对应的agent_type 为org，user_id 对应user，agent_type 为all 时agent_id 不传 | int64 |  |
|---|---|---|---|---|---|
| agentType | 是 | object key | 被取消授权（共享）者类型（team/org/user/all），all 表示授权（共享）给所有用户 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "resultList": [
      {
          "path": "/a",
          "result": "succeed"
          "errmsg": "ok"
       },
      {
         "path": "/b",
         "result": "succeed"
         "errmsg": "ok"
      }
    ]
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok注意：此接口是非事务性接口，对传入参数的每一个文件都可能独立失败。 | string |
| resultList | 取消授权结果 | List<authDeleteModel> |

authDeleteModel:

| 参数 | 说明 | 格式 |
|---|---|---|
| path | 授权（共享）文件路径 | string |
| result | 取消授权结果，succeed 成功，fail 失败。 | string |
| errmsg | 对result 的描述信息 | string |

#### 1.17.3. 获取授权（共享）列表

获取文件或文件夹的授权或分享列表。企业空间为授权，个人空间为共享。

`POST /v3/api/auth/list`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'nsid=11' \
-d 'path_type=ent' \
-d 'file_list=[{\"neid\":159,\"path\":\"/a\"},{\"neid\":5632,\"path\":\"/b\"}]' \
'https://api.zbox.filez.com/v3/api/auth/list'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| nsid | 是 | Body(form) | 命名空间id | int64 |  |
| file_list | 是 | Body(form) | 文件或文件夹集合 | JSON Array |  |
| path_type | 是 | Body(form) | 文件空间类型（ent 企业空间为授权/self 个人空间为共享） | string |  |

file_list：数组。每项结构如下

| neid | 否 | object key | 文件或文件夹id（neid 和path必须传一个） | int64 |  |
|---|---|---|---|---|---|
| path | 否 | object key | 文件或文件夹路径（neid 和path必须传一个） | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "authFileList":[
        {
        "path":"/a",
        "authList":[
             {
               "privilegeId": 3002,
              "agentId": 23,
              "agentName": "演示一级",
              "allowed_mask": "3130",
              "isTeam": false,
              "agentType": "team",
              "path": "/a",
              "nsid": 1,
              "isSubteamInheritable": false,
              "id": 54138,
              "privilegeName": "upload"
            }
      ],
      "inheritAuthList": [
                {
                    "agentId": 155,
                    "agentName": "test1",
                    "agentType": "team",
                    "effective": true,
                    "privilegeId": 2009,
                    "privilegeName": "preview"
                }
         ],
      },
     {
      "path":"/b",
      "authList":[
          {
            "privilegeId": 3002,
            "agentId": 22,
            "agentName": "演示二级",
            "allowed_mask": "3130",
            "isTeam": false,
            "agentType": "team",
            "path": "/b",
            "nsid": 1,
            "isSubteamInheritable": false,
            "id": 54139,
            "privilegeName": "upload"
        }
     ],
     "inheritAuthList": [],
   }
  ]
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| authFileList | 获取授权的文件列表 | List<authFileModel> |

authFileModel:

| 参数 | 说明 | 格式 |
|---|---|---|
| path | 路径 | string |
| authList | 文件的授权（共享）列表 | List<authListModel > |
| inheritAuthList | 文件继承上级的授权（共享）列表 | List<inheritAuthListModel> |

authListModel :

| 参数 | 说明 | 格式 |
|---|---|---|
| privilegeId | 授权码 | int64 |
| agentId | 被授权（共享）者Id | int64 |
| agentName | 被共授权（共享）name | string |
| allowedMask | 授权掩码 | int32 |
| path | 路径 | string |
| agentType | 被共享者类型（team/user/all） | string |
| nsid | 命名空间id | int64 |
| isSubteamInheritable | 是否可继承 | Boolean |
| id | 授权Id（auth_id） | int32 |
| privilegeName | 授权名称 | string |
| isTeam | 是否团队 | Boolean |

inheritAuthListModel:

| 参数 | 说明 | 格式 |
|---|---|---|
| privilegeId | 授权码 | int64 |
| agentId | 被授权（共享）者Id | int64 |
| agentName | 被共授权（共享）name | string |
| agentType | 被共享者类型（team/user/all） | string |
| privilegeName | 授权名称 | string |
| effective | 是否有效，继承自上级的权限被子文件修改时，继承的权限无效，以子文件的授权为准。 | Boolean |

### 1.18. 在线编辑

获取文档类型文件（如word,ppt,excel 等）在线编辑的地址。

`GET /v3/api/file/edit`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
'https://api.zbox.filez.com/v3/api/file/edit?neid=1315179418984&nsid=1'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| neid | 否 | Query | 文件id。neid 与nsid，path和path_type 至少选择一组填写。如果都填，则优先使用neid 与nsid。 | int64 |  |
| nsid | 否 | Query | 命名空间id | int64 |  |
| path | 否 | Query | 文件路径 | string |  |
| path_type | 否 | Query | 路径类型 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "editUrl": "http://..."
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| editUrl | 文件在线编辑地址。 | string |

### 1.19. 收藏

#### 1.19.1. 收藏文件

收藏文件或文件夹到我的收藏里。

`POST /v3/api/bookmark/create`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
‘https://api.zbox.filez.com/v3/api/bookmark/create?neid=11&nsid=11&path=/a/b&
path_type=ent’
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| neid | 否 | Query | 文件或文件夹id(neid 或path 必传一个) | Int64 |  |
| nsid | 否 | Query | 命名空间id(传neid 时必须) | Int64 |  |
| path | 否 | Query | 文件或文件夹路径(neid 或path必传一个) | String |  |
| path_type | 否 | Query | 文件空间类型（传path 时必须） | String |  |

注：在neid、nsid 和path、path_type 两组数据同时存在时，参数以neid 和nsid 优先。

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "bookmarkId": 611,
    "neid": "1375039638590197790"
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| neid | 文件或文件夹id | int64 |
| bookmarkId | 收藏书签的id | Int64 |

#### 1.19.2. 取消收藏

取消对文件或文件将夹的收藏。

`POST /v3/api/bookmark/delete`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
‘https://api.zbox.filez.com/v3/api/bookmark/delete?neid=145&bookmark_id=454
’
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| neid | 是 | Query | 文件或文件夹id | Int64 |  |
| bookmark_id | 是 | Query | 收藏书签的id | Int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

#### 1.19.3. 获取收藏列表

获取我的收藏列表。

`GET /v3/api/bookmark/list`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
‘https://api.zbox.filez.com/v3/api/bookmark/list?Page=0&number=5’
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| page_num | 否 | Query | 页码（不可为负数，从0 开始） | int32 | 0 |
| page_size | 否 | Query | 每页数量，取值范围（0，999） | int32 | 10 |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "hasMore": true,
    "content": [
        {
             "bookmarkId": 611,
             "rev": "28dfd82a5aa44e77ae1ed711959afb1f",
             "size": "14.1 KB",
            "desc": "",
            "path": "/支持预览的文件格式1/预览示例.ai",
            "nsid": 5310,
            "dir": false,
            "neid": 46357,
            "pathType": "ent",
            "modified": "2020-10-15T16:56:14+0800",
            "creator": "zwpt4",
             "creatorUid": 959,
            "updator": "zwpt4",
            "updatorUid": 959,
            "isDeleted": true,
        }
    ]
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| hasMore | 是否还有下一页（true 有下一页/false 没有下一页） | Boolean |
| content | 收藏文件List | List<JsonArray> |

收藏文件返回BookMarkMode:

| 参数 | 说明 | 格式 |
|---|---|---|
| dir | 是否为文件夹 | boolean |
| modified | 最后修改时间 | string |
| neid | 文件id | integer (int64) |
| nsid | 命名空间id | integer (int64) |
| path | 文件路径 | string |
| pathType | 路径类型: ent 企业空间，self 个人空间 | string |
| size | 文件大小 | string |
| creator | 创建者 | string |
| creatorUid | 创建者id | string |
| updator | 更新者 | string |
| updatorUid | 更新者id | string |
| rev | 文件版本 | string |
| desc | 文件备注 | string |
| bookmarkId | 收藏书签的id | Int64 |
| isDeleted | 是否已被删除 | boolean |

### 1.20. 文件搜索

搜索文件。此接口为模糊搜索。

`GET /v3/api/file/search`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
'https://api.zbox.filez.com/v3/api/file/search?query=111&neid=1000315&nsid=1&pat
h_type=ent'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| query | 是 | Query | 查询关键字 | string |  |
| limit | 否 | Query | 搜索结果限制数量。最大可填写100 | Integer | 30 |
| offset | 否 | Query | 查询条目起始索引。参考下方返回结构的nextIndex 字段说明 | Integer | 0 |
| neid | 否 | Query | 查询的起始位置文件夹id | Int64 |  |
| nsid | 否 | Query | 查询起始位置文件夹的nsid。若指定此项，则path_type 可能被忽略。 | Int64 |  |
| path | 否 | Query | 查询起始位置的路径，如果neid被指定，则此项被忽略。neid 与path 至少必填一项。 | string |  |
| path_type | 否 | Query | 可选"ent"或"self"，表示企业空间和个人空间。 | string |  |
| type | 否 | Query | 文件类型，多个之间用逗号分隔可选项包含：word （word 文件）excel（excel 文件）folder （文件夹）powerpoint（幻灯片）pdf（pdf 文件）pic（图片）video（视频）audio（音频）other（其他）若此项为空，则为全部类型。 | string | "" |
| time_start | 否 | Query | 要搜索文件的创建时间大于或等于示例：2021-04-13 15:13:03 | string |  |
| time_end | 否 | Query | 要搜索文件的创建时间小于或等于示例：2021-04-13 15:13:10 | string |  |
| size_start | 否 | Query | 要搜索文件的大小不小于：（单位MB） | int32 |  |
| size_end | 否 | Query | 要搜索文件的大小不大于：（单位MB） | int32 |  |
| search_mode | 否 | Query | 可选“name”，“tag”或者“fulltext”，分别表示按文件名搜索，按标签搜索和全文搜索（文件内容搜索）。 | string | name |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "fileModelList":
    [{
        "desc": "",
        "modified": "2021-08-13 14:37:51",
        "neid": "1316664166093688899",
        "nsid": "1",
        "path": "/ffff/aa.docx",
        "pathType": "ent",
        "rev": "28dfd82a5aa44e77ae1ed711959afb1f",
        "size": "14.1 KB",
        "creator": "zwpt4",
           "creatorUid": 959,
        "updator": "zwpt4",
           "updatorUid": 959,
        "dir": false,
        "supportPreview": true,
        "deliveryCode": ""
    }],
   "hasMore": false
   "nextIndex":1
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| fileModelList | 文件列表（见单个文件模型） | Array<File> |
| hasMore | 是否还有更多结果。如果为true，则说明仍有结果未显示，可以传入offset 继续搜索。 | boolean |
| nextIndex | 当前条件下，下一条搜索结果的起始索引。如果想继续搜索，则应传递相同的搜索条件，并把offset 置为此值。 | int32 |

单个文件模型（File）结构如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| desc | 注意：搜索接口返回描述信息为空 | string |
| dir | 是否为文件夹 | boolean |
| modified | 最后修改时间 | string |
| neid | 文件id | integer (int64) |
| nsid | 命名空间id | integer (int64) |
| path | 文件路径 | string |
| pathType | 路径类型: ent 企业空间，self 个人空间 | string |
| rev | 文件版本 | string |
| size | 文件大小 | string |
| creator | 创建者 | string |
| creatorUid | 创建者id | string |
| updator | 更新者 | string |
| updatorUid | 更新者id | string |
| dir | 是否为文件夹 | boolean |
| supportPreview | 是否支持预览 | boolean |
| deliveryCode | 外链码 | string |

### 1.21. 标签

#### 1.21.1. 新增标签

给一个文件打标签。标签为增量修改。

`POST /v3/api/file/{neid}/tag`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'tags=aaa' \
-d 'tags=bbb' \
-d 'nsid=1' \
https://api.zbox.filez.com/v3/api/file/1110024/tag
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| neid | 是 | Path | 文件id | int64 |  |
| nsid | 是 | Body(form) | nsid | int64 |  |
| tags | 是 | Body(form) | 多值参数。可填入多个tag，中间用逗号隔开，如上方示例所示。 | string [] |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "tags":[
        {
            "name":"aaa"
        },{
            "name":"bbb"
        }
    ]
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| tags | 标签数组，表示当前文件已有的全部标签。数组内容为json 对象，对象的name 属性表示标签名称。 | Array |

#### 1.21.2. 查看文件标签

查看文件已有的标签。

`GET /v3/api/file/{neid}/tag`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/file/1110024/tag?nsid=1
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| neid | 是 | Path | 文件id | int64 |  |
| nsid | 是 | Query | nsid | int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "tags":[
        {
            "name":"aaa"
        },{
            "name":"bbb"
        }
    ]
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| tags | 标签数组，数组内容为json 对象，对象的name 属性表示标签名称。 | Array |

#### 1.21.3. 删除标签

给一个文件删除标签。

`DELETE /v3/api/file/{neid}/tag`

**请求示例：**

```bash
curl \
-X DELETE
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
'https://api.zbox.filez.com/v3/api/file/11354535/tag?tags=aaa&tags=bbb&nsid=1'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| neid | 是 | Path | 文件id | int64 |  |
| nsid | 是 | Body(form) | nsid | int64 |  |
| tags | 是 | Body(form) | 多值参数。可填入多个tag，如上方示例所示。 | string [] |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "tags":[
        {
            "name":"ccc"
        },{
            "name":"ddd"
        }
    ]
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| tags | 标签数组，表示删除后仍然剩余的标签。数组内容为json 对象，对象的name 属性表示标签名称。 | Array |

## 2. 外链

### 2.1. 创建或更新外链

创建或更新外链，更新外链时需要传入外链code。

`POST /v3/api/delivery`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'expiration=-1' \
-d 'is_checked_watermark=true' \
-d 'mode=rwp' \
-d 'neid=1803' \
-d 'nsid=1' \
-d 'password=123456' \
https://api.zbox.filez.com/v3/api/delivery
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有对指定文件有权访问的用户身份申请的token 才能调用此接口。 | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| expiration | 否 | Body(form) | 过期值:{格式YYYY-MM-DD -1:表示不过期/网盘管理控制台- | string |  |
|  |  |  | 安全策略-链接安全管控中链接最长有效期时间} |  |  |
| is_checked_watermark | 否 | Body(form) | 是否开启水印 | boolean | false |
| mode | 是 | Body(form) | 访问权限:{r:允许下载,w:允许上传,p:允许预览, 三种权限可以组合} | string |  |
| nsid | 是 | Body(form) | 命名空间id | int64 |  |
| neid | 是 | Body(form) | 文件id | int64 |  |
| name | 否 | Body(form) | 外链名称。不填则会被重置为默认值。（默认值可能随网盘版本而不同） | string | YYYY-MM-DD HH:mm:ss 创建的链接 |
| password | 否 | Body(form) | 访问外链需要的密码 | string |  |
| code | 否 | Body(form) | 外链code（更新外链时传入） | string |  |
| is_login_verify | 否 | Body(form) | 登录认证 | boolean |  |
| is_snapshot | 否 | Body(form) | 文件快照（创建文件夹外链不可传入该参数） | boolean | false |
| limited_download | 否 | Body(form) | 可下载次数（创建文件夹外链不可传入该参数） | int64 | -1 |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "access_mode": 4095,
    "code": "2034f5c3e9ce443da0c7b572f033eb9a",
    "counterDownload": 0,
    "counterPreview": 0,
    "counterUpload": 0,
    "ctime": "2020-12-21T15:46:05+0800",
    "description": "",
    "expiration": -1,
    "hasPassword": true,
    "id": 1,
    "limitedDownload": -1,
    "mimeType": "other/",
    "mode": "rwp",
    "mtime": "2020-12-21T15:46:05+0800",
    "name": "2020-12-21 15:46 新建的安全链接",
    "neid": "1315179418984910876",
    "nsid": 1,
    "password": "cjmws",
    "path": "/test1",
    "pathType":"ent",
    "root": "databox",
    "type": "dir",
    "url": "http://172.16.52.151/l/AFKmY2"
}
```

**返回内容：**

返回内容为外链模型。

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| accessMode | 权限 | integer (int64) |
| code | 长链码 | string |
| counterDownload | 下载地址 | integer (int64) |
| counterPreview | 预览次数 | integer (int64) |
| counterUpload | 上传次数 | integer (int64) |
| ctime | 创建时间 | string |
| description | 外链描述 | string |
| expiration | 过期时间 | integer (int64) |
| hasPassword | 是否输入密码Default : false | boolean |
| id | 主键 | integer (int64) |
| limitedDownload | 下载次数限制 | integer (int64) |
| mimeType | 文件类型 | string |
| mode | 权限列表 | string |
| mtime | 修改时间 | string |
| name | 外链默认名称 | string |
| neid | neid | integer (int64) |
| nsid | nsid | integer (int64) |
| password | 密码 | string |
| path | 外链路径 | string |
| pathType | 路径类型 | string |
| root | databox | string |
| type | 类型 | string |
| url | 打开地址 | string |

### 2.2. 删除外链

根据外链code 删除外链。

`DELETE /v3/api/delivery`

**请求示例：**

```bash
curl \
-X DELETE \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/delivery?code=2034f5c3e9ce443da0c7b572f033eb9a
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有外链创建者的用户身份申请的token 才能调用此接口。 | string |  |
| code | 是 | Query | 创建外链时返回的code 字段 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok"
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

### 2.3. 获取外链信息

根据code 获取外链信息。

`GET /v3/api/delivery/{code}`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/delivery/2034f5c3e9ce443da0c7b572f033eb9a
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| code | 是 | Path | 外链码 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "access_mode": 4095,
    "code": "2034f5c3e9ce443da0c7b572f033eb9a",
    "counterDownload": 0,
    "counterPreview": 0,
    "counterUpload": 0,
    "ctime": "2020-12-21T15:46:05+0800",
    "description": "",
    "expiration": -1,
    "hasPassword": true,
    "id": 1,
    "limitedDownload": -1,
    "mimeType": "other/",
    "mode": "rwp",
    "mtime": "2020-12-21T15:46:05+0800",
    "name": "2020-12-21 15:46 新建的安全链接",
    "neid": "1315179418984910876",
    "nsid": 1,
    "password": "cjmws",
    "path": "/test1",
    "pathType":"ent",
    "root": "databox",
    "type": "dir",
    "url": "http://172.16.52.151/l/AFKmY2"
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| accessMode | 权限 | integer (int64) |
| code | 长链码 | string |
| counterDownload | 下载地址 | integer (int64) |
| counterPreview | 预览次数 | integer (int64) |
| counterUpload | 上传次数 | integer (int64) |
| ctime | 创建时间 | string |
| description | 外链描述 | string |
| expiration | 过期时间 | integer |
|  |  | (int64) |
| hasPassword | 是否输入密码Default : false | boolean |
| id | 主键 | integer (int64) |
| limitedDownload | 下载次数限制 | integer (int64) |
| mimeType | 文件类型 | string |
| mode | 权限列表 | string |
| mtime | 修改时间 | string |
| name | 外链默认名称 | string |
| neid | neid | integer (int64) |
| nsid | nsid | integer (int64) |
| password | 密码 | string |
| path | 外链路径 | string |
| pathType | 路径类型 | string |
| root | databox | string |
| type | 类型 | string |
| url | 打开地址 | string |

### 2.4. 获取外链列表（本次不提供）

根据文件id 获取已创建的所有外链信息。

`GET /v3/api/delivery`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/delivery?neid=1803
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| neid | 是 | Query | 文件id | int64 |  |
| nsid | 是 | Query | 空间id | int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "deliveryModelList":[{
        "access_mode": 4095,
        "code": "2034f5c3e9ce443da0c7b572f033eb9a",
        "counterDownload": 0,
        "counterPreview": 0,
        "counterUpload": 0,
        "ctime": "2020-12-21T15:46:05+0800",
        "description": "",
        "expiration": -1,
        "hasPassword": true,
        "id": 1,
        "limitedDownload": -1,
        "mimeType": "other/",
        "mode": "rwp",
        "mtime": "2020-12-21T15:46:05+0800",
        "name": "2020-12-21 15:46 新建的安全链接",
        "neid": "1315179418984910876",
        "nsid": 1,
        "password": "cjmws",
        "path": "/test1",
        "pathType": "ent",
        "root": "databox",
        "type": "dir",
        "url": "http://172.16.52.151/l/AFKmY2"
    }]
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| deliveryModelList | 外链信息列表。其中每一项都为外链模型。 | Array<DeliveryModel> |

单个外链模型的定义如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| accessMode | 权限 | integer (int64) |
| code | 长链码 | string |
| counterDownload | 下载地址 | integer (int64) |
| counterPreview | 预览次数 | integer (int64) |
| counterUpload | 上传次数 | integer (int64) |
| ctime | 创建时间 | string |
| description | 外链描述 | string |
| expiration | 过期时间 | integer (int64) |
| hasPassword | 是否输入密码Default : false | boolean |
| id | 主键 | integer (int64) |
| limitedDownload | 下载次数限制 | integer (int64) |
| mimeType | 文件类型 | string |
| mode | 权限列表 | string |
| mtime | 修改时间 | string |
| name | 外链默认名称 | string |
| neid | neid | integer (int64) |
| nsid | nsid | integer (int64) |
| password | 密码 | string |
| path | 外链路径 | string |
| pathType | 路径类型 | string |
| root | databox | string |
| type | 类型 | string |
| url | 打开地址 | string |

## 3. 团队

### 3.1. 创建团队

创建一个新团队。

`POST /v3/api/team`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'description=测试团队' \
-d 'member_limit=100' \
-d 'name=/aaa' \
-d 'quota=104857600' \
-d 'region_id=1' \
https://api.zbox.filez.com/v3/api/team
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| description | 否 | Body(form) | 团队描述 | string |  |
| member_limit | 否 | Body(form) | 团队人数上限（不控制子团队） | int32 |  |
| name | 是 | Body(form) | 团队名称，如/aaa | string |  |
| quota | 否 | Body(form) | 团队空间大小，单位Bytes（必须为1048576 的倍数） | int64 |  |
| region_id | 否 | Body(form) | 数据中心id | string |  |

注：member_limit，quota 传空则默认取网盘-管理控制台-网盘设置-账户默认设置中团队设置值，region_id 为空则在默认数据中心创建。

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "description": "测试团队",
    "id": 1,
    "memberLimit": 100,
    "name": "/aaa",
    "quota": 104857600,
    "region_id": "1"，
    "used": "0”
}
```

**返回内容：**

返回内容为团队模型。

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| description | 团队描述 | string |
| id | 团队id | int64 |
| member_limit | 团队人数上限 | string |
| path | 团队路径，如/aaa | string |
| quota | 团队空间大小，单位：Bytes | int64 |
| region_id | 数据中心id | int64 |
| used | 团队已使用空间大小。单位：Bytes | int64 |

### 3.2. 获取团队列表

根据团队id 获取子团队列表信息。

`GET /v3/api/team`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
'https://api.zbox.filez.com/v3/api/team?team_id=1'
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string | / |
| team_id | 否 | Query | 团队id | string |  |

注：不传入team_id 则获取顶级团队，传入team_id 则获取该团队下的子团队列表。

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "total": 1,
    "teamList":
    [{
        "description": "测试团队",
        "id": 1,
        "memberLimit": 100,
        "name": "/aaa",
        "quota": 104857600,
        "used": 0
    }]
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| total | 结果数量 | int |
| teamList | 团队数组。 | Array<Team> |

Team 模型如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| description | 团队描述 | string |
| id | 团队id | int64 |
| member_limit | 团队人数上限 | string |
| path | 团队路径，如/aaa | string |
| quota | 团队空间大小，单位：Bytes | int64 |
| used | 团队已使用空间大小。单位：Bytes | int64 |

### 3.3. 获取团队信息

根据团队id 获取团队信息。

`GET /v3/api/team/{id}`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/team/1
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| id | 是 | Path | 团队id | int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "description": "测试团队",
    "id": 1,
    "memberLimit": 100,
    "name": "/aaa",
    "quota": 104857600,
    "region_id": "1",
    "used": "0"
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| description | 团队描述 | string |
| id | 团队id | int64 |
| member_limit | 团队人数上限 | string |
| path | 团队路径，如/aaa | string |
| quota | 团队空间大小，单位：Bytes | int64 |
| region_id | 数据中心id | int64 |
| used | 团队已使用空间大小。单位：Bytes | int64 |

### 3.4. 更新团队信息

根据团队id 更新团队信息。

`PUT /v3/api/team/{id}`

**请求示例：**

```bash
curl \
-X PUT \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'description=%e6%b5%8b%e8%af%95%e5%9b%a2%e9%98%9f' \
-d 'member_limit=100' \
-d 'name=%2faaa1' \
-d 'quota=104857600' \
-d 'region_id=1' \
https://api.zbox.filez.com/api/v3/team/1
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| id | 是 | Path | 团队id | string |  |
| description | 否 | Body(form) | 团队描述 | string |  |
| member_limit | 否 | Body(form) | 团队人数上限（不控制子团队，必须大于团队已有人数） | int32 |  |
| name | 否 | Body(form) | 团队名称，如：bbb 修改团队名称时不能带“/”或其他特殊字符 | string |  |
| quota | 否 | Body(form) | 团队空间大小，单位Bytes（必须为1048576 的倍数，必须大于已使用的空间） | int64 |  |
| region_id | 否 | Body(form) | 数据中心id | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "description": "测试团队",
    "id": 1,
    "memberLimit": 100,
    "name": "/aaa1",
    "quota": 104857600,
    "region_id": "1",
    "used": "0"
}
```

**返回内容：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| description | 团队描述 | string |
| id | 团队id | int64 |
| member_limit | 团队人数上限 | string |
| path | 团队路径，如/aaa | string |
| quota | 团队空间大小，单位：Bytes | int64 |
| region_id | 数据中心id | int64 |
| used | 团队已使用空间大小。单位：Bytes | int64 |

### 3.5. 删除团队

根据团队id 删除团队。

`DELETE /v3/api/team/{id}`

**请求示例：**

```bash
curl \
-X DELETE \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/team/1?pass=aaaaaa
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| id | 是 | Path | 要删除的团队id | string |  |
| pass | 是 | Query | 当前用户身份密码。删除团队操作需要二次校验，需要输入密码。 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok"
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

## 4. 用户

### 4.1. 创建用户

创建一个新用户。

`POST /v3/api/user`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'email=zhang@123.com' \
-d 'mobile=13800000000' \
-d 'password=aaaaaaa' \
-d 'quota=104857600' \
-d 'status=1' \
-d 'user_name=张三' \
-d 'user_slug=zhangsan' \
https://api.zbox.filez.com/v3/api/user
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
|  |  |  | 使用具有管理员的用户身份申请的token 才能调用此接口。 |  |  |
| email | 是 | Body(form) | 邮箱 | string |  |
| mobile | 否 | Body(form) | 手机号 | string | null |
| password | 否 | Body(form) | 密码 | string |  |
| quota | 否 | Body(form) | 用户个人空间大小,单位Bytes | int64 |  |
| status | 否 | Body(form) | 用户状态:{冻结 :-1,激活:1} | int32 | 1 |
| user_name | 是 | Body(form) | 用户姓名 | string |  |
| user_slug | 是 | Body(form) | 登录名 | string |  |

注：

1、quota 传空则默认取网盘-管理控制台-网盘设置-账户默认设置中用户默认设置值。

**返回示例：**

以下结构记为用户模型（User）。

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "id": 1026,
    "userSlug": "zhangsan",
    "userName": "张三",
    "email": "zhang@123.com",
    "mobile": "13800000000",
    "status": 1,
    "quota": 104857600,
    "used": 0
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| email | 邮箱 | string |
| id | 用户id。该项是用户身份的不可变标识，创建用户后应该妥善保存该字段用于后续的修改操作。 | integer (int64) |
| mobile | 手机号 | string |
| password | 密码 | string |
| quota | 用户个人空间大小（单位：Bytes） | integer (int64) |
| status | 用户状态：冻结-1、未激活0、已激活1、过期-2、已删除-3 | integer (int32) |
| used | 用户已使用个人空间大小（单位：Bytes） | integer (int64) |
| userName | 用户姓名 | string |
| userSlug | 登录名 | string |

### 4.2. 获取用户列表

分页获取用户信息。

`GET /v3/api/user`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
'https://api.zbox.filez.com/v3/api/user?key=zhang%40123.com&page_num=0&
page_size=10 '
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| key | 否 | Query | 查询条件。可为登录名，用户姓名或者邮箱片段。 | string |  |
| page_num | 否 | Query | 页码,从第0 页开始 | int32 | 0 |
| page_size | 否 | Query | 每页数量，取值范围（0，1000） | int32 | 10 |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "total": 1,
    "userList":
    [{
        "id": 1026,
        "userSlug": "zhangsan",
        "userName":"张三",
        "email": "zhang@123.com",
        "mobile": "13800000000",
        "status": 1,
        "quota": 104857600,
        "used": 115200
    }]
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| total | 结果数量 | int |
| userList | 用户数组。 | Array<User> |

User 模型如下：

| 参数 | 说明 | 格式 |
|---|---|---|
| email | 邮箱 | string |
| id | 用户id。该项是用户身份的不可变标识，创建用户后应该妥善保存该字段用于后续的修改操作。 | integer (int64) |
| mobile | 手机号 | string |
| password | 密码 | string |
| quota | 用户个人空间大小（单位：Bytes） | integer (int64) |
| status | 用户状态：冻结-1、未激活0、已激活1、过期-2、已删除-3 | integer (int32) |
| used | 用户已使用个人空间大小（单位：Bytes） | integer (int64) |
| userName | 用户姓名 | string |
| userSlug | 登录名 | string |

### 4.3. 获取用户信息

根据用户id 获取用户信息。

`GET /v3/api/user/{id}`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/user/1
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
|  |  |  | 或者，不具备管理员权限的用户也可以输入自己的uid 调用。 |  |  |
| id | 是 | Path | 用户id | int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "id": 1,
    "userSlug": "zhangsan",
    "userName": "张三",
    "email": "zhang@123.com",
    "mobile": "13800000000",
    "status": 1,
    "quota": 104857600,
    "used": 115200
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| email | 邮箱 | string |
| id | 用户id。该项是用户身份的不可变标识，创建用户后应该妥善保存该字段用于后续的修改操作。 | integer (int64) |
| mobile | 手机号 | string |
| password | 密码 | string |
| quota | 用户个人空间大小（单位：Bytes） | integer (int64) |
| status | 用户状态：冻结-1、未激活0、已激活1、过期-2、已删除-3 | integer (int32) |
| used | 用户已使用个人空间大小（单位：Bytes） | integer (int64) |
| userName | 用户姓名 | string |
| userSlug | 登录名 | string |

### 4.4. 更新用户信息

根据用户id 更新用户信息。

`PUT /v3/api/user/{id}`

**请求示例：**

```bash
curl \
-X PUT \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'email=zhang%40123.com' \
-d 'mobile=13800000000' \
-d 'password=aaaaaaa' \
-d 'quota=104857600' \
-d 'status=1' \
-d 'user_name=%e5%bc%a0%e4%b8%89' \
-d 'user_slug=zhangsan' \
https://api.zbox.filez.com/v3/api/user/1
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。或者，不具备管理员权限的用户也可以输入自己的uid 调用。 | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| id | 是 | Path | 用户id | int64 | / |
| email | 否 | Body(form) | 邮箱 | string |  |
| mobile | 否 | Body(form) | 手机号 | string |  |
| password | 否 | Body(form) | 密码 | string |  |
| quota | 否 | Body(form) | 用户个人空间大小，单位Bytes,修改的空间必须大于已使用的空间。 | int64 |  |
| user_name | 否 | Body(form) | 用户姓名 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "id": 1,
    "userSlug": "zhangsan",
    "userName": "张三",
    "email": "zhang@123.com",
    "mobile": "13800000000",
    "status": 1,
    "quota": 104857600,
    "used": 115200
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| email | 邮箱 | string |
| id | 用户id。该项是用户身份的不可变标识，创建用户后应该妥善保存该字段用于后续的修改操作。 | integer (int64) |
| mobile | 手机号 | string |
| password | 密码 | string |
| quota | 用户个人空间大小（单位：Bytes） | integer (int64) |
| status | 用户状态：冻结-1、未激活0、已激活1、过期-2、已删除-3 | integer (int32) |
| used | 用户已使用个人空间大小（单位：Bytes） | integer (int64) |
| userName | 用户姓名 | string |
| userSlug | 登录名 | string |

### 4.5. 批量冻结用户

根据用户id 列表批量冻结用户。

`DELETE /v3/api/user/freeze`

**请求示例：**

```bash
curl \
-X DELETE \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/user/freeze?uids=1,2
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| uids | 是 | Query | 用户id 列表，用逗号分隔多个id | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "list":
    [{
        "code": "",
        "message":"成功",
        "status": 200,
        "type": "succeed",
        "uid": 1
    },
    {
        "code": "",
        "message":"成功",
        "status": 200,
        "type": "succeed",
        "uid": 2
    }]
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| list | 批量操作结果数组。 | Array<BatchUserOp> |

单个批量操作模型（BatchUserOp）定义如下

| 参数 | 说明 | 类型 |
|---|---|---|
| code | 状态码 | string |
| message | 结果信息 | string |
| status | 状态编码,200 为成功。 | int64 |
| type | 类型 | string |
| uid | 用户id | int64 |

### 4.6. 批量解冻用户

根据用户id 列表批量激活用户。

`POST /v3/api/user/active`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'uids=1,2' \
https://api.zbox.filez.com/v3/api/user/active
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| uids | 是 | Body(form) | 用户id 列表，用逗号分隔多个id | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "list":
    [{
        "code": "",
        "message":"成功",
        "status": 200,
        "type": "succeed",
        "uid": 1
    },
    {
        "code": "",
        "message":"成功",
        "status": 200,
        "type": "succeed",
        "uid": 2
    }]
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| list | 批量操作结果数组。 | Array<BatchUserOp> |

单个批量操作模型（BatchUserOp）定义如下

| 参数 | 说明 | 类型 |
|---|---|---|
| code | 状态码 | string |
| message | 结果信息 | string |
| status | 状态编码,200 为成功。 | int64 |
| type | 类型 | string |
| uid | 用户id | int64 |

### 4.7. 创建团队用户关系

将用户加入到指定团队。

`POST /v3/api/teamuser/{team_id}/users`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'uid=1,2' \
https://api.zbox.filez.com/v3/api/teamuser/1/users
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| team_id | 是 | Path | 团队id | Int64 |  |
| uids | 是 | Body(form) | 用户id。使用逗号可以分隔多个id。 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "createMember":
    [{
        "ctime": "2020-10-15T16:21:33+0800",
        "email": "test2@lenovo.com",
        "fromDomainAccount": false,
        "role": "member",
        "status": 1,
        "team": "本地团队",
        "uid": 2,
        "userName": "test2",
        "slug": "test2"
    },
    {
        "ctime": "2020-10-15T16:21:39+0800",
        "email": "test3@lenovo.com",
        "fromDomainAccount": false,
        "role": "member",
        "status": 1,
        "team": "本地团队",
        "uid": 3,
        "userName": "test3",
        "slug": "test3"
    }]
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| createMember | 当前团队下的所有用户信息。 | Array<TeamUser> |

团队用户关系模型（TeamUser）结构如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| ctime | 创建时间 | string |
| email | 邮箱 | string |
| fromDomainAccount | 是否为域用户 | boolean |
| role | 角色 | string |
| slug | 登录名 | string |
| status | 用户状态：冻结-1、未激活0、已激活1、过期-2、已删除-3 | int32 |
| team | 团队名称（非全路径） | string |
| uid | 用户id | int64 |
| userName | 用户名称 | string |

### 4.8. 删除团队用户关系

将用户从指定团队中删除。

`DELETE /v3/api/teamuser/{team_id}/users`

**请求示例：**

```bash
curl \
-X DELETE \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/teamuser/1/users?uid=1,2
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| team_id | 是 | Path | 团队id | Int64 |  |
| uids | 是 | Query | 用户id。使用逗号可以分隔多个id。 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok"
}
```

**返回内容：**

返回内容为一般操作结果模型。

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

### 4.9. 获取团队成员列表

根据团队id 获取其成员用户列表

`GET /v3/api/teamuser/{team_id}/users`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/teamuser/1/users
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token]使用具有团队管理员的用户身份申请的token 才能调用此接口。 | string |  |
| team_id | 是 | Path | 团队id | int64 |  |
| page_num | 否 | Query | 页数,从第0 页开始 | int32 | 0 |
| page_size | 否 | Query | 每页数量 | int32 | 50 |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "memberList":
    [{
        "ctime": "2020-10-15T16:21:33+0800",
        "email": "test2@lenovo.com",
        "fromDomainAccount": false,
        "role": "member",
        "status": 1,
        "team": "本地团队",
        "path": "/本地团队",
        "uid": 2,
        "userName": "test2"
    },
    {
        "ctime": "2020-10-15T16:21:39+0800",
        "email": "test3@lenovo.com",
        "fromDomainAccount": false,
        "role": "member",
        "status": 1,
        "team": "本地团队",
        "path": "/本地团队",
        "uid": 3,
        "userName": "test3"
    }],
    "total":2
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| memberList | 当前团队下的所有用户信息。 | Array<TeamUser> |
| total | 成员的实际总数量 | int32 |

团队用户关系模型（TeamUser）结构如下：

| 参数 | 说明 | 类型 |
|---|---|---|
| ctime | 创建时间 | string |
| email | 邮箱 | string |
| fromDomainAccount | 是否为域用户 | boolean |
| role | 角色 | string |
| path | 团队路径 | string |
| status | 用户状态：冻结-1、未激活0、已激活1、过期-2、已删除-3 | int32 |
| team | 团队名称（非全路径） | string |
| uid | 用户id | int64 |
| userName | 用户名称 | string |

## 5. 组织

### 5.1. 创建组织

创建一个新组织。

`POST /v3/api/org`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'org_name=test' \
-d 'parent_id=1333' \
https://api.zbox.filez.com/v3/api/org
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| org_name | 是 | Body(form) | 组织名称 | string |  |
| parent_id | 否 | Body(form) | 父组织id | Int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "accountId": 747276,
    "ctime": 1618819257094,
    "depth":2
    "id": 183199,
    "name": test,
    "parentId": 175450,
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| accountId | 账号id | int64 |
| ctime | 创建时间 | Timestamp |
| depth | 组织层级 | int64 |
| id | 组织id。该项是组织身份的不可变标识，创建组织后应该妥善保存该字段用于后续的修改操作。 | int64 |
| name | 组织名称 | string |
| parentId | 组织父级id | int64 |

### 5.2. 更新组织

根据组织id 更新组织信息。

`PUT /v3/api/org/{org_id}`

**请求示例：**

```bash
curl \
-X PUT \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d 'org_name=test' \
https://api.zbox.filez.com/v3/api/org/12233
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
|  |  |  | 使用具有管理员的用户身份申请的token 才能调用此接口。 |  |  |
| org_id | 是 | Path | 组织id | Int64 |  |
| org_name | 是 | Body(form) | 组织名称 | string |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "children": null,
    "memberNum": null,
    "orgId": 176494,
    "orgName": "new",
    "parentOrg": null,
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| children | 组织下级子组织 | string |
| memberNum | 子成员数量 | Int64 |
| orgId | 组织id | Int64 |
| orgName | 组织名称 | string |
| parentOrg | 父级组织 | string |

### 5.3. 解散组织

根据组织id 解散组织。

`POST /v3/api/org/dismiss/{org_id}`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/org/dismiss/12233
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| org_id | 是 | Path | 组织id | Int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

### 5.4. 获取组织信息

根据组织id 组织信息。

`GET /v3/api/org/{id}`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/org/12233
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| id | 是 | Path | 组织id | Int64 |  |

**返回示例：**

以下结构记为组织信息模型（OrgInfo）。

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "children": null,
    "memberNum": 11,
    "orgId": 904,
    "orgName": "sjtsnew",
    "parentOrg": {},
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| children | 组织下级子组织 | string |
| memberNum | 子成员数量 | Int64 |
| orgId | 组织id | Int64 |
| orgName | 组织名称 | string |
| parentOrg | 父级组织 | string |

### 5.5. 获取组织列表

根据组织id 组织列表。

`GET /v3/api/org/list`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
https://api.zbox.filez.com/v3/api/org/list
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| Authorization | 是 | Header | 格式为bearer [token]使用具有管理员的用户身份申请的token 才能调用此接口。 | string |  |
| org_id | 否 | Query | 组织id | Int64 | 0 |
| sort | 否 | Query | 查询顺序：递增(asc)、递减(desc) | string | asc |
| order | 否 | Query | 排序字段：name ctime | string | name |
| page_num | 否 | Query | 页码 | int64 | 0 |
| limit | 否 | Query | 每页大小 | int64 | 20 |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "total":3,
    "content":[
     {
        "memberNum":0,
        "orgId":183199,
        "orgName":"sjtsnew ",
        "parentOrg":{"orgId":175450,"orgName":"sjtsnew "}
     },
     {
        "memberNum":0,
        "orgId":183316,
        "orgName":"sjts04020",
        "parentOrg":{"orgId":175450,"orgName":"sjtsnew "}
     }
   ]
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |
| total | 组织数量 | int64 |
| content | 组织列表 | Array<OrgInfo> |

OrgInfo

| 参数 | 说明 | 格式 |
|---|---|---|
| memberNum | 子成员数量 | Int64 |
| orgId | 组织id | Int64 |
| orgName | 组织名称 | string |
| parentOrg | 父级组织 | string |

### 5.6. 创建组织用户关系

将用户加入到指定组织。

`POST /v3/api/orguser/{org_id}/users`

**请求示例：**

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
-d“uids=4516”
https://api.zbox.filez.com/v3/api/orguser/13143/users?
```

**请求参数：**

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Content-Type | 是 | Header | 必须为application/x-www-form-urlencoded | string |  |
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
|  |  |  | 使用具有管理员的用户身份申请的token 才能调用此接口。 |  |  |
| uids | 是 | Body(form) | 用户id | string |  |
| org_id | 是 | Path | 组织id | Int64 |  |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
}
```

**返回参数：**

| 参数 | 说明 | 格式 |
|---|---|---|
| errcode | 错误码，成功：0 | string |
| errmsg | 错误描述，成功：ok | string |

## 6. 全局返回码

| errorcode | 参考 | 原因 |
|---|---|---|
| 0 | {"errcode":0,"errmsg":"ok"} | 请求成功 |
| 400 | {"errcode":400,"errmsg":"batch createuser email format error"} | 参数错误 |
| 401 | {"errcode":401,"errmsg":"not authorized"} | 鉴权异常 |
| 403 | {"errcode":403,"errmsg":"ip is forbidden"} | 操作被禁止 |
| 404 | {"errcode":404,"errmsg":"source notfound"} | 请求的实体不存在 |
| 405 | {"errcode":405,"errmsg":"account cloudspace limit"} | 不允许使用请求行中所指定的方法 |
| 409 | {"errcode":409,"errmsg":"team alreadyexist"} | 请求的资源冲突 |
| 412 | {"errcode":423,"errmsg":"delete forbiddenfor shared file"} | 请求的资源未满足前提条件 |
| 500 | {"errcode":500,"errmsg":"server error"} | 服务内部错误 |

## 7. 日志管理

### 7.1. 日志查询

获取网盘日志信息

`GET /v3/api/log/get`

```bash
curl \
-H "Authorization: bearer 574a05fd-c99c-4f77-97a4-b6f807cbbade" \
‘https://api.zbox.filez.com/v3/log/get?from_date=2021-07-20&to_date=2021-08-
20&path_type=ent&action=upload_file,login&limit=50&offset=0&user_id=27’
```

| 参数 | 必须 | 位置 | 说明 | 类型 | 默认值 |
|---|---|---|---|---|---|
| Authorization | 是 | Header | 格式为bearer [token] | string |  |
| from_date | 否 | Query | 开始日期 | string | 近10天 |
| to_date | 否 | Query | 结束日期 | string | 近10天 |
| path_type | 否 | Query | 操作类型: (ent：企业、self：个人),不传值会默认查询全部空间 | string |  |
| page_num | 否 | Query | 页码 | int32 | 0 |
| page_size | 否 | Query | 页面数量 | int32 | 50 |
| action | 否 | Query | 操作名称（多个操作名称用逗号隔开） | string | 所有操作 |
| user_id | 否 | Query | 用户id | string |  |

Action 参数

| 类别 | 操作类型（action） | 名称 |
|---|---|---|
| data | upload_file | 文件上传 |
| 数据 | download_file | 下载文件 |
|  | delete_file | 删除文件 |
|  | rename_file | 重命名文件 |
|  | move_file | 移动文件 |
|  | copy_file | 复制文件 |
|  | preview_file | 预览文件 |
|  | create_folder | 创建文件夹 |
|  | delete_folder | 删除文件夹 |
|  | rename_folder | 重命名文件夹 |
|  | copy_folder | 复制文件夹 |
|  | move_folder | 移动文件夹 |
|  | sync_download_file | 同步下载 |
|  | sync_upload_file | 同步上传 |
|  | docs_edit | 编辑文件 |
|  | comment_file | 评论文件 |
|  | edit_tag | 编辑标签 |
|  | add_remark | 备注 |
|  | bookmark | 收藏 |
|  | unbookmark | 取消收藏 |
|  | restore_file | 还原历史版本 |
|  | purge_file | 回收站彻底删除 |
|  | recycle_restore | 还原文件 |
|  | create_file | 新建文件 |
|  | create_folder_by_template | 新建目录结构 |
|  | regulary_delete_file | 定时清理删除文件 |
|  | regulary_delete_folder | 定时清理删除文件夹 |
|  | ld_initialization | 盘符初始化 |
|  | ld_auto_clean_data | 盘符自动清理数据 |
|  | ld_cancel_clean_data | 盘符注销清理数据 |
|  | entry_protection_status | 进入保护状态 |
|  | exit_protection_status | 退出保护状态 |
| user | login | 登录 |
| 用户 | create_user | 创建用户 |
|  | delete_user | 删除用户 |
|  | update_user | 更新用户 |
|  | freeze_user | 冻结用户 |
|  | active_user | 激活用户 |
| team | create_team | 创建团队 |
| 团队 | delete_team | 删除团队 |
|  | update_team | 更新团队 |
|  | add_team_member | 添加团队成员 |
|  | delete_team_member | 移出团队 |
| auth | create_auth | 创建权限 |
| 授权 | delete_auth | 删除权限 |
| delivery | create_delivery | 创建链接 |
| 链接 | delete_delivery | 删除链接 |
|  | download_delivery | 下载链接 |
|  | preview_delivery | 预览链接 |
|  | upload_delivery | 上传链接 |
|  | online_edit_delivery | 修改 |
| approval | create_delivery_approval | 发起审批 |
| 审批 | agree_delivery_approval | 通过审批 |
|  | decline_delivery_approval | 拒绝审批 |
| share | create_share | 创建权限 |
| 共享 | delete_share | 删除权限 |
|  | handover_share | 共享移交 |
| file_template | create_file_template | 创建文件夹模板 |
| 文件夹模板 | edit_file_template | 编辑文件夹模板 |
|  | delete_file_template | 删除文件夹模板 |

**返回示例：**

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "content":
    [{
            "action": upload_file,
            "ctime": 2021-08-02 16:08:20,
            "device": "WEB",
            "ipAddr": "172.16.51.195",
            "userId": 27,
            "userName": "admin"
    }],
    "totalSize": "1"
}
```

**返回参数：**

| 参数 | 说明 | 类型 |
|---|---|---|
| errcode | http 响应码 成功0 | string |
| errmsg | 响应信息，成功：ok | string |
| content | 响应内容 | ArrayList<Content> |
| totalSize | 日志总数 | integer (int64) |

Content 字段如下：

| 参数 | 说明 | 格式 |
|---|---|---|
| action | 操作名称 | string |
| ctime | 执行操作时间 | string |
| device | 执行操作终端 | string |
| ipAddr | 执行操作ip 地址 | string |
| userId | 执行操作的用户id | integer (int64) |
| userName | 执行操作的用户名称 | string |
