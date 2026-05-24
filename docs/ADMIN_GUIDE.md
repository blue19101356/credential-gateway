# Credential Gateway 管理员手册

## 系统架构

`
                    +---------------------+
  用户/服务 ------> |  Nginx / LB (可选)   |
                    +----------+----------+
                               |
                    +----------v----------+
                    |  FastAPI (Uvicorn)  |
                    |  :8000              |
                    |                     |
                    |  +---------------+  |
                    |  | Auth 中间件    |  |  Ed25519 签名 / Admin Token
                    |  | RateLimit     |  |  Redis 滑动窗口
                    |  | Logging       |  |  请求日志
                    |  +---------------+  |
                    |  +---------------+  |
                    |  | Crypto 层     |  |  ECIES 加解密
                    |  +---------------+  |
                    +----+--------+-------+
                         |        |
                  +------v-+  +--v-------+
                  |PostgreSQL|  | Redis 7 |
                  |  /SQLite |  | (限流)   |
                  +----------+  +---------+
`

## 启动与关闭

### 开发模式（SQLite，零依赖）

`powershell
cd credential-gateway
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload
`

默认使用 SQLite，首次启动自动建表。按 Ctrl+C 关闭。

### 生产模式（Docker Compose）

`ash
cp .env.example .env
# 编辑 .env，将 DATABASE_URL 改为 PostgreSQL
docker compose up -d
docker compose exec app alembic upgrade head
docker compose logs -f app
docker compose down
`

## 管理后台

浏览器打开 http://127.0.0.1:8000/admin。

| 标签 | 功能 |
|------|------|
| Applications | 列出所有注册应用，点击 Revoke 吊销 |
| Credentials | 凭证概览（不含明文） |
| Access Logs | 审计日志 |

右上角 Token 输入框用于管理员认证，默认为 dmin-secret-change-me。生产环境务必在 .env 中修改：

`ini
ADMIN_TOKEN=your-secure-random-token
`

## 管理员 API

带 X-Admin-Token Header 即可调用：

`ash
# 列出所有应用
curl -H "X-Admin-Token: admin-secret-change-me" http://127.0.0.1:8000/v1/applications

# 吊销应用
curl -X DELETE -H "X-Admin-Token: admin-secret-change-me" http://127.0.0.1:8000/v1/applications/<app_id>
`

## 监控

### 健康检查

`ash
curl http://127.0.0.1:8000/health
# -> {"status":"ok","service":"credential-gateway"}
`

### 日志格式

`
method=POST path=/v1/credentials status=200 app_id=xxx elapsed_ms=2.3
`

- method / path -- 接口
- status -- HTTP 状态码（200/401/429/500）
- pp_id -- 发起请求的应用 ID
- elapsed_ms -- 响应耗时（毫秒）

## 数据库操作

### 开发环境（SQLite）

`powershell
.\.venv\Scripts\python.exe -c "import sqlite3; conn=sqlite3.connect('credential_gateway.db'); [print(row) for row in conn.execute('SELECT id,name,status FROM applications')]"
`

### 生产环境（PostgreSQL + Alembic）

`ash
alembic revision --autogenerate -m "描述改动"
alembic upgrade head
alembic downgrade -1
alembic current
`

### 环境切换

.env 中修改一行：

`ini
# 开发（SQLite）
DATABASE_URL=sqlite+aiosqlite:///credential_gateway.db

# 生产（PostgreSQL）
DATABASE_URL=postgresql+asyncpg://gateway:gateway@localhost:5432/credential_gateway
`

## 日常运维

### 查看注册应用

`sql
SELECT id, name, status, created_at FROM applications ORDER BY created_at DESC;
`

### 查看审计日志

`sql
SELECT a.name, al.action, al.credential_id, al.ip_address, al.timestamp
FROM access_logs al JOIN applications a ON al.application_id = a.id
ORDER BY al.timestamp DESC LIMIT 20;
`

### 清空测试数据

`powershell
# 开发模式：删库重启最快
Remove-Item credential_gateway.db
# 重启服务，自动建空库
`

### 限流配置

.env 中调整：

`ini
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100          # 每窗口最大请求数
RATE_LIMIT_WINDOW_SECONDS=60    # 窗口（秒）
`

SQLite 模式下无 Redis，限流自动禁用。

## 安全部署清单

- [ ] 生产环境前面挂 Nginx/Caddy 做 HTTPS 终止
- [ ] 修改默认 ADMIN_TOKEN
- [ ] 数据库密码设置为强密码，且不提交到 Git
- [ ] /admin 路径建议通过反向代理加 IP 白名单或 Basic Auth
- [ ] 定期备份数据库（密文可备份，但解密需各应用的私钥）
- [ ] 告知用户：私钥丢失 = 数据永久不可恢复

## 故障恢复

| 问题 | 处理 |
|------|------|
| 数据库损坏 | 从备份恢复。密文完整则数据安全 |
| 用户丢失私钥 | 对应的加密凭证无法解密，只能删除后重新存储 |
| 应用被吊销 | 数据保留在库中（可审计），重新注册新应用即可 |
| 服务器被入侵 | 攻击者只能拿到密文 -- 无各用户的 X25519 私钥无法解密 |
