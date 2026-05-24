# Credential Gateway

基于 Ed25519 签名认证和 ECIES 混合加密的零知识凭证管理系统。

## 架构

应用注册时提交两对密钥：
- **Ed25519** — 用于请求签名和身份认证
- **X25519** — 用于 ECIES 混合加密（ECDH + AES-256-GCM）

网关**全程不接触明文**。存储时用接收方的 X25519 公钥加密，数据库只存密文；取回时返回密文，只有持有对应私钥的应用才能解密。

```
客户端                          网关                           数据库
  │                              │                              │
  │── POST /v1/applications ────→│                              │
  │   (注册 Ed25519+X25519 公钥) │── 存储公钥 ────────────────→│
  │                              │                              │
  │── POST /v1/credentials ─────→│                              │
  │   X-App-Id + X-Signature     │                              │
  │   {type,name,value}          │── ECIES 加密(value) ────────→│
  │                              │   (仅密文)                   │
  │                              │                              │
  │── GET /v1/credentials/{id} ─→│                              │
  │   X-App-Id + X-Signature     │←── 密文 ─────────────────────│
  │←── encrypted_data ───────────│                              │
  │                              │                              │
  │ (X25519 私钥解密)            │                              │
```

## 快速开始

```bash
# 安装依赖
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt

# 启动服务（默认 SQLite，自动建表）
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload

# 浏览器打开
# Web 门户：http://127.0.0.1:8000/portal
# 管理后台：http://127.0.0.1:8000/admin
```

## API 端点

| 方法 | 路径 | 认证 | 说明 |
|--------|------|------|-------------|
| `GET` | `/health` | 无 | 健康检查 |
| `POST` | `/v1/applications` | 无 | 注册应用 |
| `GET` | `/v1/applications` | Admin Token | 列出所有应用 |
| `GET` | `/v1/applications/{id}` | 无 | 查看应用详情 |
| `DELETE` | `/v1/applications/{id}` | Admin Token | 吊销应用 |
| `POST` | `/v1/credentials` | Ed25519 | 加密存储凭证 |
| `GET` | `/v1/credentials` | Ed25519 | 列出凭证 |
| `GET` | `/v1/credentials/{id}` | Ed25519 | 取回凭证（密文） |
| `DELETE` | `/v1/credentials/{id}` | Ed25519/Admin | 删除凭证 |

### 认证方式

应用 API 请求需携带以下 Header：
- `X-App-Id` — 注册时返回的应用 UUID
- `X-Signature` — 对 `SHA256(request_body)` 的 Ed25519 签名（hex 编码）
- `Content-Type: application/json`

管理员请求携带 `X-Admin-Token` Header 即可跳过应用签名认证。

### 支持的凭证类型

| 类型 | 说明 |
|------|------|
| `api_key` | API 密钥 / Token |
| `db_password` | 数据库连接串或密码 |
| `ssh_key` | SSH 私钥（PEM 格式） |
| `cloud_key` | 云服务凭证（AWS、GCP 等） |
| `generic` | 任意非结构化密钥 |

## Python SDK

```python
from client_sdk.client import CredentialClient
from client_sdk.key_utils import generate_and_save_keys

# 生成密钥对
keys = generate_and_save_keys("./my_keys")

# 注册到网关
client = CredentialClient.register(
    base_url="http://localhost:8000",
    name="my-service",
    signing_private_key_pem=keys["ed25519_private_key"],
    signing_public_key_pem=keys["ed25519_public_key"],
    encryption_private_key_pem=keys["x25519_private_key"],
    encryption_public_key_pem=keys["x25519_public_key"],
)

# 存储凭证
client.store_credential("api_key", "stripe-prod", "sk_live_abc123")

# 取回并自动解密
secret = client.retrieve_credential("<credential-id>")
print(secret)  # "sk_live_abc123"
```

## 技术栈

- Python 3.11+ / FastAPI / Uvicorn
- PostgreSQL 15 / SQLAlchemy 2.0 (async) / Alembic
- Redis 7（限流）
- cryptography（Ed25519、X25519、AES-GCM）
- Docker / Docker Compose

## 安全特性

- 网关仅接触密文——零知识存储
- ECIES 每次加密使用临时密钥（加密场景内的前向安全性）
- Ed25519 签名将请求绑定到特定应用身份
- Redis 滑动窗口按应用限流
- 吊销应用立即拒绝所有后续请求，但历史数据保留可审计
- 各应用凭证互相隔离——A 的公钥加密的数据 B 无法解密

## 文档

- [用户操作手册](docs/USER_GUIDE.md)
- [管理员手册](docs/ADMIN_GUIDE.md)
 

初始化命令
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8000

启动命令
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8000