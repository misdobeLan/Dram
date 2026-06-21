# DRAM Tracker 行情代理后端

基于 FastAPI + 富途 OpenAPI 的行情代理服务，为前端提供实时行情、K 线与 WebSocket 推送。

## 前置条件

1. **OpenD** 必须已安装并运行。
   - 下载地址：https://www.futunn.com/OpenAPI
   - 安装后启动 OpenD GUI，完成登录。
2. Python 虚拟环境已创建并安装依赖：
   ```bash
   cd /d/Dram
   python -m venv .venv
   .venv\Scripts\pip install -r backend\requirements.txt
   ```

## 启动

### 方式一：项目根目录一键脚本（推荐）
```bash
start_server.bat
```

### 方式二：手动启动
```bash
cd /d/Dram/backend
../.venv/Scripts/uvicorn main:app --host 0.0.0.0 --port 8080
```

## API 说明

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查，返回 OpenD 连接状态与已解析代码 |
| `/api/quote` | GET | 批量返回最新行情（持仓 + DRAM ETF） |
| `/api/kline?code=US.MU&ktype=1d&num=100` | GET | 获取 K 线数据 |
| `/api/market-state` | GET | 市场状态 |
| `/ws/quotes` | WebSocket | 实时行情推送 |

## 代码映射配置

持仓与富途代码的映射关系在 `config.py` 中维护。若某个市场代码无法解析，请检查：
- OpenD 是否已登录；
- 账号是否拥有对应市场行情权限；
- 代码前缀是否正确（美股 `US.`，港股 `HK.`，A股 `SH.`/`SZ.` 等）。

## 故障排查

- `/api/quote` 返回 `503`：OpenD 未连接。请先运行 `python backend/opend_helper.py` 查看详情。
- 某个持仓显示 `—`：该代码未能解析到可用的富途代码，可能是该市场未开通行情权限。
