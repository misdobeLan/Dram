# DRAM Tracker — Roundhill Memory ETF 监控台

一个专注于美股 **DRAM ETF（Roundhill Memory ETF）** 的监控网站，用于追踪 ETF 基本信息、核心持仓、权重分布、价格走势与市场资讯。

## 功能特性

- **ETF 概览**：实时展示 DRAM 价格、AUM、费率、成立日期、管理风格等关键指标
- **核心持仓**：9 大记忆体龙头持仓权重表格与可视化饼图
- **标的详情**：SK Hynix、Micron、Samsung、Kioxia、SanDisk、Seagate 等公司卡片
- **走势图表**：基于真实 K 线的净值走势（支持 ALL / 1M / 2W 时间范围切换）
- **市场资讯**：汇总 Morningstar、Barron's、AOL/Yahoo Finance 与官方报道
- **响应式设计**：适配桌面端与移动端
- **实时行情**：通过富途 OpenAPI 接入真实行情数据

## 快速开始

### 1. 环境准备

```bash
cd d:/Dram
python -m venv .venv
.venv\Scripts\pip install -r backend/requirements.txt
```

### 2. 启动 OpenD 网关

实时行情依赖本地 OpenD 网关（默认 `127.0.0.1:11111`）。

#### 方式 A：使用项目内置网关（FUTU-OpenD-rs）

由于当前网络环境无法直接从富途/moomoo 官网下载官方 OpenD，本项目已内置兼容的社区网关 [FUTU-OpenD-rs](https://futuapi.com/)。

**离线模式（仅验证连接，无真实行情）：**

```bash
start_server.bat
```

**登录模式（获取真实行情）：**

```bash
set FUTU_ACCOUNT=你的富途账号
set FUTU_PWD=你的登录密码
start_opend_rs_login.bat
```

首次登录新设备可能需要输入短信验证码。登录成功后保持窗口运行，再启动后端。

#### 方式 B：官方 OpenD（如果你能下载）

1. 下载并安装 [富途 OpenD](https://www.futunn.com/OpenAPI)。
2. 启动 OpenD GUI 并完成登录。
3. 运行 `start_server.bat`。

### 3. 启动后端与页面

如果已经手动启动了带登录的 OpenD，直接运行：

```bash
start_server.bat
```

然后访问：http://localhost:8080

### 4. 运行数据一致性测试

```bash
run_tests.bat
```

测试会自动比对页面展示数据与富途真实行情。若发现差异，会输出具体字段；你需要修正后重新运行，直到全部通过。

## 当前测试结果

```bash
pytest tests -v
# 6 passed in ~14s
```

- ✅ `test_health`：后端健康检查
- ✅ `test_holdings`：持仓代码映射
- ✅ `test_quote_requires_connection`：行情接口
- ✅ `test_kline_requires_connection`：K 线接口
- ✅ `test_page_etf_price_matches_real`：页面 DRAM 价格/涨跌幅与真实行情一致
- ✅ `test_page_holdings_match_real`：页面持仓价格/涨跌幅与真实行情一致

## 实时行情覆盖范围

当前 OpenD 账号可获取以下市场真实行情：

| 公司 | 代码 | 市场 | 状态 |
|------|------|------|------|
| Roundhill Memory ETF | DRAM | US | ✅ 实时 |
| Micron Technology | MU | US | ✅ 实时 |
| SanDisk | SNDK | US | ✅ 实时 |
| Seagate Technology | STX | US | ✅ 实时 |
| Western Digital | WDC | US | ✅ 实时 |
| SK Hynix | 000660.KS | Korea | ❌ 账号/市场不支持，显示 "—" |
| Samsung Electronics | 005930.KS | Korea | ❌ 账号/市场不支持，显示 "—" |
| Kioxia Holdings | 285A / KI5.SG | Japan / Singapore | ❌ 账号/市场不支持，显示 "—" |
| Nanya Technology | 2408.TW | Taiwan | ❌ 账号/市场不支持，显示 "—" |
| Winbond Electronics | 2344.TW | Taiwan | ❌ 账号/市场不支持，显示 "—" |

> 若你的富途账号开通了韩股/台股/新加坡行情权限，修改 `backend/config.py` 中的 `futu_codes` 列表即可自动解析。

## 项目结构

```
├── backend/                  # FastAPI 行情代理后端
│   ├── main.py
│   ├── config.py
│   ├── futu_client.py
│   ├── models.py
│   ├── opend_helper.py
│   ├── check_futu.py
│   └── requirements.txt
├── tests/                    # Playwright 数据一致性测试
│   ├── conftest.py
│   ├── test_api.py
│   └── test_page_vs_real.py
├── tools/                    # 项目内置工具
│   └── futu-opend-rs-*/      # FUTU-OpenD-rs 网关
├── css/                      # 样式
├── js/                       # 前端脚本
│   ├── app.js
│   └── realtime.js
├── index.html                # 入口页面
├── start_server.bat          # 一键启动后端与页面
├── start_opend_rs_login.bat  # 使用内置网关登录启动
└── run_tests.bat             # 一键运行测试
```

## 数据来源

- 实时行情：[富途 OpenAPI](https://www.futunn.com/OpenAPI)
- 持仓权重与 ETF 信息：[Roundhill Investments - DRAM](https://www.roundhillinvestments.com/etf/dram/)
- 市场资讯：Morningstar、Barron's、AOL/Yahoo Finance 等公开财经媒体

## 持仓数据

| 排名 | 公司 | 代码 | 市场 | 权重（约） |
|------|------|------|------|-----------|
| 1 | SK Hynix | 000660.KS | Korea | 28.2% |
| 2 | Micron Technology | MU | US | 24.9% |
| 3 | Samsung Electronics | 005930.KS | Korea | 20.9% |
| 4 | Kioxia Holdings | 285A / KI5.SG | Japan / Singapore | 6.5% |
| 5 | SanDisk | SNDK | US | 5.1% |
| 6 | Seagate Technology | STX | US / Ireland | 4.4% |
| 7 | Western Digital | WDC | US | 4.0% |
| 8 | Nanya Technology | 2408.TW | Taiwan | 3.3% |
| 9 | Winbond Electronics | 2344.TW | Taiwan | 2.1% |

> 权重数据综合自 Morningstar、Barron's 与公开报道，实际配置请以 Roundhill Investments 官方披露为准。

## 免责声明

本网站仅供信息参考，不构成投资建议。DRAM 持仓高度集中，投资风险较大，请在投资前仔细阅读基金招募说明书并咨询专业顾问。
