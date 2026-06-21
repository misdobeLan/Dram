# FUTU-OpenD-rs（项目内置网关）

由于当前网络环境无法直接从富途/moomoo 官网下载官方 OpenD，本项目内置了社区版 Futu 网关 [FUTU-OpenD-rs](https://futuapi.com/)，作为兼容富途 OpenAPI 协议的本地网关。

## 文件说明

- `futu-opend.exe`：网关程序（兼容富途 FTAPI TCP 协议，默认监听 127.0.0.1:11111）
- `futucli.exe`：命令行客户端
- `futu-mcp.exe`：MCP 服务器

## 启动方式

### 方式一：离线模式（仅验证连接，无真实行情）

```bash
.\futu-opend.exe --api-ip 127.0.0.1 --api-port 11111
```

此模式可用于验证后端能否连通本地网关，但无法获取真实行情数据。

### 方式二：登录模式（获取真实行情）

```bash
.\futu-opend.exe \
  --api-ip 127.0.0.1 \
  --api-port 11111 \
  --login-account 你的富途账号 \
  --login-pwd "你的登录密码"
```

首次登录新设备可能需要输入短信验证码。

> ⚠️ 安全提示：请勿将密码提交给任何自动化脚本。建议在个人终端手动启动，或使用环境变量/配置文件并妥善保管。

## 与后端的集成

后端 `backend/opend_helper.py` 会自动检测以下 OpenD：

1. 已安装的官方 `OpenD-GUI.exe`
2. 本项目内置的 `tools/futu-opend-rs-*/futu-opend.exe`

启动后，后端会自动连接 127.0.0.1:11111。

## 更多信息

- 官方文档：https://openapi.futunn.com/futu-api-doc/
- OpenD-rs 文档：https://futuapi.com/en/quick-start/
