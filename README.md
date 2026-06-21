# DRAM Tracker — Roundhill Memory ETF 监控台

一个专注于美股 **DRAM ETF（Roundhill Memory ETF）** 的静态资讯网站，用于追踪 ETF 基本信息、核心持仓、权重分布、价格走势与市场资讯。

## 功能特性

- **ETF 概览**：实时展示 DRAM 价格、AUM、费率、成立日期、管理风格等关键指标
- **核心持仓**：9 大记忆体龙头持仓权重表格与可视化饼图
- **标的详情**：SK Hynix、Micron、Samsung、Kioxia、SanDisk、Seagate 等公司卡片
- **走势图表**：基于成立以来的模拟净值走势（支持 ALL / 1M / 2W 时间范围切换）
- **市场资讯**：汇总 Morningstar、Barron's、AOL/Yahoo Finance 与官方报道
- **响应式设计**：适配桌面端与移动端
- **实时价格动画**：模拟盘中价格跳动效果

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

## 本地运行

本项目为纯静态网站，无需后端。

```bash
cd d:/Dram
python -m http.server 8080
```

然后在浏览器打开：http://localhost:8080

## 技术栈

- HTML5 / CSS3
- Tailwind CSS（CDN）
- Chart.js（图表）
- 原生 JavaScript
- Google Fonts（Syne / JetBrains Mono / Noto Sans SC）

## 数据来源

- [Roundhill Investments - DRAM](https://www.roundhillinvestments.com/etf/dram/)
- Morningstar、Barron's、AOL/Yahoo Finance 等公开财经媒体

## 免责声明

本网站仅供信息参考，不构成投资建议。DRAM 持仓高度集中，投资风险较大，请在投资前仔细阅读基金招募说明书并咨询专业顾问。
