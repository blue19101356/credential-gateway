# Credential Gateway 用户操作手册

## 概述

Credential Gateway 是一个零知识凭证管理系统。你存储的每一条密钥都会用你的专属 X25519 公钥加密后再入库——网关服务器全程看不见明文，只有你自己手里的私钥能解密。

## 方式一：Web 门户（推荐，无需安装）

浏览器打开 http://127.0.0.1:8000/portal，全部操作在网页上完成。所有加密库已内置在项目中，不依赖外部 CDN，离线也能用。

### 第一步：初始化

1. 点击「Generate New Keys」，浏览器本地生成两对密钥：
   - Ed25519 签名密钥（用于每次请求的身份认证）
   - X25519 加密密钥（用于解密你存储的凭证）
2. 点击「Download Key Files」保存密钥文件。**私钥丢失 = 所有已存凭证永久无法解密。**
3. 填写应用名称（随意命名，如 my-backend）。
4. 点击「Register」注册到网关。网关记录你的公钥并分配 App ID。

> 注册后 App ID 和密钥自动保存在浏览器 localStorage 中，下次打开无需重新注册。换浏览器或清缓存后需重新导入密钥，或重新生成注册。

### 第二步：存储凭证

1. 切到「Store」标签。
2. 选择凭证类型：

| 类型 | 用途 | 示例 |
|------|------|------|
| API Key | 第三方 API 密钥 | sk-proj-abc123 |
| Database Password | 数据库连接串或密码 | postgresql://user:pass@host/db |
| SSH Key | SSH 私钥 | -----BEGIN OPENSSH PRIVATE KEY----- |
| Cloud Key | 云服务凭证（AWS/GCP） | AKIAIOSFODNN7EXAMPLE |
| Generic | 任意文本 | 任何你需要安全存储的字符串 |

3. 填写凭证名称（如 openai-prod-key）和凭证值。
4. 点击「Encrypt & Store」。明文发到网关后立即用你的 X25519 公钥加密，数据库只存密文。

### 第三步：取回凭证

1. 切到「Retrieve」标签。
2. 粘贴凭证 ID（可从 List 页复制）。
3. 点击「Retrieve」。网关返回密文，浏览器用本地 X25519 私钥实时解密显示明文。

### 第四步：管理凭证

切到「List」标签查看所有已存凭证。点击「Copy ID」复制凭证 ID，切换到 Retrieve 标签粘贴取回。

## 方式二：Python SDK

适合在代码中集成，自动签名和加解密：

`python
from client_sdk.client import CredentialClient
from client_sdk.key_utils import generate_and_save_keys

# -- 首次使用：生成密钥并注册 --
keys = generate_and_save_keys("./my_keys")
client = CredentialClient.register(
    base_url="http://127.0.0.1:8000",
    name="my-app",
    signing_private_key_pem=keys["ed25519_private_key"],
    signing_public_key_pem=keys["ed25519_public_key"],
    encryption_private_key_pem=keys["x25519_private_key"],
    encryption_public_key_pem=keys["x25519_public_key"],
)
# 保存 client.app_id，下次直接用

# -- 后续使用：加载已有密钥 --
client = CredentialClient(
    base_url="http://127.0.0.1:8000",
    signing_private_key_pem=open("my_keys/ed25519_private.pem").read(),
    encryption_private_key_pem=open("my_keys/x25519_private.pem").read(),
    app_id="<你的 App ID>",
)

# 存储
result = client.store_credential("api_key", "openai-key", "sk-proj-abc123")

# 取回（自动解密）
secret = client.retrieve_credential(result["id"])

# 列表
for c in client.list_credentials():
    print(f"{c['name']} ({c['type']})")

# 删除
client.delete_credential(result["id"])
client.close()
`

## 多用户隔离

每个应用持有独立的密钥对，凭证用各自公钥加密。A 存储的凭证 B 无法解密——即使两个人在同一台网关上操作，数据天然隔离。

验证方法：开两个浏览器（或无痕窗口），各自注册不同应用、存不同凭证，互相取回对方的凭证 ID 会直接解密失败。

## 安全注意事项

- **私钥是唯一解密手段**。离线备份，不要存到网关服务器上。
- **签名密钥和加密密钥分开**。签名密钥泄露可伪造请求但无法解密历史数据；加密密钥泄露可解密历史数据但无法伪造新请求。建议分开保管。
- Web 门户的密钥存在浏览器 localStorage 中，清除浏览器数据会导致密钥丢失。务必提前下载密钥文件。
