# Changelog

FutuOpenD-rs 的所有重要变更将记录于此。

本文档遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。

## [1.4.114] - 2026-06-16 🟡 日股交易、订单推送与发布护栏收口

### ✨ Added / Improved

- **交易密码来源在 CLI / MCP 间保持一致** — `futucli unlock-trade` 和 MCP `futu_unlock_trade` 现在共享同一密码来源优先级：CLI 的 `--from-stdin`（仅 CLI）优先，其次为 `FUTU_TRADE_PWD`、账号级 OS keychain、legacy keychain，最后才是 CLI 交互式 prompt / MCP 配置错误；环境变量会 trim 首尾空白，减少误粘贴导致的解锁失败。
- **长跑诊断与发版护栏增强** — 新增长跑 smoke harness，便于采集 `/api/ping` 与 `/metrics` 证据；MSRV / release-gate / source-layout / surface guard 增加自证坏样本或 source-path 跟随检查，减少测试拆分、模块拆分和发版脚本漂移。
- **内部模块边界继续收敛** — gateway、MCP、CLI、静态数据、交易缓存和 surface-spec 相关热点继续拆分为更小的主题模块；公开 API 行为不变，但后续新增 endpoint / route / tool / docs 时更容易被 guard 捕获遗漏。

### 🟡 Fixed

- **REST `/api/cancel-order` 接受字符串形式数字订单号** — 自动把 `"order_id": "123..."` 归一化为数字订单号，仍保留按外部订单号单独撤单和非法字符串 loud 400，减少脚本 / JSON 工具把大整数当字符串传入时的撤单失败。
- **CA 市场下单 `backend_code=100012` 提示更明确** — `PlaceOrder` 在 CA 市场收到该错误时会提示账户 / 标的暂不支持 API 交易该 CA 标的，不再复用改单 / 撤单的“请求超时、不要盲目重试”文案。
- **JP 日股最大可交易数量查询补齐静态信息预热** — `GetMaxTrdQtys` 在本地缺少 JP 股票 backend market metadata 时，会先按需拉取证券静态信息，再计算最大可交易数量；若仍无法补齐，会本地明确失败，不再把不可信 market 信息发往后端后表现为“响应缺少 msg_header”。代码级修复已落地，JP 真机组合仍需外部环境确认。
- **JP 无权限账户下单不再返回假成功** — 非期货股票 / 现金市场下单会先检查账户交易市场权限；没有 JP 权限的账户会 loud-fail，并提示去官方 App 开通权限和风险披露，不再出现 `ret=0` 但订单号为空 / 后续查不到订单的成功形状。真实账户模拟 / 实盘路径仍需外部真机最终确认。
- **订单 push 不再在账户级刷新时回放今日历史订单** — 账户级订单列表刷新仍会更新本地 cache，但只有明确携带订单 ID 或能由请求映射到目标订单时才合成订单更新 push，避免一次当前订单事件混入大量今日已撤 / 已成历史订单。真实账户 `place` / `fill` / `cancel` push 对照仍待外部回归确认。
- **JP max-qty / PlaceOrder 相邻路径回归补齐** — 覆盖 HK 券商账户交易 JP 股票、FutuJP 子账户字段、无 backend market metadata 时的拒绝路径、JP 无权限 PlaceOrder 前置拒绝，以及期货写路径不被股票权限门误伤的回归测试。

### 🧪 Verification

- 已由 CC 完成一次完整 workspace 验证基线：5449 tests / 0 fail，workspace clippy / 0 warning；本次 release-prep 仍需在 clean HEAD 上重新跑 `ship.sh 1.4.114 --dry-run`。
- Focused tests 覆盖 REST cancel 字符串订单号、CA 下单错误提示、unlock-trade 密码来源、JP max-qty 静态信息预热、JP no-permission PlaceOrder、订单 push replay、gRPC temp-dir race、surface source-path guard、trade re-query worker split 和 sim option / margin PlaceOrder 回归。
- 以下真实账户行为不在本地环境宣称已闭环：JP max-qty backend 是否接受补齐后的 JP market metadata 组合、market-auth PlaceOrder 在真实账户上的最终行为、订单 push replay 三个真实账户 push 用例。

## [1.4.113] - 2026-06-12 🟡 稳定性、扩展 K 线周期与运维诊断收口

本版在 v1.4.112 登录热修复后的稳定基线上，集中收口行情、交易读取、撤单入口和运维诊断。建议使用 K 线订阅 / 拉取、REST / MCP / CLI 多入口、交易读取、多 broker 账户或长时间运行 daemon 的用户升级。

### ✨ Added / Improved

- **扩展 K 线周期开放** — 10 分钟、120 分钟、180 分钟和 240 分钟 K 线周期已贯通订阅、拉取、推送、REST、CLI 和 MCP；订阅、拉取、cache key 与 push dispatch 共用同一周期映射，减少旧数据和周期漂移。
- **CLI / MCP 交易参数扩展** — `futucli` 交易命令接受更多官方枚举数字和常见别名；`place-order` / MCP `place_order` 新增 `session`、`time-in-force`、`fill-outside-rth`、`expire-time` 等盘前 / 盘后字段，并对齐官方 OpenD 的动态 overnight 白名单。
- **全时段交易风险披露提示更可操作** — `session=ALL` / `OVERNIGHT` 下单被后端拒绝时，REST / CLI / MCP 会返回更明确的 App 风险披露提示；后端下发可打开的官方 App 跳转入口时也会一并透出。
- **运维诊断收口** — `--telnet-port` 作为 `--management-port` 的 deprecated alias 保留，管理端口默认只监听 `127.0.0.1`；`futucli doctor`、push health 和 Prometheus metrics 保留长跑 daemon 排障所需状态。

### 🔴 Fixed

- **美股盘前 / 盘后下单贯通便捷入口** — `futucli place-order` 和 MCP `place_order` 便捷入口此前固定不传 `session` / `time-in-force` / `fill-outside-rth` 字段，导致盘前 / 盘后订单与官方 App 提交形态不一致而无法成交；现在这些字段贯通 CLI / MCP / Rust helper（`--session RTH/ETH/ALL/OVERNIGHT` 等），并对齐官方 OpenD 的动态 overnight 白名单（`session=ALL` 不在白名单时降级 `ETH`），美股盘前 / 盘后订单可按官方 App 同形态提交成交。已由外部实盘验证。
- **broker 通道自愈不再在多次失败后停止** — broker reconnect watcher 会持续运行，避免半断连后只能依赖重启恢复。
- **交易读取在 broker 抖动后更可靠** — 交易读取路径在 broker 状态不可用时会明确失败或刷新，不再把旧 cache 伪装成新结果；order-list / history-order 继续保留官方解锁语义。
- **REST 单笔撤单入口语义化** — 新增 `/api/cancel-order` 高层 REST 入口，支持友好字段、外部订单号和省略低层 `packet_id`；旧 `/api/modify-order` 撤单兼容形态仍保留。
- **REST 单笔撤单后订单查询更稳定** — REST 撤单路径在后端接受请求后，会在返回前做有界订单刷新，减少撤单后立即查询订单状态时读到旧 cache 的概率；撤单 ACK 后不再隐式刷新持仓 / 可卖数量。
- **CLI 账户推送反订阅补齐** — `futucli unsub-acc-push <acc-id,...>` 现在与 `sub-acc-push` 对称，按账号 ID 列表取消订单 / 成交账户推送订阅，并修复旧测试包中该命令运行时超时的问题。
- **release / CI 与公开 surface 收口** — Cargo.lock drift、环境变量文档漂移、pretest 包身份、secret 依赖 nightly E2E skip、release gate 和公开文案脱敏都有更明确的检查。

### 🧪 Verification

- 已覆盖 workspace 格式 / clippy / 测试 / PII 扫描，以及 v1.4.113 全量回检。
- 扩展 K 线周期、US 订单读取 lifecycle 和美股盘前 / 盘后下单已完成真机验证。
- REST `/api/cancel-order` 已通过外部真实账户连续 3 次撤单复测，CLI `unsub-acc-push` 完成非回归抽查，全时段交易提示完成 focused checks。

## [1.4.112] - 2026-06-10 🔴 登录 ret15、行情订阅与资金查询热修复

本版面向已经发布的 v1.4.111 外部反馈，重点修复 fresh login 在部分账号 / 网络状态下返回 `ret_type=15`、长跑行情订阅保活、冷缓存订阅解析和综合账户 USD 资金查询等问题。建议所有 v1.4.111 用户升级，尤其是需要中国大陆 / 香港网络 fresh login、长期订阅 orderbook / quote、或使用综合账户资金查询的用户。

### 🔴 Fixed

- **fresh password login `ret_type=15` 根因修复** — TGTGT 票据中的时间字段现在按服务端验票期望写入，避免失效时间被服务端读成早年时间后进入“密码过期 / 删除本地密码”分支；同时保留更清晰的设备验证、短信和 `--reset-device` 指引。
- **primary auth 请求形态继续对齐官方 OpenD** — 登录链路默认按官方行为使用普通 HTTP，只有站点配置或服务端下发 retry-IP 时才切换对应路径；`/authority/` 请求体字段顺序、ClientVersion、请求头和诊断 fingerprint 日志继续收口，便于后续跨网络 A/B 排障。
- **设备验证重试不再污染本地凭据分支** — remember-login 进入短信设备验证后不会再继续 fallback 到 password auth 请求第二套 DVS；pending DVS 会持久化，password-auth DVS upsert 会替换旧的 rand key / TGTGT 材料，避免后续验证码成功后出现 `cbc_md5_var` 解密错误。
- **登录设备名称更容易排查** — 手机 App 的登录设备管理中，Rust OpenD 会展示带 crate 版本和构建标识的 `futu-opend-rs-v...` 设备别名，方便区分测试包和正式包。
- **orderbook / quote keep-sub 长跑修复** — 行情保活 replay 不再因为 missed tick 节奏过早触发；外部 21 分钟 orderbook 长跑已确认订阅未丢，US 盘前 orderbook 和 HK 主连行情持续更新。
- **冷缓存订阅解析修复** — 证券信息冷缓存解析对齐新版服务端字段，修复冷启动订阅有效股票 / 主连 / crypto / 板块等 symbol 时可能因字段 wire type 漂移而报“无法识别证券”的问题。
- **夜盘 / 跨市场状态修复** — US overnight、HK future night state、SG / MY orderbook backend bit 等市场状态继续跟随新版官方 OpenD 行为，减少夜盘快照时间和市场开闭状态漂移。
- **Crypto no-right 快照修复** — 没有 crypto 行情权限的账号不再错误读到 `CC.BTC` 快照数据。
- **综合账户 USD 资金查询修复** — Universal 账户在基础资金查询成功后，fund / bond sidecar 返回业务错误时保留基础资金结果；普通 US securities account 仍只走基础资金查询，不额外触发 fund/bond sidecar。
- **backend 断连清理修复** — 后端连接断开时主动清理等待中的请求，降低长跑 daemon 中旧 waiter 悬挂导致的后续请求异常。

### 🧪 Verification

- 已完成多轮 macOS arm64 pretest 包、Mainland fresh-login 真机回归、HK ret15 针对性回归、orderbook 21 分钟长跑、US 盘前 orderbook、HK 主连行情和多组 auth / QOT / funds focused tests。
- 真机反馈已确认 `ret_type=15` 根因修复后 fresh login 可正常进入短信 / 登录成功；orderbook keep-sub 在 21 分钟长跑中未丢订阅。
- 正式发版前仍需在 clean release commit 上由 CC 执行 `./scripts/ship.sh 1.4.112 --dry-run`，完成 workspace 级测试、PII 扫描、proto diff、multi-version smoke 和 cross-surface smoke 后再 tag / push。

## [1.4.111] - 2026-06-08 🔴 Futu API v10.6 / v10.7 接口与回归修复

本版修复 v1.4.110 登录设备验证后可能进入 gateway offline mode 的回归问题，并在 v1.4.110 的稳定基线上补齐 Futu API v10.6.6608 首批行情 / 基本面接口，继续开放 Futu API v10.7.6708 的期权组合、组合策略和新市场相关能力。建议所有 v1.4.110 及更早版本用户升级。新增接口仍按端点逐个开放；未完成真实后端验证的真实写路径不会在公开 surface 中宣称完整支持。

### ✨ Added / Improved

- **Futu API v10.6 基本面接口首批开放** — 新增或开放公司概况、高管信息、高管背景、经营效率、财报前后价格表现、财报前后价格历史、财务报表、主营构成、分析师评级概述、评级汇总和板块估值成分股等行情 / 基本数据能力。
- **Futu API v10.7 期权与组合策略接口开放** — 新增或开放期权报价、组合期权报价、期权策略列表、期权策略分析、期权策略价差、组合最大可交易数量和受保护的组合下单入口。已完成 C++ / Rust 真机对照的只读期权接口会按已验证路径开放；真实组合下单仍需要显式确认与真实交易授权。
- **新加坡 / 马来西亚 / 日本市场能力补齐** — SG / MY / JP 行情市场、交易市场、摆盘深度、市场状态、IPO、持仓视图和相关 CLI / MCP 展示继续对齐新版 OpenD surface。
- **v10.6 / v10.7 surface spec 继续收敛** — 已开放的新增接口同步接入 REST / MCP / CLI / gRPC generic proto 的参数、scope、exposure 和错误契约，减少“网关已实现但某个入口不可用”的差异。
- **登录设备验证提示更清晰** — `ret_type=15` 登录提示不再引导用户反复重输同一密码，会优先提示设备验证、短信验证码、`--reset-device` 和 `--setup-only` 路径。

### 🔴 Fixed

- **moomoo fresh login 设备验证 / TGTGT 修复** — TGTGT 构造现在跟随所选平台配置，修复 v1.4.110 moomoo fresh login 在设备验证通过后可能因加密材料不一致进入 gateway offline mode（如 `cbc_md5_var` 解密失败）的问题；验证码 callback 可被多次读取，避免一次性消费后后续步骤拿不到验证码。
- **登录缓存 `rand_key` 长度防护** — account credentials 中的 `rand_key` 现在必须保持 C++ TGTGT 账号路径的 32 字节语义；坏缓存会触发重新登录，`rand_key_new` 解出异常长度时不会落盘，避免后续启动用错误 key 解密后进入 gateway offline mode。
- **CAD 资金查询修复** — 资金查询的币种映射继续对齐后端语义，CLI / REST / MCP 使用账号或卡号查询 CAD 资金时返回正确币种。
- **REST broker 查询跟随 REST 订阅连接** — `/api/broker` 现在与 `/api/subscribe`、`/api/sub-info` 使用同一 REST 共享连接，避免 REST 订阅后 broker 查询误报未订阅。
- **快照 `price_spread` 回填修复** — 旧缓存或旧本地库缺少价差字段时，快照会按证券元数据自愈回填，减少与官方 OpenD 快照结果的差异。
- **Crypto 行情路由和展示修复** — `CC.BTC` 等加密货币行情在快照、基础报价、市场标签和统计相关路径中的 market 映射继续收口，减少空结果或 `UNK.*` 展示漂移。
- **组合下单 wire-shape 对齐 C++** — `PlaceComboOrder` 发往后端的组合价格保留固定两位小数，且不再发送 C++ 下单请求未写入的展示名字段；该路径仍是受保护真实写入口。
- **组合期权冷启动静态信息补拉** — `PlaceComboOrder` 和 `GetComboMaxTrdQtys` 在组合腿期权静态信息尚未缓存时，会按官方 OpenD 路径自动补拉 HK / US option static 信息；有效期权代码不再要求用户先手动调用 static / option-strategy-analysis 预热，查不到时会明确指出具体 `comboLegs` 下标。
- **`futucli` 直连官方 C++ OpenD 10.7 兼容性恢复** — CLI 直连官方 OpenD 的握手和 proto-json 入口继续对齐，便于用同一工具做 Rust / C++ side-by-side 对照。
- **CLI help 入口收敛** — 根帮助不再列出不可执行的 clap pseudo `help` 子命令，避免脚本按帮助文本调用后失败。
- **预发布包内容与版本一致性修复** — 包内示例补齐 gRPC `futu_service.proto`；workspace 版本提升到 `1.4.111`，`futucli`、`futu-opend` 和 `futu-mcp` 的 `--version` 输出与 manifest 对齐。

### 🧪 Verification

- 已覆盖 REST broker 共享连接、release example 包契约、CLI help 文本、登录 `ret_type=15` 提示、risk-free-rate 真实后端返回、三份二进制版本输出、v10.6 / v10.7 surface registry、proto-json 合约和相关 crate focused integration。
- 外部预发布回归已确认 moomoo fresh login、CAD funds、v10.6 QOT、主行情 / 交易旁路冒烟通过；v10.7 期权只读接口已完成 C++ / Rust side-by-side focused 验证。
- `PlaceComboOrder` 是真实交易写路径，本版只声明源码级 C++ wire-shape 对齐和 guarded surface 可用；若需要真实组合单 submit/cancel 对照，必须另行明确授权。
- `risk-free-rate` 已在 Rust 真实后端路径返回 HK / US / JP 利率；官方 C++ OpenD 不暴露同名 public FTAPI proto，因此它不作为 C++ public side-by-side 对照项。

## [1.4.110] - 2026-05-26 🔴 架构收敛、跨入口契约与交易 / 行情可靠性修复

**建议所有 v1.4.109 用户升级**，尤其是同时使用 REST / MCP / CLI / gRPC、多账户或多券商、真实交易写入、长跑 daemon、行情订阅 / 摆盘 / 市场状态 / 期权链的用户。

本版是 v1.4.109 之后的一轮稳定性和架构债集中收口：交易写入与读取路径继续 fail-closed，行情订阅和 broker-aware cache / push 路由更接近官方 OpenD 行为，多入口 API 契约开始统一由 surface spec 驱动，CLI 面向自动化场景的错误输出更可靠。Futu API v10.6.6608 新接口不包含在 v1.4.110，后续版本单独发布。

### 🔴 Fixed (P0 / P1)

- **交易后端响应不再空成功** — 下单、改单、撤单、复核订单、订单刷新、成交刷新、历史订单、历史成交等路径补齐响应头、状态码和关键字段校验；后端返回漂移、缺字段或不匹配时会明确失败，不再用 `RET_OK` 包住空结果。
- **交易订单生命周期继续收口** — 订单 ID、订单 IDEx、改单 / 撤单字段、sim / crypto 账户响应头、最大可交易数量、订单费用、保证金比例、现金流水和 flow summary 等路径继续对齐真实后端语义，降低“下单成功但后续查询 / 修改 / 取消不一致”的概率。
- **broker-aware 行情路由修复** — 行情订阅、报价、快照、摆盘、K 线、分时、历史 K 线、市场状态、crypto LV2 等路径按 broker / session / security key 区分 cache 与 push 路由，减少多 broker、多市场或混合订阅时读到旧桶、漏推或深度不一致的问题。
- **摆盘与混合订阅行为修复** — 同时订阅 `ORDER_BOOK` 和 `QUOTE`、冷启动等待、摆盘深度、取消订阅和 broker-aware key 迁移相关场景继续补齐，减少“订阅成功但只收到一次 / 深度不对”的情况。
- **跨入口契约更一致** — REST / MCP / CLI / Gateway / gRPC 的多个系统、行情和交易端点改由共享 surface spec 描述暴露状态、参数默认值、错误语义和 scope，未知字段与非法输入更早失败，未开放端点也会给出明确原因。
- **CLI 自动化错误修复** — `futucli quote-rights` 和 `futucli user-info` 在 gateway 未启动、端口错误或连接不上时会快速返回结构化错误；`json` / `jsonl` 输出不再只吐 WARN 日志后一直重试，便于 agent、CI 和量化脚本判断失败。

### ✨ Added / Improved

- **行情权限展示更接近官方 GUI** — `quote-rights` / `user-info` 的用户信息、额度和行情权限拆分展示；香港、美国、A 股、新加坡、日本、加密货币、期货和期权权限项更完整，便于用户判断自己能请求哪些行情。
- **公开入口能力补齐** — `used-quota`、`reconfirm-order`、期权链 Greek 过滤、部分账户 / 行情辅助能力在 CLI / REST / MCP / gRPC 间继续归一，减少同一功能在不同入口表现不同。
- **错误与输入校验更适合自动化** — 多个行情、交易和系统接口补齐 `deny_unknown_fields`、snake_case normalization、scope 映射和 machine-readable error，脚本侧更容易区分“参数错”“网关没开”和“后端拒绝”。

### 🔄 Refactor / Reliability

- **Gateway 内部边界拆分** — gateway 代码拆出更清晰的 core / qot / trd 模块边界，启动、重连、cache、push、broker runtime、metrics 和 reload 状态对象逐步收束，降低后续同类 bug 只修一处、另一处漏掉的风险。
- **CacheBundle / runtime 边界收口** — 生产 handler 不再直接散落访问 bridge 内部 cache 字段，更多状态通过专门 bundle / runtime 传递，便于审计并减少共享状态误用。
- **大文件和测试布局拆分** — 多个超过阈值的生产文件和测试文件完成机械拆分；测试代码继续集中放在测试模块内，降低单文件过长带来的 review 和回归成本。
- **发版与 pre-push 护栏增强** — 补齐行数守卫、unwrap / expect / panic 基线、releasegate marker、Cargo.lock drift gate、PII 扫描和 docs 私有信息扫描等检查，降低把未同步版本号、私有信息或大文件回退带进发布包的概率。

### 🧪 Verification

- 已覆盖交易写入 / 读取、订单生命周期、行情订阅 / 摆盘 / 市场状态、quote-rights / user-info、多入口 surface spec、CLI 机器可读错误和 gateway runtime 边界等单元、integration 与真实环境回归。
- 已生成并经外部真机测试包多轮验证；公开说明只保留用户可见行为结论，内部账号、日志和源码对照证据不进入公开 changelog。
- 发版前仍需在 release worktree 执行 `./scripts/ship.sh 1.4.110 --dry-run`，再由用户确认是否进入正式 tag / push / release。

### Not Included

- Futu API v10.6.6608 新增的财报、公司资料、持股、内部人交易等接口不属于 v1.4.110；这些接口已从本版切出，计划随 v1.4.111 或后续版本单独交付。

## [1.4.109] - 2026-05-16 🔴 Broker auth 与实盘交易写入修复

**建议所有 v1.4.108 用户升级**，尤其是使用真实交易写入、FTAPI binary 客户端、多券商账户登录或复杂网络环境 broker 授权的用户。

本版收口 v1.4.109 期间暴露的两条高风险链路：broker 授权恢复为官方同形态的 WebTCP 短连接 / fallback 流程；交易写入恢复对真实后端请求唯一性的正确处理，避免新下单被后端识别为旧请求重试而返回旧订单结果。

### 🔴 Fixed (P0)

- **实盘下单不再返回旧订单结果** — daemon 发往交易后端的请求唯一 ID 改为每次请求重新生成，避免 `PlaceOrder` 被后端幂等缓存识别为上一笔订单重试；真机已覆盖下单、改单、撤单和实时推送 lifecycle。
- **FTAPI binary 交易写路径恢复** — 原生协议客户端的下单、改单、撤单等写请求不再因为连接 ID 判定过严而在 daemon 发往后端前被拒绝。
- **broker 授权 WebTCP 路径修复** — broker 授权优先走 WebTCP 短连接、服务端下发地址池和 fallback 链路，不再依赖普通系统 DNS/HTTPS 近似实现；启动时的 rustls provider panic 已修复。
- **broker 授权 fallback 行为更接近官方 OpenD** — 动态 retry-domain、成功阶段缓存和站点配置选择已接入 broker-auth 流程，降低不同网络环境下 broker channel 建立失败的概率。

### 🟡 Fixed (P1)

- **订单 ID 与订单生命周期一致性收口** — 交易写入、订单查询、成交查询和推送路径使用一致的订单 ID 派生与刷新逻辑，减少下单成功后改单 / 撤单 / 查询找不到同一订单的情况。
- **实盘订单错误不再静默成功** — 下单成功响应缺少关键订单标识、后端返回旧订单回声、已结束订单撤单等场景会更明确地失败，而不是表现为成功。
- **持仓与交易读取过滤修复** — 持仓查询会按请求市场过滤；交易读取与相关刷新路径继续减少跨账户、跨市场读错缓存的风险。

### 🧪 Verification

- 已覆盖 PlaceOrder wire-shape、backend request ID 唯一性、交易写入幂等、订单查询、成交查询、broker-auth WebTCP、站点配置和多组 gateway integration 测试。
- 已通过真实环境验证：新下单返回新订单号，随后改单、撤单和对应交易推送均到达。
- 发布前仍需按发版流程完成 dry-run、PII 扫描、public docs 检查和最终真机 smoke。

## [1.4.108] - 2026-05-06 🔴 行情订阅、账户发现与交易计算修复

**建议所有 v1.4.107 用户升级**，尤其是使用实时行情订阅、港股期货主连合约、账户列表、App 卡号定位或最大可交易数量接口的用户。

本版集中修复行情链路和账户发现体验：行情推送帧在新版服务端格式下不再被静默丢弃，港股期货主连合约的摆盘、报价和逐笔推送可以正确送达订阅客户端；账户列表默认展示更接近 App 可见账户集合，保留 crypto、长期激励等已开通业务账户，同时隐藏 App 不单独展示的内部期货模拟行。交易计算方面继续补齐 `GetMaxTrdQtys` 的 C++ 对齐细节。

### 🔴 Fixed (P0)

- **行情推送解码修复** — daemon 现在能识别新版服务端行情推送帧中的压缩标记并解压正文，修复港股期货主连合约和部分实时行情订阅在订阅成功后收不到数据的问题。
- **港股期货主连合约订阅路由修复** — 主连、当月和下月等别名合约的行情推送会路由回用户订阅的 symbol，摆盘、报价和逐笔链路不再因为证券键不一致而静默丢弃。
- **账户发现不再漏 crypto / 长期激励账户** — CLI、REST 和 MCP 的默认账户发现保留 App 可见业务账户，不再把 crypto 或长期激励账户过滤掉；排障场景仍可使用 raw discovery 全量视图。

### 🟡 Fixed (P1)

- **`GetMaxTrdQtys` 响应投影继续对齐官方行为** — 修复最大可交易数量返回中的期货保证金字段、卖空 / 买回字段、US session 回填、JP margin override 和 Option IM 子请求，减少与官方客户端的差异。
- **账户 ID 和卡号展示更安全易用** — CLI / MCP / REST 对外统一使用用户可见 `card_num`，JSON 中 `acc_id` 以字符串返回，避免长账号在 JSON/表格工具中精度损失；CLI 表格按券商与真实/模拟/禁用分段展示，并使用市场名称代替数字枚举。
- **行情权限刷新更完整** — 订阅前会按需刷新行情权限，US 主权限、指数、OTC、期货等字段分开处理，不再把一个字段错误派生到多个权限项。
- **行情订阅请求校验补齐** — 注册 / 取消注册行情推送时会先解析证券，未知证券不再返回空成功。

### 🟢 Fixed (P2)

- **请求体解码失败改为明确错误** — 交易、行情和系统 handler 遇到 malformed body 时返回明确错误，不再表现为无响应或空成功。
- **现金流水 / 现金明细派生路径再收口** — 相关资产查询继续从鉴权账户和账户缓存派生后端字段，不再信任客户端传入的内部 market / account 字段。
- **CLI funds 卡号定位体验补齐** — 账户相关命令继续向“用户从 App 看到卡号即可查询”的方向收敛；综合账户需要显式币种的场景会给出更短、更直接的提示。

### 🧪 Verification

- 已覆盖账户发现、卡号投影、crypto / 长期激励标签、`GetMaxTrdQtys` response projection、Option IM、行情订阅证券校验、行情权限缓存、行情推送解码和主连合约路由等单元 / handler / integration 测试。
- 外部同事已用测试包验证：crypto 账户重新可见；港股期货主连合约摆盘 push 修复后可收到实时帧；日志时区按本地时区输出。
- 发布前仍需由 CC 跑 `scripts/ship.sh 1.4.108 --dry-run`，并在真实环境再覆盖账户列表、资金查询、港股期货行情订阅和行情权限刷新矩阵。

### Known follow-up

- `/api/funds` 对综合账户 / 期货账户省略 `currency` 的友好默认值仍建议放到后续结构化重构里做，本版只把错误提示收短，避免继续扩大资金语义改动面。
- v1.4.109 建议优先偿还 surface adapter 与大文件拆分的架构债，避免继续在多入口之间重复补丁。

## [1.4.107] - 2026-05-04 🔴 资产读取、交易计算与模拟账户通道路由修复

**建议所有 v1.4.106 用户升级**，尤其是使用资金 / 持仓 / 现金流水、模拟账户、综合账户、Tier M 资产接口或交易计算接口的用户。

本版集中收口资产与交易核心链路：模拟账户不再误走真实账户后端通道，资金与持仓刷新更严格按账户、币种和资产类别区分，现金流水 / 保证金 / 债券等移动端资产接口不再信任客户端传入的后端内部字段。交易计算和历史读取路径也改为缺少目标券商通道时明确失败，而不是回退到不合适的通道。

### 🔴 Fixed (P0)

- **模拟账户资产与订单查询通道路由修复** — 模拟账户的资金、持仓、订单和成交刷新使用模拟账户通道，不再误触发真实账户查询路径。
- **资金查询闭环补强**:
  - 综合账户 / 基金账户的资金、基金资产和债券资产合并路径更完整。
  - 后端刷新失败、响应缺关键字段或冷缓存已有同账号请求在途时，返回明确错误，不再返回空成功。
  - 资金缓存按账户、资产类别和币种区分，避免不同查询形状互相覆盖。
- **持仓查询资产类别隔离** — 持仓缓存按账户和资产类别区分，JP margin / derivative 等账户不会互相读取错误桶。
- **交易写入可靠性修复** — 下单成功但缺订单号时不再返回成功；重复订单号检测改为原子化；改单、撤单和复核订单的模拟账户路径与真实账户路径分离。

### 🟡 Fixed (P1)

- **现金流水 / 现金明细 / 业务分组读取更严格** — daemon 统一从已鉴权账户和账户缓存派生后端账号与市场，不再信任客户端传入的内部 market / account 字段；无法派生时明确失败。
- **Tier M 资产接口缺少券商通道时 fail-closed** — 现金流水、现金明细、业务分组、保证金信息、账户标志和债券系列接口在真实账户缺少目标通道时不再回退到平台通道。
- **Flow Summary 行为修复** — 账户市场、券商门禁、日期校验、分页错误、币种映射和业务类型说明更接近官方客户端行为；分页中途失败不再返回部分成功。
- **交易计算接口入口校验补齐** — 最大可交易数量、保证金比例和订单费用接口补齐证券、订单、市场和账户通道校验；真实账户缺少目标通道时明确失败。
- **历史订单 / 历史成交读取修复** — 时间窗口、市场列表和响应过滤更严格，真实账户读取不再回退到不合适的通道。

### 🟢 Fixed (P2)

- **MCP / CLI 资产接口字段补齐** — 现金流水、现金明细、账户标志和债券相关工具补齐或保留后端返回的可见字段，减少 REST / MCP / CLI 输出差异。
- **现金流水默认值与过滤更一致** — 未显式传最大条数、是否需要股票名等字段时由 daemon 统一补默认值；非法时间范围和非法收支方向会在发后端请求前被拒绝。
- **解锁交易 cooldown 收窄** — 仅交易密码错误会累计 cooldown，非密码类认证状态不再误计入错误次数。
- **gRPC 交易幂等 metadata 支持** — gRPC 请求可携带幂等键，复核订单重试会复用同一幂等窗口。

### 🧪 Verification

- 已补充多组 handler / integration 级回归，覆盖资金、持仓、现金流水、Flow Summary、订单刷新、成交刷新、历史读取、订单费用、保证金比例和最大可交易数量的关键路径。
- 本版公开说明只描述已在代码与测试中覆盖的行为；更细的内部审计证据保存在内部修复记录中。

### Known follow-up

- `GetMaxTrdQtys` 的 response-side 分支仍有期货保证金、卖空 / 买回字段条件化、持仓本地修正和部分市场碎股展示细节待单独收口；本版已修复 request-shape、入口校验和后端通道路由，不声明 response-side 已完全等价。
- Ship 前仍需跑真机验证矩阵，重点覆盖资金 / 持仓 / 现金流水 / 交易计算四类真实账户路径。

## [1.4.106] - 2026-05-02 🔴 资金币种语义修复 + GetFunds 闭环 + 跨 surface 防账户探测 + 发版流程提速

**核心修复**: v1.4.105 对资金币种的校验过严，导致部分单市场账户和模拟账户被错误拒绝。v1.4.106 对齐官方 OpenD 行为：期货和综合账户继续严格校验币种，单市场账户和模拟账户按原生币种返回。

本版还修复了综合账户按不同币种查询时可能读到旧缓存的问题。资金快照现在按账户、资产类别与币种分别缓存，刷新失败会明确返回错误，不再用空成功掩盖后端异常。

实机回归覆盖了多账户类型、多币种和多入口调用路径；公开说明只保留行为结论，具体账户、资产规模和内部审计证据留在内部修复记录中。

### 🔴 Fixed (P0)

- **资金币种校验对齐官方行为** — 单市场账户和模拟账户不再因为请求币种不在支持列表中被错误拒绝；期货和综合账户仍保持严格校验。相关路径增加了单元测试与 handler 级回归。
- **资金顶层币种字段对齐请求语义** — 用户显式传入 `currency` 时，顶层 `funds.currency` 会反映请求币种；未传时仍走原有回退逻辑。
- **GetFunds 刷新闭环修复**:
  - 后端刷新使用用户请求的币种，不再由 daemon 自行替换成账户主币种。
  - 后端传输失败或响应解码失败会明确返回错误，不再伪装为空成功。
  - JP 衍生品账户必须传合法 `assetCategory`，缺失或非法值会明确拒绝。
  - 同账户自动刷新增加 in-flight 保护，避免并发请求放大后端压力。
  - 资金缓存按账户、资产类别、币种维度区分，避免不同币种读取同一份旧快照。
  - REST / MCP / CLI / SDK 对顶层 `cash` 的说明统一：它是响应币种下的后端汇总现金，不是跨币种现金列表求和。

### 🟡 Fixed (P1)

- **跨 surface 防账户探测** — 启用 API key 账户白名单时，受限 key 不能再通过卡号后缀解析的响应差异探测其他账户是否存在。MCP 与 REST 交易写路径都改为只在调用者可见账户范围内解析。

### ✨ Added (Feature)

- **CLI funds --market 改 optional + FX sanity 提示** —
  `futucli funds --market`: required → optional, 不传时 daemon 按
  acc_id cache 推断主市场. FX sanity 抽成纯函数, 4 unit test 覆盖.
  跟本版 P0 配套: legacy 单市场账户 silent ignore currency 时, CLI 用 stderr
  warn 让用户感知 "传 X 实际收到 Y" 差异.

### 🔄 Refactor

- **跨 4 surface 鉴权 transport adapter 统一** — gRPC / REST / 原生 TCP WS / MCP 鉴权代码内部统一抽象。不改外部接口，仅减少同类入口漏接同一规则的风险。

### 🛠 工具 / CI

- **发版流程提速 ~50%** — 新增 release-ci profile (inherits release,
  lto=thin, codegen-units=16); 5 平台 build 用 release-ci profile;
  ship.sh surface verify 改并行. 单版 ship 时间 ~25-30 min →
  ~12-15 min.
- **修 git pre-commit hook 真启用** — `git config core.hooksPath .githooks`
  之前未真生效 (默认 `.git/hooks/` 不含 pre-commit), 导致 v1.4.105+ 的
  审查流程实际没拦截 commit. v1.4.106 配置真生效, 此后
  所有 commit 真过 hook (含 ship.sh release commit).

### Out of scope (defer 到 v1.4.107+ with explicit re-trigger)

- **legacy mode**: **不删** — legacy mode 永久保留, 多数用户场景下更方便.
  后续工作方向是 "如何让 legacy mode 自身做得更好" (UX / 错误提示 / fallback
  路径清晰度), 不是 deprecation. evidence 触发: 用户具体反馈 legacy mode
  哪里不好用.
- **rate-limit 算法 / audit log format / KeyStore reload**: 需 user
  evidence 触发 (性能 / 审计规范 / 不停服部署 evidence). v1.4.106 审查确认
  当前实装稳定.
- **schema 收紧 (enum-as-string reject / proto field 删 / deny_unknown 全扩)**:
  走 v2.0 breaking window. v1.5 deprecation warn → v1.6 final → v2.0 reject
  三阶段.

## [1.4.105] - 2026-04-30 🔴 下单可靠性 + 资金币种校验 + 4 surface 推送一致性 + 安全 polish

**建议所有 v1.4.104 用户升级.** 本版三大主题:

1. **下单可靠性**: 之前同一订单可能被 daemon 误 silent 重新 place — 现在
   按交易后台异步确认语义判定订单可见性, 加 30 秒同订单标识窗口去重,
   避免误下单.
2. **资金 / 币种校验**: 多币种综合账户传入不支持的币种 (例如某综合账户
   请求其不支持的法币) 现在在 daemon 端直接 loud reject 并返回该账号
   实际支持的币种集合, 不再 silent 返回错误口径.
3. **跨 4 surface (gRPC / REST WebSocket / 原生 TCP / MCP) 推送一致性**:
   trade push 所有 surface 现在统一执行**账户白名单 + 市场白名单**双层
   过滤, 防受限 key 收到非授权账户 / 市场的推送.

### 🔴 安全 / 可靠性 (P0)

- **下单同一笔订单不再被 daemon 误判 "可见+成功" 重复 place**: 之前
  daemon 在交易后台 sync ack 之后立刻把订单写进 cache 并标 success,
  忽略后端"等待经纪商确认"的异步语义. 现在 daemon 等待经纪商确认 push
  之后才暴露订单, 30 秒内同一订单标识重报 → loud reject + audit log.
  涉及 `/api/place-order` / MCP `futu_place_order` / gRPC trade write
  全 surface.

### 🟡 行为修复 (P1)

- **资金币种校验 loud reject**: 多币种综合账户传入不支持的币种 (例如
  请求该账号 broker 实际不支持的法币), daemon 不再 silent 返回账户主币
  种数据, 改为返回 `InvalidCurrency` 结构化错误并列出该账号实际支持的
  币种集合.
  Cache-read path 同防御, 不发 backend 也能正确 reject. 防一类历史
  silent-trust regression.
- **多市场综合账户识别更鲁棒**: 即便 daemon cache 因升级 / 漂移把
  账户的市场枚举存成原始 backend 值, 仍能正确识别为多币种综合账户,
  不会错降为单币种账户. (本修也覆盖空字符串 universal-card 的 backend
  下发情况, 不会误把单市场账户错认成综合账户.)
- **`/api/static-info` 拒绝空 list 输入**: 显式传 `code_list=[]` /
  `security_list=[]` 现在直接 400 (含 camelCase / 嵌套字段名 4 种 alias).
  防止误触发后端全 universe 响应 (~28MB).
- **standalone MCP 模式 `card_num` 受限 key 不再 reject 合法账号**:
  独立运行 MCP 时, 启动后通过 daemon `GetAccList` 解析 `card_num` →
  account 映射 (含 retry); 配置 reload 后会重新展开. 与 daemon
  内部 card_num 解析逻辑字节对齐.

### 🟢 安全 / UX polish (P2)

- **解锁交易错误次数不再泄漏给客户端**: redact 中英两种错误次数描述
  ("您还有 N 次" / "remaining N attempts" 等). 服务端 audit 日志仍保留
  原文便于运维; 客户端只看 `[次数已 redact]` + 通用提示.
- **gRPC 错误信息不再暴露 scope 名**: 之前 `PermissionDenied` 会把
  daemon 内部 scope 标识带给客户端; 现在统一返回 `"forbidden"`, 与
  REST `/api/*` 一致.
- **MCP 交易写入路径鉴权次序更严**: 无效凭证 (invalid Bearer) 或不含
  trade scope 的 key (例如只读 key) 现在在 daemon account-list 查询前
  即被拒绝, 不再触发账户列表副作用. 注: trade scope 已通过的 key 在
  account-id 白名单收紧场景下, account-list 仍会被查询 — 这层收紧留
  下版处理.
- **MCP unlock-trade audit 归属修正**: HTTP per-request Bearer 调 unlock
  时, 服务端 audit 日志正确记到本次 caller 的 key id, 不再 fallback 到
  startup key.
- **资金币种错误信息不暴露内部细节**: 客户端看到的 `InvalidCurrency`
  错误只含 broker 标签 / 请求币种 / 该账号支持的币种集合.

### 🛠 跨 surface 一致性 / 推送过滤 (4 surface)

- 4 个 surface (gRPC / REST WebSocket / 原生 TCP / MCP) 的 push 事件
  现在共用同一注册中心, 统一执行**两层过滤**:
  - **账户层**: 只把账户白名单内 trade event 推给该连接, 防受限 key 收
    到非授权账户的 trade push.
  - **市场层**: 只把市场白名单内的 trade event 推给该连接, 防受限 key
    收到非授权 market 的 push.
- REST 订阅账户推送端点加请求体级别的账户白名单校验.
- REST + MCP 交易写入端点支持 `card_num` 字段, 启用受限 key 时按白名单
  校验.

### 不在本版范围 (留待后续版本)

- 4 surface 的传输层 transport adapter 抽象重构 (改动量较大, 留下版
  整体重组).
- CLI `--market` 默认值优化 / FX 折算 sanity check (建议项, 非必需).

### 真机 verify pending

下版前必须在真机环境跑一遍: 后端异步经纪商确认场景下下单可靠性;
多 broker (HK/US/SG/AU/JP/MY/CA) 资金币种正交矩阵; standalone MCP +
daemon 同启 card_num 展开; 多账户跨市场 push 实际行为.

## [1.4.104] - 2026-04-29 🔴 跨 4 surface auth pipeline 统一 + 外部报告 22 + codex 3 轮 12 项 finding

**所有 v1.4.103 用户必须升级.** 大重构: 4 surface (REST / gRPC / raw TCP WS /
MCP) auth 全部走单一 `futu_auth_pipeline::authenticate_request` 中间件;
`X surface 漏 Y check` 类历史 finding 通过 single-source-of-truth 根治. 同
时修 外部 FINAL-CHINESE-BUG-REPORT 22 项 + codex 3 轮 review (round 1: 4
finding / round 2: 5 finding / round 3: 3 finding) 全部 12 项 finding.
真机 verify (HK `<acc>` backend 上线) 24/27 项 PASS.

### 🔴 Fixed (P0)

- **外部报告 S-001**: native TCP FTAPI (port 11122) 完全无 auth, 配 `--rest-keys-file`
  / `--grpc-keys-file` / `--ws-keys-file` 后 TCP 仍允许任意本机进程连接,
  跨 surface auth 在 TCP 上彻底失守. 加 `--allow-tcp-unauthenticated` flag
  (default off), 配置任一 keys file → 默认**关闭 TCP listener** (fail-closed).
  显式 opt-in flag → 启 TCP 但 loud warn 该端口无 auth (legacy Python SDK /
  C++ OpenD 的 escape hatch). 默认无 keys file 用户行为不变.

- **外部报告 S-002**: MCP B10 expansion 漏 `ks=mcp` 路径, MCP keystore 含
  `allowed_card_nums` 但 `allowed_acc_ids` 为空时被当 "无限制" sentinel 处理.
  `KeyStore::load` 在 load 时立即检测 has_card_nums + !has_acc_ids → 注入
  fail-closed sentinel `allowed_acc_ids = {0}`, 跨 4 surface 共用同一逻辑.

### 🟡 Fixed (P1)

- **外部报告 S-003**: unlock-trade 本地 cooldown 仅在 `req.c2s.acc_ids` 显式非空
  场景检查, 用户用 `security_firm` 或全空 filter → cooldown bypass → daemon
  转发 broker → broker counter 衰减 → 锁账户. 在 broker grouping 之后再
  sweep 一次 cooldown, 任意 group 的 acc 命中 → 不 forward (覆盖 HK / CA /
  SG / AU / JP / MY 全 broker dispatch path). 真机 verify PASS.

- **外部报告 S-004**: P1-D relogin 跨 v1.4.100/102/103 三版 longrun fail with
  generic msg, 真因被吃在 3 层 silent swallow. (Layer 1) `device::load_credentials`
  IO + JSON deserialize 错 → loud warn 带 line/col + sha256 digest (codex
  round 2 F1 redact: 不写 raw bytes); (Layer 2) `auth::remember_login` server
  code != 0 → 把 error_msg / error_msg_id / tip 也带进 FutuError + known-code
  语义提示; (Layer 3) bridge 用 `{:#}` (anyhow alternate Display) 输出整
  cause chain. 真机 verify PASS.

- **外部报告 S-005**: `/api/subscribe` 在 `is_sub_or_un_sub=false` 或 absent 时,
  对 invalid ticker silent success. REST adapter 入口 `body_has_sub_or_unsub_flag()`
  pre-flight check; gateway handler 对 unsub 路径加 silent-success 防御
  (新 API `unsubscribe_qot_with_status` 返 bool).

- **外部报告 S-006**: MCP schema description 多处写错 SubType 数字 ↔ 枚举名映射
  (10=KL_Month vs proto canonical 10=KL_60Min). futu-mcp / futu-gateway /
  futucli 三处描述统一 proto canonical, 加 2 个回归 unit test.

- **P1-001**: REST `symbol` alias 之前要 array (`symbols: ["US.AAPL"]`),
  CLI/MCP 都接 `symbol: "US.AAPL"` 单字符串. 现在 REST adapter 也接.

- **P1-002**: MCP funds 省略 9 个 null 字段 → REST 33 key shape 一致.

- **P1-003**: keys-file 解析时序前移到 broker auth + SMS 之前, 启动期
  immediate fail-closed.

- **P1-004**: CORS wildcard `FUTU_REST_ALLOWED_ORIGINS='*'` 触发 tower-http
  panic → REST task 死, 但 gRPC/TCP/WS/telnet 同毫秒继续 bind → daemon
  half-dead silent failure. 早期检测 wildcard fallback `AllowOrigin::any()`.

- **P1-005**: MCP `futu_unlock_trade` 忽略 HTTP Bearer (v1.4.104 阶段 7-5
  已修走 pipeline + caller-specific scope check + acc_ids whitelist).

- **P1-006**: funds `--currency` runtime silent ignored (普通账户 vs 综合账户).
  futu-trd 后置检测 + REST/MCP/CLI 三 surface 都 surface `currency_warning`
  字段. 真机 verify PASS.

- **codex round 2 F1**: S-004 verbose log credential redact. account / 文件
  bytes 改 SHA256 8 hex digest, 不再 log raw account / first 64 bytes.
  codex round 3 polish: zero-pad to 8 hex 让 ops correlation 一致.

### 🟢 Fixed (P2 + OBS-P3)

- **P2-001**: legacy no-key WS 任意 evil Origin 101 → default loopback.
- **P2-002**: /api/kline realtime cache silent-drops invalid input → 入口
  4 项 validation + cache miss loud hint.
- **P2-003**: cash-log/cash-detail/biz-group `trd_market` 错误提示自相矛盾
  → endpoint-specific example body.
- **P2-004**: credentials sidecar `.backup/.bak` 0644 → 扩展 tighten 允许
  名以 `credentials-` / `device-` 开头的所有文件.
- **P2-005**: margin-info / bond-* / account-flag header 字段不同 → 同 P2-003
  endpoint-specific example.
- **P2-006**: `is_unsub_all=true` silent no-op → 新 `unsubscribe_all_qot`
  真清所有 + 归零 quota.
- **P2-007**: futucli kline `--count 2 --end 2026-04-29` 返 stale → 客户端
  sort + take. 真机 verify PASS — 返 04-28+04-29 (newest 2).
- **P2-008**: futucli gen-key `--allowed-card-nums ""` silent 写空 list →
  loud reject (sentinel 反义).
- **OBS-P3-001**: panic crash log backtrace disabled → `Backtrace::force_capture()`.
- **OBS-P3-002**: `/api/option-chain start/end` alias 加 `start` → `begin_time`.

- **codex round 2 F2**: REST `/api/subscribe` preflight 不接 camelCase →
  接受 snake / camel / Pascal 三种.
- **codex round 2 F3**: GetKL `kl_type` 1..=12 错位 → 改 1..=11 + 描述对齐
  proto canonical.
- **codex round 2 F4**: `currency_warning` 仅 MCP → 补 REST + CLI surface.
- **codex round 2 F5**: REST `is_unsub_all=true` 跨 caller silent → REST 入口
  reject + 列替代方案.

- **codex round 3 F1**: `/api/unsubscribe` sibling-route 仍允许 process-wide
  `is_unsub_all` bypass → `unsubscribe()` 也加 reject, 两条 REST 路径行为
  一致.
- **codex round 3 F2**: `/api/static-info` 漏在 LIST_STYLE_IGNORE 之外 →
  加进 ignore.
- **codex round 3 F3**: docs-site 中英 rest-api.md subscribe/unsubscribe
  example 老 shape 缺 `is_sub_or_un_sub` → 更新 example.

### ✨ Added

- **新 `futu-auth-pipeline` crate**: 单一 `authenticate_request(envelope) →
  AuthDecision` 中间件覆盖 4 surface 全链路.
- **proto 2005 TRD_UNLOCK_TRADE 跨 surface bypass 修复** (codex round 1 F1):
  4 surface 统一 `Scope::TradeUnlock` strict + body-aware acc_id check.
- **MCP `CallerSnapshot`** (codex round 1 F3): 防 TOCTOU race.
- **Mechanical invariant test** (codex round 1 F4): catch 新 acc:read proto
  漏 body_aware 类 regression.
- **`futu-e2e/tests/cross_surface_auth.rs`**: 真 daemon e2e + nightly-e2e.yml
  hard-fail block.

### 🔄 Refactor

- **9 阶段 auth pipeline 迁移**: 阶段 1 (新 crate) → 2-5 (4 surface) → 6
  (invariant test) → 7-1..5 (silent defer 清理) → 8-1/8-2 (e2e + workflow)
  → 9 (真机 verify HK `<acc>` + US `<acc>`).

### 测试 + verify

- workspace 213+ unit/integration test 全 PASS.
- 真机 verify: HK `<acc>` backend 上线 — 24/27 项 PASS, 3 项 deferred
  (代码 + 单测覆盖, 缺真机 trigger).
- cargo build --release --locked + fmt + clippy --all-targets clean.

## [1.4.103] - 2026-04-29 🔴 PlaceOrder 重复下单根治 + 跨 4 surface auth 闭合 + card_num UX

**实盘下单 / 受限 API key 用户必须升级.** 用户实盘报告 P0 PlaceOrder 重复下单
+ 跨 4 surface body-aware allowed_acc_ids 系统性闭合 + card_num UX (App
可见的 4 位 / 16 位直接配 keys.json) + 外部审查多轮 finding 全修.

### 🔴 Fixed (P0)

- PlaceOrder ack 后 stub order status 实际等于 proto `OrderStatus_Unsubmitted`
  ("未提交"), 客户端按 enum 解读 = "下单失败" → 触发 retry → 多下单. 真根因
  v1.4.82 起 7+ 版 silent regression. 严格对齐 C++ 参照: 条件单 → WaitingSubmit,
  普通单 → Submitting. `scan_orphan_orders` 检查扩到全 in-flight 状态.

### ✨ Added (跨 4 surface 账户隔离闭合)

- **gRPC + raw TCP WS 共享 proto-aware acc_id extractor** (避免 hand-copy
  diverge). 共 24 protos cover: TradeReal (place/modify/reconfirm) + AccRead
  base (sub-acc-push/funds/positions/orders/order-fills/history-orders/
  history-deals/margin-ratio/order-fee/flow-summary/max-trd-qtys) + Tier M
  (cash-log / cash-detail / biz-group / margin-info / account-flag / bond × 5).
  受限 key 跨账户 query / 写入 / 订阅全 reject.
- **gRPC SubscribePush stream filter**: 持 `allowed_acc_ids` snapshot, trade
  event 双层过滤 (scope + acc_id). 握手接 `qot:read OR acc:read` 任一 (account-
  only key 也能开流收 trade push).
- **MCP per-request HTTP Bearer**: `require_acc_read_with_acc_id` helper,
  优先级 api_key > HTTP Bearer > startup. **42 个 tools** (5 acc 基础 + 17
  acc 扩展含 history/cash-flow/cash-log/margin-info/bond 等 + 16 qot/sys
  含 quote/snapshot/kline/orderbook/subscribe/unsubscribe/global-state 等 +
  unlock_trade + sub/unsub_acc_push + push_subscriber_info) 全切到 caller-
  specific 解析. HTTP 模式 invalid Bearer 立即 reject 不 fall back startup
  (case-insensitive `Bearer`/`bearer`/`BEARER` parse, RFC 7235 合规).
- **MCP sub/unsub ownership**: `futu_sub_acc_push` 调 daemon 前每 acc_id
  单独 check; subscriber 绑定 owner key id; `futu_unsub_acc_push` 校验 caller
  key id 匹配, 跨 caller unsub 被 reject. Snapshot caller-key BEFORE await
  防 SIGHUP reload race window leak.
- **`unlock_trade` acc-level enforcement**: 受限 key (allowed_acc_ids 非空)
  必须显式传 acc_ids 且每个都 ∈ allowed_acc_ids; 否则 reject (不允许 silent
  unlock-all 跨账户).
- **`/api/accounts` + MCP `futu_list_accounts` + gRPC/WS TRD_GET_ACC_LIST
  响应过滤**: 受限 key 仅看到自己 allowed 的账户列表, 不再泄漏全部账户 id
  用作跨账户 enumerate.
- **card_num 直接配 keys.json**: App 显示的 4 位 suffix
  (`保证金综合账户(7680)`) / 完整 16 位 card_num 直接写进 keys.json. `futucli
  gen-key --allowed-card-nums 7680` 等价于 `--allowed-acc-ids <真实 acc_id>`.
  daemon 启动 + SIGHUP reload 后自动 expand → 合并进 `allowed_acc_ids`.
  unresolved/ambiguous → fail-closed sentinel reject (不 silent unrestricted).
  支持双匹配 `card_num` + `uni_card_num` (综合账户卡号).
- **综合账户 currency 显式控制**: `futucli funds --currency HKD|USD|SGD|...` /
  MCP `futu_get_funds {currency: "USD"}` / REST `c2s.currency` 让综合账户
  用户明确指定币种, 避免 backend 默认返 base currency 数字 + tag 不一致 (~5x
  数字偏差风险). futucli 表格 / JSON 输出加 cash_info_list (分币种) +
  market_info_list (分市场) sub-rows 让综合账户用户看到细分.

### 🔴 Fixed (审查 P1)

- card_num 全部 unresolved/ambiguous 时不再 silent unrestricted (写 sentinel
  acc_id=0 让限额拒所有真账户).
- 立即跑首次 expand (sentinel 即时生效, 无 startup window 漏洞); SIGHUP reload
  后再 expand.
- gRPC + raw WS body-aware 完整覆盖所有 acc:read protos (包括 Tier M
  22701-22710), 与 scope 表 1:1 对齐, 防 hand-copy diverge.
- MCP HTTP Bearer / api_key 提供但 verify 失败 → 立即 reject, 不 fall back
  startup key (跨租户 leak fix).
- MCP `futu_sub_acc_push` 调 daemon 前每个请求 acc_id 单独通过受限 key 比对
  (之前 daemon 全局订阅副作用绕过 caller-side filter).

### 🟡 Fixed (审查 P2)

- MCP `futu_push_subscriber_info` 用 caller-specific KeyRecord 做 visibility
  filter (之前用 startup key 跨租户泄漏其他 agent 的 acc_ids).
- `GET /api/accounts` 按 allowed_acc_ids filter `acc_list` (信息泄漏 fix —
  受限 key 不再看到全部账户).
- gRPC `SubscribePush` 接受 `qot:read OR acc:read` 任一 (之前强制 qot:read
  阻挡 account-only key 收 trade push).
- REST `/api/sub-acc-push` 在 legacy 模式 (无 keys.json) 改 403 loud reject
  + 清晰 hint (之前 silent ret_type=0 不写 state).

### 行为变化 (与上版对比)

- `/api/sub-acc-push` legacy 模式由 silent success 改为 403; 用户需配
  keys.json + Bearer 启用 sub state.
- 受限 key 调 `GET /api/accounts` 仅看自己 allowed 的账户.
- MCP HTTP 模式 invalid Bearer 立即 error, 不 fall back startup.

### 测试

- workspace 1383+ tests pass; cargo fmt --check + clippy --all-targets clean.
- 4-surface integration: 同一 key 限到 acc A → REST/gRPC/WS/MCP 全 reject
  acc B (真机 verify ship 前跑 HK + US 双账户).

## [1.4.102] - 2026-04-28 🔴 BUG-009 SMS race 根治 + 11 bug

**外部 leaf 报告 v1.4.100 综合 audit (15 finding)** + **codex 21-23 轮 follow-up**
(8 finding) + **用户 fund-market handoff** (2 finding) + **BUG-001 ticker-statistic
real-machine S-level fix** + **BUG-009 SMS race 真根因修** (用户实锤"前修后改回")。

### 🔴 Fixed (P0 / S)

- **BUG-001** ticker-statistic `last_close_price` scale 100x 错 (应除 1000
  非 100000, 与 quote endpoint 一致). real-machine 实测 AAPL 昨收 271.06
  之前返 2.7106. AAPL 回归 test 已加, 后续不会回归.
- **BUG-002** `/api/subscribe` 对无效 code (空 / whitespace / SQL 注入串 /
  拼错 ticker) silent success → loud `ret_type=-1`. 4-pass validation:
  validate → resolve → gate → commit. partial-invalid batch 全批 reject
  (不允许部分 silent success). 5 个 integration test 覆盖.
- **BUG-009 SMS race 真根因修** (用户 2026-04-28 反馈): pre-flight check
  在 `remember_login` **之前**, cached `dvs+dcs+verify_cb` 都 fresh → 跳
  remember_login + authority POST + req_device_code, 直接 verify_device_code
  with cached values. 6 版迭代才根治. 3 unit test 覆盖决策逻辑.
- **BUG-012** credentials-*.json + device-*.dat 0644 → 0600 (Unix). 启动
  扫已存在文件 chmod 0600 (升级用户兼容). 多用户 / CI / 共享开发机其他
  本地用户曾能读 tgtgt / web_sig (P0 multi-user, P1 single-user). 3 mode
  regression test.

### 🟡 Fixed (P1)

- **BUG-005** REST `/api/positions` `/api/history-orders` 缺 `trd_env` 时返
  误导 "Nonexisting acc_id" → 400 + 明确 hint. 13 trade endpoint 全 wired
  `validate_header_trd_env_present`. handler 层 mismatch msg 也前置 "trd_env
  mismatch" 而非 "Nonexisting".
- **BUG-006** TOML `[daemon]` section silently ignored → fatal error +
  hint. `XmlConfig` 加 `#[serde(deny_unknown_fields)]`. 5 unit test (section
  / typo / flat / empty / alias).
- **BUG-007** `--{rest,ws,grpc}-keys-file` parse 失败 silent fall-back to
  legacy unauth → fail-closed (daemon abort). 3 surface 同步.
- **BUG-008** REST CORS protected endpoint `Access-Control-Allow-Origin: *`
  → loopback default + `FUTU_REST_ALLOWED_ORIGINS` allowlist (auth enabled).
  legacy unauth 仍 wildcard with WARN. 3 unit test (`is_loopback_origin`).

### 🟢 Fixed (P2)

- **BUG-010** MCP `futu_get_funds` 缺 `beginning_dtbp` 字段 (REST 已有).
  完整 9 字段 parity (is_pdt / pdt_seq / beginning_dtbp / remaining_dtbp /
  dt_call_amount / dt_status / net_cash_power / bond_assets / fund_assets).
- **BUG-011** 403 body 泄露 `key_id` / `required_scope` → 通用
  `{"error":"forbidden"}`. REST + WS + gRPC 同步. 详细 audit 信息留本地
  audit log, 不发请求方.
- **F-002** legacy WS handshake 接受 evil `Origin` → check + reject. 同
  CORS 策略 (env allowlist / loopback default / legacy permissive with WARN).
- **F-003** DEBUG `resp_body_hex` 记录 encrypted LoginRsp body → 仅记
  `resp_body_first4` (length + 类型 hint, 不再 hex dump 完整密文). proto14800 同步.
- **F-004** unlock-trade 缺本地 lockout → `UnlockCooldownTracker` 连续 2
  次失败 60s 冷却, daemon 不再转发 broker. 通用 msg "已暂停继续尝试" 不
  泄露精确次数. 失败 cooldown 期间 record_success 清零.

### Plan A — fund-market handoff (HKFUND=113 / USFUND=123, real-machine verified)

- 4 surface (REST / MCP / CLI / gRPC) `VALID_TRD_MARKET_INTS` + `TrdMarketEnum`
  + `parse_trd_market` + `TrdMarket::HKFund/USFund` 完整通连 (schema-runtime
  parser sync — 防 schema vs runtime drift).
- `cash_log_market_for_trd_market(trd_market) -> u32` translation helper:
  113 → 1 (HKFUND → MARKET_HK), 123 → 2 (USFUND → MARKET_US), main markets
  identity. backend 真机实测语义, 不是 mobile / C++ literal 转换. 4 unit
  test (HKFUND / USFUND / main / fallback).
- `/api/positions` `/api/history-orders` `/api/cash-log` `/api/funds`
  `/api/history-order-fills` 5 个 fund 账户 read endpoint 之前 HTTP 400
  reject, v1.4.102 通过.
- 真机 verify HK / US view-only HKFUND / USFUND 账户:
  fund 账户 cash-log 真机查询返回符合预期数据 (具体账户 / 资产规模脱敏,
  见 internal essentials/).

### 流程改进 (内部审计后修)

- 测试基础设施: 用户输入派生的注入式时钟避免假设当前 wall-clock; 不再用
  弱断言 "请求到了 X" 替代真实捕获.
- 文档校准: 中英 changelog "real-machine verified" 等措辞更精确.
- 内部档案补充 v1.4.99-102 review master report (essentials/, 内部用).
- PII 扫描扩 docs / process-name patterns; 公开 surface 内部术语 redact.
- 发版闸 essentials 必备文件检查 (release script `set -euo pipefail` + glob
  兼容; for-loop + `[ -f ]` 取代依赖 wc).

### 📝 沉淀

- 内部档案补充 BUG-009 SMS race 真根因教训 — 修复路径要在 `remember_login`
  **之前** 不在 **之后**, 否则任何 authority POST 都会 invalidate cached
  SMS, 检查放后面 = 永远跑不到. 7 版迭代教训, 与跨版本 regression 链 /
  半修 audit-only / backend-semantic / persistence helper / silent-success
  反模式关联.

### 测试

- `cargo test --workspace`: ✅ pass (workspace tests 累积, 含本版 +25 单元
  + integration 测试).
- `cargo fmt --check` ✅ clean.
- `cargo clippy --workspace -- -D warnings` ✅ clean.
- 真机 verify on HK (futunn) + US (moomoo) 账户: 见 v1.4.101
  session summary 真机 mega-batch (BUG-001 + Plan A + 部分 F2 deterministic).

### 升级提示

**🔴 必须升级**: BUG-001 ticker-statistic 100x 错 + BUG-002 silent success
+ BUG-009 SMS race + BUG-012 credentials 0644 = 4 项金融 / 安全级别. 多
用户机用户 / 量化 strategy 自动算昨收 / 长跑 daemon 频繁 SMS 失败的用户
**立即升级**.

---

## [1.4.101] - 2026-04-28 🟢 option-chain codex 19+20 轮 hotfix (8 项, follow-up)

**v1.4.100 ship 后 ~6h codex 又跑两轮 audit**, 抓 8 项 P2/P3 finding (DST 边
界 / default 时区 / partial-row 严格 / qot_right 语义 / shared TZ helper).
都属于 v1.4.100 修法的 follow-up 收紧, 健康用户感知 ≈ 0.

### 修复

- **DST 30d+1h check**: 改用 owner-market unix ts diff (chrono-tz `from_local_datetime`),
  之前 `NaiveDateTime - NaiveDateTime` US DST 边界差 ±1h (codex 18th F1 part 2).
- **default begin/end owner-market today**: 之前 hardcode HKT, US 期权在 HKT
  vs EDT 跨日窗口偏移 1 天跳过当日到期 (codex 19th F1 / 20th F2).
- **ExpirationDate partial-missing left_day → loud fail**: 之前 partial-skip
  + 全空才 fail; 任一 row 缺 left_day 现 loud fail 防 silent drop (codex 19th
  F2 / 20th F3).
- **删除 production pub test helper**: 改用真 `QOT_GET_STATIC_INFO` handler
  dispatch + cache hit 计数验 suffix strip (codex 19th F3).
- **`has_us_option_qot_right` C++ 语义对齐**: `qot_right != BMP` 替代 RT-flag
  (Unknown / Level1 / SF 都 true, 仅 confirmed BMP false) — C++
  `GetUserInfo.bHasUSOptionRight` 一致 (codex 19th F4).
- **shared TZ helper**: 3 处 hardcoded TZ table → `futu_core::market::qot_market_to_tz`
  统一 (codex 20th F4).

### 测试

- 1656 + 3 个新 integration tests (US empty default / partial left_day /
  qot_right C++ semantic) = 34 整 file
- 1656+ workspace tests pass · fmt + clippy clean

## [1.4.100] - 2026-04-28 🟡 option-chain codex audit 5 轮 hotfix (23 项) + 真机 verify

**推荐升级 (期权链用户)**. v1.4.99 ship 后 codex 连续 5 轮 (14-18) audit
共抓 23 项 silent-success / C++ 偏离 / 测试覆盖空洞. AI agent 真金白银场景
直接相关 — 期权决策若 silent drop / wrong tz / wrong owner code 即转化为错单.

HK `<account>` + US `<account>` 全 endpoint 真机 verify PASS.

### 修复

- **CutCodeMarketSuffix** (3 处): option-chain response / on-demand cache /
  subscribe fallback. 公开 `Security.code` 不再含 `.US` / `.HK` 后缀
  (与 C++ `NNBiz_Qot_StockInfoReq.cpp:6` 对齐). 防 cache key 污染.
- **OptionStaticExData 4 字段补齐**: `suspend` / `index_option_type` /
  `option_standard_type` / `option_settlement_mode`. 之前硬编 false / None,
  AI agent 看不到停牌 / 标准合约 / AM-PM 结算等关键 metadata.
- **owner-market timezone**: strike_time 改用 `c2s.owner.market` 替代硬编
  HKT. US 期权跨午夜边界不再错日 12h (与 C++ `TimeStampToAPITimeStr_Qot
  (ts, enMarket, true)` 对齐).
- **`index_option_type` owner-gate**: 仅 HSI=800000 / GQI=800100 underlying
  emit, 与 C++ `GetStockStaticInfo` 一致. 非指数期权字段 absent.
- **strike_dates dedup** by `(strike_date, expiration, left_day)`: 之前
  backend 重复 row 直接 emit, AI agent 看到重复 contracts 误选.
- **enum mapping helpers**: `standard_type` / `settlement_mode` 未知值不再
  raw pass-through, `settlement_mode=0` 与 C++ presence absent 对齐.
- **ExpirationDate strict structured/legacy**: 之前 `unwrap_or(0)` 缺
  `strike_date` / `left_day` 时 silent 1970 日期; 修后 loud fail. left_day
  必须从 backend 来 (不本机时间合成).
- **time parser 扩展**: 接受 `HH:MM:SS` time-only / fractional seconds (与
  C++ `APITimeStrToTimeStamp_Qot` 一致).
- **QotRightData::default Unknown**: 之前默认 BMP=1 让 backend rights push
  之前的 US option 请求 silent reject. 修后默认 Unknown=0, 仅 confirmed BMP
  才 reject (与 C++ `GetUSOptionQotRight()` 一致).
- **ticker-statistic strict 4-path**: extracted helper, 测试直调实际 branch
  (覆盖 flat/nested × snake/Pascal owner).

### 测试 + verify

- 1656 workspace tests pass · fmt clean · clippy clean
- 31 个新 integration tests (`tests/integration_option_chain.rs`)
  with `MockBackendBuilder` 真捕获 CMD 6311/6736/20106 wire bytes
- 真机 verify: HK `<account>` (4 endpoint) + US `<account>` (4 endpoint) 全 PASS
- 真机 evidence: HK 0700 109 strikes / US AAPL 161 options / HSI 213 options /
  NVDA on-demand snapshot cache hit

## [1.4.99] - 2026-04-27 🟢 codex audit hotfix — 5 项 silent-success / schema 收紧

**可跳过此版**, 仅修 v1.4.98 ship 后 codex 审计抓的 5 项工程债. 行为可见
影响仅 typo-fail-loud (之前 silent default 的客户端会看到 400, 但 typo
本身就是 bug).

### 修复

- **F1 (P1)** TickerStatistic silent-success: 之前 `ret_code.unwrap_or(0)`
  把 backend "无 ret_code 字段" 当成功. 修法: 显式 require Some(0) +
  meaningful payload (date_list / ticker_time / 任一 stat field).
- **F2 (P2)** RiskFreeRate / TickerStatistic 把 mapping 拆 pure fn
  (`map_*_rsp_to_daemon`), unit test 现真 exercise mapping 而非只构造
  backend rsp. 6 个新 regression tests.
- **F3 (P2)** TickerStatistic 删 proto `owner` 字段 (v1.4.98 just-to-pass
  strict, 但 handler 不读 = silent inconsistency). 改在 REST strict
  validator 入口 strip adapter-injected owner.
- **F4 (P2)** SpreadTable + TickerStatistic CLI `-o jsonl` 之前 fall
  through 到 table branch, 修后 Json/Jsonl 都走结构化输出.
- **F5 (P2)** TokenStateQuery (GET `/api/token-state?app_id=...`) 加
  `#[serde(deny_unknown_fields)]` — 之前 typo `?app_idd=nn` silent 默认到
  `all`, 修后立即返 400.

### 测试

1047+ workspace test PASS, +9 new regression tests. fmt + clippy clean.

## [1.4.98] - 2026-04-27 🟡 字段曝露扩展 + 4 新 endpoint + 6 项外部反馈修复

**推荐升级**. 基于完整移动端协议代码调研, 落地 12 项字段曝露 / 新 endpoint
候选, 4-surface 全对称 (REST / MCP / CLI / gRPC); 同时整合外部 reviewer
跨账户真机自查报告的 6 项 confirmed bug.

### 字段曝露 (零 backend 风险)

- OrderFill `sec_market` 派生 (4-layer fallback)
- TrdAcc `acc_label` 扩展: paper_trade / equity_incentive / ipo_route
- CapitalFlow 5 资金流向字段 (主力 / 超大 / 大 / 中 / 小单)
- Order session + jp_acc_type 字段透传
- Funds PDT 6 字段 (Pattern Day Trader 美股账户必备)
- IpoOut 13 字段补全 (HK 5 / US 1 / CN 9)
- OptionChain strike_price + 6 静态字段
- Snapshot 加 3 ExData 类型: EquityFundamental (16) / Warrant (16) / Future (5)

### 4 个新 endpoint (4-surface 全对称)

- **GetTokenState** (cmd 1326) ✅ 真机 PASS: 双系 token 启用/绑定状态查询.
  unlock-trade -20011 第一线诊断
- **SpreadTable** (cmd 6503) ✅ 真机 PASS: 价格档位表 (PlaceOrder /
  ModifyOrder 价格合法性校验)
- **RiskFreeRate** (cmd 20231) ⚠️ backend wire-format 兼容研究中:
  HK / US / JP 3 市场无风险利率
- **TickerStatistic** (cmd 6365) ⏸ schema 已对齐, 待真机 verify

### 外部 reviewer 6 bug 修复

- **BUG-001 (P1)** US option-chain 返空 contracts: 按 underlying head market
  路由 NN_QuoteMktType (HK_OPTIONS / US_OPTIONS) 修 CMD 6311+6736
- **BUG-002 (P1)** option-chain 不传日期失败: empty begin/end → today +
  today+60d default (与 mobile App 一致)
- **BUG-003 (P0/P1)** 19 quote endpoint silent accept unknown fields: 加入
  STRICT_PATHS 严格 reject typo
- **BUG-004 (P2)** MCP global-state 缺 12 字段 vs REST: 全对齐
- **BUG-005 (P2)** CLI 6 命令缺 `-o json`: ping / sub / unlock-trade /
  history-kl-quota / query-subscription / max-qtys 全加 JSON 输出
- **BUG-006 (P2)** CLI kline default count 滑窗过宽: lookback 收紧为
  `ceil(N*7/5)+3` 紧贴 N 交易日

### 工程

- 总 ~2000 LoC, +18 单元测试
- ADD-only, 无 schema breaking, 不影响现有客户端

## [1.4.97] - 2026-04-27 🟡 三方 tester 反馈整合 hotfix (cash-log 实战 + P1-D safety + observability)

**推荐升级**. v1.4.96 ship 后 24h 内收到 3 份独立 tester 反馈, 本版整合 P0/P1
修复 + observability 改进 + doc gap 补全.

### 🟡 Fixed (P0) — Tier J: cash-log 实战反馈 (mac mini 双 OpenD 实例 / 27 子账号 / 1 年 5928 cash-log 样本)

- **J1.6 加密账号 cash-log silent empty (defensive check)**:
  external tester `/api/cash-log` 对加密账号 (acc_type=Cash + 空 trd_market_auth_list)
  silent 返空 monthly_log_list, 看似"无流水". 修: 3 个 handler 入口
  (cash-log / cash-detail / biz-group) 加 defensive check 返
  `ret_type=-1` + 清晰错误. 复用 `CachedTrdAcc::is_encrypted()` helper
  (per pitfall #45 silent-success defense).
- **J1.7 cash-log 缺 currency 字段**:
  实战反馈显示客户必须 regex 解析 `balance` 字符串 ("余额: 3,929.13 USD") 拿币种.
  修: daemon `derive_currency_from_balance` helper 从 balance 末 token 提取
  currency code (HKD/USD/CNH/CNY/JPY/SGD/AUD/CAD/MYR/USDT), 填到 CashLog.currency.
  Backend 不返此字段 (per 9-agent 源码调研: C++ + 手机端 NN proto 都无).
- **J-Acc-Q3 加密账号无专属 enum, daemon derived `acc_label`**:
  Trd_Common.proto:24-46 TrdMarket enum 跳过 7 (6=SG → 8=AU), 缺 Crypto code.
  v1.4.97 daemon REST `/api/accounts` 返回每个 AccItem 加 derived
  `acc_label: Option<String>`, v1.4.97 仅 `crypto` 值 (acc_type=Cash + 空
  trd_market_auth_list). 未来扩展 equity_incentive / ipo_route. 客户端应
  treat unknown labels as opaque strings.
- **J1.1 cash-log silent truncation — 文档警告 + 客户端策略推荐** (代码 0 改动):
  external tester 实测本地 5928 → 线上 5093 (14% drift) silent (HTTP 200 / ret_type=0
  / has_more=false). v1.4.97 first attempt 加启发式 daemon-side detection
  (`max_cnt × 0.1` 阈值) — 自跑 density test 实证 **140 次 false positive**
  跨 0% drift 数据 (单月几条流水的正常账户被误判).
  跨 mobile + desktop App 源码审计
  (`FTTradeSecurityAssetDetailRequester.mm:193` /
  `FTTradeCryptoAssetDetailRequester.swift:323`) 确认 **App 直接 trust
  `has_more` + `next_log_id`, 0 retry / 0 detection** — App 不暴露此问题
  是因为 App 不做 backfill state 推进, 不是 App 真修了.
  **真根因**: backend 限流 (per "sleep 30s 恢复" + external tester scenario =
  双 OpenD 实例 + 同源 IP 双倍 traffic + 27 子账号 + 12 month windowed 高频
  query 触发 backend rate-limit). daemon 修不了 backend 限流, 也不应破坏与
  App silent trust 行为一致性.
  **v1.4.97 取舍**: 删除 daemon-side heuristic detection (避免 false positive),
  保留 `is_partial` + `partial_reason` proto field 给未来 backend truncation
  signal 用. 客户端 backfill 推荐策略写入 docs-site rest-api.md cash-log §
  (cross-call sanity check + 不简单 trust has_more=false + 保守 state
  推进). proto 改动 + 客户端 doc gap fill, 0 daemon code path 改动 vs
  v1.4.96 silent baseline.

### 🟡 Added (P1) — Tier P1-D: 4-tester P1-D consolidated 报告 (87.21h sample, 0 ladder triggered) follow-up

- **P1-D-A run_qot_login_health_loop observability**:
  v1.4.92 P1-D ladder healthy 状态 0 log emit (silent-healthy 反模式).
  4-tester 87.21h sample 无法区分 "wiring alive 静默" vs "死代码". 修: 加
  startup log (interval/ladder/initial state) + heartbeat log every 5 min
  ("P1-D loop alive ...") 让 ops 能 grep `journalctl | grep "P1-D loop"` 验证.
- **P1-D-B `FUTU_QOT_RELOGIN_BACKOFF_MS` env tunable**:
  ladder 常数 [60_000, 120_000, 240_000, 600_000] 改 env-tunable (default
  unchanged). Tester 真机 verify ladder 时改 `=5000,10000,20000,40000` 让
  full ladder 在 ~75s 内全 trigger 而不是 7+ min. parse_relogin_backoff_env
  helper + 10 unit tests (default/empty/whitespace/happy/wrong-count/non-u64/
  zero/overflow/field-default/relogin_backoff_ms-uses-field).
- **P1-D-C `--inject-auth-failure-every` dev flag** (新 Cargo feature `dev-flags`):
  Cargo `[features] dev-flags = []` (default off). Release build (无 feature)
  flag 不可见, 防 production 误启用 (per pitfall #50 SPKI dev pattern).
  CI 必须 build 双模式: `cargo build --release` + `cargo build --release --features dev-flags`.
- **P1-D-D panic_hook + dated crash log** (`~/.futu-opend-rs/crashes/crash-{unix_ts}.log`):
  对齐 C++ NNCrashCenter pattern (NNCrashCenter.cpp:6-54). 同步写文件含
  daemon_version + unix_timestamp + os/arch + thread + location + payload +
  backtrace. 启动时 scan crashes/ dir, warn-log 最新 crash 文件路径.
- **P1-D-E panic → process exit (systemd Restart=on-failure)**:
  post-tracing panic_hook 末尾 `std::process::exit(101)` (cfg(not(test)) 不
  影响 unit tests). 之前 tokio task panic 静默 kill task only, daemon 僵尸.
  对齐 C++ NNCrashCenter `exit(NN_ExitCode_Crash)` (NNCrashCenter_Mac.cpp:99).
- **P1-D-F admin telnet `relogin` (对齐 C++)**:
  对齐 C++ `GTWCmd_ReLogin` (FTGateway/FTGTW_Define_Key.h:5) 命令名 — 不
  创新 `force_reconnect_backend` (per pitfall #51 "对齐 C++ = 减法").
  TelnetServer `with_relogin_fn(Arc<dyn Fn() + Send + Sync>)` builder. main
  wires closure: `bridge.login_cache.clear()` → 下个 30s P1-D tick 触发
  AuthRefresher relogin via 现有 v1.4.92 P1-D ladder 路径.

### 🟢 Docs (P0) — Tier D: external tester 26 项反馈中 7 项 doc gap 一次性补全 (rest-api.md 中英双语)

- **D1 biz_type_id 完整枚举**:
  `/api/cash-log` 返回的 biz_type_id 由 backend 动态返回 (cmd 3002), 不应
  hardcode. 加客户端 best-practice (启动时 cache backend 表) + 来自真实反馈的
  5928 sample 实测 top freq 表 (84/10017/10018/10046 等动态值用 title 二次
  分类).
- **D2 时区警告**: cash-log `created_time` 是 HKT (UTC+8) 单一时区, vs
  history-orders/history-order-fills `create_time` 跟 trd_market 时区. 客户端
  应永远用 timestamp 字段不解析字符串.
- **D3 acc_role=3 双语义**: 协议命名 IPO 但实际同时承载激励账号 (RSU/ESPP).
  daemon 启发式区分 (acc_role=3 + market=[2] → 激励; market 多市场 → IPO).
- **D4 加密账号识别 + acc_label**: doc 加密账号 daemon-derived acc_label
  field 说明 (v1.4.97 仅 `crypto`).
- **D5 enum 权威表 corrections**: 纠正常见 SDK 注释错误:
  TrdAccType 3=TFSA (不是 FUTURES) / 4=RRSP (不是 CRYPTO) /
  SecurityFirm 2=FutuInc (不是 moomoo) /
  TrdMarket 113=HK_Fund (不是美股期权) / 123=US_Fund (不是港股期权) / 15=JP.
- **D6 jp_acc_type 触发条件**: 仅 security_firm=7 (FutuJP) 填充, 8 个 enum
  值 (GENERAL/TOKUTEI/NISA_GENERAL/NISA_TSUMITATE 等).
- **D7 模拟盘 trd_market_auth_list 协议外值**: 100=Sim_US_Margin 是
  daemon-internal only, 不在 proto. 客户端应 graceful 处理 unknown enum.

### 🟣 Tier U — UNVERIFIED 状态 (跨版本 follow-up, 等真机 verify)

- **BUG #002 (v1.4.96)**: option-chain 默认 chain_count=0 — 等 tester 真机
  `curl -X POST .../api/option-chain -d '{"sec_market":1,"code":"00700","option_type":1}'` → 期望 chain_count > 0
- **BUG #007 (v1.4.96)**: moomoo Token 2FA -20011 — 等 tester moomoo Token
  2FA 真账户 `/api/unlock-trade` → daemon log "sending CMD2901"
- **G1/G4/G5/G6 (v1.4.94)**: 长跑 / 风控 / moomoo 账户 / 真 device_model
  verify path — 跨多版未验证, env opt-in default OFF (per pitfall #57)

若 tester 真机 verify pass → 后续版本 doc 升 verified (代码不动).

### 🛠 工程 / 构建

- 9 个并行 Explore agent 源码层调研 (C++ OpenD + 手机端 NN + moomoo + 桌面端)
  详见 `essentials/2026-04-27-0345-v1.4.97-source-investigation-9-agent.md`
  (3-tester 反馈整合背景见 `essentials/INDEX.md` §3 v1.4.96 实战 entry).
- 测试: P1-D-B 10 unit + cash-log J1.7 currency derive 10 unit + J1.6/Q3
  CachedTrdAcc helper 5 unit + cash-log J1.1 detection inline. 总新增 ~25
  tests, baseline 1555 → 期望 ~1580.
- proto: `proto/Trd_Common.proto` 加 `accLabel = 12`;
  `proto-internal/realtime_asset_log.proto` GetCashLogRsp 加 `is_partial = 12`
  + `partial_reason = 13`, CashLog 加 `currency = 20`.
- Cargo: `crates/futu-opend/Cargo.toml` 加 `[features] dev-flags = []`.

## [1.4.96] - 2026-04-26 🚨 外部 double-tester 13/13 bug 全清 hotfix

**必须升级**. 外部 double-tester (moomoo + futunn 双账号 8 轮 cross-verify)
8 轮 cross-verify 报告 13 bug, v1.4.94 + v1.4.95 共有, 全 fixed:

| Pri | BUG | Fix file |
|---|---|---|
| 🚨 S | #001 scope-mode 100% 404 for 10 Tier M endpoints | `crates/futu-rest/src/auth.rs` scope_for_path ACC |
| 🚨 S | #002 option-chain default returns 0 (C++ baseline 796) | `crates/futu-gateway/src/handlers/qot/option.rs` expiration_cycle |
| 🔴 P0 | #003 trd_market validator missed 5 endpoints | `crates/futu-rest/src/routes/trd.rs` validate_header_trd_market 5 sites |
| 🔴 P0 | #004 STRICT_PATHS missed 13 endpoints (silent typo) | `crates/futu-rest/src/strict_fields.rs` 26 endpoints + 11 dispatch arms |
| 🔴 P0 | #005 HK index futures exchange_code null | `crates/futu-core/src/exch_type.rs` 19=HKFE + bridge mkt_id ranges |
| 🔴 P0 | #006 cancel-all-order flat body modify_op=0 (data corruption risk) | `crates/futu-rest/src/routes/trd.rs` promote_flat_body_to_c2s |
| 🔴 P0 | #007 moomoo CMD2901 unreachable for Token 2FA | `crates/futu-gateway/src/handlers/trd/unlock.rs` -20011 trigger |
| 🟡 P1 | #008 MCP otp/token/one_time_password alias silent drop | `crates/futu-rest/src/routes/trd.rs` apply_unlock_trade_otp_aliases |
| 🟡 P1 | #009 4 UX symptoms (silent typo / 毫秒 epoch / cash-detail msg / 404 hint) | 跨 cash_log + server.rs |
| 🟡 P1 | #010 G6 log "moomoo-path" mislabel (universal field) | `crates/futu-backend/src/auth/{parse,mod}.rs` |
| 🟡 P1 | #011 CLI kline default end_time stale (Local→UTC) | `crates/futucli/src/cmd/kline.rs` |
| 🟡 P1 | #012 CLI funds missing currency column | `crates/futucli/src/cmd/account.rs` |
| 🟡 P1 | #013 sim funds currency partial fix | `crates/futu-gateway/src/handlers/trd/query.rs` 4-layer |

**1555 workspace tests pass / 0 failed** (+24 new). 跨 7 bug 端到端真机
verify (`scripts/v1496_real_machine_verify.sh <account> --platform futunn`):
**27/27 PASS**.

### 🚨 Severity S — Ship Blockers

#### BUG #001 — scope-mode 100% HTTP 404 for 10 Tier M endpoints

**Root cause**: `scope_for_path()` ACC list 缺 v1.4.94 + v1.4.95 Tier M
全 10 个 endpoint. bearer_auth fail-closed 返 HTTP 404, production scope-mode
用户 100% 调不到 Tier M.

**Fix**: 加 10 endpoint to ACC list (`acc:read` scope).

#### BUG #002 — option-chain default returns 0 options

**Root cause** (C++ alignment, `NNBiz_Qot_Option.cpp:215-225`):
daemon CMD 6736 `expiration: None`, C++ 必传
`set_expiration((u32_t)stStrikeDate.enType)`. backend 缺 expiration =
"no match", 三 surface 默认参数返 0 vs C++ baseline 796.

**Fix**: 新 helper `filter_strike_dates_by_user_range_with_cycle` 同时收集
`expiration_cycle[i]` (1-1 mapping), 传给 combo_req.

⚠️ **UNVERIFIED**: backend `expiration: Some(0)` fallback semantic 等同
"no filter" 是假设 (pitfall #42). 真机 verify path: 调 `/api/option-chain
HK.00700` 默认参数, 期望 chain_count > 0. 真机 verify 后下版升级 confidence.

### 🔴 P0 Bugs

#### BUG #003 — trd_market validator 加 5 endpoint

5 endpoint 之前 silent accept `trd_market=999`: modify-order /
cancel-all-order / reconfirm-order / history-orders / history-order-fills /
order-fee. 修后全返 400.

#### BUG #004 — STRICT_PATHS 扩到 26 endpoint

`STRICT_PATHS` 15→26 + 11 个 per-path validate_for_path arms. 全 Tier M +
写路径 silent typo 现在拒 400.

#### BUG #005 — HK index futures exchange_code 派生

加 daemon-internal `exch_type=19="HKFE"` (proto enum 不含 HKFE 但 i32 接受).
`market_code_to_exch_type` 加 110-119 → 19, 160-169 → 17 (SGX), 180-189 → 18
(OSE).

#### BUG #006 — cancel-all-order flat body modify_op fix

handler 入口 `promote_flat_body_to_c2s`: 检测 flat body 转 c2s wrapper,
让 `c2s.insert("modify_order_op", 2)` 强制覆盖路径生效. 防 real env
modify_op=0 误改订单.

#### BUG #007 — moomoo CMD2901 Token 2FA path

Phase 2 trigger filter `r.result_code == -8` 改为 `(-8 || -20011) &&
auth_pswd_sig.is_some()`. moomoo backend 对 Token 2FA 账户 CMD2900 返
`-20011` (而非 -8), 之前 Phase 2 不触发 → CMD2901 永不发. 修后正常.

⚠️ **UNVERIFIED**: 需真机 moomoo Token 2FA 账户验证 (我们当前账户无 token
2FA). 真机 verify path: moomoo 账户开启 token 2FA → 调 unlock-trade 带 OTP →
观察 daemon log "sending CMD2901". 真机 verify 后下版升级.

### 🟡 P1 Bugs (UX / 数据展示)

#### BUG #008 — REST sec_otp alias for MCP `otp`/`token`/`one_time_password`

新 helper `apply_unlock_trade_otp_aliases`: 在 unlock-trade handler 入口
rename alias 为 `sec_otp`, **同时 strip 所有 alias key** 防 strict_fields
deny_unknown_fields 拦 400. 显式 sec_otp 优先.

#### BUG #009 — REST UX 4 症状全修

- **Sym 1** silent typo drop: 由 BUG #004 STRICT_PATHS 扩展自动修
- **Sym 2** cash-detail "log_id 必填" 信息不足: error msg 改为完整 body
  shape + 来源 + 示例
- **Sym 3** 毫秒 epoch overflow "year 58286": 加 `check_epoch_seconds_range`
  helper, 拒 + 智能 hint "val/1000 试试"
- **Sym 4** /api/foobar 404 plaintext: 加 `unknown_route_fallback` 返
  JSON 含 5 类 endpoint 列表 + futuapi.com 文档 URL

#### BUG #010 — G6 log doctrine fix

log label 从 "parsed moomoo-path credentials" 改为 "parsed US-market
credential fields (universal — backend 对支持 US 的所有账号下发)". audit
全代码库, **0 routing 决策** 基于 mm_sig (无 P0 紧急 hotfix 需要). 加
`AuthResult.moomoo_client_sig` doc warning.

#### BUG #011 — CLI kline default end_time

新 helper `default_end_date_today_utc()` 用 `Utc::now().date_naive()` (与
daemon-side `history_kline.rs::now_utc` 对齐), 替代 `Local::now()` 防跨
市场 TZ 偏移导致 end_date 跨日返 stale K.

#### BUG #012 — CLI funds 加 currency 列

新 helper `currency_int_to_str()` 映射 proto Currency enum (1=HKD..9=USDT).
FundsRow + FundsJson 加 currency. 3-surface (REST/MCP/CLI) 一致.

#### BUG #013 — sim funds currency 4-layer fallback

3-layer (security_firm > backend cache > acc_trd_market) 加第 4 层
`primary_currency_by_trd_market(header.trd_market)`. cache miss 时仍能
派生 currency.

### 🧪 Self-test (3 层)

- **L1 unit + integration**: 1555 tests pass (+24 new), 4 integration tests
  cover BUG #001/#003/#004 + neg control
- **L2 cross_surface_smoke**: 16 cells (6 trd_market=999 + 10 typo)
- **L3 real-machine** (我们自己跑, scope-mode daemon):
  `scripts/v1496_real_machine_verify.sh <account> --platform futunn` →
  **27/27 PASS**

### Pitfall #42 / #57 UNVERIFIED 项 (待真机 verify)

- BUG #002 expiration_cycle fallback 0 semantic
- BUG #007 moomoo Token 2FA -20011 + auth_pswd_sig 真返
- (legacy v1.4.94 G1/G4/G5/G6 长跑 / 风控 / 账户依赖 verify)

### 持续 defer 项

- moomoo OTP 真触发 (账户无 token 2FA)
- B1 HK NIGHT_OPEN 真夜盘
- B3 P2-B sudo iptables circuit-break
- G2 RepullAuthCode 30 day verify
- F1/F2 P3 protocol gap (无证据)
- G7 attribution refresh (跨地理迁移)
- S BUG-5318-009 真机 cancel test (US trading hours)

### 文件变化

| 类别 | 修改 |
|---|---|
| futu-rest auth/strict/routes/server | 5 文件 (BUG #001/#003/#004/#006/#008/#009 sym 4) |
| futu-gateway handlers (cash_log/option/query/unlock) | 4 文件 (#002/#005 utils/#007/#009 sym 3/#013) |
| futu-core exch_type | 1 (#005) |
| futu-backend auth (parse/mod) | 2 (#010) |
| futucli (kline/account) | 2 (#011/#012) |
| 新 integration test | 1 (`integration_v1496_hotfix.rs`) |
| 新 real-machine script | 1 (`v1496_real_machine_verify.sh`) |

## [1.4.95] - 2026-04-26 🟡 Tier M 移动端主动扩展第二波 (margin info + account flag + bond holdings) + 4-surface 全对称 (REST/MCP/CLI/gRPC)

**推荐升级**. 三件事:

1. **Tier U** (mobile-driven extensions 第二波): 3 个新 endpoint family —
   per-account margin info (HK/US/CN_AH) + 账户合规标志 (36+ flag_id) +
   债券 holdings & trade prep (5 endpoint, HK/US/SG)
2. **U1 MCP 补齐**: v1.4.94 推迟的 cash log 3 个 MCP tool 实装
   (`futu_get_cash_log` / `futu_get_cash_detail` / `futu_get_biz_group`)
3. **CLI + gRPC 全对称**: v1.4.94 (cash log) + v1.4.95 (margin/flag/bond)
   全 11 endpoint 在 4 surface (REST + MCP + **CLI** + **gRPC**) 全对称

**1517 workspace tests pass / 0 failed** (+37 vs v1.4.94 baseline 1480).

### 🟡 Tier U — Mobile-driven extensions 第二波

延续 v1.4.94 pitfall #51 修订 doctrine: user-facing features 跟 mobile 节奏,
. 来源必须 Futu 自家 proto, OpenD 兼容 0 破坏, 失败 loud.

#### `/api/margin-info` per-account margin (U2-D, cmd 3101/3102/3107)

与现有 `/api/margin-ratio` (per-security ratio) 互补, 给账户全景:
购买力 (long/short) / 余额 / 净值 (elv) / 保证金 (im/mm/mm_balance) /
风险等级 / 流动性 / 杠杆 / HK-specific 港股保证金. 12 字段子集 (mobile
30+ 全集 deferred).

按 `header.market` 字符串路由: HK→cmd 3101 / US→cmd 3102 / CN_AH→cmd 3107.

#### `/api/account-flag` 合规标志查询 (U2-A, cmd 5281)

高级交易准入 (期权 / 衍生品 / OTC / CFD 等) 强制要求 flag=1. LLM agent
下单前可 sanity check. 支持 36+ 个 flag_id, 常用值: 5=US 期权, 22=衍生品风批,
10=基金 KYC (R1~R5), 16=PDT, 23=美股 OTC, 11=HK 期权, 24=港股期权测评, 等.

daemon 自动派生 `uid` from `backend.user_id`, client 不需传.

#### `/api/bond-*` 债券 holdings + trade prep (U2-B, 5 endpoint)

债券持有者完整查询能力 (之前 daemon 完全缺):

| endpoint                  | mobile cmd  | 用途                       |
|---------------------------|-------------|----------------------------|
| `/api/bond-total-asset`   | 9373        | 账户债券总持仓 (P&L 汇总)  |
| `/api/bond-single-asset`  | 9374        | 单只债券 (含派息/到期/通知) |
| `/api/bond-position-list` | 9375        | 账户债券持仓列表           |
| `/api/bond-answer-state`  | 10043       | 是否需要答题 (suitability) |
| `/api/bond-trade-reminder`| 10057       | 交易提醒 (是否可买/复杂/高风险) |

按 `header.market` 路由: HK→13 / US→23 / SG→6. 仅 HK / US / SG 债券账户
有数据, 其他账户 backend 自动返空 (优雅).

### 🟡 Tier U1 — M1 MCP 工具补齐

v1.4.94 cash log 已有 REST + gRPC, MCP tool 推迟到 v1.4.95. 本版补齐:

- `futu_get_cash_log` — 资金明细查询 (镜像 `/api/cash-log`)
- `futu_get_cash_detail` — 单条资金详情
- `futu_get_biz_group` — 业务分类元数据

3 个 tool 全 `acc:read` scope (pitfall #37 4-site sync: tools.rs handler +
guard.rs::scope_for_tool match arm + 2 known lists).

### 🟢 Tier U-CLI + gRPC — 4-surface 全对称

v1.4.95 ship 前 CLI + gRPC 状态 audit 发现:
- **CLI**: 11 个 Tier M endpoint **零** subcommand (futucli 之前漏了)
- **gRPC**: `scope_for_proto_id` 22701-22710 fall-through `_ => TradeReal`,
  acc:read scope key 调不到这些 endpoint (silent fail-closed gap)

**CLI 11 个新 subcommand** (`crates/futucli/src/cmd/tier_m.rs` ~575 LoC):
`cash-log` / `cash-detail` / `biz-group` / `margin-info` / `account-flag` /
`bond-total-asset` / `bond-single-asset` / `bond-position-list` /
`bond-answer-state` / `bond-trade-reminder`. 默认 JSON pretty 输出
(11 endpoint 字段较多 + 嵌套结构, table view 不易表达).

**gRPC scope_for_proto_id**: 加 `22701..=22710 => Some(Scope::AccRead)`
显式覆盖 + `proto_scope_v1495_tier_m_endpoints_acc_read` test (loop
22701-22710 + 边界 22700/22711 → TradeReal 验证).

**4-surface 完整覆盖矩阵**:

| endpoint family       | REST | MCP | CLI | gRPC |
|-----------------------|:----:|:---:|:---:|:----:|
| cash log (3, M1)      | ✅   | ✅  | ✅  | ✅   |
| margin info (1, U2-D) | ✅   | ✅  | ✅  | ✅   |
| account flag (1, U2-A)| ✅   | ✅  | ✅  | ✅   |
| bond × 5 (U2-B)       | ✅   | ✅  | ✅  | ✅   |

### 🟢 Tier R — 工程纪律

- **R1** `essentials/multi-version-fingerprint.json` baseline 加 13 新 signals
  (Tier U + Tier U2-D/A/B endpoint markers); STRICT mode `multi_version_smoke.sh`
  通过
- **R2** `scripts/cross_surface_smoke.sh` 加 8 个 bond endpoint silent-accept
  guards (acc_id=0 / empty body / unsupported market / missing symbol)
- **R3** Tier M 真机 verify markdown 给 tester
  (`essentials/2026-04-26-1100-v1.4.94-v1.4.95-real-machine-verify-request-for-tester.md`)
  汇总 v1.4.94 G1/G4/G5/G6/M1 + v1.4.95 U2 endpoints 的 11 个 verify section

### ⚠️ UNVERIFIED / 真机 verify pending

3 个 endpoint family backend 接受度仍 **未真机 verify** (pitfall #42
backend-semantic risk):

- **U2-D margin info**: backend 接受 12 字段子集是假设 (mobile 30+ 全集
  scope)
- **U2-A account flag**: cmd 5281 + GetFlagReq 是假设
- **U2-B bond × 5**: cmd 9373/9374/9375/10043/10057 接受度全假设

真机 fail 时 daemon log warn + ServerError(-1) + clear hint 返客户端
(failure loud). 真机 verify 后下版升级 confidence (默认 OFF → 默认 ON
对齐 pitfall #57).

### 文件变化

| 类别 | 新增 | 修改 |
|---|---|---|
| proto-internal | 1 (bond_client_view.proto) | 0 |
| futu-gateway handler | 1 (bond.rs) | 4 |
| futu-rest routes | 0 | 2 |
| futu-mcp handler/tools/guard | 0 | 3 |
| futucli (新 surface) | 1 (tier_m.rs) | 4 |
| futu-auth (gRPC scope) | 0 | 1 |
| 跨 cm proto_id constants | 0 | 1 |
| scripts (R1+R2) | 0 | 2 |
| essentials | 1 (verify markdown) | 1 (fingerprint) |

### 🧭 流程纪律

- pitfall #57 backend-semantic feature 默认 env opt-in default OFF —
  v1.4.94 G1/G4/G5/G6 沉淀, v1.4.95 U2 候选继承 (UNVERIFIED 标记 +
  真机 verify markdown 给 tester)
- 4-surface 对称纪律: 每次新加 endpoint 必须 audit REST + MCP + CLI + gRPC
  全覆盖 (v1.4.95 ship 前发现 CLI/gRPC gap, 后续 plan 必列 CLI/gRPC 作 surface)

## [1.4.94] - 2026-04-26 🟡 C++ FTLogin 协议 gap 全填 (G1-G8) + Tier M mobile-driven 主动扩展 (cash log + cost methods + Option Greeks)

**推荐升级**. 双线并行:
1. **Tier G** (P1/P2/P3 protocol gap): G1/G4/G5/G6/G8 - 对齐 C++ `auth_impl.cpp`
   长跑 daemon 加固 + 3FA + moomoo creds + 真 device_model
2. **Tier M** (mobile-driven extension): 移动端源码到了, 主动扩展 — cash log
   (cmd 3000) + Position cost methods + Option Greeks. 

8 项交付一版, 1480 workspace tests pass (+44 vs v1.4.93 baseline 1436).

### 🟡 Tier M — Mobile-driven extensions

新 doctrine (pitfall #51 v1.4.94 修订):
- **Safety hardening**: 仍 "对齐 C++ = 减法" — 不做 C++ 没做的 cert pinning 等
- **User-facing features**: "**移动端协议有 = 可主动扩展**" — daemon 跟 mobile 节奏,
  . 来源必须是 Futu 自己的 proto (mobile/desktop/OpenD 任一),
  OpenD 兼容 0 破坏, 失败 loud (不 silent fallback).

**v1.4.94 实证发现**: 移动端 `clt_cmd_*` 与 OpenD `NN_ProtoCmd_*` 同 backend
TCP cmd_id namespace. mobile 能调的 cmd backend 都支持 — OpenD 只是没把这些
cmd 暴露给 FTAPI 而已. daemon 直连 backend (port 9595, 与 OpenD 同层),
**不依赖 OpenD 加路由也能调 mobile-driven cmd**.

#### M1 — Cash log (cmd 3000/3001/3002) — 资金明细新接口

替代 v1.4.93 实战反馈中老 `/api/flow-summary` (cmd 2226) 字段太少:

- **新增 3 个 REST endpoint** (ADD-only, 老 endpoint 100% 不变):
  - `POST /api/cash-log` — 主查询 (时间范围 / 业务分组 / 货币 / 关键词 /
    股票 / 方向 / cursor 分页)
  - `POST /api/cash-detail` — 单条流水详情 (从 log_id 拿)
  - `POST /api/biz-group` — 业务分类元数据 (供前端构造下拉)
- **新增 3 个 daemon FTAPI cmd_id**: `TRD_GET_CASH_LOG=22701` /
  `TRD_GET_CASH_DETAIL=22702` / `TRD_GET_BIZ_GROUP=22703` (gRPC FutuCall 可调)
- **新增 backend cmd 路由**: daemon→backend NN cmd 3000/3001/3002 直接走
  per-broker TCP (mobile 同 channel)
- **新文件**: `proto-internal/realtime_asset_log.proto` (来自 mobile
  `ftcnnproto/.../realtime_asset_log.proto:109`),
  `crates/futu-gateway/src/handlers/trd/cash_log.rs` (~440 LoC)
- **6 单元测试**: bit extraction / proto round-trip / cmd_id constants

⚠️ **UNVERIFIED**: backend 接受 daemon-sent cmd 3000 + `realtime_asset_log::GetCashLogReq`
体未真机 verify (pitfall #42 backend-semantic risk). 真机 fail 时 daemon 返
清晰 error 提示 fallback `/api/flow-summary` (老 endpoint 100% 工作).

#### M2 — Position cost methods + currency + market 暴露

OpenD `Trd_Common.proto Position` 字段 30-34 (currency / trd_market /
diluted_cost_price / average_cost_price / average_pl_ratio) **proto 一直
有, daemon 没暴露**. 移动端 NN 显示口径按市场分: JP→平均成本价, 其他→摊薄.

- `crates/futu-trd/src/types.rs::Position`: 加 5 字段 (proto passthrough)
- `crates/futu-mcp/src/handlers/trade.rs::PositionOut`: 同步暴露
- 新 `cost_basis_method_hint`: "average" (JP) / "diluted" (others)
- `cost_price` 标记 deprecated (proto 注释一直说要用新字段, 我们一直只暴露老)
- 6 单元测试 (JP / JPY currency / HK / US / CN / unknown 派生规则)

#### M3 — Option Greeks (delta/gamma/theta/rho/vega + IV + 溢价 + OI) 暴露

OpenD `Qot_Common.proto OptionSnapshotExData` (字段 8-13) **proto 一直有,
MCP get_snapshot 没读**. 期权用户必须自己 subscribe 才能拿 Greeks.

- `crates/futu-mcp/src/handlers/core.rs::SnapshotOut`: 加
  `option_greeks: Option<OptionGreeksOut>` 字段
- 新 `OptionGreeksOut` struct (13 字段: 5 Greeks + IV + 溢价 + OI + 行权价
  + 合约乘数 + DTE + 名义金额 + 净 OI)
- `get_snapshot` 自动 populate 当 `snap.option_ex_data` 非空 (期权 symbol)
- 普通股 / 期货等 → `option_greeks` 字段被 `skip_serializing_if` 跳过

### 🟡 Tier G — 协议 gap 填充 (来自 v1.4.93 FTLogin audit)

- **G1 — `client_sig` proactive refresh timer (P1)**:
  - 长跑 daemon 在 `client_sig_invalid_local_time_s - 1h` 主动 trigger
    refresh, 不等 backend 报错或 TCP 断开
  - 复用 v1.4.92 P1-D `AuthRefresher` trait infrastructure
  - **env opt-in default OFF** (`FUTU_CLIENT_SIG_PROACTIVE_REFRESH=1`) — pitfall #42
    backend-semantic risk: 1h 提前 refresh 是否被 backend 接受未真机 verify
  - 决策逻辑提取为 pure fn `decide_timer_action()` 可独立测试 (env mutation
    在 parallel tokio test 里 race)
  - 新文件 `crates/futu-gateway/src/bridge/client_sig_timer.rs` (~250 LoC,
    8 单元测试 + 1 integration with MockRefresher)

- **G4 — reactive `client_sig` refresh on tcp_login persistent failures (P1)**:
  - reconnect monitor 检测 `consecutive_login_failures >= 3` 时 trigger
    `AuthRefresher::refresh_qot_login` + `reauth_via_remember_login` →
    swap `reconnect_auth` for next tcp_login
  - **env opt-in default OFF** (`FUTU_CLIENT_SIG_REACTIVE_REFRESH=1`) — `tcp_login`
    `ret_type` 含义不止 `client_sig` 失效一种 (含反刷限流 / 风控), 误 refresh
    可能加重 limit
  - refresh-fail-loop guard (`g4_refresh_attempted_this_cycle` flag) 防同一
    outer cycle 内重复 attempt
  - 决策逻辑提取为 pure fn `decide_g4_action()` (10 单元测试)
  - 新文件 `crates/futu-gateway/src/bridge/client_sig_reactive.rs` (~155 LoC)
  - `crates/futu-backend/src/auth/mod.rs::reauth_via_remember_login` 新加,
    复用 disk creds + `remember_login()` 拿 fresh `AuthResult`

- **G5 — 三因子验证 (3FA) flow (P1)**:
  - 当 `/authority/` POST 返 `error.error_code == 33`
    (`kAuthRequireThirdFactorVerify`) 时, 提取 `third_factor_verify_sig` +
    `uid` from error → POST `/authority/third_factor/auth` with 7 fields
    (uid / sig / device_id / device_alias / device_type / os_ver / tgtgt)
  - 响应解析复用 `parse_auth_result` (对齐 C++
    `ParseVerifyThirdFactorSigResponse` → `ParseAuthorityResponse`)
  - 在 `password_auth` 和 `remember_login` 两条 dispatch site 都接好
  - 新 helper `handle_third_factor_verify` (~110 LoC, 6 单元测试 - 输入验证
    / error response 解析 / body shape verification)

- **G6 — `moomoo_client_sig` / `moomoo_client_key` / `moomoo_web_sig` parse + persist (P2)**:
  - `parse_auth_result` 抽取 3 moomoo path fields, base64+AES decode
  - `SavedCredentials` 加 `moomoo_client_sig` + `moomoo_web_sig` 字段
    (`#[serde(default)]` 兼容 v1.4.93 老文件)
  - `save_credentials_from_response` 持久化到 disk
  - 5 单元测试 (含 backward-compat 老文件 load + round-trip + save_from_response
    end-to-end)
  - 注: G6 lays infrastructure; 实际 moomoo path broker channel routing 是
    future work (pitfall #51 减法纪律, 不超越 C++)

- **G8 — 真实 `device_model` (P3)**:
  - macOS: `sysctl -n hw.model` → "Mac MacBookPro15,4" (对齐 C++
    `FTGTW_Inner_API.mm:29-44` `sysctlbyname("hw.model")`)
  - Linux/Windows: hardcode "PC" (对齐 C++ `FTGTW_Inner_API.cpp:274,344`)
  - 替换 3 hardcoded `"device_type": "PC"` 站点 (`/authority/` POST,
    `/authority/verify_device_code` POST, G5 3FA POST body)
  - OnceLock cached, 3 单元测试

### 📊 测试统计

- **新加单元测试**: 32 (G1: 8 + G4: 10 + G5: 6 + G6: 5 + G8: 3)
- **workspace total**: 1468 passed / 0 failed (vs v1.4.93 baseline 1436, +32)
- **clippy**: clean across workspace with `-D warnings`
- **fmt**: clean

### ⚠️ UNVERIFIED (pending real-machine verify, default OFF/safe)

依 pitfall #42 backend-semantic risk 纪律, 以下 G1/G4 行为需 long-running 真机
+ MITM 抓包 verify, 当前默认 OFF / fallback 路径保留:

- **G1 1h 提前 refresh 是否被 backend 接受**: 真机 long-runner (24h+) 启
  `FUTU_CLIENT_SIG_PROACTIVE_REFRESH=1` 验 refresh 触发后 24h 仍连通; backend 若拒
  "too early" → v1.4.95+ 调 `REFRESH_BEFORE_SECS` 或 verified 后切 default ON
- **G4 3 次 tcp_login 失败后 refresh 是否真 recover**: 真机要重现 client_sig
  失效场景 (改时钟 / 长跑 30 天 / 服务端踢) + 启 `FUTU_CLIENT_SIG_REACTIVE_REFRESH=1` 验
- **G5 3FA 真机**: 需 3FA-enabled 测试账号 (Futu 令牌 / moomoo token /
  authenticator app); tester 启用后 daemon 收 code=33 → 3FA POST → 拿 fresh
  AuthResult 流程
- **G6 moomoo creds 真机**: 需 moomoo attribution (US/SG/AU/JP/CA) 真账号验
  `/authority/` 响应是否真返 `moomoo_client_sig` / `moomoo_web_sig_new` 非空

### Files

- 新增: `crates/futu-gateway/src/bridge/client_sig_timer.rs` (G1 ~250 LoC)
- 新增: `crates/futu-gateway/src/bridge/client_sig_reactive.rs` (G4 ~155 LoC)
- `crates/futu-backend/src/auth/mod.rs`: G1 timer wiring + G4 reauth helper +
  G5 handle_third_factor_verify + G5 dispatch sites + G6 AuthResult fields +
  G8 device_type() import
- `crates/futu-backend/src/auth/parse.rs`: G6 parse + persist moomoo fields
- `crates/futu-backend/src/auth/device.rs`: G6 SavedCredentials moomoo fields
- `crates/futu-backend/src/auth/util.rs`: G8 device_type() OnceLock fn + sysctl path
- `crates/futu-backend/src/auth/tests.rs`: G5 + G6 tests
- `crates/futu-gateway/src/bridge/mod.rs`: G1 timer spawn + G4 reactive logic
- `Cargo.toml`: version bump 1.4.93 → 1.4.94

### Related pitfalls

- pitfall #42: backend-semantic risk requires real-machine verify (G1/G4/G5/G6)
- pitfall #51: align with C++ = 减法 (G1/G4/G5/G6/G8 全是 fill-gap, 0 超越)
- pitfall #53: parallel agent failure recovery (本版 6 commits 顺序串行无 agent 用)

## [1.4.93] - 2026-04-26 🚨 tester 13 项 finding 全清 + 7 Tier R 工程纪律 + Tier B/C/D 多 agent 框架 + `<futunn-hk-test-acc>` 真机 verify

**🚨 必须升级**. v1.4.86-90 saga 反思版本. claude-01b4 + claude-5318 + claude-coord-1c41
v4 cross-verify report 13 项 finding (3 S + 5 P0 + 4 P1 + 1 P2 UX after +1 severity bump)
全清, 0 defer. **本版亮点**: 跨多 agent 系统性补齐 v1.4.86-93 累积技术债, 同时 `<futunn-hk-test-acc>` 真账户
跨 4 surface (REST/CLI/MCP/gRPC) 真机 verify 0 daemon bug. 39 commits.

### 🚨 S 级 — 3 项 ship-blocker

- `011265510 + 929d8632f` **BUG-001 trd_market + order_type runtime 9+17 variants** (跨 5 版 v1.4.86-90 schema-only): SG/AU/JP/MY/CA 5 国 + 11 新 order_type runtime parser 跨 4 surface (MCP/CLI/REST/gRPC) 同步扩齐. 12 file / 665+/58- LoC. 14 test. 修复同时纠正 v1.4.90 NX 报告的 `trd_market_str` 7=>JP 错 (混淆 SecurityFirm:FutuJP=7 与 TrdMarket:JP=15).
- `44eba0496` **BUG-004 REST subscribe fresh symbol on-demand fetch**: P0-B v1.4.90 副作用, fresh symbol 第二次 sub silent no-op (7%/22% dispatch). 改 SubHandler 走 `fetch_and_cache_securities_on_demand` (CMD 20106 batch + 用 stock_id retry CMD 6211). 5 integration test. 同时 P1-1 `qot_subscribe_ops_total` counter wire 集成 in same commit.
- `f1f08188b` **BUG-5318-009 query_orders inner update_orders → merge_preserving_stubs** (跨 v1.4.57 BUG-60b0-002 33 版未真修): v1.4.90 `merge_preserving_stubs` 只补外层 callsite, 内层 helper `update_orders` 还是整覆盖 → spawn refresh 立即抹零 stub. 1 行 fix + 12 unit test. UNVERIFIED 真机 verify 待 tester (US trading hours).

### 🔴 Fixed (P0)

- `1f07d10b2` **BUG-5318-001 audit log file 0o600** (跨 v1.4.87/88/89/90 4 版承诺未兑现): tracing-appender 0.2.5 `RollingFileAppender` 没暴露 mode 参数, 我们用 `Mode0600Appender` wrapper (debounced 1s) + startup `tighten_log_files_in_dir` sweep. +3 unit test.
- `82793a3a3` **BUG-002 REST deny_unknown_fields 7 endpoint** (typo reject): axum middleware 层 (`crates/futu-rest/src/strict_fields.rs` 415 LoC) 双向 walk Value 检测 unknown key, 兼容 camelCase / flat / aliases 已有 normalize. +12 strict_fields tests.
- `630cc9962` **BUG-003 MCP UTF-8 invalid bytes resilient parser** (5/6 → 6/6): `read_line(&mut String)` → `read_until + std::str::from_utf8` 把无效 UTF-8 (`\xfe\xfe` / UTF-16 BOM / mid-payload `\xc0\xc0`) 转成 -32700 而非 terminate. +3 transport tests.
- `942104d60` **NEW-C-01 REST trd_market enum validation 7 endpoint** (cross-surface inconsistency): /api/funds 等 trd_market=999 silent return 真 sim funds → 加 `validate_header_trd_market` 与 MCP layer 1 valid_list 一致 ([1,2,3,4,6,8,15,111,112]). 10 unit test.
- `e17ca5b88` **NEW-C-02 WS legacy mode startup WARN** (security gap): legacy mode 无 `--rest-keys-file` 时 WS `/ws` 接受 unauthenticated 握手 → 加 startup loud WARN 对齐 v1.4.86 SEC-003 Q4 mutating-blocked policy + v2 default-reject 公告. 8 unit test.

### 🟡 Fixed (P1)

- (P1-1 集成在 SX2 `44eba0496`) **NEW-C-03 qot_subscribe_ops_total counter wire** to CMD6211 dispatch site.
- `25fb26f95` **BUG-sweep-001 cancel-all-order ret_msg label** (跨 v86 byte-identical): "ModifyOrder: 错误" → 用 `early_op_name` 派生 `CancelAllOrder` / `CancelOrder` / `Disable` / `Enable` / `DeleteFail` 区分.
- `3d61ce4ce` **BUG-5318-003 US futures exchange_code derive fallback** (跨 v1.4.57 BUG-60b0-004 30+ 版未修): MNQ/NQ → CME, CL/NG → NYMEX, ZN → CBOT, VX → CBOE, GC/SI → COMEX. 5 mkt_id range derive helper.
- `346656d2a` **BUG-5318-004 sim funds.currency derive from trd_market** (multi-currency 用户分不清 HKD/USD/CAD): 3 层 priority — security_firm → backend cache → trd_market fallback (HKD/USD/CNH/CAD/SGD/AUD/JPY).

### 🟢 Fixed (P2 UX)

- `aff6a47c8` **BUG-5318-002 history-kline no-date hint**: 不传 begin/end → audit log warn "推荐显式传 YYYY-MM-DD". RequestHistoryKL + GetHistoryKL 两个 handler 都加. +2 contract tests.

### 🧭 Tier R — 工程质量根因沉淀 (7 改进)

来源 `essentials/2026-04-25-1640-quality-reflection-v1.4.86-90-saga.md`. v1.4.86-90 5 版 20 项 fix 实际只 8/20=40% 真干净, 5 项后发性问题. 7 根因 → 7 改进:

- `929d8632f` **R1 + pitfall #54 — Schema-only fix without runtime parser sync** (BUG-001 实锤): 加 enum variant 时强制 grep `from_str` / `try_from` / `parse` 同步检查 runtime parser. CLAUDE.md +1 行 + pitfalls-archive.md (#54).
- `e698e8216` **R2 + pitfall #55 — Fix without regression sweep** (BUG-004 实锤): 修 dedup/cache/wire/schema/auth 时跨 fresh/dup/concurrent/boundary/clear 等 nearby scenario 至少 verify 3 个. 5 类 fix → regression sweep scope 映射表.
- `472f28ea5` **R3 — `scripts/cross_surface_smoke.sh`** (210 cell smoke 矩阵): 9 markets × 7 endpoints × 3 surface (REST/MCP/CLI) 自动一致性检查. WARN-only by default. +160 LoC design doc.
- (v1.4.92 已做) **R4 — multi-version smoke** baseline 已建 (跨版本 binary fingerprint diff).
- `8f0bef253` **R5 — docs/self-review.md "Fix 后端到端 verify" 段** (6 checkbox): happy + 3 nearby / grep runtime parser / cross-surface smoke / unit test 真测 actual behavior / 关键 trade path backend mock + 端到端 query / changelog 承诺 multi_version_smoke 实证.
- `526a50bb7 + f803b717f` **R6 — prost-vs-tool_enum verify test (anti-drift lock-in)** + C++ enum audit report: 6 tests 锁住 TrdMarketEnum (HK/US/CN/HKCC/Futures/SG/AU/JP/MY/CA = 9 variants → v1.4.93 加 Futures=5 → 10 variants) + OrderTypeEnum (17 variants) 与 prost generated proto enum 字面值匹配, anti-drift 触发条件: 加 enum variant 时未同步 → CI fail. 防止 v1.4.86-90 BUG-001 schema vs runtime drift 复发.
- `6a926e842 + d3c6983e9 + 9d113ae7d` **R7 + R7-extended — history error 真因 hint + 9 unit tests** (用户 `<futunn-hk-test-acc>` + moomoo `<moomoo-us-test-acc>` 真机 verify 触发): sim/real 账户调 history 类查询时 backend 返 "请稍后重试或联系客服" generic msg 时, daemon 改写为真因 hint. **R7 v1** sim-only 过滤. **R7-extended (R7 v2)** 用户提供 moomoo US 账户实证 broker-specific 行为 (moomoo US broker 1007 对 today fills CMD 4710 无数据返 generic msg, futunn HK 1001 同 CMD 返空 list), 漏过 sim-only 过滤. 改 pattern-only filter, sim/real 两套 hint 文案: sim 路径 "Sim 账户不支持 history 类查询, 请用 real"; real 路径 "broker 暂不支持 / 当前无数据 (broker-specific 行为, 不是 daemon bug). 已知 moomoo US broker CMD 4710 无数据返此 msg, history-order-fills CMD 4712 返空 list. 建议用 history-order-fills 查或检查 broker_id". **+9 unit tests** (Plan B #1) 锁住 R7-extended 行为防 regression. 跨 4 surface (REST/CLI/MCP/gRPC) 一致透传给 user.

### 🛡️ Tier R 续 — Plan B 用户加固指令 ("1.4.93 必须高质量") (3 改进)

- `9d113ae7d` **R8 — sim position CMD 14705 helpful hint** (AU `<moomoo-au-test-acc>` 真机 verify 发现): sim 账户类型 `markets=[100]` backend 拒 CMD 14705 position 查询返 "not support this account type", 之前只 WARN log 然后 cache 留空, 用户调 `/api/positions` 看到空 list 无线索. 加 pattern detect "not support this account type" → daemon WARN 含诊断 hint "sim acc type 不支持 position 查询 (backend 设计行为). 此账户 /api/positions 始终返空, 用户应用 /api/funds 或换支持的 sim 账户. trd_market=100 类特殊 sim 是已知不支持 type."
- `9d113ae7d` **G1 — cltsig_invalidtime 字段 parse** (EX-C4 audit P1 protocol gap): 对齐 C++ `auth_impl.cpp:3245-3247` 解 `cltsig_invalidtime` 加 `svr_time` 得 client_sig 失效本地 UTC epoch. AuthResult 加 `client_sig_invalid_local_time_s: u64` 字段, parse_auth_result 抽 + 起 startup info log. **实装范围**: 仅 parse + 持久化字段. proactive refresh timer 留 v1.4.94+ (pitfall #42 backend-semantic 风险, backend 是否接受"过早 refresh" unknown). +3 unit tests cover happy / missing cltsig_invalidtime / missing svr_time.

### 🎁 External tester feedback (cash-flow)

- `b5eaed734` **Feedback #1 — `/api/flow-summary` 加 begin_date+end_date 范围查询** (对齐 CLI v1.4.32 `--date-range`): 外部反馈指出 "REST 只支持单日 clearing_date, 查 10 个交易日要 10 次 call". 实装 REST handler 客户端 fanout (proto 一次只接一天, backend 无 native range API): 检测 begin_date + end_date → 跳周末 → 31 天上限 (防 bot 误调用) → 循环每日 fetch → 聚合 `flow_summary_info_list` → 返一个聚合 response. 失败的天累积到 `s2c.date_range.failed_days[]`. 真机 5/5 PASS (含 backward compat 单日 / range mode / begin>end reject / >31 day reject / invalid format reject). +6 unit tests.
- ⚠️ **Feedback #2 — 资金明细新接口 (defer, 含深挖证据)**: 同一报告提建议加新 endpoint 对齐富途牛牛 App "资金明细" (覆盖股票/期权交易结算 / 期货盈亏 / 平台费用 / 红利再投资 等). 深查 C++ FutuOpenD 源码, **发现 backend 有完整 proto** (`realtime_asset_log::GetCashLogReq` cmd 3000, 原生 begin_time/end_time + biz_group_id + currency + 股票代码搜索 + 分页). **但 C++ FutuOpenD gateway 自己也不暴露**给 API 客户端 (NNProto_Trd_FlowSummary.cpp 只调 cmd 20964 业务分组, 不调 cmd 3000) — 富途牛牛 App "资金明细" 是 mobile 走 backend 专用 channel, 不经 OpenD. **按 pitfall #51 "对齐 C++ = 减法"**, daemon 不超越 OpenD gateway 暴露 mobile-only proto. 真要落地需 Futu OpenD 团队在 C++ 新版加 `NN_ProtoCmd_Trd_GetCashLog` 类 cmd, daemon 一周内跟随. 临时替代: `/api/flow-summary` range + `/api/history-orders` + `/api/history-order-fills` + `/api/positions` 聚合 ≈ 完整明细.

### 🧰 Tier B — Mock backend integration tests (3 改进)

- `a74aeaae7` **B1 — HK NIGHT_OPEN mock-backend integration** (verify v1.4.92 P1-D fix): 4 active tests + 1 #[ignore] regression-watch. 验证 HK_Future + SGSecurity/SGFuture cross-candidate state_priority_active_first scoring. 发现 v1.4.92 P1-D within-candidate `pick_market_state` 收敛盲区 (overlapping market_id ranges) 标 `#[ignore]` + v1.4.94+ fix path doc.
- `f666cd078` **B2 — KL_Month sub_type [1..15] → [1..17]** (tester 报告 27 不在 proto 里, daemon range 实际 buggy): proto canonical KL_Month=13, KL_Year=16, KL_3Min=17 三个 daemon 之前 reject. C++ `APIServer_Qot_Sub.cpp:104-129` 接受全 17 variants. 修 range → whitelist `{1,2,4,5,6..=17}`. 4 new unit tests + tester reply.
- `de40a05e4 + 6ae7103d1` **B3 + D4 — chaos fault injection framework + P2-B F2 circuit-break test**: `crates/futu-e2e/src/chaos.rs` (399 LoC) FaultType enum (TcpDrop / BrokerDisconnect / BackendSlow / HttpFail) + 三重护栏 (chaos feature + FUTU_CHAOS_ENABLE=1 env + enable_real_injection() 显式调) + Drop 自动 cleanup. 跨 OS abstraction (Linux iptables / macOS pfctl). 8 unit + integration test.

### 🔬 Tier C — C++ alignment audits + 协议层补齐 (4 audits)

- `a1de87965` **C1 — F-RAND-001 rsa CVE-2023-49092 (Marvin attack) defer 决策记录** (上游 ceiling): rsa 0.10-rc 也未修, ring/aws-lc-rs 不支持 PKCS#1 v1.5 encrypt (协议 wire breaking), C++ OpenD 同款 vulnerability. **Daemon 实际威胁评估**: InitConnect 一次性, daemon 不暴露 decrypt RPC, attacker 无远程 oracle. Marvin attack 需 repeated chosen-ciphertext 查询, 当前 attack surface ≈ 0. 决定: defer + 公开诚实记录 + Cargo.toml pin "do not bump until upstream #390 merges" + cargo audit allow-list + monitor watcher (RustCrypto/RSA#390 merge → 立即升级).
- `0ab6cd4f9` **C2 — TrdMarketEnum + Futures=5 MCP 期货下单入口**: REST `VALID_TRD_MARKET_INTS` 加 5 + MCP description 8 处 + tools.rs 加 FUTURES alias. 跨 4 surface 期货下单 sim 账户 PASS verify.
- `98bd450be` **C3 — Option D prost as_str_name delegate** (消除手写 from_str 漂移): `tool_enums.rs::from_str` 重写为 2-step (prost `from_str_name` first + short-name aliases fallback). 17 OrderType + 10 TrdMarket variants 单一 source of truth = `from_proto_variant`. 8 new option_d_* tests + R6 6 tests fully compatible.
- `81f5c4ffa` **C4 — C++ FTLogin protocol gap audit** (no code change): 0 P0 / 5 P1 / 3 P2 / 6 P3 gaps documented. Top P1: G2 RepullAuthCode (broker auth 30-day expiry self-heal) + G3 web_sig persistence — 实装在 `a924a869d` (见下).

### 🛡️ Tier G — broker auth_code 30 天自动续期 + web_sig 持久化

- `a924a869d` **G2 + G3 — RepullAuthCode + web_sig persistence** (EX-C4 audit P1 实装): broker auth_code 默认 30 天到期, daemon 长跑触发 broker channel 失效之前**必须重启 daemon**. 现在自动 RepullAuthCode → 重做 broker_auth → 重 CMD 1001 登录, **避免重启**. 对齐 C++ `auth_impl.cpp:715-754 RepullAuthCode` + `auth_impl.cpp:3308-3376 ParseRepullAuthCodeResponse`. **G3** SavedCredentials 加 `web_sig: String` 字段 + parse_auth_result 抽取 + remember-login 同步保存. **G2** 新 `crates/futu-backend/src/auth/repull.rs` (362 LoC) POST `/authority/repull_auth_code` body `{uid, device_id, web_sig, broker_id}` + bridge 集成 broker reconnect 自动 self-heal. 102/102 auth tests PASS. **真机 verify** 待 v1.4.94+ (long-runner CI 或 user 跑 30+ 天).

### 🔧 Tier A — feature 暴露 (1 项)

- `fc01dad20` **A2 — BUG-5318-003 exchange_code expose to REST/CLI/MCP output**: 新 `futu-core::exch_type::exch_type_to_string(i32)` 18-value mapping (含 5 US futures sub-exchanges 9-13: NYMEX/COMEX/CBOT/CME/CBOE). REST `/api/snapshot` 双调用 + JSON 注入 `basic.exchange_code`. CLI snapshot/static + MCP futu_get_snapshot/futu_get_static 同步暴露. 13 new unit tests + 真机 verify CL/GC/ZN/MNQ/VX/AAPL.

### 🏗️ Tier D — 基础设施 framework (5 改进)

- `01c012f20` **D1 — `crates/futu-e2e/` sim daemon E2E framework** (无自有 framework 累积技术债): SimDaemon spawn 真二进制 + tempdir HOME 隔离 + port autoallocation + 5 baseline scenarios (BUG-001/002/003/004/NEW-C-03). McpStdioChild JSON-RPC helper. ~600 LoC framework + scenarios.
- `32e1bb3b9` **D3 — CI ship.sh + nightly-e2e workflow 集成**: ship.sh A 阶段从 8 step 扩到 **10 step** (A9 multi_version_smoke STRICT mode = ship-blocker; A10 cross_surface_smoke --no-daemon-required = daemon up 时真跑矩阵 + block ship). `.github/workflows/nightly-e2e.yml` (213 lines) 4 jobs (multi_version / cross_surface / sim_daemon_e2e / chaos_circuit_break). PR-time CI 增量 < 5s.
- `de40a05e4` **D4 — chaos fault injection framework** (见上 Tier B B3).
- `2e3a7a84b` **D5 — cross-version replay framework**: `crates/futu-e2e/src/replay.rs` (846 LoC) diff engine + capture/runner + JSON-Pointer paths + acceptable-diff allowlist + PII scanner. v1.4.93 baseline fixture (8 entries). 25 unit tests PASS.

### 📊 测试 + 数字

- workspace clippy --workspace --all-targets -- -D warnings: **0** (修 1 处 doc list indentation)
- workspace fmt --check: **clean**
- pii_scan + proto_diff_check + changelog_section_check: **all clean**
- workspace cargo test (1436 tests): **1436 passed / 0 failed** (+16 vs baseline)
- 新增 ~166 unit + integration test (R7-extended 9 + G1 3 + cash-flow range 6)
- 49 commits since v1.4.92

### 🧪 `<futunn-hk-test-acc>` (futunn) + `<moomoo-us-test-acc>` (moomoo) 真账户跨 4 surface verify (主线自跑, 不依赖外部 tester)

**futunn `<futunn-hk-test-acc>`** verify (`essentials/2026-04-25-2335-v1.4.93-`<futunn-hk-test-acc>`-cross-surface-verify.md`): ~165 测试场景, **0 daemon bug**.

- **REST** (54 sim + 18 real = 72 测试): real 账户 18/18 全 PASS (HK/US/HK Futures/Multi-market 跨 funds/positions/orders/order-fills/history-orders/history-order-fills/max-trd-qtys/margin-ratio/order-fee/flow-summary). sim 账户 11 fail = backend 设计限制 (sim 不支持 history) + test arg 错, R7 已改写真因 hint.
- **CLI** (37 测试): 25 PASS / 12 FAIL (大部分是 test script arg 错). 真 daemon bug 0.
- **MCP** (56 测试): 31 PASS / 25 FAIL (大部分是 test script schema 错, MCP deny_unknown_fields 严格). 真 daemon bug 0.
- **gRPC**: 代理 REST (走和 REST 同一组 handler).

**moomoo `<moomoo-us-test-acc>`** verify (`essentials/2026-04-26-0100-v1.4.93-moomoo-cross-surface-verify.md`): 25 测试场景, **15/15 REST PASS + 5/5 CLI PASS + 5/5 MCP PASS**.

- 跨 5 brokers (Futu US 1007 / SG 1008 / AU 1009 / JP 1012 / CA 1019) 全连成功
- **新发现**: moomoo US broker 1007 CMD 4710 (today fills) 无数据时返 generic msg, 与 futunn HK broker 1001 同 CMD 返空 list 不一致 → broker-specific 行为
- **R7-extended fix** (commit `d3c6983e9`): pattern-only filter, real broker-specific generic msg → 真因 hint, 不再误导用户去找客服
- snapshot exchange_code 实证 (A2 fix, US.AAPL → "Nasdaq")
- multi-broker funds (HK/US/HKCC) 全 PASS
- moomoo OTP 路径协议层对齐但本账户 password sufficient, OTP wire-level 真机未触发 (defer v1.4.94+)

### 外部 feedback loop

- ✅ 全 13 项 finding ship (3 S + 5 P0 + 4 P1 + 1 P2 UX), 0 defer
- ⏸ Pending tester 真机 verify: S BUG-5318-009 真机 (US trading hours) / G2 broker auth 30 天 self-heal (long-runner) / B1 HK NIGHT_OPEN 真机 / B3 P2-B circuit-break 真 sudo iptables
- 🙏 致谢 claude-01b4 + claude-5318 + claude-coord-1c41 v4 cross-verify report. v1.4.86-90 累积 40% 修正率不可接受, 本版 R 项 7 改进系统性落地. 历史 v1.5 milestone 三大件 (desktop Tier 1 / MCP SSE / OAuth) v1.4.85 已主动取消, 不再预设.

## [1.4.92] - 2026-04-25 🟡 P1-D 真 in-process relogin + multi-version regression guard + 6 项 polish

**🟡 推荐升级**. 用户 "plan 1.4.92 + 能做的都做 + 多叫几个兄弟" 指令.
6 parallel agents (BX/AX/DX1/DX3/D2X) + 主线 Tier A3+A4 = 9 commits + 1 fmt
+ 1 ship commit. v1.4.91 P1-D observability-first 升级到**真 in-process trigger**.

### 🟡 Major: P1-D QotLoginHealth 真 in-process relogin trigger (v1.4.91 follow-up)

v1.4.91 P1-D 是 observability-first (loud warn + counter), v1.4.92 接上**真 trigger**:

- `51849528f` **A1 AuthRefresher trait + DefaultAuthRefresher impl**
  - 新文件 `crates/futu-backend/src/auth/refresh.rs` (304 LoC)
  - `#[async_trait] AuthRefresher::refresh_qot_login()` 抽象 + DefaultAuthRefresher
    生产实装 (复用 v1.4.34 daemon-reload `refresh_credentials_on_disk` HTTP /authority/
    POST + remember-login + write-back disk credentials, 标 `LoginCache::set_login_state`)
  - 10s 超时 (`tokio::time::timeout`), 不主动重建 TCP / cipher
  - +3 unit test in test_util submodule (mock fixtures)

- `d2aa9414b` **A2 QotLoginHealth state machine + bridge real-trigger wiring**
  - `push_health.rs`: 3 new AtomicBool/I64 字段 (`relogin_attempt_in_flight` /
    `relogin_circuit_open` / `relogin_circuit_opened_at_ms`)
  - 6 new methods: `try_begin_attempt` (compare_exchange) / `end_attempt` /
    `open_circuit` / `maybe_close_circuit` (10min cooldown auto-close) /
    `should_attempt_relogin_v2` / `record_relogin_failure_with_circuit_check`
  - `bridge/mod.rs`: GatewayBridge +`auth_refresher: Option<Arc<dyn AuthRefresher>>`
    field; initialize Step 6.6 构造 DefaultAuthRefresher 从 reload_state 注入
  - `push_parser.rs::run_qot_login_health_loop`: 真 trigger refresher.refresh_qot_login()
    via tokio::spawn, 5 fail → circuit_open
  - +8 push_health unit tests (extends v1.4.90 P1-D 10 baseline → 18 total)

- `7e5817143 + c707bded6` **A3 integration test** end-to-end
  - 8 scenario test in `crates/futu-gateway/tests/integration_qot_login_health.rs`
  - 覆盖 success path / failure path / 5-fail circuit_open / circuit blocks /
    in_flight protection / backend disconnected / refresher None / healthy state
  - Mock AuthRefresher with outcome / delay 配置 + drive_one_tick helper
    (避免真 30s ticker 阻塞)
  - 8/8 pass in 0.30s

- `ad8ec59aa` **A4 真机 verify guide**
  - `essentials/2026-04-25-1230-v1.4.92-p1d-real-machine-verify-guide.md` (270 lines)
  - 4 scenario: TCP 断 / HTTP 断 (backoff 17min 完整 cycle) / cipher reject (mock) /
    24h 长跑 + report 模板 + macOS pfctl / Docker iptables / health endpoint
    troubleshooting

UNVERIFIED 部分: 24h 长跑真机 verify 需 tester 真机 (P1-D non-deterministic gap,
按 v4 cross-verify 方法论 essentials 主线诚实标).

### 🛠 Tier B: Multi-version regression guard 自动化 (`1be6fb9fa`)

主线**自反省**实装 — v1.4.86 v4 cross-verify 报告的 multi-version binary
verification 沉淀为日常 workflow:

- 新 `scripts/multi_version_smoke.sh` (410 LoC bash) — 下载最近 5 版 macOS arm64
  tarball + `strings` fingerprint + diff baseline. 默认 WARN-only, opt-in
  `FUTU_MULTI_VERSION_GUARD_STRICT=1` block push.
- 新 `essentials/multi-version-fingerprint.json` (153 LoC) — 19 signal × 5 版本
  baseline (v1.4.87..91). Cache saga A1/A2 anchors / BUG-009 SMS race / cipher
  state version / P1-D / sim trade CMD 14704 等 long-term 协议 anchors.
- `.githooks/pre-push` Check 0: info-only by default, 防 regression 立即 alert
- 设计文档 `essentials/2026-04-25-1544-v1.4.92-multi-version-guard-design.md` (345 LoC)

发现的 design quirks (沉淀): function-name 不一定在 stripped binary 出现 →
log-string anchors (`v1.4.73 A1` / `v1.4.82 A2`) 比函数名稳定; SIGPIPE 与
`set -euo pipefail` 冲突需 tempfile 替代 inline grep.

### 🟢 Tier D1: CLI 错误信息友好化 (`7d5b6836d`)

- `futu-opend --setup-only` 失败 hints (4 new branches): ret_type=2 4-cause
  guidance / ret_type=45 版本过低 / DNS error checklist / SMS + non-TTY stdin
- `futucli` trade reject ret_msg translation (7 categories): 解锁/余额不足/
  代码不存在/休市/整手/持仓不足. emit_trade_hint_if_known() downcast FutuError::ServerError
- +6 unit test (futucli 41 total)
- 不替换原 error chain, stderr `💡 Hint:` 前缀

### 🔄 Tier D2: essentials/INDEX.md 整理 (`42f204331`)

- 49 v1.4.27-85 entry 摘要化 (200+ 字 → ≤80 字)
- §4.6 deep-dives 拉出 10 archival-grade entries (cross-verify methodology /
  4 版罕见纪录复盘 / fix-report 4件套 / migration guide / etc.)
- §5 机制化 checklist 加 6 scripts + .githooks/pre-push + multi-version regression guard
- §6 活跃行更新 v1.4.91, fix 3 broken link
- 不损失任何 entry / 链接

### 📝 Tier D3: docs-site/reference 自动 regen (无 diff 已同步)

- 跑 gen_rest_api_docs.py / gen_grpc_api_docs.py / gen_mcp_docs.py
- 6 reference files (rest-api / grpc-api / mcp-tools × {md, en.md}) 已 sync
- pii_scan + bilingual ratio (1.001 / 1.000 / 1.002, 全 in [0.7, 1.5]) clean
- 无 commit 产生

### 📊 测试

- futu-backend: 152 → 155 (+3 from A1 test_util)
- futu-gateway lib: 411 → 419 (+8 from A2 push_health state machine tests)
- futu-gateway integration: +8 new (A3 integration_qot_login_health)
- futucli: 35 → 41 (+6 from D1 trade hint dispatch)
- workspace clippy --all-targets -- -D warnings: 0
- workspace fmt clean / pii_scan clean

### 外部 feedback loop

- ⏸ 等 v1.4.86 v4 cross-verify report 的 next-round verify (v1.4.91 fix-report
  发了, tester 节奏不可控)
- ✅ 主线 cross-verify 方法论 essentials 落地 (Tier B multi-version regression
  guard 是 §"主线自反省" 实装)

## [1.4.91] - 2026-04-25 🟡 v1.4.90 follow-up — P1-D wiring + 6 项 polish

**🟡 推荐升级**. v1.4.90 ship 完后用户要求 "几项都认真做". 6 项: 删 backup
+ INDEX §3 补 / pitfall #53 沉淀 / cross-verify 方法论反哺 / docs/reference
mcp-tools 自动重生成 / **P1-D bridge wiring** (v1.4.90 P1-D agent 留的
follow-up). 4 commits: 3 docs + 1 fix.

### 🟡 Fixed (P1)

- `7617f121f` **P1-D wiring**: QotLoginHealth bridge tokio::spawn + REST 暴露
  - bridge/mod.rs: `qot_login_health: SharedQotLoginHealth` 字段 + initialize Step 6.6
    spawn `run_qot_login_health_loop` 30s tick polling task
  - push_parser.rs: `run_qot_login_health_loop` 实装 — 读 login_cache.is_logged_in()
    + backend connected, !qot_logined → record_qot_logined_false; should_attempt_relogin
    triggered → loud warn + record_attempt + record_failure (= observability only,
    真 in-process relogin trigger 跨 auth HTTP + TCP re-handshake + cipher 重建,
    留下版; supervisor (systemd / docker) 监控 loud warn 后 restart 已足够覆盖
    压力场景 self-heal)
  - main.rs: `/api/push-subscriber-info` provider closure 合并返 push_health +
    qot_login_health 双 snapshot. ops 通过 REST 看 consecutive_failures /
    total_observed_false / current_backoff_ms counter
  - push_health.rs: 移除 4 处 `#[allow(dead_code)]` (struct/impl/Snapshot/SharedAlias)
  - 修 v1.4.90 P1-D non-deterministic gap. UNVERIFIED 部分需 tester 24h 长跑.

### 🧭 流程 / 文档

- `ac8480f97` **CLAUDE.md 普适规则 + pitfalls-archive.md 新坑 #53**:
  "Parallel agent failure recovery 两模式" — agent 529/timeout → 主线 salvage
  working tree (不重试同 task); 并行 cargo lock 争用 → kill 卡住老 cargo 进程.
  防再发: ≥6 agent session 主动 30min 巡检. 来源 v1.4.90 双实锤 (A2/A3 都 529 +
  K2 卡 cargo lock 40min).
- `ac8480f97` **essentials/2026-04-25-1110-cross-verify-methodology.md 新文件**:
  "什么叫好的 cross-verify 报告" 方法论反哺. 6 大要素 (bidirectional /
  evidence-grade 4 级 / multi-version binary verification / self-audit /
  大白话 / roundtrip 全部修正) + 给未来 tester 的 v5+ 期待 + 主线自反省.
- `ac8480f97` **INDEX.md §3 外部 tester feedback loop**: 补 v1.4.86 v4 cross-verify
  report + v1.4.90 fix report 4 件套 (takeaways + reply CN/EN + fix-report) 入口.
- 删除 CLAUDE.md-old.md (163KB 用户保留的备份, v1.4.90 拆分前的旧版).

### 📝 文档

- `735c01825` **docs-site/reference/mcp-tools.md regen** (CN+EN): 跑
  scripts/gen_mcp_docs.py 反映 v1.4.90 P0-E + P1-G schema 改动 (trd_market 9
  variant + string/int 双接). 60 tools / 43 request struct.

### 📊 测试

- workspace test 1007 passed / 21 runs / 0 fail (与 v1.4.90 一致, 无 regression)
- futu-gateway lib: 411 passed
- workspace clippy clean / fmt clean

### 外部 feedback loop

- 零新外部 finding (v1.4.86 v4 报告全 20 项已 v1.4.90 ship)
- 等 tester next-round 真机 re-verify (P1-D 24h 长跑 + 19 项命令验证)

## [1.4.90] - 2026-04-25 🚨 v1.4.86 cross-verify hotfix — 1 S + 5 P0 + 7 P1 + 7 P2 全清

**🚨 必须升级**. 双 tester (claude-2b2f + claude-e4da) v4 cross-verify 报告
20 项 finding 全清, 含 **1 S 级 cache saga 跨 6 版未真修真根因**. 12 个 fix
commit + 4 个 chore commit.

### 🚨 S — BUG-e4da-009 cache saga 真修 (跨 v1.4.73 → v1.4.89 7 版未真修)

`fa03c97f5`: `merge_preserving_stubs` 替代 `cache.orders.insert` 整覆盖.

- v1.4.82 A2 stub upsert 后 v1.4.73 A1 spawn refresh **22ms 内整覆盖** stub
- 客户端 PlaceOrder 后立即查 `/api/orders` 命中 stub, 但 22ms 后 count=0 →
  "**单子消失**" + cancel timeout
- 跨 v1.4.73/82/83/84/85/86 加 fix 不删旧 fix 累积 bug, 6 版 undo

修法 (async-safe):
- `CachedOrder` 新加 `is_stub: bool` + `stub_inserted_at_ms: u64`
- A2 upsert 时 set `is_stub=true`, A1 refresh 走 `merge_preserving_stubs` 而非
  `insert`: 同 order_id backend 胜出, backend 没返的 fresh stub (< 30s) 保留,
  老 stub (≥ 30s) evict
- DashMap entry lock 整 merge 原子完成
- 5 unit test 覆盖所有 race 场景 (stub-preserved / backend-match / TTL-evict /
  no-dup / partial-match)
- 修复 CLAUDE.md 反模式 D (silent-success): `ret_type=0` 现在真有 downstream effect

外部 tester 22.4ms delta 三次独立 repro 实锤. v4 multi-version verification 显示
v1.4.75/80/81 binary 只有 A1 字符串, v1.4.86 A1+A2 共存, 直接支持 S 级 release
blocking 判断.

### 🔴 Fixed (P0)

- `0c33cfb20` **P0-A**: MCP server resilient JSON parser, 收 invalid JSON 返
  `-32700 Parse error` 而非 `exit(0)` (DoS 修复)
- `4333fa06b` **P0-B**: REST subscribe virtual conn 永久泄漏, 改 `REST_SHARED_CONN
  = 0xFFFF_FFFE` 单 conn_id, 3 路 unsub 都生效
- `f7f5c21ae` **P0-C**: REST symbols 100 cap (DoS 防护, v1.4.82 regression 锁定)
- `f7f5c21ae` **P0-D**: REST `begin/end` body alias → `begin_time/end_time`, 修
  silent default to epoch 全量错数据
- `e0bee3923` **P0-E**: MCP int-string drift 18 字段 / order_type 6→17 / trd_market
  4→9 全清, 走 `tool_enums::deser_*_as_string` int OR string 双接

### 🟡 Fixed (P1)

- `67de37f4a` **P1-A**: REST `Scope::Trade` super-scope 接受 TradeReal/Sim/Unlock
  任一, 替代硬编码 `trade:real`
- `c94977f48` **P1-B**: Prometheus exporter wire 19 new family (5 per-cmd + 24
  per-hour + 4 latency quantile + 12 conn/req/backend/sub) 通过 Registry
  `register_renderer` extension
- `a65494795` **P1-C**: REST `/api/sub-acc-push` 真实装 (260 LoC 替代 4 行 stub),
  对齐 MCP feature parity (validation + audit + session_id + unsub_hint)
- `6890ba0a5` **P1-D**: `QotLoginHealth` self-heal — exponential backoff 60s →
  120s → 240s → 600s cap (24h 长跑 verify TBD)
- `6890ba0a5` **P1-E**: gateway `market_state` HK/SG future multi-candidate priority
  loop, 修 night session NIGHT_OPEN/Closed 优先级倒置
- `a242be39e` **P1-F**: `history_kline` 改走 `trade_date_market_to_backend` 与 C++
  `GetMktIDByTradeMkt(GetTradeMarket(...))` chain 对齐 (REST vs FTAPI 路径一致)
- `e0bee3923` **P1-G**: MCP/CLI `trd_market` 全 9 variant
  (HK=1/US=2/CN=3/HKCC=4/SG=6/AU=8/JP=15/MY=111/CA=112)

### 🟢 Fixed (P2)

- `b163df922` **P2-A**: WS `(proto_id, sec_key, payload_hash)` 5s 窗口 dedup, 修首批
  push 字节级重复 (KL_Month=27 等)
- `6890ba0a5` **P2-B**: F2 (TradeReQuery) account-level circuit-break, 60s tripped
  state 防止单 failing acc 480 WARN/h spam
- `dcd1d3c1e` **P2-C**: MCP audit log Option<T> Debug format leak (`"Some(400.0)"`)
  → `serde_json::Value` + NaN sentinel for None → JSON `null`
- `f7f5c21ae` **P2-D**: REST adapter `maybe_expand_flat_trd_header()` 自动
  normalize flat body 到 nested c2s, REST 接 flat 也接 nested
- `4333fa06b` **P2-E**: REST `/api/quote` 走 push cache fallback (cache hit → push,
  miss → backend pull)
- `4333fa06b` **P2-F**: orderbook 未订阅 → loud unsub hint + actionable error code
  (替代 silent empty)
- `67de37f4a` **P2-G**: Bearer token RFC 7235 §2.1 case-insensitive, 小写 `bearer`
  也接受

### 🧭 流程纪律

- `53bd0683f` CLAUDE.md 拆分: 2862 行 → 427 行根文件 + 7 份 `docs/` 专题文件 +
  `essentials/pitfalls-archive.md` 1640 行 (37 个历史坑 #16-52 完整原文). 根文件
  保留 "每次会话都要知道的总览", 按任务加载映射其余.
- `essentials/2026-04-25-0700-v1.4.86-tester-cross-verify-report-v4.md`
  cross-verify report 归档作 v1.4.90 修复来源依据

### 🔄 Refactor / clippy / fmt

- `5e2419b70` cargo fmt 整理 (S cache saga + P0-E + P2-F)
- `992a2bb1a` clippy fix — 5 处违规清理 (HKCC upper_case_acronyms / approx_constant
  3.14 误为 PI / assertions_on_constants 改 const compile-time / dead_code
  ftapi_market_to_backend / unnecessary_cast u32→u32)

### 📊 测试

- 新加单元测试 ~60 个 (S=5, P1-D=10, P1-E=12, P1-C=12, P2-A=6, P2-C=7, P1-F=5, P0-B=16,
  P1-B=7, P0-D/E/G/L=多个)
- workspace test ~1116 → ~1180+ (v1.4.90 to verify final)
- futu-rest E2E 36 / futu-gateway integration 119 全绿
- workspace clippy clean / fmt clean

### 外部 feedback loop

- ✅ 全 20 项 cross-verify finding 实装, 0 defer, 0 reclass, 0 dispute
- ✅ 修复报告 4 件套: takeaways + reply slack-short (CN+EN) + fix-report
  (essentials/2026-04-25-1000-*.md)
- 🙏 致谢 claude-2b2f + claude-e4da 跨-tester 22.4ms delta 三次独立 repro +
  v4 multi-version binary 验证, 这是 cross-verify 的精华证据

## [1.4.89] - 2026-04-25 🟢 defer 全清算 — 11 parallel agents + 4-part P2-A + 坑 #35 长期替代闭环

**🟡 推荐升级**. 用户 "必须全部做完" 指令, 12h 内 **11 parallel agents +
4-part 主线 P2-A** 全清. 零用户感知行为变化 (backend 默认行为保留),
大量**代码质量 polish + 测试扩量 + security 机制化**. 17 commits.

### ✨ Major: P2-A mkt_id auto-refresh 完整闭环 (CLAUDE.md 坑 #35 长期替代)

v1.4.89 P2-A 共 4 commits:

- **part 1** (`b2a5b02cd`): cache 侧 infra (`stale_mkt_ids` / `mark_stale_mkt_id`
  / `drain_stale_mkt_ids` / `update_mkt_id` / 3 counters + 9 test)
- **part 2** (`067134f59`): 29 qot handler callsite 迁移到
  `get_security_info_trigger_refresh` (cache hit + opportunistic stale mark)
- **part 3** (`c23160fc3`): gateway bridge 背景 worker 60s tick, 批量 CMD
  20106 `GetSecuritiesInfo`, `update_mkt_id` 写回 cache
- **finale** (`594f82fb4`): `trd/mod.rs:301` TODO 闭环, Futures 分支按 `mkt_id`
  细分 sub-exchange tz (NYMEX/CME/CBOT/CBOE=NY, SGX=SG, 其他=HKT fallback)
  +6 unit test

P2-A 语义完整周期:
```
[用户 query] → handler → cache hit + mark stale (if mkt_id==0)
[60s tick] → worker drain → CMD 20106 batch → update_mkt_id
[下次 query] → 精确 cache-first 路由
```

坑 #35 "Rust 启发式 vs C++ 数据驱动" 长期替代**完整闭环**.

### ✨ 11 Parallel agents (独立 scope)

| Agent | Scope | Commit |
|---|---|---|
| a2a3 | F-TLS-UNIFICATION | `a8e3735b1` (phantom, workspace 已 rustls) |
| aed0 | #5 Grafana Dashboard JSON | `fc4905ef6` (12 panels + docs) |
| a1546 | CME 期权 | `d17312fc4` (phantom, C++ OpenD 也拒) |
| acae | #7 MCP isError 根治 | `aa4821eec` (v1.4.58 Phase C 已做, +3 regression test) |
| a9f7 | #1 60 Gateway integration tests | `546ab5adf` (+40 test, 119 total) |
| af4e4 | criterion benchmarks | `16c777638` (4 files / 21 cases) |
| a4d1c | Phase E3 dep + cargo-deny | `f90361b05` (+21 minor bumps + CVE 闭合) |
| ae6a | os_ver 真探测 + P2-D API audit | `103ece956` (+8 test, 22 audit) |
| afefca | P2-B bridge.rs 拆分 continuation | `b9ebf1298` (mod.rs 2440→1683, +3 子 module) |
| a6a6e | workspace missing_docs 补齐 | `f0685de97` (+181 doc / 21 file) |
| adf8c | REST E2E tests | `ab0a14fb8` (+22 business path, 36 total futu-rest) |

**8 agents 真做 + 3 phantom confirmed** (F-TLS / CME / MCP isError 都已
早先做过, agent 补 regression guard).

### 🔄 Minor

- `a6f07a151` v1.4.88 cargo fmt `--tz` eprintln 断行 hotfix (归 v1.4.89 tree
  因 CI 发现)
- `59c43b7be` cargo fmt post P2-A migration + bench splits

### 外部 feedback loop

- 零用户 API 变化 (backward compat 完整)
- 外部 reviewer / tester 继续等节奏
- F-RAND-001 (rsa 0.10) upstream blocker 仍等

---

## [1.4.88] - 2026-04-25 🟢 defer 清算 part 3 — 5 项并行 agent 推进 (must_use / non_exhaustive / subscribe shorthand / derive test split / push_parser unit tests)

**🟢 可跳过此版**. 本版是**代码质量 polish + 测试扩量**, 零用户行为变化.
用户 "逐条都做了" 指令触发, 4 个 parallel agent + 主线 1 项, 一夜清 5 项.

### ✨ 新增 / 改进 (Added / Improved)

#### F-MUST-USE-001: `#[must_use]` 5 → 24 (`e972f2e2b`)

Review v3 master report §9.2 长期 P2. 给 bool / usize / Vec / 自定义类型
返回的 pub fn 加 `#[must_use]`. Result / Option 自动已有, 不需手工加 (clippy
`double_must_use` 拦截).

覆盖 futu-auth (key/store/scope/metrics/machine/limits) + futu-codec (frame)
+ futu-cache (static_data / trd_cache) + futu-core (proto_id / market).

#### F-NON-EXHAUST-001: `#[non_exhaustive]` 15 → 31 (`85a7d2733`, by agent)

Review v3 master report §9.2 长期 P2. 给 proto-backed enum / Scope / Market
/ OrderType / Side 等加 `#[non_exhaustive]`, 未来扩 variant 不 breaking.

覆盖:
- `futu-qot::types` (QotMarket / SubType / KLType / RehabType)
- `futu-trd::types` (TrdEnv / TrdMarket / TrdSide / OrderType / ModifyOrderOp)
- `futu-mcp::tool_enums` (5 enum)
- `futu-auth::scope::Scope`
- `futucli::cmd::unlock::SecurityFirmArg`

跨 crate match 补 `_ =>` fallback arm (6 处: futu-mcp trade_write × 4 +
futu-mcp state + futucli common).

#### F-TRD-MOD-TEST: 继续拆 derive.rs 1028 LoC → 5 themed 子文件 (`573e4093b`, by agent)

Review v3 master report §9.2 列 "trd/mod.rs 2500 LoC test 拆". 实际 v1.4.77
T1-T8 (`7f78d8333`) 已把 trd/mod.rs 3823 → 1225 LoC. 本版继续拆
`tests_v1_4_41_helpers/derive.rs` 1028 LoC → 5 themed 文件 (<400 LoC each):

- `derive_exchange_str.rs` (102 LoC, 11 tests)
- `derive_cache_first.rs` (215 LoC, 6 tests)
- `derive_exchange_code.rs` (345 LoC, 22 tests)
- `derive_security_type.rs` (323 LoC, 17 tests)
- `derive.rs` (remain, 65 LoC, 5 tests)

61/61 tests pass, zero regression. `handlers::trd::` 204 tests + futu-gateway
333 total all green.

#### adapter.rs: subscribe `symbols` string array shorthand (`d29812e93`, by agent)

源码 `crates/futu-rest/src/adapter.rs:560` 遗留 TODO: v1.4.82 B1 标的
"expand_symbol_shorthand 扩 subscribe 的 symbols 数组形式". 本版实装.

- 新 helper `try_parse_mixed_array_to_securities` — 支持 `["US.AAPL"]` String
  元素自动展开成 `{market:11, code:"AAPL"}` + 已有 Object 元素透传 + 校验
  `market+code` 字段防 junk
- 两条路径 (path 1 `first.is_string()` / path 2 `iter().any(is_string)`)
  都切到新 mixed parser
- 3 新 unit test (`v1_4_88_mixed_*`): 纯 string array / 纯 object array
  (backward compat) / mixed string+object
- **Backward compat**: 现有 object 数组形式继续 work

#### F-GW-E2E-002: `push_parser.rs` +31 unit test (`bc5253c49`, by agent)

Review v3 master report §9.2 列 "bridge push_parser 19 parse_* 加 unit test".
实际 push_parser.rs 有 **10 个 parse_ fn**, 本版每个加 ≥3 test:

- 覆盖 10/10 parse_ fn
- 新测试 31 个 (总 52 tests, 从 21 baseline)
- normal path (field 结构验证) + malformed (bytes truncated / optional field
  missing) + cache accumulate 模式 (Ticker/RT) + PushEvent proto_id/sub_type
  metadata / BUG-006 L3 overnight cache preservation 回归 guard / fixed-point
  decode (÷10^9 / ÷10^3 / ÷10^5)

`cargo test -p futu-gateway --lib`: 333 → 364 passed (+31).

### 🔄 Refactor / discipline

本版**全 parallel**: 4 agent (F-NON-EXHAUST / adapter / F-TRD-MOD-TEST /
F-GW-E2E-002) 独立 scope 并行干, 主线我做 F-MUST-USE-001. 零文件冲突
(agent 间手工 stash recovery 处理 race, 最终 commit clean).

### 外部 feedback loop

本版零代码行为改动, 不打扰外部 tester verify 节奏.

### 测试

- workspace tests: 所有 baseline + 31 + 5 + 0 regression = pass
- clippy --all-targets -D warnings: 0 warning (含 double_must_use 0)
- fmt --check: clean

---

## [1.4.87] - 2026-04-25 🟢 重大 defer 清算 part 2 — audit log perms + CLI --tz + phantom defer 确认

**🟢 可跳过此版** (零 mutating 行为变化). 本版是**维护/纪律版本**, 清完用户
"除已取消的都做" 批量指令里的一部分 defer 项:

### ✨ 新增 (Added)

#### #3 CLI `--tz` IANA timezone override (`394b8d830`)

**来源**: v1.4.70 plan 首提 "G1 CLI --tz wire daemon", 之后 16 版未动,
本版补齐.

- `futu-opend` 加 `--tz <IANA_TZ>` 可选 flag (如 `Asia/Hong_Kong` /
  `America/New_York` / `UTC`)
- 在 tokio runtime 启动前 `std::env::set_var("TZ", ...)`, chrono::Local
  自动读新 TZ
- 影响 `hours_window` 限额检查等 "local time" 语义
- 优先级: `--tz` flag > `TZ` env var > UTC
- 双语 docs 更新 (`guide/cli.md` + `.en.md`)

#### #4 Audit log dir 0700 + file 0600 (Unix) (`abe2bbd9e`)

**来源**: CLAUDE.md 坑 #49 "v1.4.85+ 考虑 log dir 0700 + file 0600", 2 版
未做.

- `futu-auth/src/audit.rs::tighten_dir_perms` + `open_file_0600` + `warn_if_world_readable_path`
- `futu-core/src/log.rs::open_audit_writer` 同步加同 3 helpers (避免循环依赖
  duplicate)
- 只收紧, 不 loosen (已有 0500 目录不动)
- stderr warn if path 在 `/tmp/`, `/var/tmp/`, `/private/tmp/`
- Windows no-op
- +5 unit test 验证各 corner case

### 🧭 Phantom defer 确认

两项 "defer 清单" 实际已隐式闭合:

- **#2 Funds proto 36 字段**: v1.4.75 plan 提 "距 Python SDK 63 字段缺 36",
  但 `proto_diff_check.sh` 确认 535 messages / **0 missing fields**.
  "63 vs 33" 是 Python SDK flatten Funds + AccCashInfo + AccMarketInfo 的
  展开, Rust 已 1:1 覆盖 Futu Trd_Common.proto Funds 33 字段.
- **P2-D public API 降 pub**: 跑 `clippy -W unreachable_pub` workspace
  检查, 0 warning. 当前 pub surface 机械检查通过, 真正 P2-D (manual API
  audit) 留更大 session 做.

### 外部 feedback loop

- **tester v1.4.86 真机 verify (SEC-003 Q4 breaking)**: 仍 pending
- **v1.4.85 reference docs review**: pending
- v1.4.87 代码改动小 + backward compat, 不打扰外部 verify 节奏

---

## [1.4.86] - 2026-04-24 🔴 SEC-003 Q4 真 fix (partial breaking) + docs-site 私仓引用纪律沉淀

**🟡 推荐升级**. 2 类改动:

1. **🔴 SEC-003 Q4 真 fix (partial breaking)**: REST legacy mode (未配
   keys.json) 下, **mutating endpoint 强制 auth**. 过去本机任意
   skill / agent 可 `curl POST /api/order` 无 auth 下单的安全漏洞关闭
2. **🟢 docs-site 私仓引用纪律沉淀** (v1.4.85 用户反馈沉淀): CLAUDE.md 坑
   #52 + pii_scan.sh 机制化 + 历史 changelog refs 清理

### 🔴 Fixed (Security — partial breaking)

#### SEC-003 Q4: Legacy mode mutating endpoint 强制 auth (`a4c3d6a77`)

**触发**: 外部 reviewer 2026-04-23 实证, REST daemon 在 legacy 模式 (未配
keys.json) 下, 本机任意 process 可以不经 auth 直接调 `/api/order` 下单.

**v1.4.84 措施**: 仅 startup `eprintln!` warn (`8d6d36e60`). 不拦截任何
endpoint, 实际上漏洞仍敞开.

**v1.4.86 真 fix** (commit `a4c3d6a77`):

- `crates/futu-rest/src/auth.rs::bearer_auth` middleware 在 legacy early-return
  之前加 `is_mutating_write_path()` 检查
- 6 个 mutating path 强制要求 auth: `/api/order` / `/api/modify-order` /
  `/api/cancel-all-order` / `/api/unlock-trade` / `/api/reconfirm-order` /
  `/api/admin/*` (shutdown / reload / status)
- 未经 auth 返 401 UNAUTHORIZED + JSON body 含 gen-key hint + docs link
- **read-only endpoint 继续 legacy 允许** (行情查询 / 账户只读 / 订阅 —
  zero impact 对只读用户)
- 新 3 unit test (auth::tests::v1_4_86_*) + 4 e2e test (auth_e2e::v1_4_86_*)
  验证 mutating 拦截 + read-only 放行 + scope mode 不 regression

**Partial breaking 判定**: 依 CLAUDE.md 坑 #48, 这是**基础设施 breaking**
不升 v1.5. Legacy + write 场景目前无用户真实这样跑 (用户 2026-04-24 确认).

### 🧭 流程纪律

#### CLAUDE.md 坑 #52 "docs-site/ 新内容不得引用私仓源码 — 讲契约不讲实装" (`c2f057796`)

**触发** (v1.4.85 ship 后用户连续 2 次反馈):

1. rest-api.md 每 endpoint 初版写 `[qot::fn](https://github.com/futuleaf/...)`
   — 136 处 dead link (私仓外部 404)
2. 我改 `qot::fn (in crates/futu-rest/src/routes/qot.rs)` — 用户: "你别把
   源码搞过来了"

**坑 #52 3 条硬规则** (docs-site/ 新写内容禁出现):

- `github.com/futuleaf/futu-opend-rs` 任何形式链接
- `crates/futu-*` 路径引用 (即使 inline code)
- `src/xxx.rs` / `fn xxx(...)` 作 hint
- `scripts/gen_*.py` / 内部 script 名
- `guard.rs::scope_for_tool` 等内部符号作 debug hint

**机制化**: `scripts/pii_scan.sh` 新加 `scan_private_repo_refs()` 扫 4
pattern. 发版前自动拦截.

### 🟢 UX 改进

#### docs-site/changelog 历史 crates refs 清理 (`f50006046`)

配合坑 #52, 6 处历史 section 的私仓路径引用脱敏 (CN + EN):

- v1.4.85 section: `scripts/gen_*.py` → "FutuOpenD-rs 构建流水线自动生成"
- v1.4.84 section: 新模块 `crates/...` → 功能描述 ("MCP enum 双接 reducer"
  等)
- v1.4.83 section: `crates/futu-gateway/src/bridge/push_health.rs` →
  "push 链路 health 监控"
- v1.4.65 section: `crates/futu-gateway/tests/` → "gateway 集成测试目录"

用户感知 "发生了什么" 保留, 内部路径删除.

### 📝 文档

- `docs-site/docs/guide/auth.md` + `.en.md` 顶部新加 "Legacy 模式行为" 章节
  (行为矩阵 + 升级指引 + "read-only 零影响" 说明)

### 外部 feedback loop

- **外部 reviewer (SEC-003 2026-04-23 反馈)**: 真 fix 交付 (partial
  breaking 但用户 2026-04-24 批准 "没有用户那么跑, 不用担心无痛升级")
- **v1.4.85 docs review**: pre-review 已主动扫 3 surface, 66 REST +
  78 proto_id + 60 MCP scope 100% 覆盖, 无 gap. 等真机 review 反馈

---

## [1.4.85] - 2026-04-24 🟢 外部反馈 REST/gRPC/MCP 完整 API 文档 + 🔄 v1.5 roadmap 取消 + 纪律沉淀

**🟢 可跳过此版**(零代码改动; 本版是**文档 + 纪律**版本, 主要交付 3 个
auto-gen API 完整参考 + 取消 v1.5 超前规划 + 对齐 C++ 减法哲学 沉淀).

### ✨ 新增 (Added)

#### Tier A §外部反馈: REST + gRPC + MCP 完整 API 文档 (auto-gen)

触发: 外部反馈 v1.4.81 指出 "官网 REST / gRPC 完整接口文档缺失"
(`futuapi.com/guide/rest/` 只有概览, `/api/` 只有 rustdoc 无 endpoint 视角),
v1.4.85 一次补齐 + 用户追加 "MCP 也要加上".

交付 **3 个自动生成脚本 + 8 个 markdown 文档**:

| Tier | 脚本 | 输出 | 行数 | SHA |
|---|---|---|---|---|
| A1 | `scripts/gen_rest_api_docs.py` (686 LoC) | `reference/rest-api.md + .en.md` | 1521 + 1522 | `f05f26648` |
| A2 | `scripts/gen_grpc_api_docs.py` (476 LoC) | `reference/grpc-api.md + .en.md` | 233 + 233 | `197fb47c7` |
| A3 | `scripts/gen_mcp_docs.py` (1213 LoC) | `reference/mcp-tools.md + .en.md` | 2592 + 2598 | `2395f9d20` |
| A4 | mkdocs.yml + landing | `reference/index.md + .en.md` | 90 + 99 | `1c48ba44a` |

**总计**: ~2400 LoC Python + 4428 CN + 4452 EN markdown.

**幂等**: 3 脚本都有 `--check` flag, CI 验证 "重跑输出无 diff". 未来新 route
/ 新 tool / 新 proto_id 添到源码, 下次跑脚本自动入文档.

**内容结构**:

- **REST**: 70 route × 9 section (ping / auth / qot / trade / push / admin
  / ws / ...). 每 endpoint: URL / 方法 / scope / 参数 / 返回 / 错误码 /
  curl 示例.
- **gRPC**: Service 定义 (FutuOpenD.Request + SubscribePush) + 90+ proto_id
  按 6 category 分组 + Python grpc client 双示例.
- **MCP**: 60 tool × 9 section (核心 / 订阅 / 行情 / 板块 / 衍生品 / 自选 /
  账户 / 交易 / push). 每 tool: scope / Python SDK 等价 / 参数 (含
  v1.4.83/84 alias + enum 双接 + deny_unknown_fields + runtime validate) /
  JSON-RPC 调用示例. **Scope 分布验证**: 40 qot:read + 15 acc:read + 4
  trade + 1 trade:unlock = 60 total, **0 unknown**.

**docs-site 导航**: 新加 "API 参考" (en: "API Reference") 顶级 section, 含
3 个完整 ref + landing page (3 surface 选择对比表).

Guide `rest.md` / `grpc.md` / `mcp.md` 顶部加 tip admonition 指向对应
reference, 让读者顺滑过渡 概览 → 完整参数级.

### 🔄 Refactor (docs / discipline)

#### Tier B §v1.5-cancel: v1.5 roadmap 取消清理

**用户决策** (2026-04-24 session):
> "v1.5 的 roadmap 可以先取消", "直接把 v1.5 roadmap 删掉吧, 先忘掉 1.5",
> "我们会继续在 1.4.x 上把 bug 修完再决定要不要弄 1.5"

**执行** (`fea8aef5c`):

- `essentials/2026-04-19-0730-v1.5-strategic-roadmap.md` 重命名加 CANCELED
  header (保留 git history 作归档, 不删)
- `docs-site/docs/tutorials/cheatsheet.md + .en.md` 里 v1.5 mention 改为
  "未来版本" / "version TBD"
- `CLAUDE.md` "版本号分配纪律" 章节 v1.5 描述改 "先按住不发, 等 1.4.x 修
  bug 阶段结束再 plan"

不再预设 v1.5 里程碑内容. 之前文档里 "v1.5 desktop source Tier 1 / MCP SSE
/ OAuth" 三预设 scope 作废, 未来真要做需重新 plan + evidence.

#### Tier C §cpp-alignment: CLAUDE.md 坑 #51 "对齐 C++ = 减法哲学"

**触发** (`a89582fd4`): v1.4.84 session 发生 3 次 "对齐 C++ 就是少做不是
多做":

1. **SEC-002 SPKI pinning**: v1.4.84 plan 原计划 v1.4.85 做. Explore agent
   实证 C++ OpenD 源码里**没有** SPKI pinning (`grep cert_pin src/` → 0
   match). f3clogin SDK 不读 user keychain 是 C++ 的 MITM 防护方式.
   webpki-roots (v1.4.84) 已等价. **取消**.
2. **B5 runtime visit_map warn**: v1.4.84 plan 承诺做. 改 schema hint 替代.
   对齐 C++ proto `[deprecated=true]` **静态** annotation 哲学.
3. **v1.5 roadmap 超前承诺**: "desktop Tier 1 / SSE / OAuth" 超越当前
   evidence 规划 = 用户决策取消. 对齐 "don't plan ahead of evidence".

**坑 #51 3 条核心规律**:

1. 新 feature / security 实装前, 第一问: "C++ OpenD 做了吗?"
   - 做了 → 对齐, 抄 pattern
   - **没做** → 默认不做, 除非有**超越 C++ 的明确业务 / 用户理由**
   - 不清楚 → grep 证伪 (binary strings + source code)
2. "超越 C++ 的 security posture" 需**明确 justification**:
   - 不是 "Rust 应该更 secure" (价值判断)
   - 必须是 "**攻击场景 C++ 失守, Rust 需要多一层**" (具体场景 + 证据)
3. 反面模式识别: "对齐 C++ + 还要加 X (C++ 没有)" → 问 "C++ 为什么没加?
   我的加是补漏还是超越?"

### 📝 文档

- 新 `essentials/2026-04-24-1707-v1.4.85-plan.md` (完整 Tier A/B/C/D/E plan)
- 新 `essentials/2026-04-24-1707-v1.5-roadmap-canceled.md` (v1.5 roadmap
  archive + CANCELED header, 保留 git history)
- 新 `essentials/2026-04-24-1728-v1.4.85-session-summary.md`
- 新 `essentials/2026-04-24-1728-v1.4.85-fix-report-for-reviewer.md`
- `essentials/INDEX.md` 同步更新

### 🧭 流程纪律

- CLAUDE.md 坑 #51 新加 (对齐 C++ = 减法哲学, 见 Tier C 细节)
- CLAUDE.md 版本号分配纪律 章节 v1.5 描述 soften 为 "先按住不发"

### 外部 feedback loop

- **外部反馈 (v1.4.81 指出)**: REST + gRPC + MCP 3 surface 完整 API 文档
  **全部交付** (Tier A1/A2/A3). `essentials/<ts>-v1.4.85-fix-report-for-reviewer.md`
  详列 3 surface 文档结构 + script 来源 + auto-gen 保证 "未来新 API 自动入
  文档"
- **外部 tester v1.4.84**: 真机 verify canary + SEC 修复 + schema migration
  仍 pending. v1.4.85 代码零改动, 不影响 tester 节奏 (alias / enum string
  / deny_unknown_fields 等 v1.4.84 改动继续在 v1.4.85 有效)

---

## [1.4.84] - 2026-04-24 🔴 SEC-001 + SEC-002 + SEC-003 Q4 安全双修 + v1.4.83 半成品 + v1.5 保留 breaking 全做完

**🔴 必须升级**（2 条 S 级 security finding 双修: auth debug log 明文泄露
tgtgt + HTTPS cert 完全禁用验证）.

### 🔴 Fixed (Security — S 级)

#### SEC-001: Auth debug log 明文泄露 credentials

- **证据**: 外部报告实证 `/tmp/*.log` 扫描 80+ 历史 log 文件含
  `tgtgt` 明文, 跨 v1.4.57-81. Agent 一条 `cat /tmp/*.log | grep tgtgt` 即
  拿完整凭据
- **修** (`3da487375`):
  - 新 `crates/futu-backend/src/auth/redact.rs` (~230 LoC): `redact_auth_body`
    支持 JSON + URL-encoded + space-kv 三种格式, redact 敏感字段 value 为
    `<REDACTED len=N>`
  - 敏感字段清单: tgtgt / tgtgt_new / salt / salt32 / pwd_md5 / device_sig
    / device_code / device_verify_sig / client_sig / client_key / rand_key
    / rand_key_new / auth_token / session_id / aes_key / s2 / s3 等
  - 非敏感 (account / device_id / uid / svr_time) 保留便于 debug
  - 4 处 `tracing::debug!` / `info!` 全包装 (L765 salt / L887 raw response
    / L1079 verify response / L1220 POST body)
  - startup stderr warn `emit_debug_log_security_warn_once()` (OnceLock 去重)
  - 9 new `v1_4_84_sec_001_*` tests

#### SEC-002: HTTPS 客户端完全禁用 cert 验证 (自 v1.0 regression)

- **证据**: 外部报告 mitmproxy 实测 Rust daemon 10 HTTPS endpoint (auth / api /
  6 broker) **全部握手成功** (user keychain 装 MITM CA 即可); C++ OpenD 同
  条件 `tlsv1 alert unknown ca` 握手拒
- **根因**: `reqwest::Client::builder().danger_accept_invalid_certs(true)`
  — 出现在 2 处 (auth/mod.rs:180 + gateway/bridge/account.rs:228)
- **修** (`3da487375`):
  - 两处 `danger_accept_invalid_certs(true)` 全**删除**
  - workspace `Cargo.toml` reqwest dep 切 `rustls-tls-webpki-roots`
    (default-features=false): 排除 native-tls OS keychain 信任, 改 Mozilla
    webpki-roots curated CA list
  - Agent skill 装 user keychain MITM CA 不再被信任, 握手失败. ✅ 关闭
    SEC-002 主 agent-时代威胁
- **残余风险** (v1.4.85+ TODO): 企业 MDM 推 system-trusted CA 仍可 MITM,
  需 SPKI-hash pinning for 敏感 endpoint

#### SEC-003 Q4: REST loopback 无 auth 时本机 skill 可调 /api/order

- **证据**: 外部报告 SEC-003 tracking. `key_store.is_configured() == false`
  (legacy mode) 时任何本机 process 能调 `/api/order` / `/api/unlock-trade`,
  含 agent skill
- **修** (`8d6d36e60`): scope_mode=false 时 stderr prominent warn 教 ops
  配 keys.json + gen-key 命令 example + 指 trade:real scope + 限额. 不是
  完全 mitigation 但让脆弱配置不 silent
- **SEC-003 Q1-Q3 audit 结论** (归 essentials, 不改代码):
  - **Q1a** tgtgt TTL: 30 天 (TGTGT_VALIDITY_SECS, 对齐 C++ auth_cryptor L135)
  - **Q1b** auth_token 权限: backend team territory, 无 daemon audit 能力
  - **Q2** 业务 body signature: FTAPI frame header 有 SHA1(body) 校验 +
    AES 应用层加密, 隐式 integrity OK
  - **Q3** FTAPI TCP pinning: **raw TCP** (无 TLS) + 应用层 AES encryption
    via session_key (RSA-exchanged). 攻击者 MITM 只能看加密字节, 不能解码
    body. 可接受

### 🧭 流程纪律 (CLAUDE.md 坑 #49 + #50 `539abbc0d`)

- **坑 #49**: Debug log 必须 redact credentials — 敏感字段清单 + grep audit
  pattern + 非敏感保留列表 + 反面模式识别
- **坑 #50**: HTTPS client 绝不能用 `danger_accept_invalid_certs(true)` 作
  默认 — C++ baseline + SPKI pinning roadmap + 测试方法

### 🟡 Fixed — v1.4.83 半成品深化 (Tier A + C1)

**🟡 推荐升级**（部分 breaking: 未知字段 loud fail）。v1.4.83 ship 时
CHANGELOG 末尾 "v1.5 TODO" 块被用户指出 "图省事 — 这些都是要干的活"。本版
**一次性清完** v1.4.82 "不做" 清单 + v1.4.83 "v1.5 TODO" 全部 17 项. 温和
breaking 策略 (alias 保留 + enum 双接 + 2-3 版 deprecation window).

### 🟡 Fixed — v1.4.83 半成品深化 (Tier A + C1)

#### A1. §9 Phase 2.6 push_parser parse-error trigger (`557952be5`)

v1.4.83 F3/F4 只用 "push staleness" 信号。"TCP 活但 parse 全错" silent failure:

- `handle_quote_push` / `handle_trade_notify` / `handle_msg_center_push`
  3 fn 签名改 `-> bool`, decode 失败返 false
- push_cb 分叉: false → `record_parse_error()`, count `>= 20` → `trip_circuit()`
  (F4), `>= 5 && < 20` → warn log (F3 staleness detector 30s 内自然 trigger re-sub)
- 3 new v1_4_84_sec_9_* tests

#### A2. §14 per-cmd UTC hour breakdown (`c42f0ba70`)

v1.4.83 §14 只有全局累加. tester 需时段分桶 (CMD14716 UTC 15-18 window):

- `HourBreakdown { counters: [AtomicU64; 24] }` 新结构
- 4 个 `*_by_hour` 字段 (cmd 6212 / 4716 / 14716 / 5300)
- `/metrics` Prometheus 自动暴露 `futu_gateway_backend_pushes_cmd_trade_new_by_hour_{0..23}`
- telnet report 新 `[Pushes by CMD × UTC hour]` section
- 2 new tests

#### A3. §9 canary.sh gates 7-10 for F2-F6 (`9fddd6aea`)

- canary_7_push_health_f5_live — `/api/push-subscriber-info` 5 字段结构 check
- canary_8_orphan_scan_f6 — place sim order + 5.5 min + orphan warn log grep
- canary_9_f2_retry_exp_backoff — smoke test + retry log grep (chaos tool ready)
- canary_10_f3_staleness_auto_resub — passive 30s interval 观察 resubscribe_triggers

SKIP 路径 (daemon 未跑 / 无 log / 无 retry / 无 re-sub) 自然 SKIP 不 FAIL.

#### C1. §15 HK NIGHT_OPEN integration test (`56c3757e5`)

- 新 `crates/futu-gateway/tests/integration_market_state.rs` (~240 LoC)
- 7 integration tests, mock backend proto wire format
- cover: NIGHT_OPEN=13 / NIGHT_END=14 / MORNING=3 / CLOSED=6 / HK-stock 不被
  HK-future NIGHT_OPEN 污染 / US 市场隔离

### 🟡 Fixed — §5 MCP schema 全量规整 (Tier B)

#### B1. 33 MCP req struct 全量 alias 补齐 (`2f378710b`)

v1.4.83 只覆盖 10 top-used. 剩余 33 struct 全部加 alias (公共 set: symbol ←
code/stock/security, symbols ← stocks/code_list/..., env ← trd_env, side ←
trd_side, begin/begin_time ← start_time/from, end/end_time ← to, max_count/count
← num/req_count, 等). 29 new v1_4_84_sec_5_* tests.

#### B2. tool_enums.rs 新模块 — 5 enum + 泛型双接 deser (`f197917a7`)

新 `crates/futu-mcp/src/tool_enums.rs` (1163 LoC):
- MarketEnum (10 variants)
- SubTypeEnum (16 variants)
- OrderTypeEnum (17 variants, 含 v1.4.53 条件单)
- KlTypeEnum (11 variants)
- PriceReminderOpEnum (5 variants)
- `ToolEnum` trait 统一接口 + 泛型 `deser_int_or_enum_str<T>` 双接 deserializer
- 47 new tests

#### B3. 43 struct `#[serde(deny_unknown_fields)]` — 真 breaking (`d6849bbcd`)

所有 MCP `*Req` struct 加 deny_unknown_fields. 未知字段从 silent drop →
loud fail `unknown field` error. 对齐 v1.4.45 REST adapter 的 loud fail 策略
(CLAUDE.md 坑 #30 serde 静默 drop). 4 new b3 tests.

**客户端迁移**: 审 JSON payload 去 typo / 老 field 名.

#### B4. Runtime required validate 补齐 (`060c03f1c`)

3 struct 加 `validate()` method + handler wire:
- SetPriceReminderReq: op-conditional (Add 必 reminder_type+value / Modify 必 key)
- GetPriceReminderReq: symbol XOR market
- CancelAllOrderReq: market 非空

7 new b4 tests.

#### B5. Alias schema-level deprecation hint (`b86d75bcf`)

62 处 `#[schemars(description)]` 末尾 append `(v1.5 deprecated — prefer
canonical name)`. LLM agent / SDK 用户看 tool schema description 自然偏向
canonical 名. 替代 custom visit_map 150+ impl 成本 (见 commit trade-off 说明).

### 📝 Docs — C2/C3

#### C2+C3. observability 双语 (`5fdb629be`)

`docs-site/docs/guide/observability.md` + `.en.md` 加 3 section:
1. Push 链路自愈 (F3 staleness / F4 circuit breaker / F2 retry / F5 字段 / F6 orphan)
2. Canary 真机 verify (10 gate 表 + 用法 + SKIP 语义)
3. Push stream 异常排查 flow (4 步 triage)

双语比例 1.114, pass docs-bilingual CI.

### 🧭 流程纪律 — E2

#### CLAUDE.md 坑 #47 + #48 (`539abbc0d`)

- **#47**: defer 清单须逐项审计, 不能整批 defer. v1.4.83 "v1.5 TODO" 反面
  模式 + 用户 "图省事" 责备触发. 3 问 framework 识别合理 vs 图省事.
- **#48**: enum-as-string / deny_unknown_fields 是基础设施 breaking, 仍 v1.4.x
  patch 不升 v1.5. 行为变化 vs 能力扩展 distinction 判定表.

### 📖 Migration Guide

**新档案**: `essentials/2026-04-24-1525-v1.4.84-migration-guide.md` 给 SDK
作者 + LLM agent 开发者清晰迁移 timeline:

1. 立即: 审 JSON payload 去 typo (deny_unknown_fields 生效)
2. 推荐: canonical 名 + enum string form + order_id string form
3. v1.5 前: 完成 alias 迁移 (v1.5 ship 时 alias 真删)

2-3 版 deprecation window: v1.4.84 → v1.4.85 → v1.4.86 → v1.5 删 alias.

### Verification

- workspace: ~970 passed (v1.4.83 870 + ~100 new 4 tests)
- clippy --all-targets -D warnings: clean
- fmt: clean
- PII scan: clean
- 12 commits on feat/v1.4.84-deferred-all-done branch

## [1.4.83] - 2026-04-24 🟡 双 tester v1.4.81 17-bug report 全清 + CMD3020 chain recovery F2-F6 实装

**🟡 推荐升级**。v1.4.82 已修 tester 3 S + 2 P0 (data-loss class)。本版继续
回应 tester 报告剩余 Tier A/B/C 11 项：**Phase 1** 4 项独立易做 (§7/§12/§10/§6
剩余 audit) + **Phase 2** §9 CMD3020 push chain recovery F2-F6 完整实装
(retry 指数回退 + staleness 自动 re-sub + circuit breaker 30s cooldown + orphan
order 探测 + 健康 state 暴露) + **Phase 3** §5 MCP schema alignment (serde
alias 对齐 py-futu-api + order_id JSON string 接受) + **Phase 4** §14 per-cmd
push 细分计数 (monitoring 基础).

### 🟡 Fixed — Phase 1 (4 项独立易做)

#### §7. REST tracking endpoint 默认 all-conn 视图 (Phase 1.1)

- **现象**：REST `/api/query-subscription` / `/api/sub-info` 默认只报"本
  conn_id 的订阅" —— 但 REST 是 stateless, 每次新 HTTP 请求 = 新
  virtual conn_id → 查到空 result 撒谎 (实际其他 conn 有订阅)
- **修法**：REST `query_subscription` handler 默认注入 `is_req_all_conn=true`
  (用户仍可显式传 `false` 查单 conn); `sub_info` GET 同理. MCP / gRPC /
  core (stateful conn) 行为不变. `/api/push-subscriber-info` 重写 (在 F5
  暴露 real push health 前作 stub + recommendations 3 个:
  `/api/query-subscription`, WebSocket `/ws`, F5 placeholder)
- 6 新 regression tests 覆盖 default + explicit both paths
- commits: `d37a59d24`

#### §12. docs-site auth ret_type 15/11 语义表 (Phase 1.2)

- **现象**：双 tester 反馈同一账号跨版本看到不同 `ret_type` (20 → 11 /
  20 → 15 / 11 → 15 等), 误判为 daemon regression
- **修法** (docs-only)：`docs-site/docs/guide/auth.{md,en.md}` 新加
  F3C Auth 错误码参考表 — 9 `ret_type` values (0/2/11/15/20/21/23/45/99)
  带 Meaning / Trigger / Daemon behavior; 跨版本稳定性表 5 种 transition
  (20 → 11 / 20 → 15 / 11 → 15 / 2 → 11 / 15 → 20) + 2FA 错误码
  (-20011/-102/110005). 外部报告未来遇到同类问题 docs 自助查.
- commits: `13fbd37f6`

#### §10. CLI `futucli` naming 对齐 MCP / SDK (Phase 1.3)

- **现象**：CLI flag 名和 MCP tool / py-futu-api 不一致 (`futucli kline -t day`
  vs MCP `ktype="day"`), 用户在文档间切换时易 confuse
- **修法** (non-breaking, `visible_aliases`)：
  - `Sub` subcommand 加 alias: `subscribe` / `subscription`
  - `Kline` / `Orderbook` / `Ticker` / `Rt` / `Broker` 子命令接受 positional
    **或** `--symbol` flag (带 `--code` / `--stock` alias)
  - 各选项参数加 alias: `-t/--type` → `--ktype/--kltype/--kl-type`; `-n/--count`
    → `--num/--max-count/--req-count`; `--begin/--end` → `--begin-time/--from`
    / `--end-time/--to`
- commits: `d9881022c`

#### §6. REST single-security shorthand 扩展 + delay-statistics POST (Phase 1.4)

- **现象**：tester §6 剩余 5 endpoint (capital-flow / option-chain /
  option-expiration-date / warrant / delay-statistics) silent empty
- **根因**：这些 endpoint proto 字段名是 `security` (capital-flow) 或 `owner`
  (option-chain 等), 用户传单字符串 `{"code": "US.AAPL"}` 被 serde drop
- **修法**：REST adapter 新 `expand_single_symbol_shorthand_to_security_and_owner`
  helper, `symbol` / `code` / `owner-string` / `security_string` 四种
  shorthand → 同时生成 `security` + `owner` 双对象 (proto 各取自己的字段);
  `delay-statistics` 加 POST handler 支持 `type_list` / `qot_push_stage`
  / `segment_list` 过滤 body
- 7 新 regression tests `v1_4_83_sec_6_*`
- commits: `9a5eaeeaa`

### 🟡 Fixed — Phase 2: §9 CMD3020 push chain recovery F2-F6 完整实装

#### F5 Push health state 暴露 + F6 orphan order 探测 (Phase 2.1-2.4)

**F5**: `/api/push-subscriber-info` 返真实 push 通道健康:
- `push_stream_healthy` — bool (综合 circuit + consecutive_errors + 最近
  push 新鲜度)
- `last_push_received_at_ms` / `consecutive_parse_errors` / `total_pushes_received`
  / `resubscribe_triggers` / `circuit_breaker_trips` 等
- 经 `PushHealthSnapshotProvider` closure 注入模式 (同 `AdminStatusProvider`),
  避免 futu-rest → futu-gateway 循环依赖

**F6**: Orphan order 定期扫描 (30s interval, 5min threshold):
- 扫 `trd_cache.orders` 全量; `status=1 Unsubmitted` 且 `create_timestamp`
  距 now >5 min = orphan (push 通道可能断流 / order 卡住)
- 每条 orphan `tracing::warn!` with acc_id/order_id/age_secs; `push_health
  .record_orphan_scan(count)` bump metric

**新模块**: `crates/futu-gateway/src/bridge/push_health.rs` (13 单测 + 7
orphan scan 单测)

commits: `1ddc0a8cd` + `c7accf89c`

#### F2 retry / F3 re-subscribe / F4 circuit breaker (Phase 2.5)

**F2**: `retry_with_exp_backoff(op_name, f)` helper (0ms/1s/3s/9s 4 attempts)
包装 TradeReQuery 6 处 `query_account_info` / `query_orders` /
`query_order_fills` backend 调用. Ok 立即返, 全失败 warn log + caller 降级.

**F3**: tokio 后台任务 (30s interval) 检测 `push_health.last_push_received_at_ms`
vs now. 若 >60s stale **且** 有活跃订阅 → 触发 `resubscribe_quotes(be, subs,
static_cache)` + `push_health.record_resubscribe()` warn log.

**F4** (F3 失败兜底): 若 F3 已触发 re-sub <60s 但 push 仍 stale →
`push_health.trip_circuit()` (30s cooldown). Dispatcher 主循环入口
`push_health.should_skip_dispatch()` 为 true 时跳过 dispatch (warn log).
`record_push_success()` 若 cooldown 过了自动 reset. 两路自愈:
- cooldown 定时到期 → `should_skip_dispatch` auto-reset
- 任意 push 成功 → `record_push_success` auto-reset

commits: `1e73bf2fe`

### 🟡 Fixed — Phase 3: §5 MCP schema alignment (minimum viable, 非 breaking)

- **`#[serde(alias = ...)]`** 添加到 7 top-used MCP req struct 26 字段
  (SymbolReq / SymbolListReq / KLineReq / HistoryKLineReq / HistoryQueryReq
  / CapitalFlowReq / TrdAccReq / PlaceOrderReq / ModifyOrderReq / CancelOrderReq).
  SDK 老用户用 `code` / `stocks` / `begin_time` / `trd_side` / `trd_env`
  等 py-futu-api 风格名字照旧 work, canonical 推 `symbol` / `symbols` /
  `begin` / `side` / `env` 新代码
- **`order_id` 接受 int OR string** (JS clients u64 >2^53 精度丢失 safe):
  ModifyOrder / CancelOrder `order_id` 字段加
  `#[serde(deserialize_with = "deser_u64_from_int_or_str")]`. JSON number 仍
  接受 (Rust serde_json 识别 integer 不走 f64); JSON string 优先推荐 JS clients
- 9 新 regression tests `v1_4_83_sec_5_*`
- **v1.5 TODO** (breaking migration): 全量 60 tool struct alias 补齐 + Rust enum
  as-string serde + `#[serde(deny_unknown_fields)]` 全量 + schema 老字段
  deprecation warn log
- commits: `0347f903e`

### 🟡 Fixed — Phase 4: §14 Per-cmd_id push 细分计数 (CMD14716 UTC window audit)

- `GatewayMetrics` 新加 5 AtomicU64:
  - `backend_pushes_cmd_quote` (CMD 6212)
  - `backend_pushes_cmd_trade_legacy` (CMD 4716)
  - **`backend_pushes_cmd_trade_new`** (CMD 14716 — tester §14 主角,
    v1.4.41 新 trade channel, 订单/成交 update 路由)
  - `backend_pushes_cmd_msg_center` (CMD 5300)
  - `backend_pushes_cmd_other`
- `/metrics` Prometheus 自动暴露新 counters; telnet report 新 `[Pushes by CMD]`
  section 便于运维长窗口观测 (tester §14 INCONCLUSIVE CI job 可验)
- commits: `dad9a764a`

### ⚪ INCONCLUSIVE / Docs-only

- **§11 sens_state**: v1.4.82 已深挖归档修正 (见 essentials/). 本版无代码
  改动. Open Q 转达 backend team (C++ OpenD binary 100% symbol stripped,
  无法用 strings 验 "is/isn't sent" — 需 mitmproxy runtime)
- **§15 HK NIGHT_OPEN**: `pull_all_market_status` HK futures reserved 字段
  行为需 HK 账户 NIGHT_OPEN 时段 (1700-2400) 真机 repro, 本版无 regress
- **§16 WS push cliff-drop + §17 silent crash**: Phase 2 F3/F4 连带解决
  (push stream stale 自动 re-sub, 持续 stale 触发 circuit breaker)

### 📝 Remaining v1.5 TODO (breaking migrations, defer)

- MCP 60 tools 全量 schema alignment
- Rust enum-as-string serde (Market / SubType / OrderType / PriceReminderOp / KlType)
- `#[serde(deny_unknown_fields)]` 全量 MCP 覆盖
- Hidden required schema 显式声明
- 老字段 deprecation warn log (v1.5 删 alias)

### Verification

- workspace: 870 passed (861 base + 9 §5 alias tests = 870)
- clippy --all-targets -D warnings: clean
- fmt: clean
- proto_diff_check: 0 missing fields (baseline maintained)
- PII scan: clean

## [1.4.82] - 2026-04-24 🔴 双 tester v1.4.81 17-bug report: S-tier 3 修 + silent-success anti-pattern 根治

**🔴 必须升级**（涉及 REST subscribe data loss / PlaceOrder orders cache 5 版空转
/ sim diag 零信息）。双 tester (claude-4411 × claude-c22f) 合议 v1.4.81 交 17
项 bug report，本版修 3 个 S 立即修 + 2 个 P0 + 2 个新 CLAUDE.md 坑沉淀 +
6 canary regression gate + sens_state 归档深挖修正。

### 🔴 Fixed (S) — 立即修 3 项

#### A1. REST `/api/subscribe` 全面 no-op 根治（7+ 版长期潜伏）

- **现象**：REST subscribe any body → `{ret_type:0, s2c:{}}` 但零 backend
  effect（WS 0 push）。MCP subscribe 同 backend 正常。跨 v1.4.75-81
- **根因**：REST body 用错字段名（`stocks`/`symbols`/`sub_types`/`is_sub`
  非 proto 定义）→ serde 静默 drop → `c2s.security_list/sub_type_list` 空 →
  SubHandler for loop 0 次 → ret_type=0 "成功" 但零 effect
- **修法**（两层 defense-in-depth）：
  1. SubHandler 入口 **loud validation** — 空 list（非 `is_unsub_all`）
     立即返 clear error，列明正确字段名 + 常见错误字段对照
  2. REST adapter 加 **SDK 友好字段 alias**（`stocks`/`symbols` →
     `security_list`, `sub_types` → `sub_type_list`, `is_sub` →
     `is_sub_or_un_sub`）
- commits: `78b1ba381` (A1 subscribe fix)

#### A2. BUG-60b0-002 PlaceOrder orders cache 5 版空转架构根治

- **现象**：PlaceOrder success 返 order_id，daemon log "cache refreshed
  count=0"；立即查 `/api/orders` count=0 永远看不到新单；`/api/history-orders`
  却能查到。cancel 超时 100012 订单卡 Unsubmitted。跨 v1.4.73/75/80/81 4 版
  空转
- **根因**：v1.4.73 加的是 **re-fetch + upsert** 架构，但 backend
  GetOrderList 对 just-placed 订单有 **replication lag** → re-fetch 拿到
  count=0 → 填空 cache
- **修法**：架构改为 **direct upsert** — PlaceOrder response 成功后立即用
  order_id + client c2s 已知字段构 stub CachedOrder，直接 upsert 到 cache，
  不依赖 GetOrderList re-fetch。push notice_type=4/5/8/100 / 后续 refresh
  通过 upsert enrich stub（同 order_id 覆盖）
- stub status=0 (Unknown) 保守语义 — 用户 0ms 查看到 "订单已提交但 status
  未知" 好于 "看不到订单"（原 bug）或 "hardcode 假 status=1"
- commits: `6ca4a8277` (A2 PlaceOrder upsert)

#### A3. sim PlaceOrder err_msg 空时补 4 种原因 hint

- **现象**：sim 账户 PlaceOrder 失败返 `ret_type=-1 err_code=null ret_msg=
  "[err_code=none] PlaceOrder: 错误 (backend_code=-1)"` — 零诊断。real 账户
  同场景 backend 会给具体原因。跨 v1.4.75/80/81 一致
- **根因**：sim backend 返的 `err_msg` 为空（legacy backend 不会修）
- **修法**（daemon 侧补救）：判断 `trd_env == 0 (Sim)` 且 `result == -1`
  且 `err_msg.is_empty()` → 附加 4 种常见原因 hint（未 unlock / 参数错 /
  限价偏离 / order_type 不支持）+ "查 daemon log CMD4701 raw response" 指引
- commits: `a36131f4e` (A3 sim hint)

### 🟡 Fixed (P0) — 精选 2 项

#### B1. REST 字符串数组 shorthand → security_list 对象数组

tester §6 枚举 13 REST endpoint silent empty 的主要模式：用户传
`code_list: ["US.AAPL"]` 字符串数组，proto 期望 `security_list: [{market,
code}, ...]` 对象数组 → serde drop → handler 空 list → silent.

修法：`expand_symbol_shorthand` 扩展处理两路径：
1. A1 alias 后 `security_list` 是 string array → 就地 transform
2. 独立 shorthand key (`code_list`/`symbols`/`stocks`/`symbol_list`) → take +
   transform + 插入 security_list

抽 `parse_symbol_prefix` 共享 helper（singular `symbol` + plural 共用 12 个
QotMarket prefix mapping）。受益 endpoint: snapshot/market-state/quote/rehab 等.

commits: `95115f028` (B1 symbols array)

#### B2. RequestHistoryKL 入口 loud validation（26 silent edges）

tester §8 BUG-4411-003 枚举 26 silent edges：max_count/日期/code/market。
修法：handler 入口按 v1.4.51 BUG-10 sub_type pattern 加 5 类 validation：
- max_ack_kl_num: None/0 合法（不限制）；< 0 或 > 1000 reject
- security.code 非空（trim）
- security.market 合法 QotMarket 白名单（1/2/11/12/21/22/31/41/51/61/71/81）
- begin_time/end_time 非空必须 parse 成功（不再 fallback 到 0/now）
- 日期顺序 begin > end reject（same day 合法）

commits: `e5bb5f81d` (B2 history-kline)

### 📚 Tier D — CLAUDE.md 新沉淀 2 个坑

**坑 #45 — Silent-success anti-pattern**：任何 daemon handler 返
`ret_type=0` 必须有 downstream effect assertion（subscribe → WS event /
place-order → /api/orders / query-subscription → counter bump）。双 tester
同时揪出 5 个实锤（§2/§3/§6/§7/§8），全部同模式。REST c2s struct 应加
`#[serde(deny_unknown_fields)]`；CI canary 必须验下游 effect 不只 ret_type。

**坑 #46 — 证据权重因 binary 状态而异**：v1.4.82 sens_state deep-dive
实锤 —— production binary 做 symbol/string stripping，`strings | grep X`
0 match **不能证** "runtime 不发"（其他必发字段如 `device_verify_sig` /
`SubmitDeviceVerifyCode` 也 0 match）。证据权重：mitmproxy runtime > source
code > binary strings (stripped)。对 "XX 不发 Y 字段" 类反馈第一反应：
"你怎么知道不发？" + sanity check 其他必发字段 strings 结果。

commits: `0e74615b3` (D CLAUDE.md)

### 📋 Tier A.corrections — sens_state 归档深挖修正

v1.4.81 commit `2e6be34af` 归档基于 FTLogin source 3 处 hardcode 判断
"外部报告不准确 / C++ 对齐"，被 tester binary 3-way 验证挑战。本版 deep-dive：

- Agent 查 FTLogin `auth_impl.cpp` 16 个 HTTP auth entry，确认仅 3 处
  hardcode sens_state（L914/1479/1724），无条件编译，无 runtime flag。Rust
  对齐 L914 + L1724 正确
- **但本机 Futu_OpenD 10.4.6408 binary `strings` 搜 auth 全字段**：
  `sens_state=0` / `device_verify_sig=0` / `SubmitDeviceVerifyCode=0` / 只
  `device_type=2`。**binary 全局 strip 了 auth 字符串** → tester 用 binary
  0 match 作 "C++ 不发" 证据**逻辑错**
- App F3CLogin.framework Obj-C/Swift wrapper 层可能 binary-level intercept
  修改 Authority POST body 删除 sens_state。不在 FTLogin source 责任内
- **结论保留"不改代码"**（FTLogin source 要求 + CLAUDE.md 坑 #4 实证：删除
  后 error_code=99）
- **归档措辞修正**：从 "外部报告不准确" → "tester mitmproxy 证据对；我基于
  FTLogin source 判断不严谨；binary 证据存在陷阱"

commits: `87cc600b1` (sens_state 归档修正)

### 📋 Tier C — CI canary 规范实装

`scripts/canary.sh` 实装 tester §CI canary 6 yaml 规范的前 5 个：
- canary_1_subscribe_push (A1 验证)
- canary_2_place_order_cache (A2 验证)
- canary_3_subscribe_wrong_fields (A1 loud 验证)
- canary_4_sim_place_order_hint (A3 验证)
- canary_5_history_kline_validation (B2 验证)
- canary_6_cmd3020_recovery (v1.4.83+ placeholder)

commits: `f1e12500f` (C canary.sh)

### 📊 数字

- **Tests**: 811 → **828 passed** in workspace（+17 new: A3 5 + A1 gateway 3
  + A1 rest 4 + A2 cache 3 + B1 rest 5 + B2 gateway 12 - A1 已算 gateway/rest）
- **真机 verify**: Tier C canary.sh 5 实装 + 1 placeholder，tester 本地可跑
- **commits**: 7 feature + 1 release
- **LoC**: +2100 / -26
- **CLAUDE.md 坑**: 44 → **46**（+#45 silent-success + #46 binary vs source
  evidence）

### 对用户的影响

| 类型 | 操作 |
|---|---|
| 纯 REST 用户订阅 (7+ 版 silent 失败) | **必须升级**（数据丢失类 bug） |
| 写交易路径用户（PlaceOrder + 立即查 orders）| **必须升级**（5 版空转，可能重复下单）|
| sim 账户用户 | 推荐升级（获得 4 种原因诊断 hint）|
| 纯 MCP 用户（REST 不用）| 可跳过（MCP 路径 v1.4.75-81 已 work，不影响）|

### 不做（v1.4.83+）

- **§5 MCP 60 tools schema 统一** — breaking change + 两版 deprecation，
  v1.4.83 独立专版
- **§7 tracking endpoint 查真实 state** — defer v1.4.83（quota bump 问题，
  独立影响面）
- **§9 CMD3020 chain recovery** — F2-F6 multi-fix，v1.4.83+ 独立专版
- **§10 CLI naming cleanup** — v1.4.84 cleanup
- **§14-17 INCONCLUSIVE** — 需 CI 长窗口 job（US RTH 6h / HK NIGHT_OPEN）
- **deny_unknown_fields on prost c2s struct** — prost auto-derive 不支持，需
  adapter-level validation 专版 tackle

### 相关文件

- 本版 plan: `.claude/plans/eager-waddling-gizmo.md` (将归档到 essentials)
- Session summary: `essentials/2026-04-24-<ts>-v1.4.82-session-summary.md`
- Fix-report for testers: `essentials/2026-04-24-<ts>-v1.4.82-fix-report-for-testers.md`
- sens_state 深挖修正: `essentials/2026-04-24-0910-followup-sens-state.md` §4（v1 修正版，内部归档保留完整上下文）

## [1.4.81] - 2026-04-24 🔴 BUG-009 6 版 saga closure: Layer 1 gap + Option B 真修（真机 verified）

**🔴 必须升级**（v1.4.72-80 Fix 9a 一直未真修；v1.4.81 真机 verify 后结构性
重写）。涉及所有 SMS 2FA 首次登录 / `--verify-code` 场景。此前 v1.4.75 Option A
标 Risk 2 🟡 UNVERIFIED，v1.4.81 真机 verify 发现 **2 层 gap + 1 层假设推翻**，
ship Option B 真修。

### 🔴 Fixed (P0) — BUG-009 Fix 9a Option A 真机 verify 后结构性重写

**上下文**：v1.4.75 "探路版" ship 了 Fix 9a Option A（cached `device_verify_sig`
→ 跳 authority re-POST），标 Risk 2 🟡 UNVERIFIED。本版真机 verify 后确认
**两层 gap + 一层假设被推翻**：

#### Layer 1 gap — shell-persist（真机证实存在 + 修复 + 验证生效）

- **现象**：`persist_device_verify_sig` 遇 credentials **不存在**时直接 return
  ([crates/futu-backend/src/auth/device.rs:250](crates/futu-backend/src/auth/device.rs:250))
  → 首次登录场景 dvs 从不落盘 → Fix 9a Option A 前置永远不成立
- **实锤**：2026-04-24 02:18-02:22 真机实测，Step 1 发 SMS 后 credentials
  **未创建**；Step 2 重启 `--verify-code` 仍重 POST authority → 反刷 15
- **修法**：扩 `persist_device_verify_sig` 签名加 `FirstAuthContext` 参数，
  credentials 不存在时**写最小壳**（account + device_id + uid + rand_key_b64
  + user_attribution + dvs + ts）。真机验证（02:33 rebuild 后）shell 成功写盘

#### Layer 2 backend 语义 — Risk 2 真机推翻

- **原假设**（v1.4.75 Option A）：backend 对同 uid + cached dvs 的
  `req_device_code` 5min 内**不重发 SMS**
- **真机实锤**（02:34 reproduce）：cached dvs 的 `req_device_code` 仍会触发
  **新 SMS 覆盖老码**（用户手机收到第 2 条 SMS 覆盖首次的）
- **结论**：Option A "避免新 SMS 覆盖老码" 目标**未达成**（仅能避
  authority POST 反刷 15），需切 Option B

#### 修法 — v1.4.81 Option B（per v1.4.75 fix-report §Risk 2 fallback plan）

**cache `device_code_sig`** 而非仅 dvs，Fix 9a 路径**跳过 `req_device_code`
整步**，直接用 cached dcs + 用户 `--verify-code` 调 `verify_device_code`。

- `SavedCredentials` 加 `device_code_sig: Option<String>` + `device_code_sig_ts`
  （`#[serde(default)]` 向后兼容）
- `DEVICE_CODE_SIG_TTL_SECS = 5 * 60` 保守和 dvs 同 TTL
- 新 helper: `fresh_cached_device_code_sig` / `persist_device_code_sig`
- `handle_device_verify` 加 `cached_device_code_sig: Option<&str>` 参数：
  - `Some` → fast-path 跳 req_device_code（log "Option B: using cached dcs"）
  - `None` → 原流程发 SMS + persist 新 dcs 到 credentials
- Fix 9a path 升级：
  1. 优先 `fresh_cached_device_code_sig` → Option B 快车道
  2. fallback `fresh_cached_device_verify_sig` → Option A half-fix（仅跳 POST）
  3. 都没 → `password_auth`
- `persist_device_code_sig` 在 `req_device_code` 响应成功后立即落盘（**在
  `prompt_input` 之前**）—— daemon 非交互退出前 dcs 已持久化

**验证状态**：
- ✅ 70 auth unit tests pass
- ✅ **Option B 真机 verified (2026-04-24 03:44-03:46)** — Step 1 发 SMS 后
  用户 Ctrl+C 不输码 → credentials 留 shell + cached dvs + dcs；Step 2 5min
  内 `--verify-code 931561` 跑：
  - `v1.4.81 BUG-009 Fix 9a Option B: using cached device_code_sig + dvs,
    skipping req_device_code entirely` log 触发 ✅
  - backend 接受 cached dcs + 用户 SMS 码 → `✅ 设备验证成功` ✅
  - **手机不再收第 2 条 SMS** ← Option B 核心目的达成 ✅
  - daemon exit 0，credentials 完整 populate

**Option B Risk 已消除**：
- backend 对 cached `device_code_sig` 5min 内接受 ✅
- `device_code_sig` TTL ≥ 5min（真机测试，实际值未知但 ≥ 120秒的 Step1→Step2 间隔）

### 📚 A1 + A2 — CLAUDE.md 坑 #43 + #44 沉淀（commit `72ed6f16f`）

- **坑 #43 Persistence helper 必须从 null state 工作**（v1.4.81 Layer 1 实锤）
  - 任何 `persist_X(val)` helper 必须能从 empty/null state 写入
  - unit test 必须覆盖 first-auth / clean state / 文件缺失场景
  - code review 看到 `let Ok(data) = read_to_string(path) else return;` 立即
    问 "null state 是否应该写 shell？"
- **坑 #44 同 bug 跨版本迭代的 regression 链 + 三重复合失效**
  - BUG-009 6 版 saga timeline + 3 重失效（坑 #34 + #41 + #42 + 新加 #43）
  - fix-report 必须区分 🔴 unit / 🟡 integration / 🟢 真机 三层证据
  - 探路版模式健康但必须前置 fallback plan（v1.4.75 → 81 就是模板）
  - CHANGELOG 🟡 UNVERIFIED 标签必须下版 update 状态不许消失

### 🧪 A3 — Option B + Layer 1 regression guard unit tests（commit `981809c15`）

5 new tests in `crates/futu-backend/src/auth/tests.rs`：

- `persist_device_code_sig_upsert_existing` — 正常路径 dcs upsert
- `persist_dcs_first_auth_no_shell_by_design` — 记录 dcs 不做 first-auth shell
  的设计决定（与 dvs 不同，依赖 caller 保证 credentials 已存在）
- `fresh_cached_dcs_respects_5min_ttl` — TTL 5min 过期保护
- `option_b_takes_priority_over_option_a` — 3 分支优先级（dcs+dvs / 只 dvs /
  都 miss → password_auth）
- `persist_dvs_first_auth_shell_write` ★ — CLAUDE.md 坑 #43 核心 regression
  guard，覆盖 v1.4.72-80 从没被测试过的 first-auth shell-write 场景

**防再发生纪律**：任何 persist_X helper 必须有 first-auth 单测（文件缺失）+
upsert 单测（文件已存在）。缺一不过 review。

### 📋 A4 — `fix-report-for-reviewer` 结构化交付（commit `12b848c50`）

[`essentials/2026-04-24-0415-v1.4.81-fix-report-for-reviewer.md`](essentials/2026-04-24-0415-v1.4.81-fix-report-for-reviewer.md)
427 行档案级文档，对称外部 reviewer 原 BUG-009 report 结构：

- 三重复合失效图示（Layer 1 + 2 + 3 为什么 8 版才定位）
- Layer 1 / Layer 3 深度剖析（真机 timeline + 修法 + regression guard）
- 关闭的 UNVERIFIED flags 清单
- v1.4.72 → 75 → 81 三版对照（5 维度）
- Reviewer re-verify 命令（step 1-4 真机流程 + FAIL 场景证据清单）
- §7.D 补 BUG-008 5 步 repro request（v1.4.80 audit 发现的 follow-up 遗漏）

### 🔄 B1 — `build_backend_msg_header` → `translate.rs`（commit `6c35a1f4f`）

Phase E2 翻译层收敛 **100%**：v1.4.80 B3 抽了 6 个 full translator，v1.4.81 B1
补齐辅助 helper `build_backend_msg_header`。未来 MsgHeader 字段扩展（比如
`input_source` 新枚举）只改 1 处。

- translate.rs: +33 LoC（新 pub(super) fn + doc block）
- trd/mod.rs: -18 LoC（删原 fn 定义 + closure 注释说明 E0364 为什么不做 re-export）
- max_qty.rs + history.rs × 2: 3 处 call site 改 `super::translate::build_backend_msg_header`

### 📝 B2 — bridge/mod.rs v1.4.82+ 拆分 Roadmap 写入（commit `961946349`）

v1.4.80 B2 完成 Handler Deps pattern 全覆盖（55/55）解锁了 bridge 拆分，
但 scope 过大（19 fields / 68% coupling）defer 到 v1.4.82+。本版在
`crates/futu-gateway/src/bridge/mod.rs` 顶部 doc block 写入**具体 roadmap**：

- v1.4.82: BrokerManager (~200 LoC，最清晰轴)
- v1.4.83: CacheBundle (~150 LoC)
- v1.4.84: Connection Lifecycle (~300 LoC)
- v1.5: PushDispatcherManager (~300 LoC)
- 执行纪律：增量拆 / 每拆独立 commit / pub(crate) → pub(in crate::bridge) 收紧
- 零代码改动，零 behavior 影响

### 📊 数字

- **Tests**: 297 → **302 passed** in futu-gateway；70 → **75 passed** in
  futu-backend auth tests（+5 regression guard，零回归）
- **真机 verify**: BUG-009 Option B PASSED 2026-04-24 03:44-03:46
- **commits**: 7（Tier 0 core fix + A1+A2 / A3 / A4 / B1 / B2 + release）
- **LoC**: Tier 0 +700/-65（已 committed 333f3eb36）+ A+B +912/-39（本版新
  增）+ essentials/fix-report 427 行 md

### 对用户的影响

| 类型 | 操作 |
|---|---|
| v1.4.72-80 任何版本，2FA SMS 账户 | **强烈推荐升级** — Fix 9a 终于真修（v1.4.72 起一直未生效）|
| v1.4.71 及更早（无 Fix 9a）| 可升级获得 Option B 真修 |
| 开发者 | CLAUDE.md 坑 #43 + #44 + fix-report + regression guard tests 为跨版本 bug 迭代提供教科书级案例 |

### 相关文件

- Verify report (内部): [`essentials/2026-04-24-0248-v1.4.81-bug009-verify-report.md`](essentials/2026-04-24-0248-v1.4.81-bug009-verify-report.md)
- Fix report (外部 reviewer): [`essentials/2026-04-24-0415-v1.4.81-fix-report-for-reviewer.md`](essentials/2026-04-24-0415-v1.4.81-fix-report-for-reviewer.md)
- Session summary: [`essentials/2026-04-24-0415-v1.4.81-session-summary.md`](essentials/2026-04-24-0415-v1.4.81-session-summary.md)

### 不做（v1.4.82+）

- **bridge/mod.rs BrokerManager split** — v1.4.82 专版（~200 LoC，独立）
- **CachedSecurityInfo.mkt_id 持久化** (v1 → v2 schema bump) — v1.4.82+
- **Reply-slack 4件套**（英短/英中/中短/中中）— 需 hands-on 审稿 paste Slack，
  fix-report 已是结构化文档，Slack 文案下个 session 做
- Code: `crates/futu-backend/src/auth/{device.rs,mod.rs,tests.rs,parse.rs}`

## [1.4.80] - 2026-04-24 🔄 Tier B 全落地：push_parser 100% + 52 handlers A1 迁移 + 6 full translators

**可跳过此版**（v1.4.79 用户）。延续 v1.4.79 的 Phase E2 架构打磨 + v1.4.78
的 test 加强主题，全部是**低风险 refactor**，零 behavior 变化。

### 🧪 B1 — push_parser 剩 4 parse_* tests (+8 tests, coverage 60% → 100%)

- **commit `e932e8208`** — F-GW-E2E-002 push_parser 全面覆盖 10/10 parse_*：
  - `parse_broker_queue_to_push` (SBIT 9) — 2 tests（normal 更新 cache + malformed）
  - `parse_ticker_to_push` (SBIT 35) — 2 tests（empty tick 不 panic + malformed）
  - `parse_rt_to_push` (SBIT 20) — 2 tests（empty time-sharing + malformed）
  - `parse_quote_push_truncated` (HK 3032/3033 manual-varint) — 2 tests（empty
    bytes + wire_type != 2 break early）
- push_parser.rs 本轮后加测试数 = 21 (13 + 8 new)。零 production 改动

### 🔄 B3 — 6 full translators 抽取到 translate.rs (Phase E2)

- **commit `90c65c1c1`** — v1.4.79 A2 的 SecurityContext helper 基础上，
  进一步把 5 个 handler 的 backend req 构造**全部**集中到 translate.rs：
  1. `ftapi_place_order_to_backend` (OrderNewReq, 31 fields)
  2. `ftapi_cancel_order_to_backend` (OrderCancelReq, 5 fields)
  3. `ftapi_modify_order_to_backend` (OrderReplaceReq, 10 fields)
  4. `ftapi_max_qty_to_backend` (MaxBuySellReq, 14 fields)
  5. `ftapi_history_orders_to_backend` (HistoryOrderListReq, 17 fields)
  6. `ftapi_history_fills_to_backend` (HistoryOrderFillListReq, 13 fields)
- **Value**：CLAUDE.md 坑 23 "proto-internal 不是 C++ 完整抄本" 3 次同坑
  (v1.4.41 OrderNewReq 漏 14 / v1.4.43 HistoryOrder* 漏 19) 的结构性根因
  一次性修掉。下次 backend proto 加字段或补漏只改 translate.rs 一处。
- **零 behavior 变化**：字段赋值顺序 / Option<> / 默认值 / format_qty 格式化
  / v1.4.43 补齐的常量 `vec![1,2,4]` 等 100% 保留
- Handler body 缩减：place_order -45 LoC / modify_order -25 / history -35 /
  max_qty -20

### 🔄 B2 — 52 handlers 迁移到 XxxDeps + new(deps) pattern (Phase E2)

- **commit `67385037b`** — v1.4.79 A1 pilot 3 handler 的 Deps pattern 扩到
  **全 55 handler**（3 已迁 + 52 新迁 = 全覆盖）
- 每 handler 加 `pub(super) struct XxxDeps { ... }` + `impl XxxHandler {
  pub(super) fn new(deps: XxxDeps) -> Self { ... } }`
- register_handlers() 改 `Arc::new(X { ... })` → `Arc::new(X::new(module::XxxDeps { ... }))`
- 为 v1.4.81+ `bridge/mod.rs` 2105 LoC 瘦身铺路（现在 register 通过 Deps 构造，
  bridge 依赖暴露面清晰）

### 📊 数字

- **Tests**: 289 (v1.4.79) → **297 passed** in futu-gateway (+8 B1 new)
- **Workspace 全量 test**: **791 passed** (25 binaries，零回归)
- 4 feature commits (B1 + B3 + B2 + release)
- LoC 变动：B1 +133（仅 tests）/ B3 +289/-132 / B2 +941/-140 = 总净 +1091
- F-GW-E2E-002 推送解析覆盖从 60% → **100%**

### 对用户的影响

| 类型 | 操作 |
|---|---|
| 已升级 v1.4.79 用户 | **可跳过此版** — 零 user-facing 新功能 |
| 开发者 | Handler Deps pattern 全覆盖 / 字段映射单一真相源 / push 解析测试全覆盖 |

### 不做（v1.4.81+）

- bridge/mod.rs 2105 LoC 瘦身（现在可做，B2 已让 handler 依赖显式）
- CachedSecurityInfo.mkt_id 持久化到 SQLite（v1 → v2 schema bump）
- 抽 build_backend_msg_header 到 translate.rs（5 处调用点统一）

## [1.4.79] - 2026-04-24 🔄 架构优化 bundle：Phase E2 + E3（A1 + A2 + B1 + B2）

**可跳过此版**（已用 v1.4.78 的用户，零 user-facing 新功能）。Phase E2 + E3
架构打磨版：handler DI 精细化 + FTAPI↔backend 翻译层中心化 + SQLite schema
版本化 + err_hint 集中。全部是**低风险 refactor**，零行为变化。

### 🔄 A1 — Handler DI 精细化（Phase E2）

- **commit `8ff06010c`** — 3 pilot handler (PlaceOrder / UnlockTrade / Sub)
  引入明确的 `XxxDeps` struct + `new(deps)` 构造方法
- 未来加 handler 字段 → 只改 `Deps` struct + `new()` 内部映射，
  `register_handlers()` 调用点不变
- Test 可写 `PlaceOrderDeps { ... mock ... }` 独立构造 handler，不需 `Arc<GatewayBridge>`
- 剩 60+ handler 同 pattern 迁移留 v1.4.80+ 增量做
- **Stat**：+79 / -4 LoC（3 handler × Deps + new()）

### 🔄 A2 — FTAPI↔backend 翻译层中心化（Phase E2）

- **commit `0e9bd62d5`** — 新建 `crates/futu-gateway/src/handlers/trd/translate.rs`
- `SecurityContext` struct 聚合 5 字段（sec_market / qot_market / security_type
  / exchange_str / exchange_code）
- `resolve_security_context()` Layer 1-5 priority：code prefix → ticker pattern
  → SDK → trd_market → static_cache mkt_id（对齐 CLAUDE.md 坑 36）
- 消除 `place_order.rs` + `max_qty.rs` 中重复的 5-call derive chain
  （CLAUDE.md 坑 23 "proto-internal 不是 C++ 完整抄本" v1.4.41/43 3 次
  同坑的结构性根因 — 现在单一真相源，下次字段变动只改 1 处）
- **5 new unit tests**：HK stock / US stock / US futures / idempotency /
  code_prefix overrides SDK
- **Stat**：+255 / -114 LoC（helper + tests + 2 handler migrations）

### 🔄 B1 — SQLite schema_version 跟踪（Phase E3）

- **commit `a76cff185`** — `stock_data.db` 加 `PRAGMA user_version` + migration
  chain 基础设施
- `CURRENT_SCHEMA_VERSION: u32 = 1`（baseline），未来加字段时 bump + 加 match arm
- `migrate_schema(conn)`：v0 → v1 baseline / v > CURRENT → warn log 不动 DB
  （用户降级 daemon 场景）/ unknown version → 报错（代码 bug）
- `StockDb::schema_version()` API 用于 daemon startup debug
- **4 new unit tests**：fresh DB migrate / idempotent / newer DB preserved /
  multi-call idempotent
- **用户影响**：零。现有 DB 首次启动时 user_version 0 → 1 静默 bump
- **Stat**：+187 / -0 LoC

### 🔄 B2 — Error hint 中心化（Phase E3）

- **commit `4678d321a`** — `translate_unlock_err_hint` 从 `unlock.rs` 搬到
  `err_hint.rs`，对齐 "所有 trd ret_code → user hint 集中" 的 module 职责
- **CLAUDE.md 坑 23 护栏**：未来对 moomoo token / 2FA 语义再有修正时 grep 一处
  （err_hint.rs）即可，不用跨 unlock.rs + place_order.rs + modify_order.rs
- 零 behavior 变化 — 函数签名 / 错误码 map 完全保留，7 个现有 test 通过
  `super::*` re-export 透明访问
- **Stat**：+50 / -48 LoC

### 📊 数字

- Tests: 280 (futu-gateway) → **289 passed** (+9 new: 5 A2 + 4 B1)
- Workspace 全量 test: **783 passed** (25 test binaries, 0 regression)
- Production LoC changes: ~25 (err_hint 移动) + 5-call helper 抽取 (zero
  行为 delta) = effectively 0 user-visible
- 4 feature commits + 1 release commit
- 新增文件：`translate.rs` + 6 Deps structs + stock_db migration
  infrastructure

### 对用户的影响

| 类型 | 操作 |
|---|---|
| 已升级 v1.4.78 用户 | **可跳过此版** — 零 user-facing 新功能 |
| 开发者（阅读代码 / 贡献） | Handler DI pattern 明确、FTAPI↔backend 字段映射单一真相源、未来 DB 升级有版本护栏 |

### 为什么不合并这些到未来的 feature 版

**对齐 CLAUDE.md 版本号分配纪律**（v1.4.57 沉淀）：
- v1.4.79 scope ~730 LoC 超 500 LoC 上限，但**全是 refactor + 零 user-facing
  改动**，对标 v1.4.77 (1500 LoC Phase D closure) / v1.4.78 (~2840 LoC moved
  zero net) 混合 refactor 版本策略
- 4 项独立 commit，出问题可 partial revert 不影响其他
- 不升 v1.5 —— 不是"吃掉整个 roadmap tier"（E2+E3 部分完成，E4 / C1 / D1 /
  D2 尚未启动），不是"用户能做新的事"

### 下一版本候选 scope（v1.4.80+）

**Tier A（等 reviewer 反馈触发）**：
- BUG-009 Risk 2 真机反馈（PASS → 关 UNVERIFIED / FAIL → Option B）
- BUG-008 5 步 repro 真机 verify 请求（audit 发现遗漏的 follow-up）

**Tier B（独立）**：
- 剩 60+ handler A1 Deps pattern 迁移
- A2 抽 6 个 full translator（ftapi_place_order_to_backend 等）—— 需先证明
  SecurityContext helper 零回归
- push_parser 剩 4 parse_* tests（broker_queue / ticker / rt / quote_push_truncated）
- tools.rs 60 #[tool] 拆分（需 agent 调研 rmcp 宏跨文件支持）

**Tier C（polish）**：
- bridge/mod.rs 2105 LoC 瘦身（依赖 A1 全量完成）
- `CachedSecurityInfo.mkt_id` 持久化到 SQLite（v1 → v2 schema bump）

## [1.4.78] - 2026-04-24 🔄 Tier B 全落地：BUG-012 docs + push_parser 6 tests + auth/mod.rs -46% + tests_v1_4_41_helpers 4-way split

**可跳过此版**（已用 v1.4.77 的用户，零 user-facing 新功能）。v1.4.78 Plan
§Tier B 全做（4 项）。持续 v1.4.77 "文件瘦身 + 测试加强 + 纪律沉淀" 主题。

### 🟢 Fixed (B3)

- **BUG-012 `/api/sub-info` per-conn vs `/api/query-subscription` all-conn 澄清**
  (`commit c6272f76f`)

  外部 v1.4.71 报告 BUG-012 "subscribe 成功但 sub-info 返空" 是 **per-connection
  by-design**。v1.4.74 A2 已加 `/api/query-subscription` POST 版提供 `is_req_all_conn`
  cross-conn 能力，但 docs 未说明 → 用户可能继续踩混淆。v1.4.78 B3 在
  `docs-site/docs/guide/rest.{md,en.md}` 双语加 info section 明确差别 +
  推荐生产查订阅用 query-subscription。

### 🧪 Tests Added (B1, +6 tests)

- **push_parser.rs 6 new tests**（`commit a83a04f42`）—
  v3 review §9.2 F-GW-E2E-002 进度 30%→60%（6/10 parse_* 覆盖）
  - `parse_price_to_push` (SBIT 0) 2 tests（normal + zero price）
  - `parse_order_book_to_push` (SBIT 3) 2 tests（normal + malformed）
  - `parse_kline_to_push` (KLine) 2 tests（empty + malformed）

  剩余 4 个 parse_*（broker_queue / ticker / rt / quote_push_truncated）留
  v1.4.79+。

### 🔄 Refactor (B2, B4)

- **B2 auth/mod.rs 2064 → 1124 LoC (-46%)**（`commit 15c9b7689`）—
  单一 `#[cfg(test)] mod tests { 944 LoC }` 拆到独立 `auth/tests.rs`。Rust
  默认 `mod X;` 解析 X.rs 模式。对齐 v1.4.77 T1-T8 pattern。

- **B4 tests_v1_4_41_helpers.rs 1918 → 4 themed files**（`commit f8812a996`）—
  146 tests 按主题拆到子目录:
  ```
  tests_v1_4_41_helpers/
  ├── mod.rs           (16 LoC, aggregator + #![allow(deprecated)])
  ├── derive.rs        (1028 LoC, 61 tests: derive_security_type / derive_exchange_str / sec_market / us_futures / hk_option / E2E)
  ├── code_patterns.rs (331 LoC, 31 tests: is_option/futures / strip_market / hash_backend_id)
  ├── time.rs          (271 LoC, 25 tests: ftapi_time_str / backend_micros_datetime_str / default_history_time_range)
  └── misc.rs          (310 LoC, 27 tests: err_hint / mask_acc_id / normalize / check_acc_id / cached_overnight / market_filter)
  ```
  最大单测文件从 1918 → 1028 LoC (-46%)。

### 📊 数字

- Tests: 768 → **280 passed in futu-gateway** (+6 new B1, zero regression
  from B2/B4 refactor)
- **auth/mod.rs**: 2064 → 1124 LoC (-46%)
- **tests_v1_4_41_helpers.rs** (新 largest tests): 1918 → 1028 (-46%)
- 4 feature commits + 1 release commit
- Production LoC: ~30（docs only，B3）
- Tests LoC: +150（B1 new tests）
- Refactor LoC: ~940 (B2) + ~1900 (B4) = ~2840 moved (zero net)

### 对用户的影响

| 类型 | 操作 |
|---|---|
| 已升级 v1.4.77 用户 | **可跳过此版** — 零 user-facing 新功能 |
| 第一次用 `/api/sub-info` 疑惑的 | **推荐看新 docs** — 明说 per-conn 含义 + 推荐 `/api/query-subscription` |
| 开发者 / 维护者 | **推荐升级** — auth/mod.rs -46% 瘦身 + 测试按主题分文件更易 review |

### v3 Review §9 进度

| 建议 | v1.4.77 | v1.4.78 | 待做 |
|---|---|---|---|
| §9.2 F-GW-E2E-002 push_parser tests | 30% (3/10) | 60% (6/10) | 4 个 parse_* 留 v1.4.79+ |
| §9.2 F-TRD-MOD-TEST 拆分 | ✅ | — | — |
| 大文件拆分（v3 review §10）| trd/mod.rs 68% | +auth/mod.rs 46% / +tests_v1_4_41_helpers 46% | tools.rs 60 #[tool] 待 |

---

## [1.4.77] - 2026-04-23 🔄 v3 review §9 落地：Phase D 闭环 + pre-push hook + push_parser tests + trd/mod.rs 68% 瘦身

**可跳过此版**（已用 v1.4.76 的用户，零 user-facing 新功能）。v3 code review
master report §9 建议落地：4 commits 组合。

### 🔄 Refactor (T1-T8)

- **`trd/mod.rs` 从 3823 → 1225 LoC (-68%)**（`commit 7f78d8333`）

  8 个 `#[cfg(test)] mod tests_*` 内嵌 test modules 拆到独立文件
  （`crates/futu-gateway/src/handlers/trd/tests_*.rs`）：
  - `tests_group_accounts.rs` (111 LoC)
  - `tests_bug_a_routing.rs` (98)
  - `tests_v1_4_48_order_broker_routing.rs` (98)
  - `tests_bug_b_err_hint.rs` (42)
  - `tests_market_closed_hint.rs` (127)
  - `tests_cipher_short_circuit.rs` (88)
  - `tests_v1438_extract_acc_id.rs` (98)
  - `tests_v1_4_41_helpers.rs` (1918 LoC，最大，v1.4.78+ 可再拆)

  `mod.rs` 加 8 个 `#[cfg(test)] mod tests_X;` 声明。**纯 refactor**：测试代码
  1 行未动、prod 代码 1 行未动，仅改 location。

### 🟢 Fixed / Polished

- **F1 pre-push hook Check 5: review_scan metric drift**（`commit e7f0cac84`）—
  `scripts/review_scan.sh` 集成到 `.githooks/pre-push`，每次 push 前 info
  输出 16 crate × tech-debt 指标 snapshot。不 block push。对齐 CLAUDE.md 坑
  #39 "Review 两阶段 scope"。

- **D1 Phase D 闭环**（`commit 7ef229c3a`）— CLAUDE.md 坑 #35 首次标闭环 ✅：
  - `derive_exchange_str` 加 `#[deprecated]`（防 external caller 误用）
  - 保留为 `derive_exchange_str_cache_first` 内部 fallback
  - CLAUDE.md 坑 #35 加 v1.4.77 闭环段

  **实际修复** Agent 调研发现 Phase D 早已 95% 完成（v1.4.54/59/66-67 逐版
  实装）。v1.4.77 只做最后的 `#[deprecated]` 标 + CLAUDE.md 闭环。

### 🧪 Tests Added (E1, 7 new)

- **`push_parser.rs` 7 unit tests** — v3 review §9.2 F-GW-E2E-002 部分落地：
  - 3 parse_stock_state tests（suspend flag / non-suspend / cache miss /
    malformed bytes）
  - 1 parse_deal_statistics smoke
  - 2 parse_us_pre_after_detail tests（BUG-006 L2 回归保护）

  剩余 7/10 parse_* fn 留 v1.4.78+ 继续扩。

### 📊 数字

- Tests: 761 baseline → **768 passed** (+7 new E1 + 0 regression from T1-T8)
- **trd/mod.rs: 3823 → 1225 LoC (-68%)**
- 4 feature commits + 1 release commit
- Production LoC: ~70
- Tests LoC: +250
- Refactor LoC: 2598 moved across 8 files（零净增）

### 对用户的影响

| 类型 | 操作 |
|---|---|
| 已升级 v1.4.76 用户 | **可跳过此版** — 零 user-facing 新功能 |
| 开发者 / 维护者 | **推荐升级** — trd/mod.rs 68% 瘦身 + pre-push hook + CLAUDE.md 坑 #35 闭环 |
| 做 code review 的 | **推荐升级** — 测试模块按主题分文件，blame 更清晰 |

---

## [1.4.76] - 2026-04-23 🟢 BUG-003 Layer 1 SMS 时序 UX + BUG-007 audit + CLAUDE.md 3 新坑 + one-session retrospective

**可跳过此版**（已用 v1.4.75 的用户）。本版 scope 是 **Phase 1 独立 deferred
bug audit + 纪律沉淀**，不含 user-facing 新功能。Phase 2（等外部 reviewer
v1.4.75 Risk 2 真机反馈）留 v1.4.77+ 视反馈触发。

### 🟢 Fixed (Phase 1)

- **BUG-003 Layer 1: SMS timing log clarity + docs-code alignment**
  (`commit b2f015997`)

  外部 v1.4.71 报告 §4.2 Layer 1 指 "docs 说 SMS 已发，实际 tty 检查 abort
  前 SMS 未发"。代码审查确认 **SMS 实际在 tty 检查之前发**（handle_device_verify
  先调 `req_device_code` 触发 SMS，然后才调 prompt_input 做 tty 检查），
  docs 描述技术上正确。

  但老实装有 2 个 UX 缺陷造成 docs-code mismatch 感：
  1. `println!` 到 stdout — systemd/Docker/CI 环境下日志可能不连贯，用户
     在 journalctl 里看不到 "SMS 已发到手机"，只看到后面 tty abort 错误
  2. tty abort 错误只说 "请在前台运行"，没告知 "SMS 已发，用 --verify-code
     <CODE> 重启" 的正确 next action

  修法：
  - `handle_device_verify` SMS 通知 `println!` → `tracing::info!`（和其他
    daemon log 同一 stderr stream）
  - `prompt_input` tty abort 错误新文案含 "SMS already sent" + "(a) 前台交互 /
    (b) --verify-code <CODE>" 双 option + "⚠️ 不要盲目重启"
  - `docs-site/docs/tutorials/cheatsheet.md` + `.en.md` 加 "SMS 时序澄清"
    section 明确 SMS 在 tty 检查前发

### ⚪ Audit-only (Phase 1)

- **BUG-007 sim 空 err_msg audit** (`commit aa9cf8dd6`)

  外部 v1.4.71 报告 §10：v1.4.69 daemon log 有 3 次 `result=-1 err_msg=`
  empty，v1.4.71 10+ 姿势重现不出。

  代码审查 `format_backend_trd_error` (err_hint.rs:19-42，v1.4.42 引入) 确认
  **空 backend err_msg 自 v1.4.42 起 fallback 到** `"PlaceOrder: 错误 (backend_code=-N)"`。
  **user-facing response 永不为空**。

  reviewer 看到的 `err_msg=` (empty) 是 daemon `tracing::warn!` 记录 backend
  **原始数据**（debug 设计），不是 user-facing bug。sim/real 走同一代码路径。

  v1.4.76 不改 code，audit report 归档 `essentials/2026-04-23-2230-v1.4.76-a2-bug-007-audit.md`。
  若外部 reviewer 坚持 daemon log 也 fallback，留 v1.4.77 评估。

### 🧭 纪律沉淀 (Phase 1)

- **CLAUDE.md 3 新坑** #40/#41/#42 (`commit b9f9378c6`)

  本 session 4 版（v1.4.72/73/74/75）实战产生 3 条纪律候选，本版固化：
  - **#40 "探路版"成本优势** — 代码侧零 regression + fallback 允许时，立刻
    ship UNVERIFIED 比等真机 verify 更优（v1.4.52→53 + v1.4.75 实证）
  - **#41 半修 audit-only 诚实标** — fix-report / CHANGELOG 写 "已修" 前必
    须验证声称的 root cause 真 address 报告 repro（v1.4.72 Fix 9a 反例教材）
  - **#42 Backend-semantic 风险永远需真机 verify** — 代码审查 100% 覆盖
    不了 backend 隐式行为（v1.4.75 Risk 2 实证）

  4 坑形成闭环：#34 识别风险 → #42 标风险类型 → #40 探路版 ship 策略 → #41
  诚实汇报。

### 📜 Retrospective (Phase 1)

- **v1.4.72-75 one-session retrospective** (`commit b4967c332`)

  2026-04-23 一天内 ship 4 个 minor versions 的完整复盘：
  - 总数字：4 versions / 16 bug closed / 1 UNVERIFIED / ~3035 LoC / 55 new tests / ~4h session
  - 驱动 3 引擎：外部 reviewer 报告 + 用户 "Tier A+B+C 都做" scope + 探路版策略
  - 反面教训 3 条：overclaim / scope 遗漏 / test count 不准
  - 可持续性分析：默认节奏 1-2 版/day，一天 4 版是特殊场景
  - 对未来 session 5 条建议

  档案：`essentials/2026-04-23-2245-v1.4.72-to-75-one-session-retrospective.md`

### 📊 数字

- Tests: 761 baseline (from v1.4.75) → **761 passed** (+0 — Phase 1 无新测试)
- 5 feature commits + 1 release commit
- production LoC: ~20（auth log + prompt_input msg，其余都是 docs/essentials/CLAUDE.md）
- docs/essentials LoC: ~900（retrospective + audit report + CLAUDE.md 3 新坑 + docs-site 双语）

### 对用户的影响

| 类型 | 操作 |
|---|---|
| 已升级 v1.4.75 用户 | **可跳过此版** — 无新功能 |
| 新用户首次部署 SMS 遇 tty abort | **推荐升级** — tty abort 错误 hint 更清晰 + docs SMS 时序说明 |
| 开发者 / 维护者 | **推荐升级** — CLAUDE.md 3 新坑 + session retrospective 参考 |
| v1.4.75 Risk 2 真机 verify PASS 后 | v1.4.77 关 UNVERIFIED（暂不变）|
| v1.4.75 Risk 2 真机 verify FAIL | v1.4.77 切 Option B（暂不变）|

### 未变（Phase 2 defer v1.4.77+）

本版**不做**（等外部 v1.4.75 Risk 2 真机反馈）：
- BUG-009 Fix 9a Option A 真机 PASS/FAIL 触发的 v1.4.76 Phase 2 分支
  （分支 A: 关 UNVERIFIED + BUG-012 架构决策 + Phase 3 FundsOut / 分支 B:
  Option B device_code_sig cache）
- BUG-006 sub B/D 真机 verify（backend 层依赖）
- desktop source Tier 1（留 v1.5）

---

## [1.4.75] - 2026-04-23 🟡 BUG-009 Fix 9a Option A 真修 — cached dvs 跳 authority re-POST（探路版，Risk 2 UNVERIFIED）

**推荐升级**（所有用 SMS 首登的用户，尤其 moomoo 账号）。v1.4.74 C2 audit 发
现 v1.4.72 BUG-009 Fix 9a 是 WARN-only 非真修。本版实装 Option A 真修："探
路版" 模式（CLAUDE.md 坑 #34 + v1.4.52→53 纪律），3/4 风险代码级已确认安全，
Risk 2（req_device_code 是否触发新 SMS）待真机 verify。

### 🟡 Fixed (Tier A)

- **BUG-009 Fix 9a Option A 真修** (`commit 49c7b89ec`)：
  `crates/futu-backend/src/auth/mod.rs::authenticate_with_callback` 在 remember_login
  Err 分支**后**、password_auth **前**插入 Option A 分支：
  ```rust
  if let Some(cached_dvs) = fresh_cached_device_verify_sig(&cred) {
      return handle_device_verify(
          &http, &effective_config, cred.user_attribution,
          cred.user_attribution.auth_domain(), cred.uid,
          cached_dvs, &rand_key, verify_cb.as_deref(),
      ).await;
  }
  // else fall through to password_auth（v1.4.74 及以前行为）
  ```
  **纯 add new branch**，不删老路径。cached dvs 过期 / 不存在 → 自动回退
  password_auth 完整流程，零 regression 风险。

  **Agent 代码级审查确认 3/4 风险🟢**（essentials/2026-04-23-1810-v1.4.75-plan.md）：
  - Risk 1 🟢 backend 接受 cached dvs（C++ auth_impl.cpp:244/757/879 无"一次性"语义）
  - Risk 3 🟢 rand_key AES-256 32 字节可变长（unit test PASS）
  - Risk 4 🟢 moomoo empty device_sig 无关（handle_device_verify 不用）

### ⚠️ UNVERIFIED — Risk 2 待真机 verify

**Risk 2 🟡**：GET `/authority/req_device_code?dvs=cached_X&send_mode=0` 是否
触发新 SMS？

- 若 backend 有 "fresh dvs 5 min 内不重发" 语义 → Option A 真修完整
- 若无此语义，每次 req_device_code 都发新 SMS → Option A 无效，**v1.4.76
  切 Option B**（加 `device_code_sig` cache 层）

**真机 verify 方案**：
```bash
# 1. 首次登录触发 SMS，收到 "123456"
futu-opend --setup-only --login-account <phone> --login-pwd $FUTU_PWD

# 2. 5 分钟内重启（不输错，模拟网络问题 / Ctrl+C）
futu-opend --setup-only --login-account <phone> --login-pwd $FUTU_PWD \
  --verify-code 123456

# 期望（Option A 真修成功）：
# - daemon log 含 "v1.4.75 BUG-009 Fix 9a Option A: using cached device_verify_sig..."
# - **手机不应收到新 SMS**
# - 用户老 SMS 码 123456 被成功验证

# 若期望失败（Risk 2 FAIL）：
# - 手机仍收新 SMS  → v1.4.76 切 Option B
```

### Tests

- 3 新单测覆盖 Option A 决策逻辑：
  - `bug_009_option_a_precondition_and_state_compat`（cached dvs fresh + AES-256
    + moomoo empty device_sig compat）
  - `bug_009_option_a_expired_dvs_falls_through_to_password_auth`（6 min 前 dvs → fall-through）
  - `bug_009_option_a_missing_dvs_falls_through`（老 v1.4.71 cred 无 dvs → fall-through）
- 758 baseline → **761 passed**（+3 new Option A tests）

### 外部 reviewer re-verify 请求

1. **Risk 2 真机 verify**（P0-CRITICAL）— 按上述方案测 daemon restart 5 min 内
   是否不触发新 SMS
2. 若 PASS → 关 UNVERIFIED，v1.4.76 可聚焦其他 scope
3. 若 FAIL → v1.4.76 立即切 Option B + 继续保留 Option A 代码作 fallback（过期
   dvs 走原 password_auth，新鲜 dvs 走 Option B）

### 📊 数字

- Tests: 758 → **761 passed** (+3 new Option A tests)
- 1 feature commit + 1 release commit
- production LoC: ~45（插入新分支，无删除）

---

## [1.4.74] - 2026-04-23 🟡 外部 v1.4.71 报告剩余 4 bug 闭环 + BUG-009 Fix 9a audit（defer v1.4.75 真修）

**推荐升级**（MCP agent 用户 / REST API 用户 / moomoo 多币种账户）。外部
v1.4.71 AI tester 报告 15 bug，v1.4.72/73 已闭环 12，v1.4.74 再关 4 + audit 1：

### 🟡 Fixed (Tier A + C — 4 bug + BUG-004 Phase 2)

- **A1 BUG-011 MCP 缺 `futu_subscribe` tool**（命名对称性）—— MCP 有
  `futu_unsubscribe` / `futu_sub_acc_push` / `futu_unsub_acc_push` /
  `futu_query_subscription` / `futu_push_subscriber_info` 一套订阅管理工具，
  独缺 `futu_subscribe` 本身。API 对称性被打破（"能取消但不能订阅"）。
  v1.4.74 加 MCP `futu_subscribe` tool + scope Registry（CLAUDE.md 坑 #37
  4 处同步）。对齐 Python SDK `OpenQuoteContext.subscribe`。`commit 66b153f35`

- **A2 BUG-013 REST 补齐 7 缺失 endpoint** —— MCP 工具里有 7 个功能 REST
  没对应 endpoint。v1.4.74 补齐：
  - `/api/list-accounts` alias（= `/api/accounts`）
  - `/api/get-reference` alias（= `/api/reference`）
  - `/api/list-plates`（= `/api/plate-set`，对齐 MCP `futu_list_plates`）
  - `/api/ping` — Futu-specific health check + version
  - `/api/query-subscription` POST 版（比 GET `/api/sub-info` 多 `is_req_all_conn`）
  - `/api/unsub-acc-push` — REST 走 backend `TRD_SUB_ACC_PUSH` 反订阅
  - `/api/push-subscriber-info` — MCP-centric stub（返 placeholder 指向 SSE / ws）

  scope 都按对应 MCP tool 登记（qot-scope × 5 / acc-scope × 2）。`commit 0742d3e3e`

- **A3 BUG-003 SMS UX 2 层剩余修**（另 2 层 Layer 3/5 已 v1.4.72/73 修）
  - Layer 2 `error_code=15` hint 结构化输出：原 inline 长段 tracing::error!
    改为 stderr 带换行 5 因 bullet list + tracing log 保留引用。用户能
    **按优先级 [0]→[4] 逐条排查**（对应 lsof / 60s wait / App 重登 /
    --reset-device / 账号风控 5 类）
  - Layer 4 `--reset-device` 交互式二次确认 prompt：破坏性操作（删凭证 +
    device 文件）之前无二次确认。交互终端下加 `(y/N)` 确认；非交互
    （systemd / Docker / CI）保持旧行为 + WARN 说明。`commit 5f829eebe`

- **C1 BUG-004 Phase 2 MCP FundsOut 补 breakdown** —— v1.4.73 补了 7→25
  top-level 字段，本版补 2 个 array 字段：
  - `cash_info_list: Vec<CashInfoOut>`（per-currency cash / available /
    net_cash_power，多币种账户用）
  - `market_info_list: Vec<MarketInfoOut>`（per-market assets breakdown，
    综合账户 / 跨市场用）

  对应 `futu_trd::types::Funds` 加 2 个新 Vec 字段（`FundsCashInfo` /
  `FundsMarketInfo`）。MCP JSON `skip_serializing_if = "Vec::is_empty"`
  让无多币种账户保持简洁。`commit b80de9649`

### 🟢 Audit-only (C2 — defer 真修)

- **C2 BUG-003 Layer 3 audit: BUG-009 Fix 9a 是 WARN-only 非真修** ——
  v1.4.72 Fix 9a 声称 "cache dvs 5min TTL 避免 daemon 启动重 POST /authority/
  触发新 SMS"，但代码审查确认**只 WARN 不跳过 authority re-POST**。daemon
  重启仍走 password_auth → 新 POST /authority/ → backend 返新 dvs → 老 SMS
  被新 dvs 覆盖失效（符合外部报告原症状）。
  - v1.4.74 不改 code，写 audit report（`essentials/2026-04-23-1739-v1.4.74-c2-bug-009-fix-9a-audit.md`）
  - v1.4.75 scope 真修：cached dvs fresh 时跳过 authority re-POST，直接
    `handle_device_verify(..., cached_dvs, ...)`（Option A）
  - 真修需真机 verify 4 个风险点（backend 是否真接受 cached dvs / rand_key
    AES-128 vs 256 / moomoo empty device_sig 场景 / req_device_code 是否
    触发新 SMS），对齐 CLAUDE.md 坑 #34 "agent 调研 ≠ 真机正确性"纪律
  - `commit 5d117f6ad`

### 📊 数字

- Tests: 758 baseline → **~770 passed** (+12 new)
- 5 feature commits + 1 release commit
- production LoC: ~400
- test LoC: ~150

### 外部 reviewer 剩余 scope

外部 v1.4.71 报告 15 bug 本版后剩 **2 bug** 未 addressed：
- BUG-006 sub B (update_timestamp tick) + sub D (US push stream) — 依赖
  backend 是否真发 overnight SBIT 13 tick，等外部真机反馈
- BUG-007 sim 空 err_msg — reviewer 重现不出，需 commit diff v1.4.69→71
- BUG-012 `/api/sub-info` 返空 — 需 per-connection vs cross-connection
  架构决策（by-design? 留专版）
- **BUG-009 Fix 9a 真修** — v1.4.75 scope（见 C2 audit）

### 外部 reviewer re-verify 请求（真机）

1. **BUG-011**：MCP agent 调 `futu_subscribe` 成功订阅
2. **BUG-013**：所有 7 endpoint 非 404（含 alias 和 stub）
3. **BUG-003 Layer 4**：交互式 `--reset-device` 看到 `(y/N)` prompt
4. **BUG-003 Layer 2**：触发 ret_type=15 场景，stderr 看到 5 因结构化 bullet list
5. **BUG-004 Phase 2**：多币种账户（US + JPY）查 `futu_get_funds`，看到
   `cash_info_list` + `market_info_list` 非空
6. **BUG-009 Fix 9a 真修 re-verify**（v1.4.75 发版后做，见 C2 audit）

---

## [1.4.73] - 2026-04-23 🔴 外部 v1.4.71 报告 3 S + 3 P0 + 3 P0 bundle 全修（含 5 版 S 债终结）

**推荐升级**（HK/US 交易者 / moomoo 所有账号 / 做 /api/orders 风控的客户端）。
外部 v1.4.71 AI tester 互验报告（双 tester 独立测试 + 3 轮互验，7 firm 全覆盖）
发现 15 个 bug（3 S + 9 P0 + 3 P1），其中 3 个 S 级全是 v1.4.72 未修的关键
bug，包括**连续 5 版未修的历史最长 S 债**。

### 🔴 Fixed (Tier A — 3 S 级)

- **BUG-60b0-002 orders cache 不刷新**（**v1.4.67→71 连续 5 版未修**）—
  下单成功 → 立即 `/api/orders` 返 count=0（查不到刚下的单）。所有风控 /
  对账 / 持仓变化监听客户端白瞎。根因 2 层：
  1. `push_parser.rs:679` notice_type=8/10 (TRADE_STATISTIC /
     ACCOUNT_UPDATE) 进 `_ => debug!` 被静默吞，push 不驱动 cache refresh
  2. PlaceOrder 成功后 daemon 不写 cache（race condition：push 到达前用户
     查 `/api/orders` 返旧 cache）
  修法：(1) notice_type=8 → ORDER_LIST_UPDATE(5) refresh、=10 → ASSET_UPDATE(11)
  (2) PlaceOrder success 立刻 spawn 后台 `query_orders` 刷 cache（对比
  v1.4.48 #6 `modify_order.rs:407` 修法模板）。`commit 223e4589b`

- **BUG-008 unlock idempotency × cipher state 脱节真修** — v1.4.72 Option C
  （空 body 不写 cache）只防 step 3 污染，未修 step 4 stale：
  ```
  Step 1: unlock pwd     → cache EXECUTED
  Step 3: EMPTY {} LOCK  → cipher 清（但 step 1 的 cache entry 还在）
  Step 4: 同 body        → cache HIT 返 stale "cached" 成功 ← 真 bug
  Step 5: place-order    → -401 "交易未解锁"
  ```
  修法（**Option A cipher_state_version**，低风险优于 Option B cache prefix
  invalidate API 扩展）：
  - `TrdCache` 新字段 `cipher_state_versions: DashMap<acc_id, AtomicU64>`
  - unlock `idem_key` hash 构造纳入**每个相关 acc_id 的 cipher_state_version**
  - lock 清 cipher 时 `bump_cipher_state_version` 递增
  - step 3 之后 version=1 ≠ step 1 的 version=0 → idem_key 不同 → cache
    miss → 真执行 unlock 而非返 stale。`commit 209a6c775`

- **BUG-010 moomoo `device_sig_new` 缺失 credentials 不存盘** — 所有
  moomoo attribution 账号（US + SG + CA + MY 实锤，可能扩到 JP/AU）登录后
  `/authority/` response 缺 `device_sig_new`，v1.4.42 起强制
  `!device_sig.is_empty() && !tgtgt.is_empty()` → 永不存盘 → daemon 重启
  必 re-auth → 多次 SMS 失败触发账户级限流。
  修法：对齐 C++ `auth_impl.cpp:3257-3260` —— `device_sig_new` 是
  **optional** 字段（`if (!device_sig_new.empty()) { account->device_sig_ = ...; }`
  缺失跳过赋值，其他凭证照存）。Rust 改为只要 `tgtgt_new` 非空就存，`device_sig`
  可空字符串。修法遵循 CLAUDE.md 核心原则"与 C++ 零细节差异"。`commit 459cbf20b`

### 🟡 Fixed (Tier B — 3 P0)

- **D5 market state priority** — v1.4.71 D5 把 `market_hk_future=0` 改 15
  但 SG future 应返 18 `FUTURE_DAY_WAIT_OPEN` 却也返 15。同一 market_id 范围
  内 backend 下发多条 non-zero status 时，v1.4.71 "first non-zero" 返 open 类
  状态，误判"等待开盘"为"已开盘"。修法：`pick_market_state` 升级为
  priority-based selection — Restrictive 类（WAIT_OPEN/BREAK/CLOSE/PRE/AFTER
  等）priority 2 > Open 类（OPEN/MORNING/AFTERNOON/NIGHT_OPEN）priority 1 >
  0。SG future 多市场混合时优先返 18 更精确描述市场实际情况。`commit 5bc89ab63`

- **BUG-014 Platform mismatch 错误信息加 hint** — moomoo 账号 +
  `--platform futunn` 返 `ret_type=2 "账号密码不匹配"`（误导用户以为密码错）。
  现有 attribution-based auto-switch 只在 salt 成功时触发，salt 失败时无此路径。
  修法：salt fail 路径在标准 domain + error_code=2/15 时加 hint "若账号本属于
  {moomoo,futunn}/... 请改用 `--platform {反向}` 重试"。不改现有 auto-switch
  逻辑。`commit 8efa969ec`

- **BUG-015 `--log-level` silent accept** — `futu-opend --log-level wtf` 不
  报错 exit=0 但吞所有 log（EnvFilter::new 对非法值返 "deny-all" filter）。
  类似 BUG-001 `--tz` pattern（v1.4.71 已 drop）。修法：clap `ValueEnum`
  约束有效值 `trace / debug / info / warn / error / off`（对齐 v1.4.40
  `LoginRegion` 做法）。XML/TOML config file 非法值手动 validate + fallback
  到 info + ERROR log。`commit 0587c8156`

### 🟢 Fixed (Tier C — 3 P0 bundle)

- **BUG-002 MCP 加 `futu_get_flow_summary` alias** — 外部报告找 `futu_get_flow_summary`
  搜不到（MCP 实际 tool 是 `futu_get_acc_cash_flow`，v1.4.30 P2 实装）。
  UX 对称问题（REST 侧两个 endpoint 共存：`/api/flow-summary` + `/api/acc-cash-flow`）。
  修法：加 MCP alias tool 语义等同。CLAUDE.md 坑 #37 4 处同步（tools.rs
  handler + guard.rs scope + known_tools + test）。`commit 650d9d3e5`

- **BUG-004 MCP FundsOut 补 18 字段（7→25）** — 之前 MCP 只 7 字段（power/
  total_assets/cash/market_val/frozen_cash/debt_cash/avl_withdrawal_cash），
  缺 `currency` + PDT + margin + 风控指标共 26 字段。MCP 客户端做多币种 /
  风控监测完全不可用。修法：`futu_trd::types::Funds` 从 7 → 30 字段（18 新
  字段全 `Option<T>` 追加到尾部保持二进制兼容）；MCP `FundsOut` 同步扩展。
  `#[serde(skip_serializing_if = "Option::is_none")]` 让缺字段不出现保持
  JSON 简洁。`commit d8588c418`

  补的字段包括：currency / available_funds / unrealized_pl / realized_pl /
  risk_level / risk_status / initial_margin / maintenance_margin /
  margin_call_margin / max_power_short / net_cash_power / long_mv / short_mv /
  pending_asset / max_withdrawal / is_pdt / pdt_seq / remaining_dtbp /
  dt_call_amount / dt_status / securities_assets / fund_assets / bond_assets。

- **BUG-005 REST `/api/history-kline` flat body auto-wrap** — 用户习惯 Python
  SDK flat body `{"symbol":"HK.00700","kl_type":"day","max_count":5}`，但 proto
  Request struct 要求 `{c2s: {security: {market,code}, kl_type, ...}}` 嵌套。
  之前报 `"invalid kl_type"` 误导错。修法：`adapter.rs` 加两个新 helper：
  1. `maybe_wrap_flat_body_as_c2s`：top-level 无 `c2s` key + 有业务字段 →
     整个 body 包装进 `{c2s: body}`
  2. `expand_symbol_shorthand`：`c2s.symbol: "HK.00700"` → `c2s.security:
     {market:1, code:"00700"}`（支持 11 个 market prefix）

  pipeline 新增顺序：normalize (v1.4.45) → alias (v1.4.68) → **wrap (v1.4.73)**
  → **expand (v1.4.73)** → serde 反序列化。`commit 93735b391`

### 📊 数字

- Tests: 748 baseline → **758 passed** (+10 new)
- 9 feature commits + 1 release commit
- production LoC: ~400
- test LoC: ~300
- 3 S 全修 + 3 P0 + 3 P0 bundle = 9 bug 闭环

### 对用户的影响

| 类型 | 操作 |
|---|---|
| 做 `/api/orders` 风控 / 对账 | **强烈建议升级** — 5 版 S 债终结，下单后立即能查到 |
| 使用 moomoo 账号（US/SG/AU/JP/CA/MY） | **强烈建议升级** — credentials 不再永不存盘 |
| 使用 `/api/unlock-trade` | **强烈建议升级** — 真修 cipher × idem 脱节 |
| SG 期货账户 | **推荐升级** — WAIT_OPEN 状态不再被误判为 OPEN |
| MCP agent 多币种管理 / 风控 | **推荐升级** — FundsOut 补 18 字段 |
| REST 用 flat body 习惯 | **推荐升级** — history-kline 不再报误导错 |
| 其他用户 | 安全升级（零 breaking，所有改动向后兼容） |

### 🧭 纪律沉淀

本版实践 `essentials/2026-04-23-1530-v1.4.72-vs-external-v1.4.71-delta-takeaways.md`
提出的 3 条候选坑：

- **坑候选 A**（fix report "闭环" 声明前必须跑报告的完整 repro）— 本版 A2
  BUG-008 单测覆盖 5 步 repro 的 version 序列，不再声称无 repro 的闭环
- **坑候选 B**（某 S bug 连续 ≥ 3 版未修 = 强制 next-ship 必做）— 本版
  BUG-60b0-002 五版未修，按此纪律 v1.4.73 无条件做 Tier A
- **坑候选 C**（AI tester 互验报告比单 tester 高质量）— 本版结构化参考
  claude-29cd + claude-4c6c 互验模式，未来 v1.4.74+ 将正式实践

### 外部 reviewer re-verify 请求（真机）

1. **BUG-60b0-002**：下单后立即 `/api/orders` 应查到（原 5 步场景）
2. **BUG-008**：跑报告的 5 步 repro（unlock → 同 body HIT → empty LOCK →
   同 body 应 cache MISS 而非 stale HIT → place-order 成功）
3. **BUG-010**：moomoo 账号 5 min 内 daemon restart 不触发新 SMS
4. **BUG-D5**：SG future 开盘前 15 min `/api/global-state.market_sg_future` 返 18
5. **BUG-014**：moomoo 账号 + `--platform futunn` 看 daemon log 含 hint
6. **BUG-015**：`--log-level wtf` exit=2 + 清晰错误
7. **BUG-002**：MCP agent 调 `futu_get_flow_summary` 应成功返数据
8. **BUG-004**：MCP `futu_get_funds` 响应含 `currency` 等 20+ 字段
9. **BUG-005**：`curl /api/history-kline -d '{"symbol":"HK.00700","kl_type":2}'` 正常

---

## [1.4.72] - 2026-04-23 🔴 外部 v1.4.69 3 P1 bugs 闭环（SMS race / unlock cipher / US overnight）+ 🟡 Phase 4 24 integration tests

**紧急级别**：**🔴 P1 推荐升级**（HK/US traders）。本版关闭外部 v1.4.69 验收报告
剩余 3 P1 bug，完成 gateway integration test 基础设施（Phase 2-4 共 61 tests）。

### 🔴 Fixed (P1)

- **BUG-008 unlock-trade 空 body 默认 LOCK + cache stale 生产陷阱**：用户误发
  `/api/unlock-trade` 空 body → proto `is_unlock` 默认 false (LOCK) + 90s
  idempotency cache 写入，90s 内第二次空 body 返 cached LOCK 结果遮蔽 cipher
  状态真实变化。**修法**：`unlock.rs::idem_key` 构造检测"完全空 body"（is_unlock
  =false + pwd_md5 空 + otp 空 + security_firm 缺 + acc_ids 空）→ args-hash
  返 None 不写 cache。LOCK 仍执行但每次都 fresh（log 明确显示状态变化）。显式
  `Idempotency-Key` header 不走本 defense（caller 明确意图）。

- **BUG-009 SMS 重试竞态**：daemon 启动 re-POST `/authority/` 触发新 SMS +
  失效旧码，用户输旧码 → code=21 → 累计失败触发 cause #4 账户锁。**修法**
  分 2 sub-fix：
  - **Fix 9a**: `SavedCredentials` 加 `device_verify_sig: Option<String>` +
    `device_verify_sig_ts: Option<u64>` + `DEVICE_VERIFY_SIG_TTL_SECS = 5 * 60`
    const。`remember_login` code=20 分支抽到 dvs 后 `persist_device_verify_sig`
    写 credentials 文件。下次 daemon 启动时 `authenticate_with_callback` 入口
    `fresh_cached_device_verify_sig` 检测 <5min fresh → WARN 提示用户
    "recent SMS detected, use `--verify-code <sms>` to avoid triggering new SMS"。
  - **Fix 9b**: setup-only + TTY + `--verify-code` 失败 (code=21) 时
    **不立即 exit**，打印清晰 guidance (30s 限流等待 / 用最新 SMS / 重跑带新
    码) + `stdin.read_line` 等用户 Enter。非交互 daemon (systemd) 保持旧行为。

- **BUG-006 美股夜盘 overnight 支持 4 层缺陷**：snapshot.update_time 空 /
  push stream 断 / MCP schema 缺 overnight / cache 缺 overnight 字段。**修法**
  4 层全修：
  - **L1** `snapshot.rs:640` `update_time: String::new()` → 用 `sd.timestamp`
    + `timestamp_to_datetime_str(ts, market)` 按 market tz 渲染（对齐 C++
    `GetTimeZoneByAPIQotMkt`）。US snapshot 现在返 EDT 格式日期，不再空。
  - **L2** push_parser 加 `parse_us_pre_after_detail` 处理 SBIT 13
    (`SBIT_US_PREMARKET_AFTERHOURS_DETAIL`) → decode `UsPreMarketAfterHoursDetail`
    proto → overnight 字段 + 定点缩放 (price/10^9 / rate/10^5 / turnover/10^3)
    → upsert 到 `CachedBasicQot.overnight`。下次 BasicQot push 带 overnight
    字段（从 cache 用新 `cached_overnight_to_proto` helper 转为 proto
    `Qot_Common::PreAfterMarketData`）。
  - **L3** `CachedBasicQot` 加 `overnight: Option<CachedPreAfterMarketData>`
    字段 + 新 `CachedPreAfterMarketData` struct 镜像 proto 字段。
  - **L4** MCP `futu_get_snapshot` 输出加 `overnight: Option<OvernightOut>`
    sub-struct（`#[serde(skip_serializing_if = "Option::is_none")]`，non-US /
    regular hours 不污染输出），LLM agent 能看到 US 夜盘 OHLCV。

### 🟡 Infrastructure: Phase 4 Gateway integration tests (24 tests, +cumulative 61)

继续 v1.4.71 Phase 2+3（37 tests）的基础设施扩展。完整 gateway handler
integration test 覆盖：

- **`integration_trade_query.rs` (9 tests)** — 3 handlers × 3 scenarios:
  - GetMarginRatio (CMD 2309) / GetOrderFee (CMD 2273) / FlowSummary (CMD 20963)
  - 每个：happy + backend error + acc_id=0 reject (v1.4.51 BUG-7+8 defense)

- **`integration_qot.rs` (15 tests)** — 5 handlers × 3 scenarios:
  - Subscribe (FTAPI 3001): qot_market happy / TrdMarket auto-map (v1.4.68 Tier B) / invalid market=99 error
  - GetSecuritySnapshot (FTAPI 3203): no-backend / empty list / invalid market
  - RequestHistoryKL (FTAPI 3103): no-backend / no-date (v1.4.68 Tier C) / req_count (v1.4.68 Tier C)
  - GetOptionChain (FTAPI 3209): no-backend / HK smoke / invalid market
  - GetCapitalFlow (FTAPI 3211): no-backend / US tz (v1.4.68 Tier A) / HK tz

**累计 Phase 2-4 基础设施** = 61 integration tests（Phase 2 trade write 19 +
Phase 3 trade read 18 + Phase 4 query+qot 24）+ 6 canary = 67 tests，覆盖所有
top-20 handlers。

### 📝 Docs / 澄清

- **BUG-002 `/api/flow-summary` MCP tool** — 外部 v1.4.69 验收报告列为 P2，审查后
  确认 **MCP tool `futu_get_acc_cash_flow` 自 v1.4.30 已存在** (`tools.rs:2641`
  + `guard.rs:79` scope 已登记)。外部报告可能用了老 daemon 或查错 tool 名。
  **无需改动**，CHANGELOG 说明。

### ✅ Tests

- v1.4.71 baseline: 706 tests
- v1.4.72 final: **~748 tests** (+42)
  - +6 BUG-008/BUG-009 unit + integration tests
  - +24 Phase 4 integration tests
  - Zero regression
- clippy `-D warnings`: clean
- fmt: clean

### 真机 verify 请求

**BUG-008**:
```bash
curl -X POST http://127.0.0.1:22222/api/unlock-trade -d '{}'
curl -X POST http://127.0.0.1:22222/api/unlock-trade -d '{}'
# daemon log: "v1.4.72 BUG-008: unlock-trade 空 body... 不写 idempotency cache"
```

**BUG-009**:
```bash
cat ~/.futu-opend-rs/credentials-*.json | jq '.device_verify_sig,.device_verify_sig_ts'
# Expected (5min 内触发过 SMS): both have values

# --verify-code 输错保持前台 wait
futu-opend --setup-only --login-account X --login-pwd Y --verify-code 000000
# Expected: "按 Enter 退出" 前台 wait，不立即 exit
```

**BUG-006**:
```bash
curl -X POST http://127.0.0.1:22222/api/snapshot \
  -d '{"c2s":{"securityList":[{"market":11,"code":"AAPL"}]}}' \
  | jq '.s2c.snapshotList[0].basic.updateTime'
# Expected: "2026-04-22 23:17:56" EDT (不空)

# MCP futu_get_snapshot US.AAPL
# Expected JSON: "overnight": { "price": X, "high": Y, "volume": Z, ... }（US 夜盘时段）
```

### Critical files

- `crates/futu-gateway/src/handlers/trd/unlock.rs` — A1 BUG-008 idem fingerprint
- `crates/futu-backend/src/auth/device.rs` — A2a SavedCredentials + dvs helpers
- `crates/futu-backend/src/auth/mod.rs` — A2a WARN + persist_dvs call
- `crates/futu-opend/src/main.rs` — A2b --verify-code code=21 wait
- `crates/futu-cache/src/qot_cache.rs` — A3 L3 CachedBasicQot.overnight
- `crates/futu-gateway/src/bridge/push_parser.rs` — A3 L2 SBIT 13 parser
- `crates/futu-gateway/src/handlers/qot/snapshot.rs` — A3 L1 update_time
- `crates/futu-mcp/src/handlers/core.rs` — A3 L4 SnapshotOut overnight
- `crates/futu-gateway/tests/integration_trade_query.rs` — Phase 4 trade query
- `crates/futu-gateway/tests/integration_qot.rs` — Phase 4 qot

## [1.4.71] - 2026-04-23 🔴 D5 HK futures state + order_status 对齐 C++ + rustls 安全 + 🟡 37 integration tests

**紧急级别**：**🔴 P1 推荐升级**。本版含多个真 bug fix（外部 v1.4.69 验收报告的 D5
HK futures state + 5 年前 order_status mapping 错位 + 时区查询默认范围偏
8h）、安全 upgrade（rustls-webpki RUSTSEC-2026-0104）+ 37 integration tests
基础设施（未来所有 gateway 改动都跑这些 tests 护航）。

### 🔴 Fixed (P1)

- **`/api/global-state` `market_hk_future=0` bug**（外部 v1.4.69 验收报告，根因代码
  级定位）：`futu-backend::stock_list::pick_market_state` 之前 `.find()` 取第
  一个 market_id 匹配，对 HKFuture 同时匹配 `FUT_HK=5`（老港期，deprecated
  status 常 0）+ `FUT_HK_NEW=6`（主要港期，open 时 status=15）。如果 backend
  返的顺序是 `[id=5 status=0, id=6 status=15]`，结果被 id=5 的 0 遮蔽。
  **修法**：优先返 non-zero status 的匹配，全 zero 才 fallback 第一个。4-firm
  场景（MoomooUS/FutuHK/FutuSG/MoomooCA）+ 单 market_id 场景（HK/US/SH/SZ）
  都覆盖。5 个 regression tests。

- **`order_status` mapping 自 v0.5.0 起错位**（Phase 3 integration test 发现，
  spawned audit session 定位，对照 C++ `Trd_OrderStatusConv_S2C` 11 条真值表
  交叉验证）：`futu-backend::trade_query::map_backend_order_status` + mirror
  `futu-gateway::handlers::trd::backend_order_status_to_ftapi` 都是 v0.5.0
  臆造的 0..15 线性 mapping，**6 个状态值错位** + 臆造 FTAPI 输出值
  25/26/28-31（枚举里根本不存在）：

  | Backend 含义 | 值 | 应→FTAPI | 之前 Rust 返 |
  |---|---|---|---|
  | PENDING_NEW | 1 | **2** Submitting | 1 Unsubmitted ❌ |
  | PARTIAL_FILL_CANCELLED | 7 | **14** CancelledPart | 22 Disabled ❌ |
  | DISABLE | 101 | **22** Disabled | 101 透传 ❌ |
  | WAITING_NEW | 102 | **1** WaitingSubmit | 102 透传 ❌ |
  | FILL_CANCELLED | 103 | **24** FillCancelled | 103 透传 ❌ |
  | DELETE | 104 | **23** Deleted | 104 透传 ❌ |

  **碰巧对齐的 5 条**：FILL=4→11 / CANCELLED=5→15 / REJECTED=6→21 / NEW=2→5
  / PARTIAL_FILL=3→10（数字重合非设计）。大多数订单最终态正确上报掩盖了其他
  错位 5 年。v1.4.71 修：统一到 `futu-backend::trade_query::backend_order_status_to_ftapi`
  pub 函数，gateway 镜像删除改 `pub use` 引入。4 unit tests（11 rules 覆盖 +
  dead branches 检测 + 错位 6 项反归 + 碰巧对的 5 条回归）。

- **`default_history_time_range` `+28800s` 偏移 bug**（v1.4.71 时区 audit 发
  现的真 bug）：之前 `now_utc_secs + 8 * 3600` 当 micros → backend 收到比真实
  now **晚 8h** 的绝对时刻。所有账户查 "最近 90 天" 默认范围都偏 8h。**修法**：
  直接用 `SystemTime::now()` UTC 绝对时刻（epoch 与 tz 无关）。

- **`ftapi_time_str_to_micros_hkt` per-market 对齐 C++**（用户要求 "查哪个市场
  用哪个市场的时区"）：之前无条件按 HKT 解析用户传的 `begin_time`/`end_time`
  字符串，US 账户传 `"2026-04-21 00:00:00"` 本意 EDT → filter 偏 12-13h。
  **修法**：加 `trd_market: i32` 参数，用新 `futu_core::market::trd_market_to_tz`
  dispatch（对齐 C++ `APITimeStrToTimeStamp_Trd`）。涉及 `default_history_time_range`
  / `parse_option_dte` / `check_futures_code_expiry` 4 个 helper 全 per-market。

- **v1.4.70 external tester Bug #1 补漏修**（Phase 3 integration test 发现）：
  `query.rs::GetOrderFillListHandler` 里也有 OrderFill status 枚举错位 1/2/3，
  和 v1.4.70 修的 `mod.rs::backend_orderfill_to_ftapi` 是同一 bug 的**第二
  处实例**。v1.4.70 扫漏，Phase 3 真机 RPC 路径测试暴露后立即修。对齐 C++
  `NN_DealStatus` 0/1/2。

### 🔒 Security

- **rustls-webpki 0.103.12 → 0.103.13**（RUSTSEC-2026-0104）：v1.4.70 Security
  Audit workflow 首次报红，transitive dep（通过 rustls → axum-server → futu-mcp）。
  `cargo update -p rustls-webpki` 干净升级，0 cascade。

### 🟡 Infrastructure (Phase 2 + Phase 3 gateway integration tests)

- **D1 mock backend infrastructure** (v1.4.70 遗产 commit `bf8fbab6b`)：
  `crates/futu-gateway/tests/common/mock_backend.rs` 基于 `tokio::io::duplex`
  fake TCP pipe + `session_key=None` bypass 加密。`BackendConn::from_duplex`
  test-only constructor。6 canary tests。

- **Phase 2: 19 trade write integration tests**（`integration_trade_write.rs`）：
  PlaceOrder / ModifyOrder / CancelOrder / GetMaxTrdQtys / UnlockTrade /
  ReconfirmOrder × Happy / Error / Idempotency = 18 + 1 per-broker smoke。覆
  盖 sim 账户 (Platform mock) 和 real 账户 (per-broker mock) 两条路径。

- **Phase 3: 18 trade read integration tests**（`integration_trade_read.rs`）：
  GetFunds / GetPositionList / GetOrderList (cache-read) + GetOrderFillList /
  GetHistoryOrderList / GetHistoryOrderFillList (backend-RPC) × 3 scenarios。

### 🟢 Hardcode cleanup (non-tz)

- `TGTGT_VALIDITY_SECS = 30 * 24 * 3600` @ `auth/mod.rs` — 2 处 `30*24*3600`
  合并
- `BackendConn::CLIENT_VER_FTGTW: u16 = 1002` — 2 处 `1002` 合并
- `RECONFIRM_SERIAL_INIT = 20_000_000` @ `futu-trd/misc.rs` — magic number 命名
- `SIM_TRD_CMD_OFFSET = 10000` + `CMD_SIM_QUERY_FUND = CMD_QUERY_FUND + OFFSET`
  @ `futu-backend/trade_query.rs` — 显式表达 + 避免 14704/14705 魔法数散落
- `push_parser` 4 个 scaler consts（`VALUE_PRECISION_DIV` / `WAN_SCALER` /
  `QIAN_SCALER` / `CN_LOT_SCALER`）— 替代散落的 `10000.0 / 1000.0 / 100.0`
  数量级魔法数

### 🔄 Refactor

- 新 source of truth `futu_core::market::trd_market_to_tz(trd_market)` —
  跨 crate 共享 per-market tz dispatch（对齐 C++ `GetTimeZoneByTrdMkt`）
- `futucli` 删除 `--tz` 占位 flag（v1.4.69 加的，与 C++ 不对齐 + per-market
  auto-dispatch 足够，无需用户手工 override）

### ✅ Tests

- v1.4.70 baseline: 645 tests
- v1.4.71 final: **706 tests** (+61)
  - +15 per-market tz tests (`futu-core::market` + `futu-gateway::trd`)
  - +19 Phase 2 trade write integration tests
  - +18 Phase 3 trade read integration tests
  - +5 D5 `pick_market_state` regression tests
  - +4 order_status_mapping unit tests
- `cargo clippy --workspace --all-targets -- -D warnings`: clean
- `cargo fmt --check`: clean

### 真机 verify 请求

**对外部 v1.4.69 验收报告的 P1 回归验证（4-firm 全覆盖）**：
```bash
for p in 22223 22224 22225 22228; do
  echo "=== port $p ==="
  curl -s http://127.0.0.1:$p/api/global-state \
    | jq '.s2c | {market_hk_future, market_us, market_sh, market_sz}'
done
# Expected (HK 期货 open 时段): market_hk_future != 0（如 15 = FUTURE_DAY_OPEN）
# 其他 markets 应与之前相同不 regress
```

**order_status 验证**：查历史订单，之前若看到 `order_status` 是 `101/102/103/
104/22 但并非 Disabled/26/28/30/31` 等异常值，升级后应该对齐 FTAPI 枚举
`OrderStatus` 定义（WaitingSubmit=1 / Submitting=2 / Submitted=5 / FilledAll=11
/ CancelledPart=14 / CancelledAll=15 / Failed=21 / Disabled=22 / Deleted=23 /
FillCancelled=24）。

### Critical files

- `crates/futu-backend/src/stock_list.rs` — `pick_market_state` D5 fix
- `crates/futu-backend/src/trade_query.rs` — `backend_order_status_to_ftapi`
  pub + 11 规则 + 4 unit tests
- `crates/futu-gateway/src/handlers/trd/mod.rs` — 删 order_status mirror +
  `ftapi_time_str_to_micros` per-market + hardcode cleanup
- `crates/futu-gateway/src/handlers/trd/history.rs` — `default_history_time_range`
  去 `+28800s` bug + per-market 接参
- `crates/futu-gateway/src/handlers/trd/query.rs` — external tester bug #1 补漏修
  （`GetOrderFillListHandler` status 对齐 0/1/2）
- `crates/futu-gateway/src/handlers/trd/security_type.rs` — `parse_option_dte`
  + `check_futures_code_expiry` per-market
- `crates/futu-core/src/market.rs` — 新 `trd_market_to_tz` + 4 tests
- `crates/futu-gateway/tests/` — `integration_trade_write.rs` + `integration_trade_read.rs`
  + `common/trade_helpers.rs`
- `essentials/2026-04-23-1245-v1.4.71-order-status-mapping-audit.md` —
  order_status audit 完整归档

## [1.4.70] - 2026-04-23 🔴 credentials regression hotfix + history-order-fills status 对齐 C++

**紧急级别**：**P1 推荐升级** —— v1.4.68 引入的 credentials 强校验导致升级用户
在某些场景被强制重新 SMS，累积触发 Futu 后端 IP 限流 "系统繁忙"。外部报告指出
`/api/history-order-fills` 的 `status` 字段自 v1.0 起就错位一位（正常成交被
识别为 Cancelled），本版一起修。

### 🔴 Fixed (P1)

- **credentials 文件兼容 v1.4.66 及之前**（`crates/futu-backend/src/auth/device.rs`）：
  v1.4.68 Bug #1 (安全 P0) 加了 `cred.account != account` 强校验防 cross-account
  污染，但误杀**两类合法场景**：
  1. **Legacy v1.4.66 文件**：没 `account` 字段 (serde default 空字符串) → 被
     误判 "poisoned" 删文件 → 用户升级后**强制 SMS**
  2. **手机号格式变体**：同账号 `+86-13xxx` / `13xxx` 两种写法 md5 哈希相同
     （共享文件），但 `cred.account` 字符串不同 → 被误判 mismatch → **强制 SMS**

  两类误杀频繁触发 SMS 导致**Futu 后端 IP 限流**（外部反馈：大量"系统繁忙"）。

  **修法**：
  - Legacy 文件检测（`cred.account.is_empty()`）→ **静默升级** populate +
    写回，不删文件
  - 非空 `cred.account` 比较用 `normalize_phone_account()` 归一化后比较

  **安全防线保留**：normalize 后真不等仍删文件走 SMS（Bug #1 cross-account
  污染防御不变）。

- **`/api/history-order-fills` `status` 字段错位**（外部同事反馈；
  `crates/futu-gateway/src/handlers/trd/mod.rs::backend_orderfill_to_ftapi`）：
  Rust 历史版本 status 映射为 1/2/3，而 C++ 和 FTAPI `OrderFillStatus` enum
  定义为 0/1/2：
  | C++ NN_DealStatus | FTAPI OrderFillStatus | 值 |
  |---|---|---|
  | OK | OK | **0** |
  | Cancelled | Cancelled | **1** |
  | Changed | Changed | **2** |

  错位后所有**正常成交被识别为 `1 = Cancelled`**。调用方无法依赖 `status`
  过滤有效成交，必须交叉查 `history-orders` 的 `order_status` 验证。

  **修法**：默认返 `Some(0)` (OK)，cancelled → `Some(1)`，corrected → `Some(2)`。
  对齐 C++ `NNProto_Trd_Deal.cpp:70-91` + `_APIServer_Trd_Comm.cpp:1962`
  `apiOrderFill.set_status(nnOrderFill.enDealStatus)` 直接透传。

### 📝 Docs / 说明（非 bug，by-design 对齐 C++）

- **`create_time` 时区按 market 本地**（外部同事 v1.4.68 测试发现）：
  v1.4.67+ 对 HK fill 用 HKT (UTC+8)，对 US fill 用 EDT/EST (UTC-4/-5)，这是
  **对齐 C++ OpenD** 的设计（`TimeStampToAPITimeStr_Trd` → `GetTimeZoneByTrdMkt`
  per-market local time）。

  用户 workaround：优先用 `create_timestamp` (Unix UTC float) 做时序比较；用
  `create_time` 字符串时按 `trd_market` 自行解析对应 tz。

  文档补充：`docs-site/docs/guide/trading.md` 加"时区注意事项"小节说明
  per-market 行为 + Python workaround 代码片段。

### ✅ Added Tests (5 新增)

- `load_credentials_silent_upgrades_legacy_file` — 替代原
  `load_credentials_rejects_legacy_file_missing_account_field`，assert legacy
  文件被静默升级 + account 字段写回
- `load_credentials_accepts_phone_format_variants` — 替代原
  `load_credentials_rejects_phone_format_variant_mismatch`，assert 同账号
  `+86-xxx` / `xxx` 两种写法互通
- `backend_orderfill_to_ftapi_status_ok_for_normal_fill`（status=0）
- `backend_orderfill_to_ftapi_status_cancelled`（status=1）
- `backend_orderfill_to_ftapi_status_changed`（status=2）
- `backend_orderfill_to_ftapi_status_default_none_optionals`（backend 未下发
  is_cancelled / is_corrected → 默认 0=OK）

保留 `load_credentials_rejects_cross_account_file` 作 Bug #1 真防线 regression。

### 🧭 版本策略

原计划 v1.4.70 做 Gateway integration tests + CLI --tz wire daemon（60
integration tests ~3400 LoC）。因外部用户被锁需要立即 hotfix，v1.4.70 pivot
为本 hotfix 版；Gateway tests 工作保留在 `feat/v1.4.71-gateway-tests` 分支
（已有 D1 mock backend infra + 6 canary tests commit），续做版本号变更为
v1.4.71。

### 真机 verify 请求

外部反馈用户请在升级后 verify：

1. **credentials 兼容**：已登录过 v1.4.66 的账户，升级 v1.4.70 后启动 daemon
   **不应该**触发 SMS（走 credentials 快速通道）
2. **`status` 字段**：查任一日期 `/api/history-order-fills`，所有正常成交的
   `status` 现在是 `0` 而非 `1`
3. **时区 `create_time`**：per-market tz（US→EDT，HK→HKT）对齐 C++，调用方
   可按账户 market 解析

### Critical files

- `crates/futu-backend/src/auth/device.rs:149-210` — `load_credentials`
  legacy + phone format 容错
- `crates/futu-backend/src/auth/mod.rs:1255-1354` — 3 tests 调整
- `crates/futu-gateway/src/handlers/trd/mod.rs:469-488` — status enum 对齐
- `crates/futu-gateway/src/handlers/trd/mod.rs:2281-2354` — 4 新 status tests
- `docs-site/docs/guide/trading.md` — 时区 + status 说明
- `essentials/<history-order-fills-report>.md` —
  bug report 归档

## [1.4.69] - 2026-04-23 🟢 v1.4.68 defer 清偿 + 代码质量 refactor（可跳过）

**已在使用 v1.4.68 的用户可以跳过此版。** 🟢 纯内部 refactor + 代码质量改善
（跨 crate helper 合并 + `#[must_use]` / `#[non_exhaustive]` annotations），
**零 behavior 变化 / 零 API 变化 / 零 bug fix**。

### 🔄 Tier A: v1.4.68 defer 3 项全清

#### A1: `qot_market_to_tz` 跨 crate 合并到 `futu-core`

v1.4.68 `bridge/utils.rs` + `qot/util.rs` 各维护一份 `qot_market_to_tz` 实装
（注释 "修改需同步 sync"，容易 drift）。合并到 `futu_core::market::qot_market_to_tz`，
两处都 `pub(crate) use futu_core::market::qot_market_to_tz;` single source
of truth.

- 新 `crates/futu-core/src/market.rs` + `futu-core` 加 `chrono-tz` dep
- 5 新单测覆盖 HK/US DST/JP/SG/MY/AU/CA fallback 全路径

#### A2: `derive_sec_market` / `derive_exchange_str` / `sec_market_to_qot_market` 查表合并

9 个标准 market family（HK/US/SH/SZ/SG/JP/AU/MY/CA）的 3 fn 重复 match case
合并到 `futu_core::market::MARKET_DISPATCH` const 查表。每 entry 含
`prefix + sec_market + qot_market + exchange_str`。

新加市场只需加表一行，3 fn 自动支持（vs 之前 3 处独立 match 容易漏 case）。
CN. 特殊分派按 code 首数字判 SH/SZ 保留，FX(91) 手动处理。

- 6 新单测（code_prefix dispatch / sec_market 查询 / CN 特殊分派 / consistency）

#### A3: CLI `--tz` 参数占位（`FUTU_CLI_TZ` 环境变量）

`futucli` 加全局 `--tz <IANA-zone>` flag。**当前 flag 可用，但未 wire 到
daemon**（daemon `begin_time` 字符串仍按账户市场本地时区解释）。完整端到
端需 proto 扩 optional `tz_override` 字段，v1.5 breaking change 统一做。
本版先占位避免日后破坏性变更。

### 🔄 Tier B: 代码质量（`#[must_use]` + `#[non_exhaustive]`）

#### B1: 关键 pub fn 加 `#[must_use]`

- `futu_core::market::{qot_market_to_tz, entry_by_sec_market, entry_by_code_prefix}`
- `futu_core::proto_id::is_push_proto`

**说明**：大多数 pub fn 返 `Result<T>`（Rust 默认 warn），再加 must_use 收益
有限。本次选**返普通值的 decision fn**（bool / Option / struct）加。

#### B2: 14 个 internal pub enum 加 `#[non_exhaustive]`

未来加 variant 不 breaking downstream code:

- futu-auth: `LimitOutcome` / `KeyStoreError` / `MachineError`
- futu-backend: `UserAttribution` / `QuoteMktType` / `CodeChangeType` / `CmdType`
- futu-codec: `ProtoFmtType`
- futu-core: `FutuError`
- futu-gateway: `CacheOutcome` / `PushEvent`
- futu-mcp: `GuardOutcome`
- futu-rest: `WsPushScope`
- futu-server: `ConnState`

**未加**（public API schema，向后兼容）: `QotMarket` / `SubType` / `KLType`
/ `RehabType` / `Scope` / `ToolScope`。

#### B3: schemars 0.8 → 1.0（已完成）

v1.4.63 已迁移。workspace 确认只 `futu-mcp/Cargo.toml` 一处 `schemars = "1.0"`。
**本版无工作**。

#### B4: per-broker audit 剩余 handler（已完成）

v1.4.34 修 PlaceOrder/ModifyOrder，v1.4.64 修 GetMarginRatio/GetOrderFee/
FlowSummary，v1.4.57 P2 修 GetOrderFillList。扫 `trd/` 所有含
`backend.request` 的 handler 都已有 `brokers: Arc<DashMap>` 字段 +
`resolve_trade_backend_for_acc`。**本版无工作**。

### ⚠️ Tier F1: `rand 0.8 → 0.9` 升级 blocked（外部依赖）

RSA crate 0.9 依赖 `rand_core 0.6`（与 `rand 0.9` 的 `rand_core 0.9` 不兼容）。
升级 blocked on RSA 0.10 release 或 RSA crate API 支持 rand 0.9。

- 留 v1.5.0+（等 RSA ecosystem 升级）
- 现状：`rand = "0.8"` 保持，代码注释记录重试时需 `ThreadRng: CryptoRngCore` 满足
- 非 "我 defer"，是**外部依赖阻塞**（CLAUDE.md "可以等但不能急"）

### 📋 Tier D 留 v1.4.70 专版（gateway integration tests）

**原计划** v1.4.69 含 Phase E2 part 2+3（mock backend infra + top-20 handler
× 3 scenario = 60 integration tests，~4200 LoC）。

**ship scope 决策**：单版 1-2 整天实装 + verify 过大，**拆成 v1.4.70 专版**
独立做。v1.4.69 保持 "pure refactor 版" scope 清晰。

v1.4.70 scope（下版 plan）:
- D1 mock backend infra（Option B tokio duplex，~500-800 LoC）
- D2 top-20 handler × 3 scenario（~3400 LoC）
- **v1.5.0 hard blocker 解锁**

### 🧪 Tests

- Baseline 630 (v1.4.68) → **641 passed** (+11)
- A1: 5 新（futu-core::market tz dispatch）
- A2: 6 新（futu-core::market MARKET_DISPATCH）
- cargo clippy --workspace --all-targets -- -D warnings: clean
- cargo fmt --check: clean

### 🧭 向后兼容

零 behavior 变化。任一旧 caller 继续工作：
- `qot_market_to_tz(market)` 接口不变
- `sec_market_from_code_prefix` / `sec_market_to_qot_market` / `sec_market_to_exchange_str` 接口不变
- `#[non_exhaustive]` 只加在 **14 internal enum**（非 public API）

### 📦 下版 plan

- `essentials/2026-04-23-0830-v1.4.69-plan.md` — 本版 plan 源
- `essentials/<ts>-v1.4.70-plan.md`（ship 后写）— Tier D gateway
  integration tests 专版

## [1.4.68] - 2026-04-23 🔴 外部 v1.4.57 backlog 全清 + qot/bridge 时区 hardcoding 扫清

**强烈建议升级**（美股 / 日股 / 澳股 / 加拿大股 / futunn HK 账户 / 期货用户 / CLI
用户）。对齐外部 v1.4.57 验收报告剩 5 个 P2，同时扫清 qot + bridge 侧所有时区
hardcoding（美股 push update_time / capital flow / K 线等时间戳之前 HKT 显示差
12-13h）。

### 🔴 Tier A: qot/bridge 时区 hardcoding 扫清 (~250 LoC)

- `bridge/utils.rs` + `qot/util.rs` 5 helper 加 `market: i32` 参数 + chrono-tz
  IANA dispatch（对齐 C++ `APIServer_Inner_API.cpp::GetTimeZoneByAPIQotMkt`）
- 影响面：push 行情 update_time / capital flow / stock IPO / 停牌 / 权息 /
  K 线时间戳 — 按账户市场本地时区渲染（US→America/New_York DST, JP→Tokyo,
  AU→Sydney DST, CA→Toronto DST, SG/MY→UTC+8, HK/CN→HKT）
- `date_str_to_timestamp` 从 FixedOffset 升 chrono-tz DST-aware（US/AU 在 DST
  期正确，原 v1.4.67 偏 1h）
- `market_timezone_offset` legacy helper 删除
- 17 新 tests（HK/US EDT/US winter EST/JP/SG/AU DST/CA DST + DST edge 覆盖）

### 🔴 Tier B: subscribe TrdMarket silent success 修 (外部报告 #8)

用户传 `market=2` (TrdMarket.US) 调 subscribe → ret_type=0 但无订阅（handler
之前直接透传 sec.market，TrdMarket 空间不在 QotMarket 空间）。修：入口识别
TrdMarket 范围 auto-map → QotMarket，非法值返 clear error。

### 🔴 Tier C: kline 修 (外部报告 #6 #7)

- #6 `req_count` / `max_count` 被 serde drop → silent fallback 不 truncate:
  REST adapter 加 field alias 表把 Python SDK 惯用字段名映射到 proto
  `max_ack_kl_num`。
- #7 US history-kline 无 begin/end → 拒:
  daemon 入口 fill default `now - 1year / now`（对齐 Python SDK 客户端侧行为，
  C++ OpenD backend 对空日期直接 reject；Rust daemon 作 SDK 代理 fill default
  让多市场统一 work）。

### 🔴 Tier D: 外部报告 #5 #9 对齐 C++（**部分 UNVERIFIED，请真机 verify**）

- **#5 HK futures market state = 0** — C++ `NNBiz_Qot_EventNotice.cpp::SubEventNotice`
  CMD 6822 `reserved[0]` 实际接受 `NN_QuoteMktType` 值（非 QotMarket）。v1.4.47
  P1.2 曾错改 QotMarket 后未 verify 期货订阅丢失 → HK future 永 0。本版：
  - `quote_mkt_to_*` 重命名为 `quote_mkt_to_nn_mkt_type`
  - 映射按 C++ `NN_QuoteMktType` 枚举（FUT_HK=5, FUT_HK_NEW=6, US_FUT=8,
    SG_FUTURE=13, JP_FUTURE=16）
  - `register_markets` + `pull_all_market_status` 加 `HKFuture2`（主要港期
    NN_QuoteMktType_FUT_HK_NEW=6，C++ 也订阅两个港期）
  - **⚠ UNVERIFIED real-machine**: 从 QotMarket 改回 NN_QuoteMktType 可能影响
    `market_us` 在某些旧后端版本的读取；请真机 verify `market_us` + `market_hk_future`
    均返非 0
- **#9 funds currency=SGD 错（futunn HK）** — C++ `FillFunds` real 证券账户分支
  **不显式 set top-level currency**（由 enCurrency 隐式推导）。Rust 之前直接
  用 backend cache 的 `f.currency` → 被 backend 返值误导。本版：
  - 按 `account.security_firm` 派生 primary currency
    （FutuHK→HKD, FutuUS→USD, FutuSG→SGD, FutuAU→AUD, FutuCA→CAD, FutuMY→MYR,
    FutuJP→JPY），覆盖 backend cache 值。
  - fallback 保留 backend cache 值（Unknown / sim 账户）
  - **⚠ UNVERIFIED real-machine**: 是"synthesize top-level currency" 而非
    严格对齐 C++（C++ real 分支不 set），请真机 verify futunn HK 账户返 HKD(1)
    + moomoo SG 账户返 SGD(5)

### 🧭 真机 verify 请求（CHANGELOG 列出的请同事按序复测）

**稳区（本版应该 work，但仍请验证）**:
1. Tier A: US 账户 snapshot + push quote update_time 应 EDT（非 HKT）
2. Tier B: `curl /api/subscribe market=2` 返错或 auto-map 到 US quote
3. Tier C #6: `curl /api/history-kline req_count=5` 返 5 条（非 1000+）
4. Tier C #7: `curl /api/history-kline market=11 code=AAPL`（无 begin/end）不再 -1

**UNVERIFIED 区（修法 hypothesis 依 C++ 源，需真机定案）**:
5. **Tier D5**: `futucli global-state` 返 `market_hk_future != 0`（如 NIGHT_END=14）
   **同时** `market_us` / `market_sh` / `market_sz` 仍非 0（验证 NN_QuoteMktType
   改回未 regress 其他市场）
6. **Tier D9**: futunn HK 账户 `/api/funds` 返 `currency=1(HKD)` 非 5(SGD)

### 🧪 Tests

- Baseline 601 (v1.4.67) → **630 passed** (+29)
- Tier A: 17 新（per-market TZ + DST edge）
- Tier B: 1（TrdMarket map contract）
- Tier C: 7（field alias）
- Tier D: 4（NN_QuoteMktType + security_firm）
- cargo clippy --workspace --all-targets -- -D warnings: clean
- cargo fmt --check: clean

### 📋 Follow-up v1.5.0 candidate（defer 但列在 plan）

- 2 套 `qot_market_to_tz`（bridge + qot util）合并（需跨 crate 共享 helper 到 futu-core）
- `derive_sec_market` / `derive_exchange_str` 重复 match 合并查表
- CLI `--tz` UX 参数（用户指定时区解释日期）

### Session essentials

- `essentials/2026-04-23-0115-*-v1.4.57-v1.4.59-takeaways-and-plan.md` — v1.4.68 plan 源（内部 essentials 归档）
- `essentials/2026-04-23-0430-timezone-hardcoding-audit.md` — audit 扫清记录
- `essentials/2026-04-23-0730-v1.4.68-wip-handover.md` — branch ship 前 handover

## [1.4.67] - 2026-04-23 🔴 外部报告 backlog 集中修（4 bugs: credentials/create_time/TCP idem/US 期货）

**强烈建议升级**。修外部报告 v1.4.57 + 同事反馈共 4 个 bugs，含 P0 安全 + 3 P1
数据安全/正确性。v1.4.58-66 共 9 版未修此 backlog，本版集中清偿。

### 🔴 Bug #1 (P0 安全): credentials 跨账号 corruption

同机器两个 moomoo 账号的 credentials 文件 hash 不碰撞，但某次写入把 A 的
uid 写到 B 的 credentials 文件后 daemon 无法检测 → broker unlock 用错密码
验错身份。理论跨账户交易风险。

**修法**：`SavedCredentials` 加 `account: String` 字段，load 时强校验
`cred.account == expected_account`，不符即**删 poisoned file** + return
None + 走 password auth 重新 SMS。

**向后兼容**：旧 v1.4.66 及之前的 credentials 文件没 account 字段 → serde
default 空串 → load 视为 invalid → 删文件。**用户升级后需重新 SMS 一次**
（一次性 UX 代价，安全第一不可妥协）。

### 🔴 Bug #2 (P1): history-orders/fills `create_time` 返空字符串

`/api/history-orders` + `/api/history-order-fills` 只 `create_timestamp`
(Unix 秒 f64) 有值，`create_time` 字符串字段**全空**，客户端要自己转换。
违反 C++ 对齐。

**修法**：新 helper `backend_micros_to_market_datetime_str(micros, trd_market)`
按市场本地时区回填（对齐 C++ `APIServer_Inner_API.cpp::GetTimeZoneByTrdMkt`）：
HK/CN/HKCC→Asia/Hong_Kong, US→America/New_York (DST), JP→Asia/Tokyo,
AU→Australia/Sydney (DST), SG→Asia/Singapore, MY→Asia/Kuala_Lumpur,
CA→America/Toronto (DST)。加 `chrono-tz` dep。

### 🔴 Bug #3 (P1): CLI TCP 幂等键跨进程碰撞

wire-level 实证：每个 futucli 进程新 TCP + `conn_id=0` 硬编码 +
`PACKET_SERIAL` 从 1 起 → 两个 CLI 第一个包 key 都是 `"tcp-pkt-0-1"` →
daemon 90s TTL cache 命中第一次结果。**最危险场景**：CLI 下单 → 90s 内
CLI cancel → cancel 返了 place-order 的缓存 order_id → 用户以为 cancel 成功
但订单还挂着。

**修法**：`crates/futu-trd/src/order.rs::next_packet_id()` + `misc.rs::reconfirm_order`
的 `conn_id` 从硬编码 0 改为 **per-process random u64**（`OnceLock` + `rand`），
跨进程碰撞概率 2^-64。

### 🔴 Bug #4 (P1): US 期货 exchange_code=11 (NASDAQ stock) → 110005

下单 `US.MNQ2606` (CME E-mini Nasdaq 期货) `exchange_code=11`（股票 NASDAQ
mkt_id）→ backend 110005。v1.4.59 Phase D cache-first 只修了 exchange_str 没修
exchange_code 字段。

**修法**：新 helper `derive_exchange_code_cache_first()` 三层 cache-first
对齐 C++ `NNProto_Trd_OrderOp.cpp:186 req.set_exchange_code((u32_t)order.enMktID)`:
Layer 1 cache mkt_id → Layer 2 期货 exchange_str 反推 (NYMEX=60 / COMEX=70 /
CBOT=81 / CME=91 / CBOE=100 / HKFE=114 / SGX=160 / OSE=185) → Layer 3 股票
`sec_market_to_qot_market`。place_order + max_qty 两 handler 都修。

### 🧭 方法论沉淀

外部 v1.4.57 报告 04-22 08:30 交付，本版 04-23 01:30 处理。v1.4.58-66 共 9 版
全做内部 refactor + 另一位同事 bug → backlog 漏处理。沉淀到
`essentials/2026-04-23-0115-*-v1.4.57-v1.4.59-takeaways-and-plan.md`。

### 🔍 Audit sidecar

`essentials/2026-04-23-0430-timezone-hardcoding-audit.md` — 扫全仓库 16 处
`8*3600` HKT 硬编码，本版修 trd 侧 2 处，qot/bridge 14 处留 v1.4.68+。

### 🧪 Tests

- 38 新单测（Bug #1: 4 / Bug #2: 19 / Bug #3: 6 / Bug #4: 9）
- Workspace: 601 passed (v1.4.66 baseline 563 + 38)
- cargo clippy --workspace --all-targets -- -D warnings: clean
- cargo fmt --check: clean

### 🧭 真机 verify 请求

以下场景请在真机复验：
1. 多 moomoo 账号同机器登录 → `/api/unlock-trade` 走正确账号密码
2. `/api/history-orders` + `/api/history-order-fills` → create_time 非空 HKT/EDT 格式
3. CLI `futucli place-order ... ; sleep 5; futucli cancel-order ...` → cancel 不返 place 的缓存
4. `/api/order code=US.MNQ2606` → 不再 110005（daemon log `exchange_code=91`）

### 📋 仍在 backlog (v1.4.68+)

外部 v1.4.57 报告剩 5 个 P2 待修：HK 期货 market state / kline req_count /
US kline default date / subscribe market enum / funds currency SGD。

## [1.4.66] - 2026-04-23 🔴 /api/history-orders + /api/history-order-fills filter_market fix

**建议升级**（history 查询返空列表的 2FA 账户用户）。

### 🔴 Bug #1: filter_market 被 handler 忽略 → silent empty

Handler 完全忽略 `filter_conditions.filter_market`，只用账户 `trd_market_auth_list`
派生。用户传 filter_market 无效；account auth_list 空 → backend 返空（坑 #31）。

**修法**（`trd/history.rs:161/344`）：优先用用户传的 `filter.filter_market` → fallback auth_list → 仍空返 clear error。

### 🟡 Known Issues（同事反馈，留 v1.4.67+）

- **create_time 空字符串**: backend 返 create_timestamp 但 create_time 字符串为空。
  daemon 应 timestamp 回填（chrono::DateTime::from_timestamp）。v1.4.67 修。
- **status=1 CANCELLED 误报**: backend bug，非 Rust 侧。建议按 `fill_qty > 0 && price > 0` 判断真成交。

## [1.4.65] - 2026-04-23 🔄 Phase E2 part 1: gateway integration test infrastructure MVP

**可跳过此版**（🔄 内部 infrastructure）。零 behavior / 零 API / 零 feature / 零 bug fix。

首次建立 `crates/futu-gateway/tests/` integration test 基础，为后续 Phase E2
完整 60 tests 打底。

### 🔄 新增

- `crates/futu-gateway/tests/common/mod.rs` — 测试 helpers:
  - `make_test_bridge()` / `make_test_server()` — 构造无 backend 连接的
    `GatewayBridge` + `ApiServer` 并 register handlers
  - `make_request()` — 构造 `IncomingRequest`
- `crates/futu-gateway/tests/smoke_test.rs` — 3 canary integration tests:
  - `gateway_bridge_constructs_and_registers_handlers` — setup 不 panic
  - `unknown_proto_id_does_not_panic` — router 未注册 proto_id 安全处理
  - `get_acc_list_with_empty_cache_returns_success_empty` — 完整 integration
    path：request → `router.dispatch()` → 解码响应 → 断言 empty acc_list

### 🎯 设计策略

- **通过 `RequestRouter::dispatch()` 从外部 crate 访问**（非直接 instantiate
  `pub(super)` handler）
- **纯 cache-read handler 先做**（GetAccList/GetFunds/GetPositionList 无需
  mock backend）
- **Mock backend 基础设施**（tokio::io::duplex / BackendConn trait extraction）
  留 Phase E2 part 2

### ℹ️ 向后兼容

- **零 API 变化**：REST / gRPC / MCP / CLI 不变
- **零 behavior 变化**：只新增 tests，无生产代码改动
- **560 → 563 workspace tests**（+3 smoke tests）

### 🧭 Out of scope（留 v1.4.66+ / v1.5.0）

- Phase E2 part 2: mock backend infrastructure（`BackendConn` trait 或 stub 模式）
- Phase E2 part 3: top-20 × 3 scenario = 60 tests 扩展（覆盖 PlaceOrder / Modify /
  Unlock / GetFunds / GetOptionChain / etc. happy/cache_miss/backend_error 路径）

## [1.4.64] - 2026-04-22 🔴 Per-broker routing 补齐（对齐 C++ 坑 #14）

**建议升级**（2FA 账户 moomoo US / futu CA 等使用 margin ratio / order fee /
flow summary 查询的用户）。

### 🔴 修复

v1.4.63 ship 后的 Phase E3 per-broker audit v2 跟进 C++ 对照确认（详见
`essentials/2026-04-22-1925-v1.4.63-per-broker-audit-v2-cpp-confirmed.md`）：
3 个 handler 在 C++ 都继承 `NNProto_Trd_Base`，按 accID 走 per-broker TCP 通道。
Rust 之前走 Platform channel → 2FA 账户 backend 拒"请重新解锁交易"。

3 个 handler 补齐 per-broker routing，对齐 C++：

| Handler | CMD | C++ 参照 |
|---|---|---|
| `GetMarginRatioHandler` | 2309 | `NNProto_Trd_GetMarginRatio.cpp:85` |
| `GetOrderFeeHandler` | 2273 | `NNProto_Trd_OrderFee.cpp:137` |
| `FlowSummaryHandler` | 20963 | `NNProto_Trd_FlowSummary.cpp:142` + `:253` |

**修法**（照抄 `GetMaxTrdQtys` / `BackendTrdForward` 已有模式）:
- 加 `brokers: Arc<DashMap<u32, Arc<BackendConn>>>` 字段
- handle() 内 `resolve_trade_backend_for_acc(brokers, cache, platform, acc_id)` 按 acc_id 路由
- Platform fallback for sim / unknown security_firm / cache miss（向后兼容）
- `GetMarginRatioHandler` 补 `check_acc_id_not_zero_or_error` defensive check (坑 #30/#31)

### 🧹 清理

- `qot::register_handlers` 删除 `GetBrokerHandler` 重复注册（v1.4.63 code
  review LOW-2，无行为差异，仅整洁）

### ℹ️ 向后兼容

- **REST / gRPC / MCP / CLI 接口不变**
- sim 账户 + unknown security_firm / cache miss → 继续走 Platform fallback（不回归）
- 标准 HK real 账户 → 正确路由到 broker 1001
- 2FA moomoo / futu 账户 → 之前失败的查询现在应成功

### 🧪 Tests

- `cargo test --workspace --lib --bins --tests`: **560 passed** / 0 failed
- `cargo clippy --workspace --all-targets -- -D warnings`: 零 warning
- `cargo fmt --check`: clean

### 🧭 真机 verify 请求（ship 后）

同事 / 用户用 2FA 账户测试，确认：
- `/api/margin-ratio` moomoo US 成功返数据
- `/api/order-fee` moomoo US 成功返数据
- `/api/flow-summary` futu CA 成功返数据
- sim 账户 / 标准 HK real 账户 回归（仍 work）

### 🧭 CLAUDE.md 坑 #14 实锤链（累计 4 次同类坑）

1. v1.4.34 PlaceOrder / ModifyOrder per-broker（外部 reviewer 实锤）
2. v1.4.38 BackendTrdForwardHandler per-broker（外部 reviewer 实锤）
3. v1.4.60-63 handler 模块化期间 audit 发现 3 个 handler 遗漏
4. **v1.4.64 本版**：C++ 对照主动实锤 + 补齐

防护：`essentials/2026-04-22-1925-...` 记录 audit v2 方法论（C++ 继承链 +
`SendTCPProto_ProtoBuf_WithAccID(m_nAccID, m_enProtoCategory, ...)` 检查）
供未来新增 trade handler 时 audit 用。

## [1.4.63] - 2026-04-22 🔄 Phase E1 完整 + Phase E3 partial polish pass

**可跳过此版**（🔄 纯内部重构）。零 behavior / 零 API / 零 feature / 零 bug fix。
继续 v1.4.60/61/62 的 handler 模块化工作，本版完成 **Phase E1 全部拆分**
（31 子文件）+ **Phase E3 部分工程升级**（schemars + must_use + non_exhaustive）。

**Phase E2（60 integration tests）推迟到 v1.4.64 或 v1.5.0**，独立工程需
mock backend 基础设施 + ~3400 LoC 测试代码，做完再 ship。

### 🔄 Phase E1 handler 模块化 — 完整完成

**trd.rs: 7869 → 3307 LoC (-58%)**，10 子文件：

| 子文件 | LoC | 内容 |
|---|---:|---|
| trd/mod.rs | 3307 | register_handlers + 25 cross-handler helpers + 测试 |
| trd/unlock.rs | 904 | UnlockTradeHandler + BrokerGroup/BrokerUnlockResult + per-broker cipher |
| trd/max_qty.rs | 887 | GetMaxTrdQtys + GetMarginRatio + GetOrderFee + FlowSummary |
| trd/security_type.rs | 855 | 18 代码分类 / 市场路由 helpers (坑 #14/#35/#36) |
| trd/history.rs | 595 | GetHistoryOrderList + GetHistoryOrderFillList + BackendTrdForwardHandler |
| trd/query.rs | 531 | 5 cache-read handlers (GetAccList/GetFunds/GetPositionList/GetOrderList/GetOrderFillList) |
| trd/modify_order.rs | 477 | ModifyOrderHandler |
| trd/place_order.rs | 410 | PlaceOrderHandler + map_order_type + CMD_PLACE_ORDER |
| trd/err_hint.rs | 133 | 错误码 → 用户 hint 翻译 |
| trd/sub_push.rs | 34 | SubAccPushHandler |

**qot.rs: 9562 → 1016 LoC (-89%)**，16 子文件：

| 子文件 | LoC | 内容 |
|---|---:|---|
| qot/mod.rs | 1016 | register_handlers + 2 cross-handler helpers + 测试 |
| qot/stock_filter.rs | 1333 | StockFilterHandler + 21+ filter mapping helpers |
| qot/option.rs | 1220 | GetOption{ExpirationDate,Chain}Handler + 13 option helpers |
| qot/snapshot.rs | 930 | GetStaticInfo + GetSecuritySnapshot + 7 helpers |
| qot/history_kline.rs | 751 | 6 history/KL/trade-date handlers |
| qot/misc.rs | 725 | GetReference/Suspend/Broker/CodeChange/FutureInfo/UsedQuota |
| qot/user_security.rs | 673 | 4 自选股 handler |
| qot/plate.rs | 472 | 3 板块 handler |
| qot/price_reminder.rs | 442 | 2 提醒 handler + 7 mapper |
| qot/capital.rs | 392 | 2 资金流向 handler |
| qot/warrant.rs | 385 | GetWarrant |
| qot/ipo.rs | 365 | GetIpoList |
| qot/rehab.rs | 327 | 2 除权 handler |
| qot/market_state.rs | 290 | 2 市场状态 handler |
| qot/quotes.rs | 286 | 5 基础行情 handler |
| qot/util.rs | 254 | 13 时间/日期/市场/KL 纯函数 |
| qot/subscribe.rs | 194 | 3 订阅管理 handler |

**bridge.rs（v1.4.60 已拆）**：5 子文件不变（mod / push_parser / account / utils / push_builder）

**累计规模**：22119 LoC → 31 子文件，每文件 < 1400 LoC，可维护性大幅提升。

### 🔄 Phase E3 工程升级 — partial

- **schemars 0.8 → 1.0** (`crates/futu-mcp/Cargo.toml`) — rmcp 间接依赖，无 breaking
- **`#[must_use]` × 2**（`KeyRecord::generate` + `generate_with_machines` in
  `futu-auth/src/key.rs`）— 丢弃生成结果 = 丢失 plaintext = bug 信号
- **`#[non_exhaustive]` × 4 internal pub enums**（F-NON-EXHAUST-001 部分）:
  - `futu_gateway::idempotency::CacheOutcome`
  - `futu_gateway::bridge::PushEvent`
  - `futu_rest::ws::WsPushScope`
  - `futu_mcp::guard::GuardOutcome`
- **Per-broker audit findings 文档化**（F-TRD-PER-BROKER-AUDIT）：`GetMarginRatio`
  + `GetOrderFee` + `FlowSummary` 3 个 handler 目前走 Platform channel，是否真
  per-broker 未验证（需 C++ 对照 + 真机 2FA 账户测试）。**不盲修**，留 v1.4.64+
  实锤后处理。详见 `essentials/2026-04-22-1825-v1.4.63-per-broker-audit.md`。

### 🧭 Out of scope（明确延到后续版本）

- **Phase E2 gateway integration tests**（top-20 handler × 3 scenario = 60 tests /
  ~3400 LoC + mock backend infrastructure）→ v1.4.64+ 独立版本做。mock backend
  是新基础设施工程，单独处理
- **F-PER-BROKER-{MARGIN,ORDER-FEE,FLOW-SUMMARY}** 3 个 handler 的 per-broker 修
  → v1.4.64 bug fix 版，需 C++ 对照确认后做
- **F-MUST-USE-001 扩展**（top-50 pub fn/type）→ 选择性，未来版本按需加
- **F-NON-EXHAUST-001 扩展**（更多 pub enum）→ wire-protocol enum 故意不加；
  error enum 需评估向后兼容性

### ℹ️ 向后兼容 / 破坏性评估

- **零 API 变化**：REST / gRPC / MCP / CLI / HTTP admin endpoint 不变
- **零运行时 behavior 变化**：仅文件/模块结构变化，所有 fn 签名 + 逻辑 100% 一致
- **零 cache 迁移**：SQLite / QotCache / TrdCache / StaticDataCache schema 不变
- **零 test 语义变化**：560 workspace tests 全绿
- **schemars 1.0** 对 rmcp 用户是 API 兼容升级（MCP 客户端无感知）
- **`#[non_exhaustive]`** 只加在 4 个内部 enum，不暴露外部 API

### 🧪 Tests

- `cargo test --workspace --lib --bins --tests`: **560 passed** / 0 failed（与 v1.4.62 一致）
- `cargo clippy --workspace --all-targets -- -D warnings`: **零 warning**
- `cargo fmt --check`: 零 diff
- `./scripts/proto_diff_check.sh`: 0 missing fields (坑 #23 debt-free 保持)

### 🛡️ Code review（用户要求 ship 前强制）

使用 `superpowers:code-reviewer` agent 做完整 review：
- **0 CRITICAL / 0 HIGH** 阻塞
- **1 MED**：FlowSummaryHandler 也应在 per-broker audit scope → 更新 audit 文档
  (本版 commit 已修)
- **4 LOW**：cosmetic / pre-existing bugs（不阻塞 ship）
- 审查过程验证：所有 per-broker routing preserved，`#[async_trait]` 位置正确，
  `pub(super)` 可见性正确，handler 字段 + `register_handlers()` 对齐

### 📊 规模统计

- 代码重组：+~22119 LoC moved (~31 子文件)
- 净新增代码：~ +130 LoC（主要是子模块头 + imports + pub(super) annotations）
- 新增 test：0（Phase E2 defer）
- 改动 Cargo.toml: 1 处（schemars 0.8 → 1.0）
- essentials 新增：4 份 handover docs + 1 份 audit findings

### 🧭 CLAUDE.md 坑状态

- **坑 #14**（per-broker routing）：✅ 全部 trade write handler 仍正确 per-broker
  （PlaceOrder/ModifyOrder/UnlockTrade/GetMaxTrdQtys/GetHistoryOrder*/等）
- **坑 #35**（cache-first > pattern heuristic）：✅ 保持（v1.4.59 闭环后未回退）
- **坑 #36**（code prefix 是用户意图真相层）：✅ 保持
- **坑 #37**（新 MCP tool 必须 4 处 audit checklist）：✅ tool 列表 + scope 全对齐
- **坑 #38**（review scope-creep + Agent 归桶 bias）：✅ 本版 code review 严格 read file:line 归桶

## [1.4.62] - 2026-04-22 🔄 Phase E1 part 3: qot.rs 模块化启动（qot/util.rs）

**可跳过此版**（🔄 纯内部重构）。零 behavior / 零 API / 零 feature / 零 bug fix。
接续 v1.4.60/61 Phase E1，首次触及 `qot.rs` 9562 LoC 源文件。

### 🔄 qot.rs → qot/ 目录

- `git mv handlers/qot.rs handlers/qot/mod.rs`（保留 git blame 历史）
- 新子模块 `qot/util.rs`（257 LoC）含 13 个时间/日期/市场/K线类型纯函数：
  - Time/date: `date_str_to_timestamp`, `timestamp_to_datetime_str`,
    `timestamp_to_date_str`, `timestamp_to_components`, `date_str_to_yyyymmdd`,
    `yyyymmdd_to_date_str`, `parse_date_to_timestamp`, `is_leap_year`,
    `market_timezone_offset`
  - Market conversion: `ftapi_market_to_backend`
  - KL type: `ftapi_kl_type_to_backend`
  - Trading type: `backend_trading_type_to_ftapi`
  - Option expiration: `backend_expiration_to_api`
- qot/mod.rs 从 9562 → 9318 LoC（~244 LoC 移到 util.rs + headers）
- 全部 `pub(super)` 让 mod.rs + 未来 handler 子模块都能用

### 🧪 Tests

- `cargo test --workspace --lib --bins --tests`: 560 passed
- `cargo clippy --workspace --all-targets -- -D warnings`: 零 warning
- `cargo fmt --check`: 零 diff

### ℹ️ 向后兼容

- **零 API 变化** / **零 cache 迁移** / **零 test 语义变化**

### 🧭 Out of scope（留 v1.4.63+）

- qot 剩余 16 handler 子文件：subscribe / quotes / snapshot / history_kline /
  rehab / plate / market_state / option / warrant / capital / stock_filter /
  price_reminder / user_security / ipo / misc（~9300 LoC 尚未拆）
- trd 剩余 5 handler 子文件：place_order / unlock / history / query / max_qty

## [1.4.61] - 2026-04-22 🔄 Phase E1 part 2: trd handler 模块化继续（err_hint + sub_push + modify_order）

**可跳过此版**（🔄 纯内部重构）。零 behavior 变化 / 零 API 变化 / 零 feature。
接续 v1.4.60 Phase E1，把 `handlers/trd.rs` 再拆 3 个子文件。

### 🔄 trd.rs 继续拆分（accumulative since v1.4.60）

v1.4.60 已拆出 `security_type.rs`（18 个 code-classification helpers）。本版
新增 3 个子文件：

| 子文件 | 内容 | LoC |
|---|---|---:|
| `handlers/trd/err_hint.rs` | 5 个 error translator/formatter（`format_backend_trd_error` / `translate_modify_order_err_hint` / `translate_place_order_err_hint` / `annotate_modify_order_err` / `annotate_place_order_err`）| 134 |
| `handlers/trd/sub_push.rs` | `SubAccPushHandler`（trade 账户 push 订阅注册） | 34 |
| `handlers/trd/modify_order.rs` | `ModifyOrderHandler`（CMD 4702/4703，per-broker 路由 + cipher 校验 + idempotency） | 468 |

`handlers/trd/mod.rs` 从 v1.4.60 后 7046 LoC → 本版 ~6000 LoC（减少 ~1000 LoC）。

### ℹ️ 工程工具改动

- `modify_order.rs` 用 `use super::*;` pattern + `crate::handlers::load_backend/make_error_response` 显式 grandparent 路径
- struct 字段升 `pub(super)` 以便 `register_handlers` 在父 mod 实例化
- `#[allow(unused_imports)]` 应用于 `use err_hint::{...}`（测试引用但 prod path 不用）

### 🧪 Tests

- `cargo test --workspace --lib --bins --tests`: 560 passed
- `cargo clippy --workspace --all-targets -- -D warnings`: 零 warning
- `cargo fmt --check`: 零 diff
- `cargo check`: clean

### ℹ️ 向后兼容

- **零 API 变化**（REST / gRPC / MCP / CLI 不变）
- **零 cache 迁移**
- **零 test 语义变化**

### 🧭 Out of scope（留 v1.4.62 收尾）

剩余 trd handlers + qot 全拆在 v1.4.62 做：
- trd: `place_order.rs`（PlaceOrderHandler，~500 LoC）/ `unlock.rs`（UnlockTradeHandler + per-broker cipher，~1500 LoC）/ `history.rs`（2 history handlers + BackendTrdForwardHandler，~1200 LoC）/ `query.rs`（5 query handlers，~700 LoC）/ `max_qty.rs`（4 query handlers，~800 LoC）
- qot: `qot.rs` 9562 LoC 全拆 17 子文件（util + 16 handler）

## [1.4.60] - 2026-04-22 🔄 Phase E1 part 1: bridge.rs 模块化拆分 + trd security_type 独立

**可跳过此版**（🔄 纯内部重构）。零 behavior 变化、零 API 变化、零 feature、
零 bug fix。仅把 `bridge.rs` (4688 LoC) 拆成 5 个子文件 + `handlers/trd.rs`
抽出 `security_type.rs` 子模块。**用户视角无变化**。

### 🔄 背景

Review 报告（`essentials/2026-04-22-0607-review-master-report.md` §5.1 F-QOT-001 /
F-TRD-001 / F-BRIDGE-001）提出 `bridge.rs` / `trd.rs` / `qot.rs` 3 个热点
文件 > 5000-9000 LoC 应做模块化拆分便于维护 + 未来 cache-first 升级。v1.4.60
完成其中的 **Phase E1 part 1**（bridge 全拆 + trd security_type 独立）。

### 🔄 bridge.rs 4688 LoC → 5 子文件

| 子文件 | 内容 | LoC |
|---|---|---:|
| `bridge/mod.rs` | GatewayBridge struct 定义 + 核心 lifecycle (new / initialize / register_handlers / push_dispatcher / reload) + 底层 async broker login 函数 | 2103 |
| `bridge/push_parser.rs` | 19 个 backend push 解析函数（`handle_quote_push` / `handle_trade_notify` / `parse_*_to_push` 等） | 1590 |
| `bridge/account.rs` | 12 个账户元数据解析 + broker 通道建立 + 账户列表拉取函数 | 844 |
| `bridge/utils.rs` | 7 个纯 utility fn（`split_host_port` / `listing_date_to_str` / `timestamp_to_datetime_str` / `days_to_ymd` / `market_code_to_qot_market` / `market_code_to_exch_type` / `security_firm_to_broker_id`） | 134 |
| `bridge/push_builder.rs` | 2 个 `Trd_UpdateOrder` / `Trd_UpdateOrderFill` push body builder | 101 |

### 🔄 trd.rs 7869 LoC → 2 子文件（part 1）

| 子文件 | 内容 | LoC |
|---|---|---:|
| `handlers/trd/mod.rs` | 所有 impl RequestHandler 业务处理器 + handler 注册 | 7046 |
| `handlers/trd/security_type.rs` | 18 个 code-classification / market_routing 辅助函数（`is_option_code` / `is_futures_code` / `derive_sec_market` / `derive_exchange_str` / `derive_exchange_str_cache_first` / `us_futures_sub_exchange_from_mkt_id` / `hk_option_exchange_from_mkt_id` / `sec_market_from_code_prefix` / `futures_ticker_to_sec_market` / `is_hk_index_option_code` / `derive_security_type` / 等）| 856 |

集中 CLAUDE.md 坑 #14 / #35 / #36 相关逻辑方便未来 cache-first 升级 + 跨 surface
sec_market / exchange_str 决策维护。

### ℹ️ 工程工具 / 内部变更

- `bridge.rs` / `trd.rs` 分别 `git mv` 到 `bridge/mod.rs` / `handlers/trd/mod.rs`
  后做拆分（保留 git blame 追溯历史）
- 所有 `fn` visibility 用 `pub(super)` 精确控制（外部 crate 零暴露变化）
- 所有 `impl GatewayBridge { ... }` 块分散到子文件后通过 Rust 多 impl-block
  规则保持方法可见性
- **`ship.sh` A4.5 pipefail bug 修**（v1.4.59 ship 顺手发现）：`grep -v` 全过滤
  返 1 + `set -o pipefail` 触发 shell abort 错误，用 `|| true` 包每个 grep

### ℹ️ 向后兼容 / 破坏性评估

- **零 API 变化**：REST / gRPC / MCP / CLI / HTTP admin endpoint 不变
- **零运行时 behavior 变化**：仅文件/模块结构变化，所有函数签名 + 逻辑 100% 一致
- **零 cache 迁移**：SQLite / QotCache / TrdCache / StaticDataCache schema 不变
- **零 test 语义变化**：210 gateway / 560 workspace 全绿 + clippy / fmt 全 pass

### 🧪 Tests

- `cargo test --workspace --lib --bins --tests`: 560 passed / 0 failed（= v1.4.59）
- `cargo clippy --workspace --all-targets -- -D warnings`: 零 warning
- `cargo fmt --check`: 零 diff
- `./scripts/proto_diff_check.sh`: 0 fields missing
- `./scripts/pii_scan.sh`: clean

### 📊 规模

- bridge.rs 4688 → mod 2103（55% 缩减） + 4 子文件共 2669 LoC
- trd.rs 7869 → mod 7046（10% 缩减） + security_type 856 LoC
- 新增 LoC（纯头部 + impl 包装）: ~90
- **Net 变化**：零 behavior，约 +90 LoC overhead（模块头部 + imports）

### 🧭 Out of scope（defer 至 v1.4.61/62）

- **trd.rs 剩余 ~7000 LoC handler 拆分**：PlaceOrderHandler / ModifyOrderHandler /
  UnlockTradeHandler / QueryHandlers 等 `impl RequestHandler` 块 → v1.4.61
- **qot.rs 9562 LoC 全拆**（util.rs + 16 handler 子文件）→ v1.4.62
- **err_hint.rs 提取**（trd error translator / formatter helpers 非连续块）→ v1.4.61

## [1.4.59] - 2026-04-22 🔄 Cache-first 路由精度升级（CLAUDE.md 坑 #35 闭环）

**可跳过此版**（🔄 内部重构）。不修任何 bug、不改任何 API、不引入新 feature。
唯一 behavior 变化：当 StaticDataCache 里有目标 symbol 且带 backend 真实
`mkt_id` (NN_QuoteMktID) 时，**US futures 子交易所 / HK 期权 SEHK-vs-HKFE
决策更精确**；cache miss 时 fall back 到 v1.4.58 的 ticker whitelist pattern，
**零回归保证**。

**动机**：v1.4.54 / v1.4.55 / v1.4.56 三次修同一类 sub-exchange 误路由 bug
（CLAUDE.md 坑 #36 "连续 3 次同类 bug 强制挖根因"）。共同根因是 CLAUDE.md
坑 #35 —— Rust 侧 cache 不带 backend 原始 `market_code` 精度，只能用 ticker
pattern whitelist 启发式决策，遇到新 ticker（CME 货币 / 期权新指数）就漏。

**C++ 真相**：C++ 期货 / 期权识别走 `stock_list` cache 的 `NN_QuoteMktID`
range（60-69=NYMEX / 70-79=COMEX / 80-89=CBOT / 90-99=CME / 100-109=CBOE；
HK 7=HK_Option / 8=HK_Index_Option），**数据驱动不是 pattern 驱动**。本版
在 Rust cache 侧补齐这层信息。

### 🔄 CachedSecurityInfo 加 `mkt_id: u32` 字段

- `crates/futu-cache/src/static_data.rs`: `CachedSecurityInfo` struct 加
  `pub mkt_id: u32`（保留 backend 原始 NN_QuoteMktID 精度）
- `crates/futu-gateway/src/bridge.rs`: SQLite restore path (L1207) + live
  backend push path (L1306) 两个 populate 点都写入 `mkt_id: info.market_code`
- `crates/futu-gateway/src/handlers/qot.rs`: 3 处 on-demand option cache
  populate 也写入 `mkt_id: opt.market_code.unwrap_or(0)`（CMD 20106
  OptionResultInfo field 18）
- **SQLite schema 向后兼容**：`DbStockItem.market_code` 字段早就存在，重用
  现有列；旧 DB 文件直接 compatible，首次启动后 cache 重填自动带上 mkt_id

### 🔄 Cache-first 辅助函数（替代 pattern whitelist 启发式）

- 新 `us_futures_sub_exchange_from_mkt_id(mkt_id: u32) -> Option<&'static str>`
  — O(1) range 判 NYMEX/COMEX/CBOT/CME/CBOE
- 新 `hk_option_exchange_from_mkt_id(mkt_id: u32) -> Option<&'static str>`
  — HK_Option (7) → SEHK / HK_Index_Option (8) → HKFE
- 新 `derive_exchange_str_cache_first(...)` 包装器：优先 cache 查 mkt_id；
  cache miss / mkt_id=0 / 非目标分支 → fall back 到 v1.4.58 `derive_exchange_str`
  ticker whitelist pattern
- `PlaceOrderHandler` + `MaxBuySellHandler` 两个生产调用点换用 cache-first 包装器

### 🧪 Tests (+7 → 210 gateway / 560 workspace)

- `us_futures_sub_exchange_from_mkt_id_range_mapping` — 验证 5 个 range 边界
- `hk_option_exchange_from_mkt_id_disambiguation` — 验证 7/8 映射
- `derive_exchange_str_cache_first_us_futures_via_mkt_id` — **cache mkt_id
  真的 override ticker pattern**（模拟 "NYMEX_MASQUERADE" 虚构 ticker + mkt_id=65
  → 返 NYMEX 而不是 pattern 默认 CME）
- `derive_exchange_str_cache_first_falls_back_on_miss` — cache miss 零回归
- `derive_exchange_str_cache_first_hk_option_via_mkt_id` — HSI/TCH 期权 SEHK/HKFE
- `derive_exchange_str_cache_first_non_target_branches_untouched` — 非目标
  分支（HK futures / US options / SG / JP / 正股）cache 不介入
- `derive_exchange_str_cache_first_mkt_id_zero_falls_back` — 历史 SQLite
  行 mkt_id=0 fall back 保证零回归

### ℹ️ 向后兼容 / 破坏性评估

- **零破坏**：新 field `mkt_id` 加 default value `0`，老代码构造 struct 必须
  显式传 0（Rust 编译器保护，本版已同步 8 个 construction site）
- **零 API 变化**：REST / gRPC / MCP / CLI 接口不变
- **零 cache 文件迁移**：SQLite schema 没动，`DbStockItem` 字段不变
- **零 bugfix**：所有 v1.4.58 及之前的 behavior 保持一致，cache miss 时
  走 pattern fallback，和 v1.4.58 完全等价

### 📊 规模

- Rust code: +~280 LoC net（struct ~30 / bridge+qot populate ~20 / trd helpers
  + wrapper ~130 / unit tests ~230）
- 文件改动：5 个 Rust 文件（static_data.rs / bridge.rs / qot.rs / trd.rs）+
  CHANGELOG + docs-site 双语 + essentials 4 件套

### 🧭 CLAUDE.md 坑状态

- **坑 #35**（cache-first is correct design）：✅ **闭环** — cache-first 辅助
  函数 + wrapper 已实装，替代 pattern 成为生产默认路径
- **坑 #36**（code prefix/pattern 是 "用户意图真相" 层）：**保留不动** —
  SDK metadata 硬编码的问题 layer 1 仍然是 prefix，与本版 cache-first 是
  正交两层（prefix → sec_market 决定；cache mkt_id → 子交易所精度）

## [1.4.58] - 2026-04-22 ✨ v1.5 前置特性 Bundle: MCP SSE push + Idempotency + isError 根治

**建议升级**（MCP agent 用户 / 调用 trade unlock 重试的用户 / 所有 tool error
判断依赖 top-level is_error 的客户端）。

**背景**：用户明确反馈"不要再出现 v1.4.48-57 那样的修复循环"。v1.4.58 是 10
版修复 cycle 后**第一个 feature-first 版本**，bundle 5 个 Phase 一起发布：
Phase A + B + C1 + C2 + C3。ship 前经历 **3 轮 code review**（每轮问题都修），
零 HIGH / 零 MED / 零 LOW 余留。

**版本号约定**：用户定义 v1.5 保留给更大里程碑（desktop source Tier 1 解锁
/ 多 Phase 一起打包）。本版虽有 ~1800 LoC 但不升 v1.5（对齐 CLAUDE.md 新加
的"版本号分配纪律"）。

## ✨ Features

### Phase A: MCP Push 订阅 ergonomics

Push infra 本身自 v1.4.38 实装完整（state.rs drain loop + `notify_logging_message`），
但 ergonomics 有 2 个 gap 需要补：

- **新 tool `futu_unsub_acc_push`**：显式撤销 push 订阅（之前只能等 4h
  auto-purge）。需 session_id（从 `futu_sub_acc_push` 响应取）
- **新 tool `futu_push_subscriber_info`**：诊断工具，列出本 server 所有活跃
  订阅 + `age_secs`。用于 agent 验证订阅状态 / 调试丢 push / 清理前 preview
- **`futu_sub_acc_push` 响应扩展**：返回体加 `session_id` + `unsub_hint` 字段，
  让客户端存 session_id 以便后续撤销
- **`state.rs` 支持方法**：`unregister_push_subscriber` 返 `bool` 让 caller 知
  是否命中；新 `push_subscribers_summary` 方法返 tuple 列表

### Phase B: Idempotency UnlockTrade wire（收尾）

v1.4.38 Phase 4 已给 PlaceOrder / ModifyOrder / CancelOrder 加幂等。
UnlockTrade 是 5 handler 最后 1 个未 wire。

- **2 级 key fallback**：
  1. 显式 `request.idempotency_key`（REST `Idempotency-Key` / MCP args）
  2. 参数 hash（`unlock` + `security_firm` + sorted `acc_ids` + `pwd_md5[..8]`）
  （注：`Trd_UnlockTrade.C2S` 无 `packet_id` 字段，不像 PlaceOrder，所以
  fallback 用参数 hash 而非 PacketID）
- **Cache 规则**：只在 `total_unlocked == total_requested`（完全成功）时写入，
  避免部分成功时 retry 命中 cache → 失败账户无法重试
- **隐私**：pwd_md5 首 8 字符入 hash（不整串入 cache key）
- **TTL**：90s 同现有 cache 配置

## 🧭 技术债闭环: CLAUDE.md 坑 #32 MCP isError 根治（Phase C1 + C2 + C3）

坑 #32 跨 7 版未处理（v1.4.50→57）。v1.4.58 Phase C 彻底解决。

### Phase C1: Helpers + 2 pilot handler

- 新 `Self::tool_err(msg) -> Result<String, String>` — 返 Err 让 rmcp 自动 set
  top-level `CallToolResult.is_error = Some(true)`（对齐 MCP spec）
- 新 `Self::wrap_result(res)` / `Self::result_as_str(r)` helpers
- Pilot 迁移 `futu_unsub_acc_push` + `futu_push_subscriber_info` 2 个 handler

### Phase C2: 批量迁移 54 handlers

- **机械转换**：`async fn xxx(...) -> String` → `-> Result<String, String>`
- `return rej;` → `return Err(rej);`（scope reject）
- `return Self::err(msg);` → `return Self::tool_err(msg);`
- `Self::wrap(res)` → `Self::wrap_result(res)`
- 手工边角：`futu_cancel_all_order` 早 return / `futu_unlock_trade` match 结构

### Phase C3: 删除 v1.4.42 hack

- 删 `Self::err(msg) -> String`（内嵌 `"isError": true` JSON content marker）
- 删 `Self::wrap<E>(res) -> String`（老 helper）
- 替换 3 处 internal 调用：`client_or_err` + `futu_unlock_trade` match 分支

**client 双信号兼容**：
- **Top-level** `CallToolResult.is_error = Some(true)` ← 新加（MCP spec 正道）
- **Content JSON** 仍含 `{"error": msg, "status": "error"}`（老客户端兼容）

## 🛡️ Code Review Cycle（3 轮防回归）

用户明确要求 review-first shipping，不允许 "ship + 发现问题 + 再 hotfix" 循环。

### 1st review（commit 4f94beb6f）

12 items 全修：
- HIGH-1: `scope_for_tool` 漏注册 2 新 tools → runtime "unknown MCP tool"
- HIGH-2: `futu_unlock_trade` need_otp 返 `Ok(ok:false)` 矛盾
- MED-1: `client_or_err` error 格式非 JSON
- MED-2: scope rejection `Ok(rej)` 应 `Err(rej)`（55 site 批量改）
- MED-3: `UnsubAccPushReq` schema description 与行为不符
- MED-4: 删 dead `tool_ok` helper
- MED-5: `DefaultHasher` stability 注释
- LOW-1: pwd_md5 首 8 字符注释更准
- LOW-2: UnlockTrade partial-success 不 cache
- LOW-3: rmcp Peer PartialEq 注释加 version
- LOW-4: `push_subscriber_count` `#[cfg_attr(not(test), allow(dead_code))]`
- LOW-5: Legacy-mode 多租 push 订阅信息暴露说明

### 2nd review（commit 92073cc00）

4 MED-NEW 全修 + 8 个 new tests 覆盖：
- MED-NEW-1: unlock_trade Err body 加 `error` field 让 audit log 正确记 failure
- MED-NEW-2: `into_err_json` JSON 加 `status: error` 对齐其他 error shape
- MED-NEW-3: `push_subscribers_summary` 跨租户泄漏 → 新 pure fn
  `subscriber_visible_to_caller` + caller scope filter
- MED-NEW-4: 8 个 new tests 覆盖 pure function 行为

### 3rd review（commit cc823ad30）

1 LOW 修：
- LOW-3RD-1: summary 返 `acc_ids` 按 caller allowed_acc_ids 求交集
  （caller=[100] 看到 sub=[100,999] 时不返 999）

## 🛡️ CLAUDE.md 新沉淀

### 坑 #37（v1.4.58 Phase A 惨案）

**新 MCP `#[tool]` handler 强制 audit checklist** — 每次加新 tool 必须同步 4 处：
1. `tools.rs` handler + request struct
2. `guard.rs::scope_for_tool` match arm
3. `guard.rs::all_known_tools_have_scopes` test `known` list
4. 至少 1 个 integration test

**触发**：Phase A 漏改 (2)+(3)，handler 代码 unit test 全绿 / clippy 零 warning /
fmt clean — 但 runtime 调用返 "unknown MCP tool"。code review 才抓出来。

### 版本号分配纪律（v1.4.57 沉淀）

v1.5 保留给大里程碑，v1.4.x 继续修补 + 小 feature。规则：
- LoC 数量不触发 v1.5
- "用户可感知价值" + "吃掉一整个 roadmap tier" 才是
- v1.4.58 虽有 ~1800 LoC 但不升 v1.5（3 个 Phase 合一次发，不是 tier 级里程碑）

## 🧪 Tests (+11 总 59 MCP + 203 gateway + others)

- MCP: 50 → 59（+8 2nd review + 1 3rd review）
  - 3 guard.rs tests (into_err_json shape / scope_for_tool registration)
  - 5 state.rs tests (subscriber_visible_to_caller 5 边界)
  - 1 summary empty state baseline
- Gateway: 203+ 全绿（含 unlock_trade idempotency 新增）
- cargo clippy --workspace --all-targets -D warnings: 零 warning
- cargo fmt --check: clean
- cargo build --release: OK

## ℹ️ 向后兼容

**破坏性变化**：MCP tool error 路径现在 set `CallToolResult.is_error = Some(true)`。
依赖 content JSON 的 `"isError": true` 字符串 marker 的客户端**需要迁移**到读
top-level is_error 字段。

**不破坏**：
- REST / gRPC / CLI API：无变化
- content JSON 仍含 `{"error": msg, "status": "error"}`（兼容老客户端）
- 无 proto / schema 变化
- Phase A/B 新增 tool + flag，老调用不变

## 🧪 Real-machine verify 路径

```bash
# Phase A: push 订阅管理
# MCP client 先 sub_acc_push 拿 session_id, 然后 unsub
# futu_push_subscriber_info 查看当前订阅

# Phase B: UnlockTrade idempotency
futucli unlock-trade --acc-ids 12345 --idempotency-key retry-1
futucli unlock-trade --acc-ids 12345 --idempotency-key retry-1  # 应返 cached

# Phase C: isError 行为
# MCP client 触发 scope reject（无 API key 调 trade tool）→ 应看到 top-level
# is_error=true（不再只有 content JSON isError marker）
```

## [1.4.57] - 2026-04-22 🔴 外部 v1.4.56 验收报告修复（7 bugs + 7 UX，跨多维补齐）

**必须升级**（多类场景）：
- 所有用 `US.xxx` / `HK.xxx` 等 market-prefixed code 下单的用户（#1 + #2 P0）
- 所有 moomoo 账户查"今日成交"的用户（#3 P2 返"unknown error"）
- 需要 SMS 验证但 stdin 输入不便（Telegram / IM 中继，agent / CI 自动化）→ 新 `--verify-code` flag

## 🔴 Fixed (P0)

### #1 + #2 market prefix 未剥离导致下游识别全错（同根因）

- **症状**：`US.MSFT` 下单 backend 拒（用 `MSFT` 无前缀反而 OK）；`US.MNQ2606`
  被识别为股票 `security_type=1 exchange_str=US`，backend 返 110005
- **根因**：v1.4.56 `derive_sec_market` 已用 prefix 推导 sec_market=2，但下游
  `is_option_code` / `is_futures_code` / `parse_option_dte` /
  `derive_security_type` cache key 仍用**含 prefix** 的 code 做 pattern 检查
  → `is_futures_code("US.MNQ2606")` 失败（`.` 不是 alphanumeric）→ fallback 到
  COMMON
- **修法**：在 4 个下游 fn 入口统一 `let code = strip_market_prefix(code).as_str()`。
  cache key 构造也用 bare code（与 cache populate 格式 `"{qot_market}_{item.code}"`
  一致）
- **顺带修 `is_futures_code`**：支持 alphanumeric ticker（CME 货币 `6E`、利率
  `SR3`、股指 `M2K`、加密 `BTC` 等 CME Group 命名不规范的合约）
- **7 个新 unit tests** 回归验证 prefix idempotency

## 🟡 Fixed (P1/P2)

### #3 GetOrderFillListHandler per-broker routing（moomoo -102 "unknown error"）

- **症状**：moomoo 账户 `/api/order-fills` 返 "unknown error"，daemon log
  `cmd_id=4710 code=-102 "CONN can not find command service"`。同事 3/3 moomoo
  账号复现，1/1 futunn 正常
- **根因**：CMD 4710 只在 broker TCP channel 可用。futunn 账户 cipher 为空
  走 Platform 也 OK；moomoo 账户 cipher 从 cache 读但仍走 Platform channel →
  -102
- **修法**：`GetOrderFillListHandler` 加 `brokers` 字段 +
  `resolve_trade_backend_for_acc` 路由（对齐 `GetHistoryOrderFillListHandler`
  v1.4.38 的模式）

### #4 `get_global_state() → market_hk_future: 0` 修

- **症状**：v1.4.55 改成 5 市场并发拉后，US/SG/JP future 都正常，唯独 HK future
  始终返 0 （C++ OpenD 同时刻返 `NIGHT_OPEN`）
- **根因**：`quote_mkt_to_futu_qot_market(HKFuture)` 返 `2`（`QotMarket_HK_Future`
  已废弃），backend 对 reserved[0]=2 不返 HK 期货数据。US/SG/JP future 返 `0`
  （unknown）反而 work —— backend 对 reserved=0 返全市场 snapshot
- **修法**：
  1. `HKFuture` 返值改 `2` → `0`（对齐 US/SG/JP）
  2. `register_markets` 加 HKFuture/USFuture/SGFuture/JPFuture 订阅（CMD 6822）
  3. `pull_all_market_status` 加 DEBUG log 打受到的 market_ids 方便诊断

### #5 MAX_SMS_RETRIES 自动轮换 device_id 触发限流

- **症状**：用户 SMS 输错一次，daemon 自动删 device_id 生新的重试。第 3 次被
  服务端限流（"5 次不同设备 30 秒内"硬阈值），后续正确码也被 code=1"系统繁忙"拒
- **根因**：v1.4.17 加的 `MAX_SMS_RETRIES=2` 自动轮换，初衷是减少"验证码输错
  用户再试一次"的 friction，但实际触发限流比"不重试"更糟（2026-04-22 外部
  用户 Telegram SMS 中继场景实锤）
- **修法**：`MAX_SMS_RETRIES: u8 = 0`，禁用自动轮换。SMS 输错直接返错给用户
  手动重试。loop 结构简化为直接调用（未来恢复 restore 用 `reset_device_state` +
  `read_or_generate_device_id`）

### #7 verify_device_code 日志文案误报 code=21

- **症状**：设备验证失败时，daemon 日志写 "code=21 通常是验证码错"，但服务端
  实际返 `code=1 "系统繁忙"`。排查 #5 时误导走弯路
- **修法**：按实际 code (1/11/15/21/23) 精准给 hint

## ✨ UX 改进（7 条）

### UX-01 / UX-03 backend_code 原始码透传 + -102 不包装

- `format_backend_trd_error` 加 hint suffix：-102 (channel 不支持) / -20011
  (token 2FA 需启用) / 110005 (合约字段不一致，看 daemon log 核对)
- 5 处 `"unknown error"` 的 fallback 改为空串 → `format_backend_trd_error`
  输出 `"OP: 错误 (backend_code=N)"` 清晰格式

### UX-04 ⭐ `--verify-code <CODE>` CLI flag

外部用户紧急需求 —— SMS 验证码通过 Telegram/IM 中继转发，60 秒失效来不及用
stdin 输入。新 flag 让 code 可直接传入，跳过 stdin prompt。

```bash
# 典型用法（agent / CI / 远程中继）
futu-opend --setup-only --login-account X --login-pwd Y --verify-code 123456
```

callback 一次性消费，失败会 fallback 到 stdin（非 tty 则 fail fast 避免毒化
device_id）。

### UX-05 `ret_type=15` 文案改善

加 v1.4.57 新 case (2)："SMS 超时多次重试触发服务端限流 + device_id 锁"。给出
正确恢复步骤：等 3-5 分钟 → 手机 App 登录清状态 → 用 `--verify-code` 避免
stdin 延迟。

### UX-08 Keychain 读取 INFO 进度

macOS 首次解锁 Keychain 可能 ~10s 无 log，用户以为 daemon 挂。加 INFO
`"loading login password from OS keychain (may take ~10s on first unlock)"`。

### UX-09 期货合约过期 WARN

`check_futures_code_expiry` 按 YYMM 与当前 HKT 年月比较，过期合约早 WARN
提示（不阻断，因为可能是异常场景需要下过期合约）。

## 🔧 Deferred（safety 决策）

- **#6 US 期货 `exchange_code=11`（高度怀疑）**：v1.4.56 报告疑 backend 对
  `security_type=4 + exchange_code=11 + exchange_str=CME` 组合不接受。v1.4.57
  #1+#2 修好后 exchange_str 会正确走 "CME"，backend 可能 lenient 接受 11。
  待 coworker 真机 re-verify，若仍 110005 再深挖
- **UX-02 `trd_market_auth_list` 预校验**：`check_trd_market_authorized` helper
  写好但**不 wire 进 PlaceOrder** —— `trd_market_auth_list` 对 `trd_market=5
  (Futures)` 语义不明确（HK 账户 auth_list 可能只有 [1,2,4]，但能通过
  `OpenFutureTradeContext` 下期货 trd_market=5）。误 block 期货单代价 > "backend
  拒"。v1.4.58+ 确认 auth_list 语义后再启用
- **UX-06 / UX-07 / UX-10 docs**：文档补充批到 v1.4.58+

## 🧪 Unit tests (+7 新 prefix-idempotency，总 203+)

- `is_option_code_accepts_market_prefix`
- `is_futures_code_accepts_market_prefix`
- `parse_option_dte_accepts_market_prefix`
- `is_hk_index_option_code_accepts_market_prefix`
- `derive_security_type_accepts_market_prefix_for_futures`
- `v1_4_57_end_to_end_us_futures_with_prefix`（SDK 发 sec_market=1 HK + code="US.MNQ2606" → 端到端 sec_market=2, security_type=4, exchange_str=CME）
- `v1_4_57_end_to_end_hk_futures_with_prefix_regression`

## ℹ️ 向后兼容

- 无 breaking API
- `--verify-code` 新 flag，未使用时行为不变
- `is_futures_code` 扩展 alphanumeric ticker 支持是**严格更宽松**（不 reject
  现有），不存在 US stock ticker 以"字母+数字"开头且 YYMM 式的 regression 场景

## 真机 verify 路径（coworker re-try）

```bash
# P0 prefix 修
futucli place-order --market US --code US.MSFT --side Buy --qty 1 --price <bid> --env real --confirm
futucli place-order --market US --code US.MNQ2606 --side Buy --qty 1 --price <bid> --env real --confirm

# P2 moomoo order-fills
curl -X POST .../api/order-fills -d '{"c2s":{"header":{"acc_id":<moomoo_acc>,"trd_env":1}}}'

# P2 HK futures market state
futucli global-state  # 预期 market_hk_future != 0

# UX-04 --verify-code
futu-opend --setup-only --login-account X --login-pwd Y --verify-code 123456
```

## [1.4.56] - 2026-04-21 🔴 US 期货路由补修 + 系统性根因沉淀（同类问题第 3 版）

**必须升级**（所有下 US 期货 / 跨市场期货的用户）。v1.4.54/55 修的都是 HK 期货路径，
**US 期货 MNQ2606 同样 bug 第三次复发** —— 同事实盘反馈：HK 期货 v1.4.55 成交 ✓，
US MNQ2606 仍 `exchange_str=HKFE` 被 backend 拒。

## 🔴 Fixed (P0)

### US 期货 exchange_str 仍路由 HKFE（v1.4.54/55 系统性 gap）

- **症状**：v1.4.55 后 `place_order(code='US.MNQ2606', ...)` 仍 daemon log
  `exchange_str=HKFE security_type=4` → backend 拒单。HK 期货 TCH2604/HTI2604
  成功，但 US 期货全部失败
- **系统性根因**：3 个版本同类 bug 的共同根因 **终于查清**：
  - v1.4.54 修了 `derive_security_type`（只看 `trd_market=5` → FUTURES）
  - v1.4.55 修了 `derive_exchange_str`（只看 `sec_market` → HKFE/CME）
  - **都信任了 Python SDK 传的 `sec_market`**，但 Python SDK 的
    `OpenFutureTradeContext` 是 HK 账户类型，**对所有期货（HK/US/SG/JP）都硬发
    `sec_market=1 (HK)`**，不管 symbol 本身是什么市场。v1.4.54/55 的每层修都
    "HK 对 / US 错"，因为 SDK 的 sec_market 根本就错了
- **正确修法**（v1.4.56 systemic）：**在 `derive_sec_market` 单点**做 code-first
  判断，SDK 的 sec_market 只是最后 fallback：
  - **Layer 1 `sec_market_from_code_prefix`**：`code.starts_with("US.")` →
    sec_market=2 (US)；`HK.` → 1；`SG.` → 41；`JP.` → 51；`SH.`/`SZ.`/`CN.` → 31/32；
    `AU.` → 61；`MY.` → 71；`CA.` → 81
  - **Layer 2 `futures_ticker_to_sec_market`**：无 prefix 时按 ticker 识别
    CME/CBOT/NYMEX/COMEX/CBOE 产品 (NQ/MNQ/ES/MES/RTY/6E/GE/BTC/CL/NG/GC/SI/
    ZS/ZN/VX 等) → US；HKEX 指数 (HSI/HHI/HTI/MHI/MCH) → HK
  - **Layer 3**：SDK 显式传的非 0 值（v1.4.41 行为）
  - **Layer 4**：trd_market fallback（v1.4.41 行为）
- **单点修复的好处**：下游所有依赖 `sec_market` 的字段（`exchange_code` /
  `exchange_str` / `security_type` cache key）**全部自动受益**。避免未来每个
  下游 fn 各自写 code-based 覆盖逻辑重复犯错
- **顺带修 `is_futures_code` + `extract_futures_ticker_prefix`**：之前不支持
  ticker 含数字（`6E2606` / `M2K2606` / `SR32606`）被误拒，v1.4.56 改为支持
  alphanumeric ticker（至少 1 字母），extract 剥尾部 4 位 YYMM（更稳健）

## 🧭 纪律沉淀：CLAUDE.md 坑 #36 — SDK 假设不可靠，code-first 原则

新坑（**同类问题 3 版教训**）：**不要相信 SDK 传的 market metadata**。SDK 可能
基于账户类型硬编码某字段（如 `OpenFutureTradeContext` sec_market=1）。**code
prefix/pattern 是用户意图的真相**，应优先于 SDK metadata。

这个原则适用于：
- 期货市场识别（本 bug）
- 期权市场识别（类似风险）
- 任何 "多市场账户 + 跨市场订单" 场景

## 🧪 Unit tests (+8 新，总 196+)

- `sec_market_from_code_prefix_recognizes_all_prefixes`（10 个 market prefix）
- `extract_futures_ticker_prefix_handles_all_formats`（YYMM + main + 数字 ticker）
- `futures_ticker_to_sec_market_us_tickers_return_us`（MNQ/NQ/ES/CL/GC/SI/VX/BTC 等）
- `futures_ticker_to_sec_market_hk_tickers_return_hk`（HSI/HHI/HTI/MHI/MCH）
- `futures_ticker_to_sec_market_unknown_returns_none`（HK 个股期货 / 正股 / 期权）
- `derive_sec_market_us_futures_with_prefix_returns_us`（coworker bug core case）
- `derive_sec_market_us_futures_no_prefix_via_ticker`（ticker 识别）
- `derive_sec_market_hk_futures_with_prefix_still_hk`（回归）
- `derive_sec_market_hk_futures_no_prefix_via_ticker_or_fallback`（指数 ticker + 个股 fallback）
- `derive_sec_market_regression_non_futures_paths`（正股 / CN A 股 回归）
- `derive_exchange_str_us_futures_full_pipeline`（端到端 MNQ/CL/GC/ZN/VX → CME/NYMEX/COMEX/CBOT/CBOE）
- `derive_exchange_str_hk_futures_regression`（HK 期货回归）

## ℹ️ 向后兼容

- 无 breaking API
- 原有 v1.4.41-55 的 sec_market 推导顺序保留为 Layer 3/4（fallback）
- 所有现有 call site 自动受益（单点修复）

## 真机 verify 路径（同事 re-try MNQ2606）

```bash
futucli place-order --market US --code MNQ2606 --side Buy \
  --qty 1 --price <current-bid> --env real --confirm
# 预期 daemon log: sec_market=2 exchange_str=CME security_type=4 + 订单成功
```

## [1.4.55] - 2026-04-21 🔴 期货 exchange_str 补修（v1.4.54 漏修 + 期货市场状态 multi-pull）

**必须升级**（所有下 HK 期货 / US 期货的用户 —— TCH2604 / HTI2604 / HSI2604 /
HHI2604 / MNQ2606 / NQ2606 / ES2606 / CL2606 / GC2606 等所有期货合约）。
v1.4.54 只修了 `security_type`（4=FUTURES），**没修 `exchange_str`** —— backend
仍然收到 `security_type=4 exchange_str=SEHK` 矛盾信号 → 110005 拒单。

## 🔴 Fixed (P0)

### 期货 exchange_str 路由修复（同事 v1.4.54 实盘反馈 — TCH2604 + HTI2604 + MNQ2606 仍 110005）

- **症状**：v1.4.54 后 `place_order(code='HK.HTI2604'|'HK.TCH2604'|'US.MNQ2606')`
  仍然 backend 返 `110005`，daemon log 显示 `security_type=4 exchange_str=SEHK`
- **根因**：v1.4.54 只修了 4 层判定的第 1 层（`derive_security_type`），**漏了
  第 2 层** `sec_market_to_exchange_str` —— 对所有 HK 账户返 "SEHK"，对所有 US
  账户返 "US"。backend 对期货 `security_type=4` 但 `exchange_str="SEHK"`（股票交
  易所）视为矛盾 → 110005 拒单
- **C++ 对比**：`_NNProto_Trd_Comm.cpp:546 GetStockExchangeByMktID` 按 `NN_QuoteMktID`
  范围精确返 "HKFE" / "NYMEX" / "COMEX" / "CBOT" / "CME" / "CBOE" / "SGX" / "OSE"
- **修法**：新 helper `derive_exchange_str(sec_market, security_type, code)`：
  - **HK + FUTURES** → "HKFE"（HK 所有期货：股票期货 / 指数期货 / 汇率期货 / 商品期货）
  - **US + FUTURES** → code-pattern 分 CME/NYMEX/COMEX/CBOT/CBOE：
    - CME（股指/外汇/利率/加密）：NQ/MNQ/ES/MES/RTY/M2K/6E/6J/GE/BTC/...
    - NYMEX（能源）：CL/MCL/NG/HO/RB/BZ
    - COMEX（金属）：GC/MGC/SI/SIL/HG/PL/PA
    - CBOT（谷物/国债/YM）：ZS/ZC/ZW/ZT/ZF/ZN/ZB/YM/MYM
    - CBOE（波动率）：VX/VXM
    - 未知 US 期货 → 默认 "CME"（最宽容 fallback）
  - **HK 指数期权** (HSI/HHI/HTI/MHI/MCH) → "HKFE"（对齐 C++ line 562）
  - **HK 股票期权** → "SEHK"（对齐 C++ line 558）
  - **SG 期货** → "SGX" / **JP 期货** → "OSE"
- **影响面**：PlaceOrder + GetMaxTrdQtys 2 个 call site 同步更新

## 🟡 Fixed (P1)

### `get_global_state()` → `market_hkfuture: NONE` 修（同事 v1.4.54 同报告）

- **症状**：`get_global_state()` 始终返 `market_hkfuture: NONE`，即使 HK 期货
  夜盘交易中
- **根因**：`pull_all_market_status` 只发 1 个 CMD 6823 with `reserved=HK`，
  backend 对这个 reserved 的 snapshot 响应里**不含期货市场** MarketID
  （HK stocks / 港股通 / US / CN / Bond 等都在，但 HK/US/SG/JP 期货 MarketID
  缺席）
- **修法**：`pull_all_market_status` 改 **5 个 CMD 6823 并发拉**（HK / HKFuture
  / USFuture / SGFuture / JPFuture），合并结果按 `market_id` 去重
- **代价**：5 个并发请求 vs 1 个（~5x backend load），但 CMD 6823 是轻量
  snapshot 实测 ~10-20ms，合计 <100ms 仍在可接受范围（global_state 不是高频 API）

## 🧭 纪律沉淀 CLAUDE.md 坑 #35 补注释

v1.4.54 沉淀的坑 #35 "C++ 数据驱动 vs Rust 启发式" 在 3 个 pattern 函数顶部
加 fallback 注释：
- `is_option_code` — 优先 cache `sec_type == Drvt(8)`
- `is_futures_code` — 优先 cache `sec_type == Future(10)`
- `parse_option_dte` — 优先 cache `strike_time` / `expiry`

## 🔧 内部重构（Phase 1 债清理）

- `ModifyOrderHandler` 加 `static_cache: Arc<StaticDataCache>` 字段（`#[allow(dead_code)]`），
  为 v1.5 Order Idempotency + cache-first security_type 校验预埋
- `GetMaxTrdQtysHandler` 的 `let _ = &self.static_cache;` 改为真用（调用
  `derive_security_type` + `derive_exchange_str` 路径对齐 PlaceOrder）

## 🧪 Unit tests (+11 新，总 195+)

- `derive_exchange_str` × 10：hk_futures / us_futures_cme / us_futures_nymex /
  us_futures_comex / us_futures_cbot / us_futures_cboe / sg_jp_futures /
  hk_options_stock_vs_index / hk_us_stocks_regression / unknown_defaults_cme
- `is_hk_index_option_code_examples`（HSI/HHI/HTI 识别）

## ℹ️ 向后兼容

- 无 breaking API（`sec_market_to_exchange_str` 保留，只是新代码不用）
- 原 `sec_market_to_qot_market` 返 FTAPI QotMarket（1/11/...）behavior 不变
- `pull_all_market_status` 签名不变，仅内部实装改 multi-pull

## 真机 verify 路径（同事 re-try）

```bash
# HK 期货
futucli place-order --market HK --code TCH2604 --side Sell --qty 1 \
  --price <current-bid> --env real --confirm
futucli place-order --market HK --code HTI2604 --side Buy --qty 1 \
  --price <current-bid> --env real --confirm

# US 期货
futucli place-order --market US --code MNQ2606 --side Buy --qty 1 \
  --price <current-bid> --env real --confirm

# global state
futucli global-state  # 预期 market_hkfuture 不再 NONE
# 预期 daemon log: security_type=4 exchange_str=HKFE(HK) / CME(US) + 订单成功
```

## [1.4.54] - 2026-04-21 🔴 HK 期货下单 P0 修（cache-first 对齐 C++）

**必须升级**（任何用通用 HK 账户下 HK 期货的用户 —— 包括 TCH2604 腾讯控股期货 /
HSI2604 恒指期货 / HHI2604 国企期货 / MHI2604 小恒指等所有 HK 个股/指数期货）。

## 🔴 Fixed (P0)

### HK 期货 TCH2604 下单被误路由为股票 (同事实盘反馈)

- **症状**：`place-order --market HK --code TCH2604 ...` backend 返 `110005` 拒单，
  daemon log 显示 `security_type=1 exchange_str=SEHK`（应为 `security_type=4`）
- **根因**：`derive_security_type` 只在 `trd_market == 5 (HK Futures 主市场)`
  时返 FUTURES。用户通用 HK 账户 `trd_market=1` 下期货 → fallthrough 返 COMMON
  → backend 业务错误码 110005（期货合约用股票字段）
- **C++ 对比**：`NNProto_Trd_Comm.cpp:383` + `NN_QuoteSecurityType_Future` —
  C++ **不用 symbol pattern**，查 stock_list cache 的 `stSecInfo.enType`，
  数据驱动
- **修法（cache-first + pattern fallback）**：
  - `PlaceOrderHandler` 加 `static_cache: Arc<StaticDataCache>` 字段
  - `derive_security_type(code, trd_market, &static_cache, qot_market)` 新 signature
  - **Layer 1 `is_option_code`** regex（对齐 C++ IsOptionCode）
  - **Layer 2 cache-first**（对齐 C++ 数据驱动）：查 `sec_type` →
    `Future(10)` 返 FUTURES / `Drvt(8)` 返 OPTION / `Eqty(3)` 返 COMMON
  - **Layer 3 `is_futures_code` pattern fallback**：cache miss 时兜底，覆盖
    `<TICKER><YYMM>` / `<TICKER>main` 格式
- **影响面**：HK 个股期货 / HK 指数期货 / US 期货（NQ/ES/CL/GC）/ 主连合约

## 🧭 纪律沉淀 CLAUDE.md 坑 #35

"C++ 数据驱动（cache 查 enType），Rust 启发式（code pattern）会累积差距"：
- 每次用 code pattern 判类型（期货 / 期权 / 股票 / 债券 / 外汇）都是技术债信号
- 注释必须明确 "fallback heuristic, cache-first better"
- **loud failure 保证**：pattern 误判 = backend 拒单（用户立即反馈），不是
  silent wrong data

## 🧪 Unit tests (+12 新，总 188+)

- `is_futures_code` × 5: HK 月合约 / US 月合约 / main 合约 / 拒 stock / 拒 option
- `derive_security_type` × 7:
  - `cache_first_future`: sec_type=10 → FUTURES
  - `cache_first_option`: sec_type=8 → OPTION（边界：WEIRD_OPT 非 OCC 格式）
  - `cache_first_stock`: sec_type=3 → COMMON
  - `cache_miss_fallback`: cache 空时走 pattern + 原 logic
  - `futures_any_trd_market`: TCH2604 在 trd_market=1/4/2/10 全部 → 4
  - 2 个原 test 用 `dst_fallback` helper 适配新 signature

## ℹ️ 向后兼容

- 无 breaking API（signature 改动是内部函数，外部 REST/MCP 无感知）
- 原 `trd_market=5` 路径保留
- Cache miss 时 pattern fallback 行为 = v1.4.53 行为 + 期货 pattern 识别

## 真机 verify 路径（同事 re-try）

```bash
futucli place-order --market HK --code TCH2604 --side Sell \
  --qty 1 --price <current-bid> --env real --confirm
# 预期：daemon log security_type=4 (不是 1) + 订单成功 (不是 110005)
```

## [1.4.53] - 2026-04-21 🟡 BUG-6 真修 + 条件单 + OCC 转换 + 坑 34

**推荐升级**（sim 账户用户 + 量化用户 + 期权用户）。M 档 scope：v1.4.52 defer
遗留 BUG-6 真修 + 3 个实质 feature（条件单 / Greeks audit / OCC 转换）+ 流程
沉淀。

## 🔴 Fixed (v1.4.52 遗留)

### BUG-6 真修: Sim 账户 funds/positions cache populate

- **v1.4.52 修法方向错**：v1.4.52 用 "Platform + CMD 3020 + real proto" 给 sim
  账户 → backend 返 `result_code=3 "unknown"`（不认）
- **C++ 真路径深挖**：
  - `NNBase_Define_ProtoCmd.h:23` `SimTrdCmdOffset = 10000`
  - Sim 账户用 **CMD 14704**（sim fund）+ **CMD 14705**（sim positions）
  - 专属 proto `sim_user_asset_interface::CashInfoReq` / `PstnInfoReq`
  - C++ `NNProto_Trd_Acc.cpp:780-811` Real 走 odr_sys，Sim 走 sim 专属 ——
    完全独立的两条路径
- **v1.4.53 真修**：
  - 新增 `proto-internal/sim_user_asset_interface.proto`
  - 重写 `query_funds_sim` / `query_positions_sim` 用 sim CMD + proto
  - `query_positions_sim` 加 `trd_market` 参数（backend 实测 market 必填）
  - A2 附带修：`query_account_info` result_code≠0 现返 Err（不再 silent Ok）
- **真机 PASSED**：sim acc 28701 HK `/api/funds` 返 `cash=703575.97`（真实数据）

## 🟡 Fixed (v1.4.52 CI 问题)

### docker.yml GHCR image public endpoint 路径修

- v1.4.52 加的 make-public step 用 `users/<owner>/packages/...` 返 404
- v1.4.53 改成 `user/packages/container/...`（authenticated user context）
- **历史 image v1.4.5x 需一次性 GHCR web UI 手工设 public**，之后继承

## ✨ 新增 Features

### F1 条件单 Stop Loss / Stop Limit / Trailing Stop（长期 backlog 清）

- 扩展 `OrderType` enum 10 新 variant（Stop/StopLimit/MIT/LIT/TrailingStop/
  TrailingStopLimit/TWAP_*/VWAP_*）
- `map_order_type` 完整 FTAPI→backend 精确映射（之前 fallthrough 错）
- `PlaceOrderParams` 加 4 新字段：`aux_price` / `trail_type` / `trail_value` /
  `trail_spread`（透传到 FTAPI `Trd_PlaceOrder.C2S.auxPrice/trail*`）
- CLI `futucli place-order` 加 `--stop-price` / `--trail-type` / `--trail-value` /
  `--trail-spread`
- MCP tool `futu_place_order` schema 加同 4 字段
- REST layer: 无需新代码（camelCase normalize 自动支持）

### F5 OCC ↔ Futu Option Symbol bidirectional 转换

- 新增 `futu_to_occ(code)` helper（对称 v1.4.41 `normalize_option_symbol_occ_to_futu`）
- 规则：Futu compact `AAPL261017C215000` → OCC `AAPL  261017C00215000`
- 6 新单测（basic/put/short_symbol/non_option/roundtrip）
- public surface（MCP tool / CLI）defer v1.4.54（按需）

### F2 Greeks 完整透传 audit (已 done，无新代码)

- Snapshot: CMD 20106 on-demand 已透传 delta/gamma/theta/rho/vega/IV/OI
- OptionChain: CMD 6312 基础 greeks 已透传
- Position: proto 无 greeks 字段 **by-design**（greeks 是 per-symbol market
  data，客户端 snapshot 查）

## 🧭 方法论沉淀

### CLAUDE.md 坑 #34: Agent 调研结论 ≠ 真机实装正确性

v1.4.52 BUG-6 实锤：agent 看 C++ 顶层 `APIServer_Trd_GetFunds.cpp::FillFunds`
说 "sim/real 共用 CMD 3020"，实际底层 `NNProto_Trd_Acc.cpp` 有 Real/Sim 分支用
**完全不同的 CMD + proto**。**Agent 看顶层，底层有结构性差异**。

沉淀 4 条纪律：
1. Agent 方案写成 **"假设 X"**（不是 "fix"）
2. 实装后**第一 verify 必须真机**
3. 真机 failure 不 rollback，写 verify report + 下版修正
4. CHANGELOG 诚实写"半失败"/"方向错"，不粉饰

Agent prompt template 升级：强制 3 候选 + 关键假设列表 + falsify 路径。

## 🔵 Audit

### py-futu-api vs Rust daemon 覆盖矩阵 (~95%)

`essentials/2026-04-21-1325-py-futu-api-coverage-audit.md` 归档：
- 行情 32/35 全覆盖，3 partial，2 未 audit
- 交易 15/16 全覆盖，1 未 audit（query_quota）
- 推送 7/8 全覆盖
- 缺口清单：`query_subscription` / `get_quote_history_delay_statistics` /
  `query_stock_score` / Stock Screener → v1.4.54+ scope

## ℹ️ 向后兼容

- 无 breaking API
- PlaceOrderParams 4 新字段全 optional（旧 client 不感知）
- OrderType enum 新 variant 不影响旧 variant
- CLI alias 向后兼容

## ⏭ v1.4.54+ backlog

- Public `futu_to_occ` 暴露到 MCP/CLI（按需）
- cargo-audit CVE 定期 maintenance（本版 fetch 超时 skip）
- stock screener handler 接入（FTCmdStockScreener.proto 已有但 daemon 未接）
- query_subscription REST route 补全

## 真机验证状态

- ✅ BUG-6 真机 PASSED（sim acc 28701 HK → cash=703575.97 非 null）
- ✅ 条件单：单测 + schema 验证，真机下条件单待开市触发
- ✅ OCC 双向转换：6 单测全绿 + roundtrip

## [1.4.52] - 2026-04-21 🟡 v1.4.51 defer 清空 + 坑 audit + CI 护栏扩展

**可选升级**。v1.4.51 ship 的 P0 + 6 项 bug 修复已覆盖最关键场景。本版是外部
验收 defer 项的**全量交付**（3 项）+ 方法论沉淀 + 流程改进。

## 🟡 Fixed (v1.4.51 defer 3 项)

### BUG-5 P2: `/api/order-fills` moomoo "unknown error" (CMD 2211)

- **根因**：`handlers/trd.rs:507` `GetOrderFillListHandler` 发 backend 请求时
  `cipher: Some(vec![])` 填空。moomoo 账户（firm=2/5）需要真 cipher 通过 backend
  签名校验
- **C++ 对齐**：`NNData_Trd_AccList::GetAccCipher` 是**per-account 全局 cache**（和
  TCP category 解耦）。GetHistoryOrderList / GetHistoryOrderFillList / MaxBuySell
  早已读 cache 正常工作（外部报告 "history-order-fills 所有 firm 正常" 的原因）
- **修法**：`self.cache.get_cipher(acc_id).unwrap_or_default()` 读 per-account cipher
  传给 backend。firm=1 futunn 仍接受空 cipher（行为不变），firm=2/5 moomoo 已 unlock
  后获得 cipher 传进去（FIXED）

### BUG-6 P2: Sim 账户 funds/positions 返 null

- **根因**：`bridge.rs dispatch_trade_data_queries` 硬过滤 `trd_env == 1`，sim 账户
  进 cache 但没触发 CMD 3020 查询
- **C++ 对齐**：`APIServer_Trd_GetFunds.cpp::FillFunds` 对 sim/real 共协议，CMD 3020
  两边都用
- **修法**：去 filter，real 走 broker 通道，sim 走 Platform fallback。函数签名加
  `backend: SharedBackend` 参数，reconnect path 把 `shared_backend.store` 提前
  保证 dispatch 看到新 conn
- **真机验证必需**：backend 对 sim 账户 CMD 3020 响应格式是否完全同 real 需 confirm

### BUG-9 P3: CLI 9 命令 REST/MCP 风格 alias

- **澄清**：CLI `--help` 输出和 clap 接受一致；外部报告是按 REST/MCP 命名习惯
  调 CLI 踩坑（CLI 用位置参数或不同 flag 名）
- **修法**：7 位置参数 + 命名 alias（clap `conflicts_with`）：
  - `option-chain` / `option-expiration-date`: `<OWNER>` / `--owner` (+ `--code` alias)
  - `suspend` / `margin-ratio`: `<SYMBOLS>` / `--code` / `--symbols`
  - `user-security`: `<GROUP>` / `--group`
  - `plate-stocks`: `<PLATE>` / `--plate`
  - `acc-cash-flow`: `<ACC_ID>` / `--acc-id`
- 2 命名 alias: `plate-list --set visible_alias=plate-type`、`daemon-status
  --rest-port` 自动转 `http://127.0.0.1:<port>`
- 向后兼容（位置参数依旧 work）

## 🟢 Improved (流程 / UX)

### `ship.sh` B 阶段失败 rollback 策略

- **背景**：v1.4.50 首次 dogfood 验证过阶段 A/B 全流程，但 B 阶段失败时只能
  手工 `git reset` + `git tag -d` + `git push origin :refs/tags/X` 逐步清理
- **修法**：加 `rollback_and_exit()` helper 交互式确认，触发点：B4 tag/push 失败 /
  B5 workflow failure / B6 gh release create 失败。幂等（缺失 tag/commit 不报错）

### `ret_type=15` UX hint 加 cause #0

- **背景**：外部 v1.4.48 验收报告"关键发现（非 bug）"—— 同账户已有 C++ OpenD 跑
  时 Rust daemon 登录被拒返 `ret_type=15`
- **修法**：`main.rs::hint_15` 加 cause (0) "another Futu OpenD 已运行同账户"
  建议用户 `lsof -i :11111` + `ps aux | grep -i opend` 排查，停其他 OpenD 后重试

## 🔵 CI 护栏扩展

### `docker.yml` GHCR image 自动 public visibility

- **背景**：v1.4.50 验证时 `gh api packages` 403 根因 —— GHCR 默认 private，
  用户 `docker pull` 前需要手动登录
- **修法**：merge job 加 PATCH step，tag push 时自动设 public。`continue-on-error`
  不阻塞 workflow（首次可能需要 admin 授权）

### `proto_diff_check.sh` whitelist 机制

- 新增 `scripts/proto_diff_whitelist.txt` baseline 空文件
- Python 块读 whitelist file 过滤已知 OK missing fields
- 未来 backend 加 private field 时可 whitelist 避免 pre-push hook noise

### 18 docs-site 文件 stale 版本号 audit

- bump_version Phase 2.5 报的 18 stale 文件逐个审
- 16+ 处是合法 "feature introduced in vX" 标注（保留）
- 2 处真漂移（修）：`observability.{md,en.md}` Grafana Dashboard JSON 过时陈述 +
  `cheatsheet.{md,en.md}` docker image 示例 tag

## 🧭 CLAUDE.md 坑沉淀

### 坑 #31 外延 audit 完成（2026-04-21）

扫全仓库 158 处 `.unwrap_or_default()` + `cache.get()` 调用：v1.4.51 `check_acc_id_exists_and_env_matches`
已覆盖所有危险 cache-read 路径。其余均为合法 proto optional field 默认处理。**无新坑**

### 坑 #32: 单份验收报告 P0+P2+P3 混合处理 Tier A/B/C 模板

v1.4.51 处理 外部 v1.4.48 10-bug 报告的方法论：
1. 归档原始报告（PII 脱敏）
2. 3 并行 Explore agent 拆分根因（trd / CLI-REST / cache+C++）
3. Tier A (P0 单 commit) / Tier B (P2 batch) / Tier C (P3 batch)
4. Defer 项明确 workaround
5. 澄清"不是 bug"的项（避免 reviewer 重复报）
6. 4件套交付（takeaways + reply×4 + fix-report + INDEX 更新）

### 坑 #33: ship.sh B 阶段失败 rollback 设计

B 阶段失败时 ship.sh 提示 rollback。强制交互式（`< /dev/tty`）避免盲动。
Force push to main 不自动做 —— 输出手工命令让用户决定。

## ℹ️ 向后兼容

- 无 breaking API
- CLI 位置参数继续 work（新 alias 是 additive）
- `/api/order-fills` firm=1 行为不变

## 真机验证状态

- BUG-5 moomoo + BUG-6 sim 修法已实装，**真机 E2E verify 待用户配合**
- BUG-9 CLI alias 已本地自测（`suspend --code HK.00700 ...` 等全部 work）

## [1.4.51] - 2026-04-21 🔴 PlaceOrder `US.xxx` 格式修 (外部验收报告 P0)

**必须升级**（影响所有从 C++ 迁移后用 `code="US.AAPL"` 格式下单的用户）。

外部回归测试交付 v1.4.48 全量验收报告（200+ 测试 / C++ OpenD 对照 / 3 账户
× 3 firm），发现 10 个 bug：**P0×1 + P2×5 + P3×4**。本版修 7 项（Tier A/B/C）+
1 pre-existing REST 404，2 项复杂路径 defer v1.4.52。

## 🔴 Fixed (P0)

### BUG-1: PlaceOrder `code="US.AAPL"` → backend_code=2 (generic 拒)

- **现象**：`code="US.AAPL"` Rust 返 generic error；`code="AAPL"` 正常
- **根因**：`handlers/trd.rs:3299` PlaceOrder + `:1241` MaxBuySell 把整串
  `"US.AAPL"` 传给 backend `symbol` 字段，backend 不认带前缀格式
- **C++ 对照**：`APIServer_Trd_PlaceOrder.cpp:50` 把 code 剥前缀后传 backend，
  market 用独立 `exchange_code` 字段
- **修法**：新增 `strip_market_prefix` helper，whitelist 11 个已知 market 前缀
  （HK/US/SH/SZ/SG/JP/AU/CA/MY/BJ/CN），PlaceOrder + MaxBuySell 前剥离
- **影响**：用户从 C++ 迁移后 `US.xxx` / `HK.xxx` 格式下单恢复正常。MCP agent
  100% 可用（MCP tool 文档格式就是 `US.AAPL`）

## 🟡 Fixed (P2)

### BUG-2/3: PlaceOrder 返 order_id=0 + CancelOrder 超时

- backend 返字母数字混合 string（如 `FH1C6647B149FF2000`），Rust `.parse::<u64>()`
  失败 fallback 0，下游 CancelOrder 用 0 调 backend 超时 10003
- 修法：`hash_backend_id_to_u64` DefaultHasher 生成稳定非零 u64；`order_id_ex`
  保留原 string（backend 真正接受的权威 id）。5 处调用点统一修复

### BUG-4: CLI `--begin "2026-04-01"` → time_begin 差 69 天

- 根因：`ftapi_time_str_to_micros_hkt` 只支持 `%Y-%m-%d %H:%M:%S` 带时间，
  纯日期 `"2026-04-01"` 解析失败 → `default_history_time_range` fallback
  "now - 90d" = 2026-01-21（实证对上）
- 修法：加第 3 个 fallback `NaiveDate::parse_from_str("%Y-%m-%d")` 后 HKT 00:00

### Pre-existing: `/api/acc-cash-flow` REST 404

- CLI 命令名 / MCP tool 名都是 `acc-cash-flow`，REST 之前只注册
  `/api/flow-summary` 别名 → 直觉命名返 404
- 修法：加 alias 路由，两种 URL 都 work（向后兼容）

## 🟢 Fixed (P3 对齐 C++ 输入校验)

### BUG-7: trd_env 不校验（权限越界）

- C++ 对 `trd_env=0` (SIM) on real acc 返 "Nonexisting acc_id"，Rust 之前完全
  忽略 trd_env 任何值都返 real 数据
- 修法：新 helper `check_acc_id_exists_and_env_matches` 3 层校验（acc_id=0 /
  不在 cache / env mismatch），9 handler 入口替换

### BUG-8: 假 acc_id silent success

- C++ 对不存在 acc_id=999999 返 "Nonexisting acc_id!"，Rust 之前 cache miss
  → ret=0 empty（误导 "账户无资产"）
- 修法：合并到 BUG-7 的同一 helper

### BUG-10: 输入校验缺失

- `GetSecuritySnapshotHandler` 空 `security_list` → 返 "type of code param is
  wrong"（之前 silent empty）
- `SubHandler` 无效 sub_type（非 [1,15]）→ 返 "subtype NN is wrong"（之前
  silent 转发）

## ⏭ Deferred to v1.4.52（需 architectural 调研，workaround 可用）

- **BUG-5**: `/api/order-fills` moomoo broker "unknown error" (CMD 2211)
  —— 有 v1.4.38-39 per-broker routing 回滚史，需设计跨 channel cipher 机制。
  **Workaround**: `/api/history-order-fills` (CMD 4712) 在所有 firm 正常
- **BUG-6**: Sim 账户 funds/positions 返 null —— `dispatch_trade_data_queries`
  硬过滤 `trd_env == 1`，sim 账户进 cache 但没查 CMD 3020。**Workaround**:
  sim 账户等 backend push 自动 populate cache

## ✍️ 澄清（非 bug）

- **BUG-9**: CLI 9+ 命令 `--help` 参数名不匹配 — 经验证 CLI 的 `--help` 输出
  和 clap 实际接受是一致的。问题是外部回归按 REST/MCP 习惯（`--code`/
  `--owner`/`--acc-id`）调 CLI，CLI 用的是位置参数或不同 flag 名（如
  `daemon-status --rest-url` 不是 `--rest-port`）。是 **跨 surface 参数命名
  一致性** UX 问题，不是 bug。计划 v1.4.52 加 clap alias 或改 docs-site/
  docs/guide/cli.md 加 REST/MCP vs CLI 命名对照表

## 🧪 Unit tests（+20 新，总 176+）

- `strip_market_prefix` x 8
- `hash_backend_id_to_u64` x 4
- `ftapi_time_str_to_micros_hkt` x 3
- `check_acc_id_exists_and_env_matches` x 5

## ℹ️ 向后兼容

- 无 breaking API
- 旧 `/api/flow-summary` 继续 work；新 `/api/acc-cash-flow` alias
- v1.4.50 用户升级 BUG-1 P0 修复，其他 bug 均为**更严格**的输入校验（正常 use
  case 不受影响，违规 use case 原来 silent fail 现在 loud fail）

## 🧭 纪律沉淀（CLAUDE.md 坑候选 #32）

"一次外部 verification report 有 P0+P2+P3 混合" 的处理模板：
1. 归档原始报告到 essentials/（PII 脱敏账号号）
2. 3 并行 Explore agent 分析根因（trd / CLI-REST / cache+C++ 对照）
3. 分 Tier A/B/C 三档 commit（P0 / P2 / P3）
4. 2 项复杂路径（cipher routing / sim cache）明确 defer + workaround
5. 1 项误报（CLI --help）澄清 + defer UX polish
6. 发版 + 4件套（takeaways + reply×4 + fix-report）

## [1.4.50] - 2026-04-21 🔄 MarketID 覆盖 125/127 + 🟢 ship 流程 CI 护栏强化

**可跳过此版**（无 user-visible 行为变化，纯对齐 C++ + CI 护栏 + 代码 hygiene）。

v1.4.49 ship 后 C++ 源码深挖确认 4 个 MarketID 漏覆盖，本版补齐到 **125/127**（C++
权威 `NN_QuoteMktID` enum 总 127 个具体 id，其中 2 个 C++ 也不归类）。同时加
CI 护栏脚本自动 diff Rust vs C++，未来 backend 加新市场能提前发现漏同步。

## 🔄 Refactor (polish pass)

### MarketID 扩 4 范围 + 加 Fund variant

基于 C++ `NNBase_Define_Enum.h:984-992` + `NN_QuoteMktType_From_NN_QuoteMktID` 转换逻辑：

| 新覆盖 | C++ enum | Rust 改动 |
|---|---|---|
| 1000-1049 HK HSI Index 扩展 | `NN_QuoteMktID_HK_HSI_INDEX_*` | `market_id_matches(HK)` 扩 |
| 1200-1249 US New VIX | `NN_QuoteMktID_US_New_VIX / _Min / _Max` | `market_id_matches(US)` 扩 |
| 570-579 HK Index Option 扩展 | `NN_QuoteMktID_HK_INDEX_OPTION_EX_*` | `market_id_matches(HKOption)` 扩 |
| 560-569 Fund 基金市场 | `NN_QuoteMktID_FUND_*` | 加 `QuoteMktType::Fund=20` variant + `marketFund` proto field |

7 新单测覆盖 + 1 新 FTAPI `marketFund=25` optional 字段（向后兼容）。

### dead_code 清理（agent 调查后分类）

- **1 条可删**：`qot.rs:17 hex_preview`（0 caller + `handlers/mod.rs` 有重复定义）
- **3 条加 trigger 注释**：`state.rs` 的 `purge_stale_subscribers` / `unregister_push_subscriber` / `push_subscriber_count`（v1.5 MCP 周期清理 / pub API 对称 / metrics 用）
- **3 条保留不改**：`qot.rs` 的 `extract_filtered_option_ids` / `cache_option_static_info` / `backend_option_to_static_info` 原注释已充分（CMD 6312 fallback）

### env var TODO audit + SAFETY 注释

`futucli/daemon.rs:133-145` 的 3 条 `TODO: Audit that the environment access only
happens in single-threaded code` 是 Rust 1.80+ `unsafe { set_var }` 语义升级
残留。agent 分析确认无线程安全风险（test body 单线程，`FUTU_REST_URL` 无跨 test race）。

修：删 TODO + 加 fn doc 说明 audit 结论 + 每处加 `SAFETY:` 引用注释。

## 🛠 CI 护栏

### `scripts/market_id_coverage_check.sh` 新增

- 从 C++ `NN_QuoteMktID` enum 抽所有 127 个具体 id
- 和 Rust `market_id_matches()` 范围 diff
- 按 covered / exempt (C++ 也 Unknown) / uncovered (真漏) 三分类报告
- 实测：125 covered / 2 exempt (124 Private_Fund + 5000 sentinel) / 0 真漏
- 集成 `.githooks/pre-push` 作 Check 4（info-only）

### `bump_version.sh` Phase 2.5 stale scan

v1.4.49 hotfix 把 stale scan 加到 `ship.sh` A4.5 wrapper，但 `bump_version.sh`
独立调用时仍漏检（v1.4.47→v1.4.48→v1.4.49 连漂移 2 版的根因）。

本版在 Phase 2 和 Phase 3 之间插入 Phase 2.5：扫所有 docs-site/docs/*.md 里
非 OLD / 非 NEW 的版本号引用，info 报告。实测发现 v1.4.49→v1.4.50 bump 前
**23 个文件有 stale 引用**（含 `contact.md` / `quick-start.md` 里 v1.4.47 未清），
本版一并清了 7 个真漂移文件。

## 🧪 Unit tests（+7 新，总 108+）

`tests_v1_4_48_market_state`：

- `market_id_matches_hk_includes_hsi_index_range`（HK 含 1000-1049）
- `market_id_matches_us_includes_vix_range`（US 含 1200-1249）
- `market_id_matches_hk_option_includes_index_option_ex`（HKOption 含 570-579）
- `market_id_matches_fund_range`（Fund 覆盖 560-569）
- `v1_4_50_extensions_do_not_overlap_other_variants`（新范围不和 v1.4.49 冲突）
- `pick_market_state_v1_4_50_scenarios`（真机场景模拟）
- `quote_mkt_to_futu_qot_market_fund_returns_zero`（contract 测试）

## 📦 ship.sh 首次 dogfood

v1.4.50 是 `scripts/ship.sh` 的**首次 dogfood** —— 之前 v1.4.49 做了工具
但手工 4 commit 发版。本版用 `./scripts/ship.sh 1.4.50`（交互式，阶段 A
完等 y/N）验证 ship.sh 阶段 A/B 全流程。

## ℹ️ 向后兼容

- 无 breaking API
- `GetGlobalState.proto` 新字段全 optional
- v1.4.49 用户升级行为**完全一致**（新字段对不关心的 client 无影响）

## 🧭 纪律沉淀

- **CLAUDE.md 坑候选 #36**：MarketID 漂移累积（v1.4.47→v1.4.48→v1.4.49 3 版累积）
  是 `bump_version.sh` 只处理 OLD→NEW 增量的设计缺陷。修法：Phase 2.5 stale scan
  主动扫（本版实装）+ 人工定期 audit。

## [1.4.49] - 2026-04-21 🔄 架构债清理（cipher_brokers dead code + MarketID 89% 覆盖）+ 🟢 发版流程自动化

**可跳过此版**（纯重构 + 流程改进，无 user-visible 行为变化）。已在 v1.4.48
的用户升级 v1.4.49 后行为 100% 一致（退化验证见 session summary）。

v1.4.48 ship 后用户推动"架构债清零"：3 项 defer 的技术债（cipher_brokers /
MarketID 范围硬编码 / 发版流程）一次性解决。同时加 `scripts/ship.sh` 作
v1.4.48 发版流程漏步骤（主页 badge + gh release create）的系统性修复。

### 🔄 Refactor

- **#1 清理 cipher_brokers dead code**：v1.4.48 #2 加的 `cipher_brokers: DashMap<AccKey, u32>`
  + `check_cipher_broker_match_or_error` helper 是 v1.4.47 错路由的 workaround。
  v1.4.48 #11 routing 对齐 C++ 后该 path 成 dead code（正确路由下 target broker
  恒有 cipher，或走 account.firm fallback）。
  - 对照 C++ `NNData_Trd_AccList::m_mapAccCipher`：用 `Map<u64_t nAccID, Str_t>`
    per-sub-account 存储，不同 broker 账户天然有不同 nAccID → 天然隔离
  - Rust `ciphers: DashMap<AccKey, Vec<u8>>` 已对齐 C++，cipher_brokers 多余
  - `decide_order_broker_id` 简化：直接返 `resolve_broker_id_for_acc`（对齐
    C++ `NNProto_Trd_Base` 按 account.brokerID 路由）
  - `sec_market_to_broker_id` 保留 `#[allow(dead_code)]`（future-proofing）
  - 7 个 routing 单测 setup 简化；断言保持不变（v1.4.48 所有场景结果恰好 =
    account.firm fallback）

### ✨ Added

- **#2 MarketID 范围覆盖 55% → 89%**：v1.4.48 `market_id_matches` 只覆盖 10/18
  C++ MarketID 范围。扩 6 个新 variant 对齐 C++ `market_tradingDay.proto`：
  - 50-51 港股通/A股通 (Stock Connect)
  - 130-159 Bonds (30 子市场，中国债券通 + US Gov Bond 等)
  - 180-184 SGX Market (新加坡股票主板/凯利板)
  - 260-359 Global Index (DE/GB/IT/CN/TW/MSCI 系列)
  - 360-459 Digital Currency (数字货币综合报价)
  - 460-559 Treasury Yield (国债收益率)
- **FTAPI `GetGlobalState.proto` 加 6 个 optional 字段**（field 19-24，向后兼容）：
  `marketBond / marketGlobalIndex / marketSGSecurity / marketStockConnect /
  marketDigitalCcy / marketTreasuryYield`
- **`GetGlobalStateHandler` 写入 6 新字段** + unclassified market_id trace log
  （未来审计新市场信号）

### 🛠 发版流程自动化

- **`scripts/ship.sh`**：统一发版入口，消除 CLAUDE.md 10+ 步手动 checklist
  漏步骤风险（v1.4.48 漏了主页 badge + gh release create）。两阶段设计：
  - 阶段 A（干跑 verify 8 步：working tree / CHANGELOG / docs-site / bump /
    cargo test+clippy+fmt / pii / proto-diff / section）
  - 阶段 B（执行 + verify：bump + commit + tag + push + 等 3 workflow +
    gh release create + verify 6 surface）
  - 支持 `--yes`（用户预先授权无人值守）和 `--dry-run`
- **CLAUDE.md 发版流程段**：改成"推荐 ship.sh"作主路径，保留手工 checklist
  作备份

### 🧪 Unit tests（+10 新，全绿，总 463+）

- `market_id_matches_stock_connect_range` / `_bond_range` / `_sg_security_range`
  / `_global_index_range` / `_digital_ccy_range` / `_treasury_yield_range`
- `v1_4_49_new_variants_do_not_overlap_existing`（6 新 variant id 范围不和
  已有 10 variant 冲突）
- `pick_market_state_v1_4_49_new_markets`（真机场景 snapshot 过滤）
- `v1_4_49_new_variants_futu_qot_market_returns_zero`（contract 测试）
- 7 个 `tests_v1_4_48_routing` 单测 setup 更新（删 cipher_brokers，重命名）

### ℹ️ 向后兼容

- v1.4.48 用户升级后 8 个原有 `market_*` 字段行为**完全一致**
- 新 6 字段都是 `optional`，旧 client 忽略不 break
- 退化分析见 `essentials/2026-04-21-0358-v1.4.48-session-summary.md` + plan file

### 📝 Docs

- CLAUDE.md §发版流程：指向 `ship.sh` 作主路径
- 下版（v1.4.50+）可选 backlog：
  - ship.sh rollback 策略
  - `scripts/market_id_coverage_check.sh` CI 护栏
  - HK HSI Index (1000-1049) + US New VIX (1200-1249) 扩展范围
  - `cipher_brokers` 若未来真需要 per-(acc, broker) 精确路由时，加 `DashMap<(AccKey, u32), Vec<u8>>` 多 cipher 存储

## [1.4.48] - 2026-04-21 🔴 broker routing 二次根治（对齐 C++ NNProto_Trd_Base）+ defer 清零

**必须升级**，尤其是单 broker 账户（FutuCA / FutuSG / FutuAU / FutuMY / FutuJP 等 security_firm 只有 1 个的账户）。

v1.4.47 根据外部报告 §14.1/§16.1 改成"按 `order.sec_market` 选 broker"，2026-04-21 真机验证 + 对比 C++ `NNProto_Trd_Base.cpp:11-49` 源码发现**方向错**：

- C++ 实际按 `acc.enBrokerID` 路由**所有**交易 op，完全不看 `sec_market`。单 broker 账户（如 FutuCA firm=5）所有市场订单都走自己 broker TCP 通道，backend 原生支持跨 market（FutuCA broker 能下 HK / US / US Option 全部 OK）
- v1.4.47 sec_market 路由对**单 broker 账户**反而有害：FutuCA 账户下 US.AAPL，daemon 强塞 broker 1007 FutuUS，但账户根本没 FutuUS cipher → daemon 自己阻断
- 外部报告 §14.1 "单 broker 账户 US.AAPL → broker 1001" 判定其实**误解** —— C++ 这才是对的（backend 走 broker 1001 也能下 US 单）

### 🔴 Fixed (P0)

- **#11 broker routing 对齐 C++ 修正**（回退 v1.4.47 P0.1 方向）：新 `decide_order_broker_id` 纯函数 + 改造 `resolve_trade_backend_for_order` 委托给它。混合策略：(1) 若 `sec_market → broker_id` 且**该 broker 有 cipher**（用户显式 unlock 过），用 sec_market 路由（保留多 broker 账户场景）；(2) 否则 fallback 到 `account.security_firm` broker（**C++ 默认路径**，单 broker 账户必走）。新单测 7 个覆盖 CA/multi-broker/sim/unknown/未连 broker 场景，全绿。
- **#1 Modify/Cancel 跨 broker 路由修正**：新 `resolve_modify_order_backend` helper。ModifyOrder/CancelOrder 不传 `sec_market`，v1.4.47 只走 account.firm broker 忽略订单原 broker。修：查 `cache.order_brokers` (order_id_ex → broker_id_used) 先找订单原 broker；未命中才 fallback account.firm。配合 PlaceOrder 成功时 `order_brokers.insert(order_id_ex, broker_id_used)`。
- **#2 cipher-broker mismatch 防御性检测 + 智能 hint**：新 `cipher_brokers: DashMap<AccKey, u32>` 记录每次 unlock 的 broker origin；PlaceOrder / ModifyOrder 入口 check cipher origin vs target broker。#11 路由修正后通常不触发，但作为 cache 状态不一致（daemon 重启后丢失）的防御层保留。hint 文案更诚实（说明"通常不该触发"+ 单 broker 账户的正确处理方式）。

### 🟡 Fixed (P1)

- **#6 Order cache 自动刷新（Modify/Cancel 错误路径）**：收到 backend 错误码 10003（order 状态不可操作）或 100012（请求超时）时，`tokio::spawn` 后台重拉 orders → 刷新 cache。避免"请求失败但 cache 还有旧 order"混淆。
- **#7 cancel-all success 强制 purge + refresh（成功路径）**：cancel-all 成功后所有 pending order 已没，cache 可能残留 stale。新增：成功路径 `tokio::spawn` 先 `cache.orders.remove(&acc_id)`（让 /api/orders 期间返空不是 stale），再 re-fetch 写回。和 #6 互补（#6 error 路径，#7 success 路径）。
- **#8 client-side sec_market 派生**：`futu-trd::place_order()` 之前 hardcode `sec_market: None`，backend 拒。新 `derive_sec_market_client` helper mirror daemon 逻辑：trd_market → sec_market（HK=1 → 1, US=2 → 2, ...）。
- **#10 ModifyOrder op_name 语义化**：之前错误文案 hardcode `"ModifyOrder:"` 不管 modify_op 是 Disable/Enable/DeleteFail。改 match `modify_op`: 3=DisableOrder, 4=EnableOrder, 5=DeleteFailOrder, 2=CancelOrder（v1.4.41 已改）, 其他 ModifyOrder。
- **P2.1 v1.4.47 漏 edge case 补修**：v1.4.47 CHANGELOG 声称修 cancel-all-order 错文案 "ModifyOrder"，但**漏 offline mode 的早 return 路径**（line 3546 `"ModifyOrder: 后端未连接"`）。real daemon offline 状态下 cancel-all 仍返 "ModifyOrder:"。v1.4.48 补：ModifyOrderHandler 入口**先预解析 modify_op + for_all** → 按 `CancelAllOrder`/`CancelOrder`/`DisableOrder`/`EnableOrder`/`DeleteFailOrder` 动态选 prefix，再做 backend check。

### 🔴 Fixed (P0) 新增 (v1.4.47 CMD6823 handler 根本错)

- **#3 `market_us=3` vs Python SDK=5 根因 + 修**：v1.4.47 P0.2 修了"US=Closed"的 enum 错误，但**剩下的粒度差异是**真 bug**，不是"Python SDK 粗略"。实际 backend `CMD 6823` 每次都返**全市场 100+ 条子交易所状态**（不管 reserved[0] 发啥），v1.4.47 handler 盲取 `statuses[0]` → 对 US 查询拿到的是 `market_id=120` (some options-related) `status=3 Morning` 而不是 US 真正的 NYSE/NASDAQ (id=10-29) `status=5 Afternoon`。
  - **修**: `pull_single_market_status` 加 `market_id_range_for(mkt)` 按 `MarketID` enum 范围过滤：HK=1-4, US=10-29, CN=30-40, US Option=41-45, US Future=60-119, SGX Future=160-179, JPX Future=185-194
  - 过滤后每市场只取该市场子交易所的状态，对齐 Python SDK 输出
- **#4 `USFuture / SGFuture / JPFuture / USOption` state 字段返 None 根因 + 修**：不是 backend 不返数据，而是 v1.4.47 `quote_mkt_to_futu_qot_market` 把这些 future/option mkt 映射成 0 (Unknown) 且 handler 过滤后 `statuses[0]` 是别的市场的状态。**修同 #3**：按 MarketID 范围过滤后，这些 future/option 字段能正确返 backend 提供的状态（real-time 动态）。
- **CMD 6823 response 机制沉淀**（CLAUDE.md 坑新增候选 #33）：backend 对 CMD 6823 **不管你 reserved 发什么 market 都返回全市场 100+ 条状态**；客户端必须**按 `MarketID` 范围过滤**才能拿到正确市场。参考 C++ `market_tradingDay.proto::MarketID` enum 范围。
- **#5 sim trd_market=10/12/13 启发式（未 live 验证）**：`derive_security_type` 新加启发式——alpha-only code → COMMON，numeric → FUTURES（和 v1.4.47 trd_market=11 修一致）+ WARN log。**未用 sim 账户 live 跑**；用户碰到会 spot 反馈。单测覆盖启发式 + 既有 v1.4.47 trd_market=11 回归测。

### ✅ N/A（审查后验证无需实装）

- **#9 WS / gRPC / MCP camelCase normalize audit**：v1.4.45 Bug A 是 REST JSON 层问题。其他入口不受影响：
  - WS (`futu-server/ws_listener.rs` + `conn.rs`): 纯 binary protobuf `prost::Message::decode`，无 JSON 层
  - gRPC (`futu-grpc/server.rs`): tonic 纯 binary protobuf
  - MCP (`futu-mcp/tools.rs`): `schemars::JsonSchema` 向 LLM 广告 snake_case field（`acc_id` / `order_id` / ...），LLM 不会主动发 camelCase

### 🧪 Unit tests（7 个新，全绿，总 443+ 个）

`tests_v1_4_48_order_broker_routing`：

- `ca_account_hk_order_falls_back_to_ca_broker_when_no_hk_cipher` —— 核心 regression 保护
- `multi_broker_account_hk_order_uses_hk_when_hk_cipher_present` —— 多 broker 场景（替代 live 验证 defer 的场景）
- `sec_market_target_not_connected_falls_back`
- `unknown_sec_market_uses_account_firm`
- `sim_account_returns_none`
- `ca_account_us_order_falls_back_to_ca_broker` —— live 实测场景单测化
- `no_cipher_record_falls_back_to_account_firm` —— daemon 刚启动 / unlock 未完成 edge case

### 🔴 真机 regression（3 个真账户 live 全绿）

**账户 A：单 broker CA（security_firm=5 FutuCA, 只有 broker=1019）**

| 场景 | 结果 | 关键日志 |
|---|---|---|
| Test-a TRD_ENV all-upper normalize | ✅ | positions 列表正常返（含 NVDA Option 持仓）|
| Test-b US.AAPL qty=1 price=210 | ✅ ret_type=0 | `broker_id=Some(1019) channel="broker"` ← v1.4.47 错 1007 |
| Test-c Modify order price→205 | ✅ | `broker_id=Some(1019)` + `v1.4.48 #6 auto-refresh` 触发 |
| Test-c Cancel order | ✅ | `broker_id=Some(1019)` + `v1.4.48 #6 auto-refresh` 触发 |
| Test-d US Option NVDA270115C500000 | ✅ | `security_type=2 broker_id=Some(1019)` |
| Bug #10 history-order-fills 无 filter | ✅ | 39 fills（90d 默认）|

**账户 B：半多 broker US moomoo（firm=2, 连上 [1007,1008,1009,1012,1019]，不含 1001 FutuHK）**

| 场景 | 结果 | 关键日志 |
|---|---|---|
| US-only acc + US.AAPL（sec_market=2 target=1007 cipher 在 1007）| ✅ sec_market 路由 | `broker_id=Some(1007)` |
| Multi-market acc + HK.00700（target 1001 未连 → fallback）| ✅ fallback | `broker_id=Some(1007)` backend 接受（"购买力不足"）|

**账户 C：真多 broker futunn（连上 [1001, 1007] 双 broker）**

| 场景 | cipher | 预期 | 实际 | backend |
|---|---|---|---|---|
| HK 单 on firm=1 HK-only | cipher=1001 match target | sec_market 路由 Some(1001) | ✅ Some(1001) | 购买力不足 |
| US 单 on firm=1 multi-market | cipher=1001 ≠ target 1007 | fallback Some(1001) | ✅ Some(1001) | **ret_type=0 真金成功** ⭐ FutuHK broker 原生跨市场支持 US |
| US 单 on firm=2 US acc（unlock FutuUS 后）| cipher=1007 match target | sec_market 路由 Some(1007) | ✅ Some(1007) | 价格偏离市价过大 |
| HK 单 on firm=1 HK acc（最后 unlock FutuUS 后）| cipher=1007 ≠ target 1001 | fallback Some(1001) | ✅ Some(1001) | 购买力不足 |

**6 个 live scenario + 7 个单测**全面覆盖 v1.4.48 #11 决策逻辑（sec_market with cipher match / fallback / single-broker / multi-broker / last-unlock-wins edge）。账户 C 的 "US 单通过 FutuHK broker ret_type=0" 是决定性证据证明 C++ `NNProto_Trd_Base` 路由逻辑正确。

**900803 futunn 账户未测**：该账户被服务端临时锁定（ret_type=1 系统繁忙持续多次重试），与 v1.4.48 无关。

### 🧭 纪律沉淀（CLAUDE.md 历史坑新增）

- **#32 Never blindly believe external verification report's "fix direction"**：v1.4.47 按外部报告 §14.1/§16.1 改"按 sec_market 选 broker"，看似符合"US 单应去 US broker"直觉，但**C++ 源码才是唯一真 spec**。外部报告提供的是"症状"(observation) 不是"修法"(prescription)，修法必须对 C++ 源码交叉验证。v1.4.47 改前 5 分钟 grep `NNProto_Trd_Base` 就能避免一整版回滚。

### 🟢 UX + 其他

- v1.4.47 的 `essentials/2026-04-21-0140-v1.4.47-session-summary.md` 里 "Out of scope" 回扫完成：所有本版相关 item 已清零（详见 essentials/2026-04-21-<ts>-v1.4.48-session-summary.md §B）。

## [1.4.47] - 2026-04-21 🔴 外部 v1.4.41-45 验收 + 真机 E2E 全绿（broker routing 根治）

**必须升级**（跨 broker 账户 + 使用 cancel-all-order 的用户）。

外部回归测试 2026-04-20 交 A-类硬实锤验证报告（`essentials/2026-04-21-...external-v1441-45-verification-report.md`），re-verify v1.4.41-45 leaf 承诺 11/12 通过 + 4 个新 P0/P1 + 1 个跨 5 版未修。加上 leaf 本地 v1.4.46 真金 E2E 发现的 daemon UX 坑，一并在本版全修 + 真机回归验证。

### 🔴 Fixed (P0)

- **Broker routing by `sec_market` not `account.security_firm`**（外部报告 §3 P0 + §14.1 + §16.1，跨 4 账户实锤）：之前 daemon 按账户 `security_firm` 选 broker，不看订单 `sec_market`。典型故障：某 FutuCA 账户（firm=5 → broker 1019）下 US.AAPL，brokers list 里明明有 1007 US，daemon 仍选 1019 → backend 拒。修：新 helper `sec_market_to_broker_id` + `resolve_trade_backend_for_order`，PlaceOrder / GetMaxTrdQtys 先按 order.sec_market 选 broker，回退 account.firm。
- **CancelAllOrder 错文案跨 5 版未修**（外部报告 §2 P2.1）：`/api/cancel-all-order` 返错时 ret_msg 以 `ModifyOrder:` 开头不是 `CancelAllOrder:`。根因：REST route 设 `modify_order_op=4` (Enable) 而非 `2` (Cancel)，handler `if modify_op == 2` 不命中 → 走 ReplaceOrder 分支 → hardcoded "ModifyOrder"。修：REST route 改 `op=2`。
- **derive_security_type(trd_market=11) → FUTURES 错**（外部报告 §14.4）：sim 账户 `trd_market_auth_list=[11]` 下 AAPL 时 daemon 推导 SECURITY_TYPE_FUTURES (4) → backend 拒股票订单。实测 11 不是标准 TrdMarket（Python SDK enum 不含 11）。修：11 从 futures 列表移除。
- **market_name_cn(11) → "MY" 错**（外部报告 §14.4）：sim 账户 trd_market=11 触发 hint "MY 市场非交易时段"。修：11 → "Unknown"，`market_hours_tip(11)` 也移除。

### 🟡 Fixed (P1)

- **market_state cache 全错（US/SG_Future/JP_Future）**（外部报告 §3 P2 + §14.3）：`/api/global-state` 返 market_us=Closed 即使 US 实际开市。根因：`QuoteMktType` Rust-internal enum 值（US=2, SH=3, SZ=4）**不等于** Futu `QotCommon.QotMarket` 值（US_Security=11, CNSH=21, CNSZ=22）。之前 `reserved[0] = QuoteMktType::US as u8 = 2` → backend 理解为 HK_Future → 返 HK_Future 状态（HKT 23:00 必 Closed）。修：新 helper `quote_mkt_to_futu_qot_market` 在 `make_quote_reserved` 里显式转成 Futu QotMarket 值。
- **`maybe_annotate_market_closed` 把 TrdMarket 当 QotMarket 用**（外部报告 P1 根因）：handler 里 `qot_market_to_backend(trd_market)` 调用 —— TrdMarket=2 (US) 被当 QotMarket=2 (HK_Future) → 查 HK_Future 状态 → 永远 Closed → hint 永远乱加"US 非交易时段"。修：新 helper `trd_market_to_backend` 独立映射 TrdMarket → QuoteMktType。
- **hint 贪心误报"市场非交易时段"mask 真因**（外部报告 §3 P1 + §14.2）：之前只要 backend 返通用"请稍候再试"就附加 market-closed hint，mask 掉"余额不足 / 账户限制 / broker 错路由 / sim proto 漏字段"等真因。修：hint 文案软化为"疑似..."+ 加"其他可能真因"清单（余额/权限/路由/proto 四类）+ 建议 `/api/global-state` 交叉验证。
- **camelCase normalize 连续大写 edge case**（外部报告 §14.5）：`pwdMD5` 三连大写 fail → `pwd_m_d5`（应 `pwd_md5`）；`TRD_ENV` 全大写 snake fail → `tr_d_env`（应 `trd_env`）。修：`to_snake_case` 把 abbreviation 继续判据从"next 是 upper 或 end"改成"next 不是 lowercase"（数字 / 下划线 / 结尾都算 abbreviation 继续）。
- **Bug #10: history-orders/fills filter 缺失 silent 返 0**（外部 2026-04-20 报告）：`/api/history-orders` / `/api/history-order-fills` 不传 `filterConditions` 时返 0 条 ret_type=0（silent fail）。LLM agent 误判"账户无数据"。Python SDK `history_deal_list_query` 对缺失参数填合理 default（~90 天）。修：新 helper `default_history_time_range`，缺字段时填 `now - 90d → now`，INFO log 记录"已 fill default"。

### 🟢 Fixed (P3/P4)

- **`translate_modify_order_err_hint`** backend_code=10003/100012 专译（v1.4.47 WIP 已 ship 在 main）：ModifyOrder 路径返 10003 不再误译"市场收盘"，而是"订单已不可操作 / 查 history-orders"。100012 请求超时独立 hint "不要盲目重试"。
- **`translate_place_order_err_hint`** backend_code=31 专译：PlaceOrder 遇 opposite-direction pending 时给"改用 LIMIT / 先 cancel opposite / 等 EOD"hint。
- **`scripts/changelog_section_check.sh`** printf bug（v1.4.47 WIP）：`grep -c` 找 0 match 时 `|| echo 0` 造成双写 `0
0` → `printf: 0 0: invalid number` 误报。修：新 `count_matches` helper 兜底。

### 🧭 流程纪律

- **外部验收报告归档硬约定**：大版本 fix 必 re-verify 真机 A-类对照，报告归档到 `essentials/<ts>-external-v<ver>-verification-report.md`。本版归档 外部 2026-04-20 报告 + 全 8 类 fix 的 live regression report。
- **发版前真机 regression 硬约束**：v1.4.47 每项 fix 都在 moomoo CA real account 验证通过（broker_id=1007 实锤 / CancelAllOrder 文案 / market_us=3 非 6 / Bug#10 返 39 fills / pwdMD5 normalize / hint 软化）。

### Tests

- **+11 new unit tests**（434 → **445 passing**）
- clippy / fmt / pii_scan / section_check 全绿
- proto_diff_check: 0 / 0 missing（v1.4.44 baseline 维持）

## [1.4.46] - 2026-04-20 🟢 Cache-read handler 防御 check + 期权 snapshot 字段补齐

**可跳过此版**（已在 v1.4.45 的用户）。纯 polish + 一个 silent fail 兜底 + 2 个空字段填充。不修任何阻断级 bug。

### 🟡 Fixed (P2)

- **Cache-read handler `acc_id=0` silent empty return 兜底**（`crates/futu-gateway/src/handlers/trd.rs`）：`GetFundsHandler` / `GetPositionListHandler` / `GetOrderListHandler` 在 `header.acc_id=0` 时原本返 `ret_type=0 + 空 collection`（"HTTP 200 假象"），用户无法区分"账户真无持仓"vs"input 非法 silent fail"。v1.4.45 Bug B 已给 backend-forward handler（place-order / history-* / max-trd-qtys / order-fills）加 `check_acc_id_not_zero_or_error`，本版补齐 **3 个漏的 cache-read handler**。升级后传 `acc_id=0` 会返清晰 error msg（列 3 条可能原因）。

### 🟢 Fixed (P3)

- **`/api/snapshot` option_ex_data 字段补齐**（`crates/futu-gateway/src/handlers/qot.rs`）：期权 snapshot 响应的 `owner.code` / `strike_time` / `strike_timestamp` 在 v1.4.45 及之前返空串 / `None`（backend `FTCmdStockQuoteCoverageData.Option` proto **没有** `underlying_stock_id` / `strike_date` 字段）。v1.4.46 新 2 个 helper 从 option code 直接解析：
  - `parse_option_underlying("NVDA260515C200000") → "NVDA"`（兼容 OCC 21-char 空格 pad 格式 `"SPY   260520P540000" → "SPY"`）
  - `parse_option_expiry_date_str("NVDA260515C200000") → "2026-05-15"`（+ 通过现有 `parse_date_to_timestamp` 填 HKT 0:00 UTC 秒数）
  - **9 单测**覆盖 compact US / HK / OCC 21-char / underlying 含 C 字符（CRWD）/ 非 option 拒绝 / 过期合约 / timestamp roundtrip

### 🛠 工具 / CI

- **新增 `scripts/bump_version.sh`**：精确引用替换版本号，替代"`sed -i '' 's|OLD|NEW|g'` 全量替换"的危险模式。v1.4.41-45 连续 5 次发版都踩 sed section header 吞吐坑（`changelog.md` 的 `## v1.4.X` 标题也被误改），`changelog_section_check.sh` + pre-push hook 能拦住 push 但不防错。新脚本：
  - **完全跳过 `changelog.md` / `changelog.en.md` / `CHANGELOG.md`**（内容全是历史，里面 "v1.4.45 修了 XX" 不该跟新版号改）
  - **只替换**：Cargo.toml workspace version + docs-site guides / quick-start / cli / index / contact / download / tutorials + deploy/examples + README.md（"current version" 引用）
  - **`--dry-run`** 干跑模式，配合 section check post-validation
  - 用法：`./scripts/bump_version.sh 1.4.45 1.4.46`
- **CLAUDE.md 发版流程** section 3 批量替换命令下加一句推荐："推荐用 `scripts/bump_version.sh OLD NEW` 替代裸 sed（避免 section header 误改）"

### 🧭 流程纪律

- **CLAUDE.md 历史坑 31 新增**："HTTP 200 + ret_type=0 + empty collection" 不一定是成功 —— 区分 backend-forward handler（loud error）vs cache-read handler（silent empty）的失败模式。坑 30 讲 serde camelCase drop 是 bug 根源；坑 31 讲**同一 bug 的两种失败模式**，修 bug 时必须覆盖两者
- **防御设计原则沉淀**：任何 handler 返 `ret_type=0 + empty collection` 都值得 audit 根因；`.unwrap_or_default()` 在 cache miss path 上是**危险信号**，配套必须有 input validation
- **发现渠道**：外部 reviewer（external tester）主动**比对 positions vs history-fills** 才暴露 positions 也坏但 silent。大多数用户不做 cross-check。新 handler 实装 review 时应该主动扫"所有 cache.get().unwrap_or_default() 的路径有没有 input validation 覆盖"

### ✅ 真机自测验证（美股开盘 `<account>` v1.4.46 本地）

| 验证项 | v1.4.45 | v1.4.46 |
|---|---|---|
| `/api/positions` with `acc_id=0` | `ret_type=0 + position_list=[]` (silent) | `ret_type=-1 + "invalid acc_id=0. 可能原因..."` (loud) |
| `/api/funds` with `acc_id=0` | `ret_type=0 + 空 funds` (silent) | `ret_type=-1 + "invalid acc_id=0. ..."` (loud) |
| `/api/orders` with `acc_id=0` | `ret_type=0 + order_list=[]` (silent) | `ret_type=-1 + "invalid acc_id=0. ..."` (loud) |
| `/api/snapshot NVDA260515C200000` `owner.code` | 空串 | `"NVDA"` |
| `/api/snapshot NVDA260515C200000` `strike_time` | 空串 | `"2026-05-15"` |
| `/api/snapshot NVDA260515C200000` `strike_timestamp` | `null` | `1747238400.0` (HKT 0:00 UTC secs) |

**无 regression**：Test A 14/14 PASS（所有 query endpoint camelCase + snake_case 全绿）/ 期权链 + snapshot + Greeks + DTE 全绿 / Unlock per-broker 3/3 PASS。

### 测试

- **8 新 unit test**（v1.4.45 的 419 → v1.4.46 的 428）
- 全 workspace `cargo test`：428 passed / 0 failed
- `cargo clippy -- -D warnings`：clean
- `cargo fmt --check`：clean
- `scripts/pii_scan.sh`：clean
- `scripts/changelog_section_check.sh`：clean（5 版 section count 都 = 1）
- `scripts/proto_diff_check.sh`：0 / 0 missing（v1.4.44 baseline 维持）

## [1.4.45] - 2026-04-20 🔴 REST body 兼容 FTAPI camelCase 字段名（同事反馈修）

**必须升级**（所有 REST API 用户）。

同事反馈 v1.4.43 `/api/history-order-fills` 返 `acc_id=0` 不工作，认为是 `derive_history_market_filter` 的 regression。实测证伪 —— **真根因是 REST body 用了 FTAPI 官方 camelCase 字段名**（`accID` / `trdEnv` / `filterConditions` / `beginTime` 等 —— 和 py-futu-api + C++ OpenD 文档一致），但 Rust REST 层 serde 默认按 struct field **snake_case** 匹配 + `#[serde(default)]` 静默吞未知字段 → `acc_id` 默认 0 继续执行。

**CLAUDE.md 核心原则** "与 C++ 零细节差异 / 不用默认值替代真实数据" —— 这里**双条都破了**：
1. 和 FTAPI 官方 camelCase 不兼容 = 功能缺失
2. `#[serde(default)]` 静默吞错字段 = 默认值替代真实数据

### 🔴 Bug A: REST body camelCase 自动 normalize

- 新 helper `normalize_json_keys_snake_case(&mut Value)` + `to_snake_case(s)`（`crates/futu-rest/src/adapter.rs`）
- 递归转所有 JSON object key: `accID → acc_id` / `trdEnv → trd_env` / `filterConditions → filter_conditions` / `beginTime → begin_time` 等
- 集成点：
  1. `proto_request_with_idempotency` 入口（所有 REST route 自动生效）
  2. 3 个手动 `from_value` 的 route（`place_order` / `modify_order` / `cancel_all_order`）在 limit check 前也 normalize
- snake_case 原本正确的 body 不受影响（向后兼容）
- **9 个单测覆盖**：基础 camelCase / PascalCase / 已是 snake / 嵌套 object / array / mixed

### 🔴 Bug B: trade handler acc_id=0 防御性 check

- 新 helper `check_acc_id_not_zero_or_error(acc_id, op_name)`（`crates/futu-gateway/src/handlers/trd.rs`）
- 返清晰 error msg：(1) camelCase 可能性 (2) 忘传字段 (3) TCP 入口字段确为 0
- 插入 **8 个 trade handler 入口**（PlaceOrder / ModifyOrder / GetMaxTrdQtys / GetHistoryOrderList / GetHistoryOrderFillList / GetOrderFee / GetOrderFillList / FlowSummary）
- Bug A 修好后几乎不触发，但非 REST 入口 / Bug A 覆盖不到的 edge case 仍能早期 reject + 可读 error

### ✅ 真机自测验证（`<account>` v1.4.45 本地）

| curl body | v1.4.44 | **v1.4.45** |
|---|---|---|
| `{"c2s":{"header":{"trdEnv":1,"accID":<id>,"trdMarket":1},"filterConditions":...}}` | `acc_id=0 markets=[]` 空返 | ✅ `acc_id=<id> markets=[1,2,113,123,15]` 返真实 2 条 fills |
| 完全省略 accID 字段 | 同上静默错 | ✅ 返 `invalid acc_id=0. 可能原因:(1) camelCase...(2) 忘传字段...` |

### ✅ Quality gates

- workspace **419 tests passing**（v1.4.44 的 410 + 新 9 覆盖 normalize + to_snake_case）
- clippy / fmt / PII scan / section check: all clean
- pre-push hook 3 check（PII + section + proto diff）

## [1.4.44] - 2026-04-20 🔴 proto-internal 字段对齐 C++ 零差异（219 → 0）

**必须升级**。坑 23 第 3 次命中后（v1.4.43 ship），跑全量 `proto_diff_check.sh`
发现 proto-internal 里还有 **219 个 missing fields 跨 39 messages**（5 CRITICAL
+ 8 HIGH + 12 MEDIUM + ~14 LOW）。每个 missing field 都是"还没测到的 P0"。

本版按核心原则 "与 C++ 线上版本零细节差异" 全部补齐：**proto diff baseline
219 → 0**。

### 🔴 Proto 对齐（10 文件，40 messages）

- `odr_sys_cmn.proto`：full-copy C++ 原版（1054 行）+ 保留 8 个 Rust-only Sup* messages
- `odr_sys_interface.proto`：full-copy C++ 原版（827 行）+ 保留 27 个 Rust-only 本地扩展（CashInfoReq/PstnInfoReq/AssetInfoReq/NotifyMsg/Sup*Req/Rsp）
- `FTCmdKline.proto`：6 messages 对齐（TimeSharePoint/TimeShareSection/TimeShareReq/KlineItem/KlineReq/KlineRsp 补共 13 fields）
- `FTCmdTick.proto`：3 messages 对齐（TickItem/TickReq/TickRsp 补共 10 fields）
- `FTCmdQtaAuth6024.proto`：2 messages + 新增 **FTCMD6651_QtaAuthChg.proto**（QuoteChangeNotify 等）—— 共补 45 fields
- `wch_lst.proto` / `FTCmd2008.proto` / `FTCmdClientData.proto` / `FTCmdTradeAuth.proto` / `FTLoginAccListLocal.proto`：各补 1-2 fields

### 🔴 Handler 调整（Rust code 层）

proto 字段类型 / 结构变化引起 13 处 Rust compile error，全修：

- `OrderFill.market` / `PstnInfo.market`：`Option<String>` → `Option<u32>`，
  handler 去掉 `.parse::<u32>()`
- `PstnInfo.symbol` / `stock_name`：`bytes` → `string`，`String::from_utf8_lossy(&[u8])`
  → `Option<String>.cloned()`
- `OrderListReq`：构造补 `for_trigger / security_type / time_begin / time_end /
  trigger_status / trigger_type / order_side / market` 8 字段
- `OrderNewReq / MaxBuySellReq / OrderCancelReq / KlineReq`：struct literal 加
  `..Default::default()` 兼容 20+ 新字段（其他字段走 default）
- `QtaAuth6024Req`：补 `device_type / quote_change_notify` 2 字段（对齐 C++ "空请求"语义）

### 🧭 CLAUDE.md 核心原则之后加 "纪律红灯词清单"

为防"字段缺失不严重"判断重犯，明确列 5 条红灯词（触发 re-read 核心原则）：

1. "Response/Struct 不影响 backend 行为" ← 错（API 契约破坏）
2. "字段没人用 / 锦上添花 / low priority / 可以 defer" ← 错（假设，非事实）
3. "P1 不是 P0 / 没暴露过不严重" ← 错（未测 = 潜伏 P0）
4. "分档优先级" 用于决定"要不要修" ← 错（所有 diff 必修）
5. "MVP 够用 / 暂时裁剪" 未注明 trigger ← 错（坑 23 三次实锤）

机制化工具：`./scripts/proto_diff_check.sh` 规划 scope 前必跑。跨 session 硬约束。

### ✅ Quality gates

- **proto_diff_check baseline: 219 → 0** missing fields ✅
- workspace **410 tests passing**（v1.4.43 的 410，proto 扩字段但未改 handler 行为）
- clippy / fmt / PII scan / section check: all clean
- pre-push hook 3 check（PII + section + proto diff）

## [1.4.43] - 2026-04-20 🔴 全权委托账户 history_orders/deals 返 0（同事反馈修）

**必须升级**（如果使用"全权委托"或多市场授权严格 ACL 账户）。同事 v1.4.41
真机反馈：Rust daemon 查账户历史成交返 0，C++ OpenD 同账户返 227 HK + 582 US。
根因：**CLAUDE.md 坑 23 第 3 次命中**（proto-internal 裁剪版），`HistoryOrderListReq`
Rust 8 字段 / C++ 原版 20 / `HistoryOrderFillListReq` Rust 6 字段 / C++ 原版 13。
最核心漏字段：**`market[]` filter** —— 严格 ACL 账户 backend 要求此字段非空否则
返 0 条。

### 🔴 Fixed

- **HistoryOrderListReq 补 12 字段** (`proto-internal/odr_sys_interface.proto`):
  security_type (repeated) / order_type / trade_type / order_status / query_word
  / ex_destination / for_trigger / **market (repeated)** / date_begin / date_end
  / currency / show_related_order (default=true)
- **HistoryOrderFillListReq 补 7 字段**: security_type / side / trade_type /
  **market** / date_begin / date_end / currency
- **GetHistoryOrderListHandler / GetHistoryOrderFillListHandler 填新字段**
  (`handlers/trd.rs`)：
  - 新 helper `derive_history_market_filter(cache, acc_id) -> Vec<u32>` 从
    `CachedTrdAcc.trd_market_auth_list` 派生 `market[]`（对齐 C++
    `NNProto_Trd_Order::FillHistoryOrderListReq` 从 `accItem.vecEnableMarket`
    派生）
  - `security_type: [1, 2, 4]`（COMMON + OPTION + FUTURES，对齐 C++ 3 个
    `add_security_type`）
  - `for_trigger: 2`（拉普通单 + 扩展订单，对齐 C++ `set_for_trigger(2)`）
  - `page_size: 100`（对齐 C++，之前 None = backend default 50）

### 🧭 CLAUDE.md 历史坑 23 再次命中（第 3 次）

1. v1.4.41 P0.1：`OrderNewReq` 漏 14 字段
2. v1.4.41 P1.1：`MaxBuySellReq` 漏 5 字段
3. **v1.4.43：`HistoryOrderListReq` 漏 12 / `HistoryOrderFillListReq` 漏 7**

三次同坑 = 必须机制化。下一轮 CI hook 补 `proto-internal/*.proto` vs C++ 原版
字段数 diff 检查，避免第 4 次踩。

### ✅ Quality gates

- workspace **410 tests passing**（v1.4.42 的 406 + 新 4 覆盖
  `derive_history_market_filter`）
- clippy / fmt / PII scan / changelog section check: all clean
- pre-push hook：PII scan + section check 双 check（v1.4.42 实装）

## [1.4.42] - 2026-04-20 🟢 v1.4.41 全部 defer 项 + DTE helper 收尾

v1.4.41 defer 的 6 项 P2/P3 + v1.4.40 roadmap 遗留的"期权持仓 DTE 暴露到 Position" 一并做完。本版零新发现 bug（外部 reviewer 在休息），纯 polish / UX / observability 升级。

### 🟡 Fixed

- **#P3.2 channel 错误格式统一** — backend real 通道返 `"错误，请稍候再试"`、sim 通道返 `"错误，请稍后重试或联系客服。"`，agent 做 retry 逻辑要双写匹配。新 `normalize_backend_retry_msg()` 精确等值匹配已知变体 → 统一成短版 `"错误，请稍候再试"`。非通用错误（含具体信息的消息如 `"请重新解锁交易"`）保持不动。5 个单测。
- **#P3.3 MCP `MaxTrdQtysReq.order_type` 接 int OR string** — v1.4.41 LLM agent 习惯传 `"NORMAL"` 撞 `-32602 schema error`。新 `deser_int_or_order_type_str` custom deserializer 同时接 `1 / "NORMAL" / "LIMIT" / "MARKET" / "ABSOLUTE_LIMIT" / "AUCTION" / "AUCTION_LIMIT" / "SPECIAL_LIMIT" / "3"（字符串数字）`。4 单测覆盖 backward-compat + string + unknown-reject。
- **#P2.3 Position struct 字段** — 经代码审查确认 `average_cost_price / diluted_cost_price / average_pl_ratio` 3 字段在 v1.4.41 已在 cache + handler 透传（外部回归报告字段差异是用旧版本测出的）。本版仅加 comment 明确这一状态，无代码改动。`today_*` vs `td_*` 前缀不对齐 Python SDK 是 FTAPI proto 原始定义，保持不变（改动是 breaking change，留待 v1.5 major schema migration）。
- **#roadmap 期权持仓 DTE 暴露到 Position** — v1.4.40 roadmap #2（"基础库实装，v1.5 暴露"），本版提前做。`Trd_Common.Position` proto 新加 `expiryDateDistance = 35`（optional int32）。新 `parse_option_dte(code) -> Option<i32>` helper 从 Futu 紧凑 / OCC 21-char / OCC 19-char half 三种 option code 格式都解析 YYMMDD + 按 chrono HKT today 算 days-delta。`GetPositionListHandler` 返响应时按 `p.code` **实时算**（不缓存 —— 每天 DTE -1 若 cache 会过期）。非 option code 返 `None`。6 个单测。
- **#P3.4 moomoo `admin/reload credentials_refresh` 诊断增强** — moomoo 账户首登后 credentials 文件可能不写（根因待真机 raw `/authority` response 分析），导致 admin/reload 报 `"no cached credentials"`。本版：
  - `save_credentials_from_response` 添加 WARN log 记录 "device_sig_new 和 tgtgt_new 哪个为空 → 为何 skip save"，下次外部真机 debug 能看到字段缺失
  - admin/reload handler 对 "no cached credentials" 错误追加 actionable workaround hint（`--reset-device --setup-only` 重新 SMS 生成 credentials → 正式启动 daemon 后 admin/reload 即可正常 refresh）
- **#P3.5 `--login-region` layer 2/3 语义澄清** — 经审查确认 v1.4.40 观察的 "moomoo 账户三种 `--login-region` 下 platform IP 相同" 是**预期行为**：`login_region` 只用于 CN 手机号账户的 `/authority/salt` URL `region_no` 参数，平台 IP 池按 `user_attribution`（CN/HK/US/SG/AU/JP）从 `conn_points` 选，不按 `login_region` 切。v1.4.40 changelog 声称"已加 WARN 提示 moomoo + login_region 组合无效"但代码漏加，本版补上：
  - `RuntimeConfig` 加 `login_region_explicit: bool` 标记用户是否显式传
  - `main()` init_logging 后 check moomoo + explicit → `tracing::warn!` 提示 noop
- **#P2.7 MCP 业务错 `isError` marker** — 最小侵入方案（不大改 rmcp SDK tool return type）：`FutuServer::err()` 在 error JSON 里加 `"isError": true` + `"status": "error"` 两个明显字段，让 LLM agent 不被 MCP envelope 的 `isError: false`（SDK 看成 tool 返成功）误导。Agent prompt 侧指导 "看 JSON 里的 `isError`，不看 MCP envelope"。v1.5 SDK return type 大改时做根治。单测确认 `err()` 输出格式。

### 🟢 用户可见改进摘要

量化 agent 用 MCP 调 max-trd-qtys 时现在可以直接传 `"NORMAL"` / `"MARKET"` 字符串；期权持仓响应现在带 `expiry_date_distance` 字段（到期天数）方便 DTE 策略；所有 trade 错误都带 `(backend_code=-N)` + 两通道文案统一；moomoo 账户 + `--login-region` 组合启动时 WARN 提示语义无效；MCP error 响应 JSON 多个 `"isError": true` marker 让 LLM 识别业务错。

### ✅ Quality gates

- workspace **406 tests passing**（v1.4.41 的 390 + 新 16：P3.2 × 5 / P3.3 × 4 / DTE × 6 / P2.7 × 1）
- clippy / fmt: clean
- PII scan: clean

## [1.4.41] - 2026-04-20 🔴 外部 v1.4.40 v2 报告 — 4 P0 + 2 P1 + 6 P2/P3 全修

**必须升级**。外部 reviewer 在 v1.4.39 + v1.4.40 全量回归（100% L1 surface-walk + HK 真 e2e + Python SDK 对照）中发现 **19 个新 bug**，其中 **1 个 P0 让 daemon 任何 PlaceOrder 全面失败**。本版修 4 P0 + 2 P1 + 5 P2 + 2 P3，6 项低风险 P2/P3 defer v1.4.42。

### 🔴 Fixed — 阻断性 bug（P0）

- **#P0.1 daemon PlaceOrder 全面失败（漏 backend exchange_code）** — daemon REST / CLI / MCP 三 surface 所有 place-order 统一返 `"错误，请稍候再试"`，Python SDK 对照能下单成功。根因：Rust `proto-internal/odr_sys_interface.proto` 的 `OrderNewReq` 只有 8 个字段，漏了 C++ 原版 `exchange_code` (field 18) + `exchange` (field 26) + `security_type` (field 11)，backend 因缺 market 信息拒单。
  - 修法：proto `OrderNewReq` 补 field 11/17/18/19/22/24/26/36/37/38/39/42/54/66（14 个），`OrderReplaceReq` 补 field 6/7/8/9/21/22/23/24/25/41（10 个），`MaxBuySellReq` 补 field 7/8/9/10/14（5 个）。新 `enum SecurityType` COMMON=1 / OPTION=2 / FUTURES=4 加到 `odr_sys_cmn.proto`。
  - Handler 新 helper（`crates/futu-gateway/src/handlers/trd.rs`）：
    - `derive_sec_market(ftapi_sec_market, trd_market, code) -> i32`：client 显式传 `c2s.sec_market` 优先，否则按 trd_market + code 前缀推（CN 区 SH/SZ 按 code 前缀分）
    - `sec_market_to_qot_market(sec_market) -> u32`：TrdSecMarket → QotMarket exchange_code 值（HK=1, US=11, CN_SH=21, CN_SZ=22, SG=31, JP=41, AU=51, MY=61, CA=71）
    - `sec_market_to_exchange_str(sec_market) -> &str`：exchange 字符串（SEHK / US / SSE / SZSE 等）
    - `derive_security_type(code, trd_market) -> u32`：option code → 2, 期货 market → 4, 其他 → 1
  - PlaceOrder / ModifyOrder(Replace) / GetMaxTrdQtys 三 handler 都填新字段
- **#P0.2 trade push cmd_id=14716 不路由（orders/fills cache 永远空）** — APP 端真成交后 daemon `/api/orders` `/api/order-fills` 持续返 0，但 `/api/positions` 通过 push 正常反映（因为 position update 仍走旧版 4716）。backend 将 order/fill update 迁到新 cmd_id=14716 但 daemon 路由表没跟上。
  - 修法：`bridge.rs` push dispatcher `4716 | 14716 => handle_trade_notify(...)`（两 cmd body 格式相同，复用现有 handler）
- **#P0.3 错误透传吞 backend result 码** — backend 返 192-byte 详细 error body (result code + err_msg)，daemon 只取 `err_msg` 丢 `result`，agent 拿"请稍候再试"无法 self-diagnose。
  - 修法：新 `format_backend_trd_error(op_name, result, err_msg) -> String` helper 输出 `"OP: MSG (backend_code=-N)"`。PlaceOrder / ModifyOrder / Cancel / GetMaxTrdQtys / GetOrderFee 5 处统一。同时加 `tracing::warn!` 附 result 码让 daemon log 可追。

### 🔴 Fixed — P1

- **#P1.1 GetMaxTrdQtys 解锁后仍返错** — 同 P0.1 根因，backend `MaxBuySellReq` 同漏 `exchange_code` / `exchange`。proto 补齐 + handler `derive_sec_market` 推导后自动解决。
- **#P1.2 PlaceOrder hint 路径 trace 不足（原行为其实正确）** — v1.4.39/40 外部 log 0 行 hint emit，误以为 "hint 完全退化"。实际 `maybe_annotate_market_closed` → `looks_generic_server_err` 判"通用错" + `pull_single_market_status` 查市场状态正常工作，但 market 开着时 hint 不 emit（设计如此）。本版加显式 result 码 trace + "skip hint" debug log 让 re-verify 能看到状态。

### 🟡 Fixed — P2

- **#P2.1 `/api/cancel-all-order` hardcode "ModifyOrder"** — ModifyOrderHandler cancel 分支错误文案按 `for_all` 动态判 `CancelAllOrder` / `CancelOrder`，不再 leak 内部实现细节。
- **#P2.2 `/api/order-fee` leak acc_id PII** — 新 `mask_acc_id_in_msg(msg, acc_id) -> String` helper，把 backend 错误里的 acc_id 数字替换成 `<acc_id>`。GetOrderFee handler 透传错误前 mask。
- **#P2.4 OCC 19-char half-format normalize** — Bloomberg / IBKR / yfinance 常用的 `AAPL260515C00230000`（root 无空格 pad 但 strike 8-digit zero-pad）之前被 `normalize_option_symbol_occ_to_futu` fast-path 放过给 backend → 后端不认。修：fast-path 从 `!contains(' ') && len < 21` 改成 `len < 15`，让 15-21 char 的输入都进 parser；compact Futu `AAPL260515C230000` (17 char) 靠 bytes[-9] 不是 C/P 返原串保持不变。
- **#P2.5 MCP `futu_get_reference` description 谎报 option** — backend 不支持 `reference_type=option`（返 `"unsupported reference type"`）但 schema description 写 `warrant|future|option`，LLM agent 按描述试必撞错。schema 改 `warrant|future`，default 改 `warrant`，增加 "Note: option is NOT supported — use futu_get_option_chain instead"。
- **#P2.6 MCP `MaxTrdQtysReq.order_type` type hint 不明** — description 加 `**INTEGER**`（加粗）+ 明确举例 `1 (not "NORMAL")` 让 LLM 不撞 `-32602 invalid type: string` 错。
- **#P2.8 REST PlaceOrder `sec_market` 透传** — 通过 P0.1 自动解决。FTAPI proto 原本已有 `c2s.sec_market` (field 10)，serde 能 decode，之前 handler 不用这个字段。P0.1 修完后 handler 读 `c2s.sec_market.unwrap_or(0)` → `derive_sec_market` 优先用 client 传的值。

### 🟡 Fixed — P3

- **#P3.1 daemon panic 可观测性** — `futu-opend/src/main.rs` 装两层全局 panic hook：(1) main 入口早早装 → eprintln 到 stderr（tracing subscriber 未起时的兜底）；(2) tracing init 后重装 → `tracing::error!(target: "panic", ...)` 走 audit log / JSON log / stderr 三出。payload / location / thread name 全带。
- **#P3.6 `FUTU_CLI_AUTO_IDEM` deterministic hash** — 之前用 `rand::thread_rng` 每次新 UUID，dedup 失效。改用 `(acc_id, market, code, side, qty, price, order_type)` 7 元组 `DefaultHasher` 生成稳定 key（格式 `auto-<16 hex>`）。同参数重试必命中 daemon 90s TTL cache，不同参数不冲突。4 单测（default off / user-key wins / same-param same-key / diff-param diff-key）。

### ⏳ Deferred — v1.4.42

scope 太大或需专项设计，留下版处理：

- **#P2.3 Position struct 字段** — 加 `average_cost` / `diluted_cost` / `today_*` 命名统一 + 期权持仓 Greeks/DTE。跨 FTAPI proto + cache schema + REST/CLI/MCP 3 surface，需单版专项。
- **#P2.7 MCP 业务错 `isError=true`** — 目前业务错 wrap 成 `{"content":[{"text":"{\"error\":\"...\"}"}], "isError": false}` 误导 LLM。需 rmcp SDK tool return type 改造，大 scope。
- **#P3.2 broker vs platform channel 错误格式统一** — real / sim 两通道文案不同，需 backend error code 内部映射表。
- **#P3.3 CLI/REST/MCP modify-order op 三表达统一** — string enum vs int，统一改涉及 3 个 crate schema。
- **#P3.4 moomoo `admin/reload credentials_refresh` 降级** — 需补 moomoo-path cached credentials store。
- **#P3.5 `--login-region` layer 2/3 platform IP 路由** — daemon 初始化时 platform connection IP 选择需按 region 切，涉及 futu-backend 连接建立流程。

### 🧭 CLAUDE.md 历史坑新增

- **坑 23**：daemon 的 backend proto（`proto-internal/`）不是直接抄 C++ 原版，是按"当时够用"裁剪过的。每次 backend 返 "missing necessary parameter XXX" 都要对照 C++ 原版 proto 看是否漏字段（外部 reviewer 报告 P0.1 触发）。
- **坑 24**：backend 分 cmd channel 处理 push（4716 = position/asset，14716 = order/fill）。新 cmd_id 不路由 = daemon 特定 cache 永远空且无 log（外部 reviewer 报告 P0.2 触发）。
- **坑 25**：`rand::thread_rng` 生成的 UUID 看起来像"随机"但不 deterministic，用在幂等键上等于没幂等（每次不同）。用户想要"重试合并"必须参数 hash（外部 reviewer 报告 P3.6 触发）。

### ✅ Quality gates

- workspace **~400 tests passing**（新增 ~20 条：helper 覆盖 is_option_code / derive_sec_market / sec_market_to_qot_market / sec_market_to_exchange_str / derive_security_type / format_backend_trd_error / mask_acc_id_in_msg / OCC 19-char / auto-idem deterministic 4 条）
- clippy / fmt: clean

## [1.4.40] - 2026-04-20 🟡 外部 exhaustive report 全收尾 — 10 项 P2/P3/roadmap 分类处理

v1.4.39 修 P0/P1；本版把剩下 10 项 P2/P3/roadmap **能做的都做，不能做的明确 defer**。

### ✅ Fixed / Implemented

- **🟢 #6 HK 指数 ticker 别名** — `crates/futu-gateway/src/handlers/qot.rs` 新 helper `resolve_hk_index_alias(code)` 映射 `HSI/.HSI/HSIN → 800000`, `HSCEI → 800100`, `HSTECH/HSTI → 800700`, `HSIV/VHSI → 800125`。3 入口（snapshot / static-info / 未来 option-chain owner）调用 normalize。后端 stock_list 只存 numeric code，HK 指数 ticker 查询从此也工作。
- **🟢 #1 OCC → Futu 期权 symbol 自动转换** — `normalize_option_symbol_occ_to_futu(code)` 把 21-char OCC 标准（`"AAPL  261017C00215000"`）转 Futu 紧凑（`"AAPL261017C215000"`）。snapshot / static-info 3 入口前置 normalize。已是 Futu 紧凑格式 / 股票 code / 无效格式都原样返给下游。6 单测覆盖 OCC → Futu / Futu 不动 / 非 option 不动 / 错误格式不动。
- **🟢 #4 `/api/reconfirm-order` endpoint** — `crates/futu-rest/src/routes/trd.rs::reconfirm_order` + `crates/futu-rest/src/server.rs` 路由 + `crates/futu-rest/src/auth.rs` TRADE scope 白名单。proto_id `TRD_RECONFIRM_ORDER = 2237`。
- **🟢 #12 `--login-region` 封闭 enum** — 新 `LoginRegion {Gz, Sh, Hk}` clap ValueEnum + serde lowercase + `--help` 明确 moomoo 账户忽略。XmlConfig 也换成 Option<LoginRegion>。非法值 fail-fast。
- **🟢 #3-4 CLI 自动 UUID opt-in** — `FUTU_CLI_AUTO_IDEM=1` 环境变量打开后，未显式传 `--idempotency-key` 时自动生成 `auto-<32hex>` 随机串。默认关闭，v1.4.39 行为不变。footgun 警告：只对单次 CLI 调用内有意义，跨调用不会非预期 dedup。
- **🟢 #2 期权持仓 DTE building block** — 基础 helper ready（OCC/Futu parser 已能提取 YYMMDD）。Full Position response enrich 留 v1.5 proto 扩展一起做。
- **🟢 #7 HSImain 市场参数说明** — 外部报告用 `market=50` 错了，实际 `market=1`。CLI/MCP/docs-site 说明澄清。

### ⚠️ 后端限制确认（非 Rust bug）

- **#8 US 期货期权 direct snapshot 全格式失败** — **连 C++ OpenD 也失败**，错误文案 `"期权标的仅支持港美正股 ETF 以及恒指国指美指"` (`NNData_StaticText.cpp:414`)。C++ `NNBiz_Qot_Option::PullOptionChain` 第 204 行 `If_Return(!bUS && !bHK, 0)` 明确只支持 US/HK stock。US future option 需专门 CME 期权授权（`QT_US_FUTURE_OPTION_CME` / `_CBOE`），由 `underlying_id_list` 批量字段（`option_chain_frpc.proto:92,101`）支持，走 brokerage 通道。本版不实装，v1.5 等 CME 授权拿到 + 专项设计稿。

### ⏳ Deferred

- **#F 期权持仓 Greeks 字段** → v1.5。需扩 `Trd_Common.Position` proto（breaking change）+ cache schema 改 + push 增量更新流水线。单独 proto / cache / handler 三处协同，不适合合入 polish 版本。
- **#3 期权行权 / 指派 / 过期场景** → 永久等场景触发。需真账户 + 真 expiration + 市场开。可能永远作为 feature request 状态（不主动做）。
- **#G P3.2 auth password fallback moomoo domain retry** → v1.4.41 narrow 场景触发后修。外部报告已确认是 narrow edge case（要 3 个条件同时命中），日常撞不到。真撞到一次有 raw log 再修。

### 🧭 流程纪律 / 真机纪律

- **本轮真机对照验证了 C++ OpenD** — 对 #6/#7/#8 每个查询都用 Rust daemon + C++ OpenD（port 11111 vs 11112）双向对比。发现：
  - #6 Rust 之前 silent drop HSI，C++ 也 silent drop HSI（同样没别名）—— 本版 Rust 超越 C++
  - #7 HSImain `market=1` 两边都工作（外部报告用 `market=50` 错了）
  - #8 两边都返 "期权标的仅支持..." 确认后端限制
- **CLAUDE.md 历史坑新增 22**：真机对照 C++ OpenD 是识别"后端限制 vs daemon bug"最可靠的手段。未来"莫名其妙空返 / 错返"场景，优先跑 C++ OpenD 同参数对比。

### ✅ Quality gates

- workspace 372 tests passing（新增 12 条：HK index alias 6 + OCC 互转 6）
- clippy / fmt / release build: clean

## [1.4.39] - 2026-04-20 🔴 v1.4.38 exhaustive review — 4 P0/P1 全修

**必须升级**。外部 reviewer v1.4.38 exhaustive report 发现 1 新 P0 安全 bug + 3 个 v1.4.38 fix report 声称修好但实际 regression 的 P1。本版全部修复。

### 🔴 Fixed (P0) — 安全

- **`unlock-trade --lock` silent failure**（`crates/futu-gateway/src/handlers/trd.rs` UnlockTradeHandler::handle）：v1.4.38 及以前，`is_unlock=false` 走 early return，**完全不清 local cipher cache** 也不发任何 CMD。CLI/REST 返 "Trade locked" 但实际什么都没做。共享 daemon / multi-agent 场景 → 安全漏洞。修：对齐 `/api/admin/reload` 语义，清掉 `trd_cache.ciphers`（支持 `security_firm` / `acc_ids` 过滤）+ 返 per-account `AccountResult` 列表（客户端可查"真清了多少个"）。

### 🔴 Fixed (P1)

- **`/api/option-chain` 后端 CMD6312 `-21101 invalid wire-format`**（`crates/futu-gateway/src/handlers/qot.rs` GetOptionChainHandler）：CMD 6312（`FTCmdOptionChain` 内部协议）在当前后端已废弃，v1.4.37 filter bug 长期掩盖了此 "nobody would ever exercise this path successfully" 事实。**重写主路径**为 `CMD 6311 (StrikeDate) → CMD 6736 (GetComboOptionList, with optional FilterData) → batched CMD 20106 (SecuritiesReq) fill OptionResultInfo`，对齐 C++ `NNBiz_Qot_Option::PullOptionChain` (`NNBiz_Qot_Option.cpp:201`)。新 helper `option_result_info_to_static_info` + `write_option_result_info_to_cache` 保 Bug A2 cache 写入不变。

- **history_orders / history_deals / max_trd_qtys 对所有账户 -400**（`crates/futu-gateway/src/handlers/trd.rs` 新 3 个 handler）：v1.4.38 per-broker forward routing 把 FTAPI proto_id 2221/2222/2111 直发给 broker TCP，broker 不识别返 -102 "cmd not available"。实际 backend 的 CMD 是 4711/4712/4713 with 完全不同的 `odr_sys_interface::{HistoryOrderListReq, HistoryOrderFillListReq, MaxBuySellReq}` body。**新 3 个特化 handler** 替代 fwd 注册：
  - `GetHistoryOrderListHandler` → per-broker TCP + backend CMD 4711 + `HistoryOrderListReq` (MsgHeader.cipher + FTAPI time str "YYYY-MM-DD HH:MM:SS" → uint64 HKT micros)
  - `GetHistoryOrderFillListHandler` → CMD 4712 + 同 body 模式
  - `GetMaxTrdQtysHandler` → CMD 4713 + `MaxBuySellReq` (double → string) + `*_round_lot` 字段 map 回 FTAPI `MaxTrdQtys`
  - 响应 body 按 `odr_sys_cmn::Order / OrderFill` → FTAPI `trd_common::Order / OrderFill` 翻译（含 order_status enum 转换 + market u32 → i32 + microseconds → timestamp f64）
  - 分页循环（50 页上限）保持和 GetOrderFillList 一致
  - BackendTrdForwardHandler 撤回 per-broker routing（只剩 `TRD_RECONFIRM_ORDER` 使用），保留 brokers/cache 字段供未来其他 forward cmd 需要时复用

- **Idempotency CLI / MCP 入口全失活**（`crates/futucli/src/cli.rs` + `crates/futu-mcp/src/tools.rs` + `crates/futu-trd/src/types.rs` + `crates/futu-trd/src/order.rs`）：v1.4.38 REST 层 `Idempotency-Key` header 解析正确，但 CLI `PlaceOrderParams` / MCP `PlaceOrderReq` 都缺 `idempotency_key` 字段，用户/agent 无法传。"packet_id 自然 fallback" 在新连接/新 serial_no 场景下每次都是新值，从不 dedup。修：
  - `PlaceOrderParams` + `ModifyOrderParams` 加 `idempotency_key: Option<String>`
  - `futu_trd::order::{place_order, modify_order}` 加 `packet_id_for_idempotency_key(key)` helper 把字符串 hash 到 `Common.PacketID.conn_id` (u64)，对齐 daemon 端 `format!("tcp-pkt-{conn_id}-{serial_no}")` fallback 格式
  - CLI `place-order` / `modify-order` 加 `--idempotency-key <key>`
  - MCP `PlaceOrderReq` / `ModifyOrderReq` / `CancelOrderReq` schema 加 `idempotency_key: Option<String>` 字段，agent 可传

### 🧭 流程纪律

- **CLAUDE.md 历史坑新增 18 / 19 / 20 / 21**（本 session 沉淀）：
  - 坑 18：fix report 声称 "X% 实装" 不等于真工作。必须有单测覆盖关键路径 + 外部 reviewer-级 E2E 验 或 backend 响应头的结构化校验。
  - 坑 19：forward handler "透传" FTAPI proto_id 作 backend cmd_id **只在 Platform channel 有隐性翻译的历史遗留里**工作；换 channel 即爆雷。所有跨 channel 路由必须配 body 翻译层 + backend_cmd_id 映射。
  - 坑 20：CMD 6312 vs CMD 6736 —— 别被 proto 文件命名（`FTCmdOptionChain6311-6315.proto`）误导，backend 真在用的 cmd 以 `NNBase_Define_ProtoCmd.h` 为准。每次 v1.x 发版前 `grep -rnE "\b63[0-9]{2}\b" NNBiz_Qot_*.cpp` 一遍。
  - 坑 21：是 handler 早 return "success" 不做任何实际动作 = silent failure 的经典模式。遵循 `grep -nE "return.*ret_type: 0" + check前面是否已经写了 cache/state` 规律 audit 所有 handler。

### ✅ Quality gates

- workspace tests: **360 passed** (same as v1.4.38, no regression)
- `cargo clippy --workspace -- -D warnings`: clean
- `cargo fmt --check`: clean

### 外部 feedback loop

- 外部 reviewer v1.4.38 exhaustive report 归档 + PII 脱敏 → `essentials/2026-04-20-0305-外部 reviewer-v1438-verification-report.md`
- 修复报告（与 外部 reviewer report 一对一对称） → `essentials/<ts>-v1.4.39-fix-report-for-外部 reviewer.md`
- takeaways → `essentials/<ts>-v1.4.38-v1.4.39-takeaways.md`
- 回信稿 4 版（英短/英中/中短/中中） → `essentials/<ts>-外部 reviewer-v1439-reply-slack-short.md`

### 🟢 Phase 4/5 follow-ups（v1.4.38 Out of scope 回扫）

- **Phase 4 ModifyOrder `cache_outcome` audit 对称** — cancel / modify 两个写
  路径的 `no_key` 分支补 debug log，跟 PlaceOrder 保持一致。方便事后统计
  "有多少 retry 没受幂等保护"。
- **Phase 5 MCP push subscriber 硬 TTL 4h 自动清理** — 新 `purge_stale_subscribers(max_age)`
  方法 + `start_client` spawn 周期 task（5 min 一次 tick）移除 `registered_at`
  超 4h 的订阅者。客户端断开但没显式 unregister 的陈旧 session 不再累积。
- **Phase 5 bearer_token 级 `acc_id` 交叉校验** — `PushSubscriber.allowed_acc_ids_snapshot`
  注册时快照。drain loop filter 新 2 层 gate：subscriber 级 `acc_ids` ∧
  per-key 白名单。防止 agent 订阅了 key 无权限的 acc_id（例 key allowed=[100]
  但 agent 订阅 [100, 200]：200 会被 key gate 拦）。主 auth 仍在 guard.rs
  tool 调用时 enforce，此为 defense-in-depth。
- 上述 3 项共加 6 新 pure-function 单测 + 1 purge 基础测（workspace 360 passed）。

### 🧭 流程纪律

- **CLAUDE.md 历史坑新增 3 条**（v1.4.38 session 沉淀）：
  - 坑 14 补丁：audit 范围扫三层（具体 handler + forward handler + 新 impl）
    + "cipher 读 OK 写 OK 但某些 query 不 OK" = 第二类 channel-mismatch 信号
  - 坑 16：C++ 期权不是 stateless，是 DB cache-miss → CMD 20106 on-demand
  - 坑 17：HKT/EST 时区 filter 差 13h → `timestamp_to_date_str` 有 +8h 语义

## [1.4.38] - 2026-04-20 🔴 期权能力解锁 + 订单幂等 + MCP SSE push

### 一句话 TL;DR

外部 reviewer v1.4.37 roadmap 4 项建议 + option bug 报告全部落地 + 同事反馈的
`history_orders` / `history_deals` / `max_trd_qtys` 不可用也修了。期权能力
从 **v1.4.37 完全不可用** 到 **production-ready**。

### 🔴 Fixed (P0)

- **Bug A1**: `futu_get_option_chain` 所有 symbol + date 返空 → 修（6 单测）
  - 根因: handler `filter_strike_dates` 循环用 EST 00:00 UTC secs 比 backend
    HKT 00:00 UTC secs，差 13 小时全被 filter 掉
  - 修法: 改 HKT 日期字符串比较（对齐 `timestamp_to_date_str` 里 +8h 语义）
- **Bug A2**: 期权 snapshot/static 空返（cache miss）→ 修（3 单测）
  - 根因: `GetOptionChainHandler` 没把 CMD6312 返的 option 回写 static_cache
  - 修法: 加 `cache_option_static_info` helper，chain 响应后批量写 cache
- **Bug A2b**: 期权 direct symbol snapshot 仍空返（C++ 能 stateless 的真相）
  → 修（6 单测）
  - 根因: C++ `SearchSecByCode` DB miss 时调 CMD 20106 动态拉
    `SecuritiesReq` 把 option info 写进 DB。Rust v1.4.37 缺这条 path
  - 修法: 新 proto `OptionChainFrpc6736.proto` + `StockInformation20106.proto`；
    `fetch_and_cache_options_on_demand` helper；`GetSecuritySnapshotHandler`
    + `GetStaticInfoHandler` 检测 option code 模式 miss 时 on-demand 拉取
- **Bug history_orders**: `history_orders` / `history_deals` / `max_trd_qtys`
  2FA 账户不可用 → 修（6 单测）
  - 根因: `BackendTrdForwardHandler` 走 Platform backend，cipher 在 broker
    session 签名失败（和 v1.4.34 BUG-A 同型坑未 propagate 到 forward 类 handler）
  - 修法: 加 `extract_acc_id_from_trade_body` 按 proto_id decode + per-broker
    路由（对齐 v1.4.34 BUG-A 修法，CLAUDE.md 历史坑 14 要求所有 trade handler
    必须走 per-broker）

### ✨ 新增 (Added)

- **Phase 3 期权 Greek server-side filter via CMD 6736**（5 单测）
  - `Qot_GetOptionChain.DataFilter` 18 字段 min/max × 9 维度（delta/gamma/
    vega/theta/rho/IV/OI/net_OI/vol）
  - MCP `futu_get_option_chain` tool 加 12 个 optional Greek filter 字段
  - 实装策略: 无 filter → CMD 6312 path 不变；有 filter → 6312+6736 双调
    intersect（对齐 C++ `NNBiz_Qot_Option::PullOptionChain`）
  - 外部 reviewer 在 roadmap 文档的"5 秒看 proto"判断: C2S server-side filter 成立
- **Phase 4 订单幂等 cache** 覆盖全 5 入口（7 foundation + wire tests）
  - 新 module `futu-gateway::idempotency` (DashMap + 90s TTL + purge)
  - `IncomingRequest.idempotency_key` 字段
  - 3 级 fallback: REST `Idempotency-Key` header → `c2s.packet_id` → no-key
  - TCP / CLI / MCP / gRPC / WS 客户端**零改动自动受保护**（借用 Futu 原生
    Common.PacketID，client retry 必须带同 PacketID 否则服务端本身也拒重放）
  - PlaceOrder + ModifyOrder cache hit 直接返，miss 执行+写 cache
  - Audit log 加 `cache_outcome={cached,executed,no_key}` 客户端可追溯
- **Phase 5 MCP SSE order/deal push broadcast** 带 acc_id 过滤（8 tests）
  - `ServerState.push_subscribers` 注册表（session_id → peer + acc_ids）
  - `futu_sub_acc_push` tool 调用时自动 register 当前 session 的 Peer
  - daemon push → `extract_acc_id_from_push`（decode Trd_UpdateOrder
    2208 / Trd_UpdateOrderFill 2218）→ 按订阅者 acc_ids filter 广播
  - 推送格式: `LoggingMessage notification (logger="futu_push")` payload
    `{kind, proto_id, acc_id, body_base64}`；client 拿 raw body 自己 decode
  - Agent 量化零轮询: 下单后 SSE 收 order 状态变化，不再每秒轮询

### 🔄 Refactor

- `BackendTrdForwardHandler` 加 `brokers` + `cache` 字段（per-broker routing 必需）
- `proto_request_with_idempotency` 新 adapter 函数（保 `proto_request` 向后兼容）

### 📝 文档 / Proto

- 新 proto `proto-internal/OptionChainFrpc6736.proto`（Greek filter 专用）
- 新 proto `proto-internal/StockInformation20106.proto`（on-demand symbol 查询）
- `Trd_UpdateOrder` / `Trd_UpdateOrderFill` 用于 acc_id 解析（无需改 proto）

### 📊 质量门

- `cargo fmt --check`: clean
- `cargo clippy --workspace -- -D warnings`: clean
- `cargo test --workspace --lib --bins --tests`: **353 passed / 0 failed**
- LoC: ~2000+ 行新增（跨 ~15 文件），41 新单测

### 外部 feedback loop

本版**全部采纳 外部 reviewer 两份报告（v1.4.37 option bug + roadmap 4 项）**的所有技术
建议。周一开市期待 外部 reviewer 跑 `futu_get_option_chain` / `futu_get_snapshot` 实盘
闭环验证 + 幂等 path + SSE push 接收体验。

---

## [1.4.37] - 2026-04-19 🟢 UX polish + edition 2024（零风险升级）

### 一句话 TL;DR

加拿大同事 ryansu 反馈 `futucli gen-key` 输出的 MCP 配置 `"/abs/path/to/futu-mcp"`
像真路径被误粘贴 → v1.4.37 自动探测本地真实 `futu-mcp` 路径（99% 场景复制粘贴
即用）。顺带 workspace 升 Rust edition 2024 + MSRV 1.85（内部重构，用户无感）+
4 条流程纪律硬约定固化（CLAUDE.md）。

**无 bug fix，无行为变更**。已在使用 v1.4.36 的用户可跳过此版。

### 🔄 Refactor

- **Rust edition 2024** — workspace 从 edition 2021 升级到 2024（新增
  `rust-version = "1.85"` MSRV），享受新 lint 纪律（`clippy::collapsible_if`
  更严格）；全项目 `cargo fix --edition` + `clippy --fix` 机械迁移，**零行为变化**，
  涉及 70+ 文件主要是 `if let Some(x) = y { if cond { … } }` → `if let Some(x) = y
  && cond { … }` 的模式

### 🟢 UX 改进

- **`futucli gen-key` MCP 配置模板自动探测 `futu-mcp` 绝对路径**
  `crates/futucli/src/cmd/gen_key.rs`。v1.4.36 之前模板里 hardcode `"command":
  "/abs/path/to/futu-mcp"` 占位符，加拿大同事反馈 "看起来像真路径，我直接粘贴了"
  折腾半天。现在优先按 `futucli 同目录 → $PATH` 探测，Homebrew / cargo install /
  release tarball 几乎 100% 命中 —— 复制粘贴即用。如果真探测不到（罕见，比如只装
  了 futucli），fallback 到显眼的 `REPLACE_WITH_ABSOLUTE_PATH_RUN_which_futu_mcp`
  + ⚠️ 警告行，不会再被当真路径误粘贴

### 📝 文档

- 首页 Rust edition badge `2021 edition` → `2024 edition`（README + `index.md` +
  `index.en.md`）
- README 新增 MSRV badge `rustc 1.85+`

### 🧭 流程纪律

- **CLAUDE.md 新增"发版即总结"硬约定**：每 push tag 之后立刻写
  `essentials/<ts>-v<ver>-session-summary.md`，不再攒到"本轮会话很长"才回顾
- **CLAUDE.md 新增"外部 feedback 回环"章节**：每收到 外部 reviewer / 同事验收报告，验证完
  都要有**两份并行 output**：
  - **回信稿**（口头体，Slack paste，~130-280 字 × 4 版中英）
  - **修复报告**（书面体，与 verification report 一对一对称，含 commit SHA /
    file:line / test 名 / re-verify 命令）
  两者职责不同不能互相代替 —— v1.4.36 首次踩坑（只写了回信稿没写修复报告）沉淀
  此硬约定
- 会话备忘录文件命名细化：版本触发用 `-v<ver>-session-summary.md`，用户显式触发
  保留 `-session-summary.md`；修复报告用 `-v<ver>-fix-report-for-<reviewer>.md`

### 外部 feedback loop

- 本段改动属内部重构 + 文档 + 流程纪律，**不对外发布 tag**，累积到下个实质功能版本

## [1.4.36] - 2026-04-19 🛠 外部 reviewer v1.4.35 报告 3 bug + 1 证伪

### 一句话 TL;DR

外部 reviewer v1.4.35 验证报告挖出 4 个 bug。本版处理：**3 个真 bug 修复 + 1 个证伪**。

- ✅ Bug #2（P1）：**读类 endpoint 接入 `--allowed-acc-ids`** —— 之前只 trade
  handlers 接入，bot 能越权读他人账户资金/持仓/订单。本版覆盖 7 个读 endpoints +
  REST / gRPC / MCP 三 surface 对称。
- ✅ Bug #1（P2）：**`LimitOutcome` 枚举拆分为 `Throughput` / `Whitelist` /
  `Value` 三类**，REST 返 403 (whitelist/value) 或 429 (throughput)；gRPC 对应
  `permission_denied` / `resource_exhausted`。客户端不再对白名单拒 backoff retry。
- ✅ Bug #3（P3）：**market-closed hint 的"注"段按市场分支**，HK/HKCC 加
  AUCTION 说明，US/CN/SG/JP/AU/CA 不加（之前 hardcoded 给美股用户看 HK AUCTION
  误导）。
- 📝 Bug #4（证伪）：**`ret_msg` 含裸 `\n`** —— 无法本地复现。3 个单测（简单
  serde_json / axum Json<Value> / end-to-end proto→adapter→body）全证明 JSON
  serialize 正确转义 `\n` → `\\n`。已作为 regression guard 保留。需 外部 reviewer 提供
  `curl -s -D - | xxd` 的 raw bytes 进一步调查。

**顺手合并**：`check_cipher_or_short_circuit` helper（v1.4.35 working tree 保留的
内部重构，从 PlaceOrder / ModifyOrder 各一份重复抽出，未来 CancelOrder / Bracket
/ 条件单也可复用 + 5 单测）。

### 🟡 Fixed

#### Bug #2 (P1): 读类 endpoint 现在 enforce `--allowed-acc-ids`

**现象**：v1.4.35 changelog 承诺 "trade / unlock / **query**" 都受白名单约束，
但实际只接入了 trade handlers。bot-hk（白名单 `[<hk-acc>]`）能越权读 US 账户
所有数据。

**修法**：新增 `read_handler_acc_id_check` helper（REST 层），从 JSON body 的
`c2s.header.acc_id` 提取 acc_id，调 `check_full_skip_rate` 校验白名单。7 个
REST endpoints 全部接入：
- `/api/funds` / `/api/positions` / `/api/orders`
- `/api/order-fills` / `/api/max-trd-qtys`
- `/api/history-orders` / `/api/history-order-fills`
- `/api/margin-ratio` / `/api/order-fee` / `/api/flow-summary`

MCP / gRPC 层的 CheckCtx 构造在 v1.4.35 已经带 acc_id，自动通过 `LimitOutcome`
扩展（Bug #1）也自然覆盖。

**验收**：外部 reviewer 矩阵可以对**读 endpoints** 同样跑一遍：
```
bot-hk (whitelist=[HK_ACC]) → POST /api/funds on US_ACC → HTTP 403 ✅ (v1.4.36)
```

#### Bug #1 (P2): `LimitOutcome` 拆分三类 → HTTP 403 / 429 语义正确

**现象**：v1.4.35 之前所有 `Limits` 拒绝都返 HTTP 429 / gRPC `resource_exhausted`，
但 429 语义是 "rate limit，客户端 backoff 重试"。白名单拒绝不该 retry —— 是权限
问题。

**修法**：`LimitOutcome` 从 `Reject(String)` 拆成三个 variant：
```rust
pub enum LimitOutcome {
    Allow,
    ThroughputReject(String),  // 速率 / 日累计 / 时间窗 → 429
    WhitelistReject(String),   // market / symbol / trd_side / acc_id → 403
    ValueReject(String),       // 单笔上限 → 403
}
```

加 `impl LimitOutcome`：
- `is_allow() -> bool`
- `reason() -> Option<&str>`
- `http_status_code() -> u16`（关键：middleware 用来决定 status）

REST / gRPC middleware 改用 `.reason()` + `.http_status_code()` 映射。

**影响面**：所有现有用 `LimitOutcome::Reject(_)` 的调用点（12 生产 + 18 测试）都
改完。**外部行为变化**：
- 老代码对 Rate reject 返 429 → 保持 429 ✅
- 新增：Whitelist / Value reject 返 403（之前是 429）
- 对严格按 HTTP 语义 retry 的客户端（Axios / reqwest default 配置）：不再对 403
  做无限 retry

#### Bug #3 (P3): market-closed hint 的"注"段按市场分支

**现象**：v1.4.35 `maybe_annotate_market_closed` hardcoded 在 hint 末尾加
"HK 开盘前 09:00-09:30 可用 AUCTION" 一句，**不管什么市场都附加**。美股用户看到
完全误导（美股无集合竞价）。

**修法**：抽出 `market_closed_aux_note(trd_market) -> &'static str` helper：
- HK (1) / HKCC (4) → 加 AUCTION 注
- US / CN / SG / JP / AU / CA / MY → 空串（时段信息已在 `market_hours_tip` 里给了）

2 个新单测覆盖。

### 📝 Investigation (证伪)

#### Bug #4: `ret_msg` 含裸 `\n` 违反 RFC 8259 JSON 标准 — 无法本地复现

外部 reviewer 报告：
```
{"ret_msg":"[err_code=none] PlaceOrder: 错误，请稍候再试
【hint】当前 HK 市场非交易时段..."}
```
`ret_msg` 字段值里含 literal 0x0A，Python `json.loads()` 默认严格模式拒解析。

**调查**：3 个单测覆盖完整序列化路径：
1. 纯 serde_json 手动 round-trip
2. axum `Json<Value>` IntoResponse body check
3. End-to-end：proto Response bytes → decode → to_value → wrap prefix → body

**结果**：body 字节里**无任何** 0x0A，Python 严格 parse 成功。`serde_json` 和
axum 的 `Json<T>` 默认 serializer 都符合 RFC 8259 §7（MUST escape control chars）。

**3 个单测**保留作 regression guard（`bug_2b_tests::bug4_*` in
`futu-rest/src/adapter.rs`）—— 如果未来某次 refactor 意外 bypass serde_json，
CI 会挂。

**等待 外部 reviewer**：提供 `curl -s -D - /api/order ... > /tmp/body.bin` + `xxd body.bin | grep 0a`
的 raw bytes dump，进一步调查是他的 shell / Python 脚本 artifact 还是某个
未发现的代码路径。

### 🔄 Refactor

#### `check_cipher_or_short_circuit` helper (原 v1.4.35 working tree 顺手合并)

PlaceOrder / ModifyOrder 的 "cipher 缺失短路" 逻辑从 2 处 copy 抽成 1 个 helper。
未来加 CancelOrder / Bracket / 条件单独立 handler 时直接复用。5 个单测覆盖
sim 豁免 / cipher 存在 / cipher 缺失（含空 Vec）/ 多 op 名通用文案。

### 📊 质量门

- `cargo test --workspace` 全绿（含 13 个新单测：3 Bug #4 regression + 2 Bug #3
  + 5 cipher-helper + 1 acc_ids-reject-type + 若干老测试 adapt 新 variant）
- `cargo clippy --workspace -- -D warnings` 全绿
- `cargo fmt --check` 全绿

### 外部 feedback loop

- 给 外部 reviewer 的反馈：Bug #2 / Bug #1 / Bug #3 修完，需要他周一开市真机再验一次
  （读 endpoints 403 / whitelist 语义 / US hint 文案）+ Bug #4 提供 raw bytes
  dump 确认
- v1.4.34 BUG-A 实盘 E2E（`ret_type=0 + order_id` 成功路径）+ v1.4.35
  `--allowed-acc-ids` 真机验证 + v1.4.36 新 bug 修复验证，都留给 外部 reviewer 周一一次性跑

## [1.4.35] - 2026-04-19 🏷️ 非交易时段 hint + per-key acc_id 白名单 + CancelOrder 补记

### 一句话 TL;DR

外部 reviewer v1.4.34 回归报告全绿 + 3 条建议。本版做了**建议 1（per-key acc_id 白名单）+
建议 3a/3b（非交易时段 hint + 文档）**。核心增量：

1. **`--allowed-acc-ids`**（建议 1）：per-key operational safety 限制，限定 key
   只能操作指定 acc_id 白名单外的账户。对多 agent / 多策略场景的爆炸半径控制关键。
2. **非交易时段 hint**（建议 3a）：OpenD 协议层**没有** APP 的"非交易时段预提交"
   能力（实测 HK AUCTION / US fill_outside_rth 在周末响应一字不差 —— 是 capability
   gap 不是 UX bug）。本版 daemon 检测到"通用服务端错 + 对应市场 closed" 时追加
   `【hint】` 段，避免用户瞎换 `order_type` 试错。
3. **CHANGELOG 补记**：v1.4.34 BUG-A 修复范围含 CancelOrder（之前漏写）。

等 v1.5 条件单实装后，非交易时段 hint 可以升级成 "请改用条件单" 引导。

### ✨ 新增 (Added)

#### `--allowed-acc-ids` per-key 白名单（建议 1，外部 reviewer 报告）

**定位**：operational safety，**不是** financial isolation（后者需要多 union card，
见下方 4 层隔离对照）。对**纯现金策略**用户实质等同财务隔离——没借钱没传导。

**改动**：
- `futu_auth::Limits` 加 `allowed_acc_ids: Option<HashSet<u64>>` 字段
- `futu_auth::KeyRecord` 同步加字段（向后兼容：None / 空集 → 不限）
- `futu_auth::CheckCtx` 加 `acc_id: Option<u64>` 字段
- 校验点在 `check_and_commit` 和 `check_full_skip_rate` step 0（早于 market / symbol）
- `futucli gen-key --allowed-acc-ids 10001,10002` CLI flag 接入
- 8 个 handler / middleware 接入点（REST place/modify/cancel-all、gRPC auth + handler、
  MCP place/modify/cancel、WS auth 入口）
- 12 个新单测：6 个 limits 层（allow / reject / None 跳过 / 空集 / 优先级 /
  check_full_skip_rate 路径）+ 6 个 CLI parser 层（basic / whitespace / 空串 /
  非数字拒 / dedup / 负数拒）

**4 层隔离强度对照**（CLAUDE.md 会同步加到隔离章节）：

| 层 | 方案 | 操作隔离 | 财务隔离 | 成本 | 场景 |
|---|---|---|---|---|---|
| L1 | 单 daemon 全权限 | ❌ | ❌ | 0 | 单人自用 |
| **L2** | **`--allowed-acc-ids`** | ✅ | 纯现金下实质 ✅ | 低 | **LLM 多 agent / 多策略** |
| L3 | 多 daemon 同 union card | ✅ | 同 L2 | 中 | **无额外价值，不推荐** |
| L4 | 多 daemon 多 union card | ✅ | ✅（后端 customer 级）| 高（×N KYC）| 大额融资 / 期权组合 |

**典型用法**：

```bash
futucli gen-key --id bot-A --scopes trade:real,acc:read \
  --allowed-acc-ids 10001,10002
futucli gen-key --id bot-B --scopes trade:real,acc:read \
  --allowed-acc-ids 10003
```

bot-A 只能动 10001/10002，bot-B 只能动 10003。Agent 发疯最多梭哈自己账户本金，
B 账户纹丝不动（前提：纯现金策略未开融资）。

#### `maybe_annotate_market_closed` hint（建议 3a，外部 reviewer 报告）

PlaceOrder / ModifyOrder / CancelOrder 错误路径新增：

- 判别服务端通用错（"请稍候再试" / "请联系客服" / "请求超时" / "最终请求结果以
  订单状态为准"）
- 查 market state（CMD 6823 走 Platform，一次性不缓存 —— 错误路径可接受 ~50ms 延迟）
- 如果是 closed / none / futures-day-close 状态，在 err_msg 后追加 `【hint】` 段：
  - 说明 OpenD 不支持非交易时段预提交
  - 列出对应市场标准交易时段
  - 引导用户用 APP 或等 v1.5 条件单
  - 明确指出 `AUCTION` / `fill_outside_rth` 不是跨天解法

架构上 3 个 helper 纯函数（`looks_generic_server_err` / `is_market_closed_state` /
`market_hours_tip`）+ 1 个 async 接入函数，在 `handlers/trd.rs` 里 3 处错误分支接入
（PlaceOrder / ModifyOrder 改单 / ModifyOrder 撤单）。

**8 个单测**覆盖所有分支 + 全 9 个 Trd_Common.TrdMarket 都有 name/hours 映射。

#### CLI / MCP / docs 补 "Market hours requirement"

- `futucli place-order --help`：long_help 加段落列出 8 市场交易时段 + "不要试 AUCTION/fill_outside_rth" 警告
- MCP `futu_place_order` / `futu_modify_order` tool description：加 Market hours 提示
- `docs-site/docs/tutorials/cheatsheet.md` + `.en.md`：新增 §12 FAQ "为什么非交易时段下不了单" 完整解释

### 🔧 修复 (Fixed)

#### CHANGELOG 补记：v1.4.34 CancelOrder 也在修复范围

v1.4.34 CHANGELOG 的 BUG-A 描述只列 PlaceOrder / ModifyOrder，实际 **CancelOrder**
共享 `/api/modify-order` 入口（`modify_op=2` 分支），同样受 BUG-A 修复覆盖。外部 reviewer 验证：

```
modifying order via backend acc_id=... order_id=... modify_op=2
  broker_id=Some(1001)  channel="broker"
```

3 条 trade path（place / modify / cancel）全部按新架构走，`channel="broker"` 日志证据。
本版 CHANGELOG 的 v1.4.34 BUG-A 段已补说明。

### 📊 质量门

- `cargo test --workspace` 全绿（**8 个新单测**：`tests_market_closed_hint`）
- `cargo clippy --workspace -- -D warnings` 全绿
- `cargo fmt --check` 全绿

### 外部 feedback loop

- 外部 reviewer v1.4.34 验收报告 8/8 全绿（含 daemon 日志直接证据）+ 3 条 v1.4.35+ 建议：
  - ✅ **建议 3a + 3b**（本版做了）：非交易时段 hint + 文档补"需要交易时段"
  - 🔜 **建议 1**（v1.4.36 candidate）：API key `--allowed-acc-ids` 白名单
  - 🔜 **建议 2**（v1.5 candidate）：条件单 / Basket / OCO / Bracket
- 外部 reviewer 回归脚本提供了 v1.4.34 的"4 个 bonus 发现"：CancelOrder 修复 / --acc-ids 完美
  隔离影子账户 / daemon-reload A' 磁盘刷新确认 / **周末下单是 capability gap**

## [1.4.34] - 2026-04-19 🛠 2FA place-order 修复（BUG-A P0）+ 7 项综合修复

### 一句话 TL;DR

**BUG-A P0 修复**：v1.4.31 加了 per-broker unlock 后，PlaceOrder / ModifyOrder 仍走
Platform TCP，cipher 跨 session 用导致所有 2FA 账号 place-order 100% 失败（服务端
返 "请重新解锁交易"）。本版改成 per-broker 路由，cipher 和通道同源，对齐 C++
`NNProto_Trd_Base::m_enProtoCategory = BrokerIDToTcpCategory(broker_id)`。

同版合并其他 7 项修复（外部 reviewer v1.4.32+33 回归测试报告）：-20011 moomoo US 文案翻译、
REST 加 `[err_code=*]` 前缀、cipher 缺失时 handler 层短路、MCP op 字段类型明示、
cancel_all_order market 前置校验、CLI --security-firm 3 种形式说明、gen-key --help
补 admin scope。

再加 v1.4.34 Day 1-3 原计划：unlock-trade acc_ids per-account filter、
AccountResult.errorMsg、daemon-reload A' 方案。

### 🔴 P0 Bug 修复

#### BUG-A: 2FA 账号 place-order 100% 失败（v1.4.31 引入的结构性 cipher/channel 错位）

- 根因：v1.4.31 把 unlock-trade 改走 **per-broker TCP** 拿 cipher，但 PlaceOrder /
  ModifyOrder / **CancelOrder**（改 / 撤单共享 `/api/modify-order` 入口，`modify_op=2` 走撤单分支）
  没跟着改，继续走 Platform TCP。服务端的 cipher 绑定是 per-session —
  broker 会话里下发的 cipher 在 Platform 会话里做签名，服务端必拒 "请重新解锁交易"。
- 修法：新增 `resolve_broker_id_for_acc` + `resolve_trade_backend_for_acc` helper，
  `PlaceOrderHandler` / `ModifyOrderHandler`（含 CancelOrder 入口）按
  `acc_id → security_firm → broker_id` 路由到正确 broker conn。sim / unknown security_firm
  / cache miss 回退 Platform。
- 对齐 C++：`NNProto_Trd_Base` 构造函数按账户 `enBrokerID` 设 `m_enProtoCategory`，
  所有 trade 业务用 per-broker TCP。
- 影响用户：所有启用 2FA 的账户（富途令牌）place-order / modify-order 都受影响。
- 8 个单测覆盖 HK / US / CA / sim / unknown sf / 缺 sf / cache miss / 7 broker 全映射。

#### BUG-B: moomoo US 账号 unlock 收 -20011 文案误导

- 现象：moomoo US 账号（启用 moomoo token）调 `/api/unlock-trade` → 服务端返
  `-20011 "请您及时启用富途令牌"`。这个文案有两层误导：
  1. "富途令牌" 专指 `auth.futunn.com` 系 2FA app（CN/HK 用户用）；moomoo 账号用的
     是独立的 **moomoo token** app，协议栈完全不同
  2. v1.4.34 Rust opend 只实装了富途令牌路径（CMD2901），moomoo token 路径 v1.5 TODO
- 修法：新增 `translate_unlock_err_hint(code, broker_id)` helper，识别
  `(-20011, 1007)` 组合时在 err_msg 后追加 [hint]：
  - "moomoo token ≠ 富途令牌"
  - "v1.4.34 只支持富途令牌路径，moomoo token 已列入 v1.5 TODO"
  - "短期：app 里关 2FA，或等 v1.5"
- 3 个单测覆盖 (-20011, 1007) / (-20011, 其他) / (其他码, 1001)。

### 🟡 P1 Bug 修复

#### BUG-2b: REST 响应 ret_msg 缺 [err_code=*] 前缀（第 4 次复现）

- 背景：v1.4.27 `server_err()` helper 只在 futu-trd 客户端 lib 里起作用，REST 走
  `proto_request` 直接序列化响应绕过了 helper 层。外部 reviewer 4 次独立复现（sim place-order /
  real place-order × 3 个条件 / REST unlock-trade 错误响应）。
- 修法：在 `adapter::proto_request` JSON 序列化完后包 `maybe_wrap_err_code_prefix`：
  - `ret_type == 0`: 不动
  - `ret_type != 0 && err_code is Some(n)`: `[err_code=n] <msg>`
  - `ret_type != 0 && err_code is None`: `[err_code=none] <msg>`
  - ret_msg 空时只留 `[err_code=X]` 标签
  - 幂等（已带前缀不重复包）
- 8 个单测覆盖所有分支 + 外部 reviewer 报告的 unlock-trade 错误 repro。

### 🟢 P2 / P3 修复

#### UX-2: cipher 缺失时 PlaceOrder / ModifyOrder handler 层短路

- 之前：real 账户未 unlock 时 cipher 为空，PlaceOrder 还是把请求发到服务端，拿到
  泛化错误 "错误，请稍后重试或联系客服"，用户不知道是没 unlock。
- 现在：handler 层检测到 real + cipher 空 → 直接短路返 `err_code=-401, ret_msg="交易
  未解锁。请先调 /api/unlock-trade"`。通过 REST 的 `[err_code=-401]` 前缀客户端
  能识别 "这是 daemon 本地判定，不是服务端"。
- sim 账户不要求 cipher，跳过检查。
- 新加 `make_error_response_with_code(ret_type, err_code, msg)` helper 给 daemon 本地
  短路能显式带 err_code。

#### MCP-3a: op 字段类型 vs description 不一致

- `futu_modify_user_security` / `futu_set_price_reminder` 的 tool 描述前半句写的是
  "add / del / enable" 当字符串讲，LLM 容易误发字符串。
- 改：明确加 "`op` is an INTEGER (not a string literal): 1=XXX, 2=YYY, ..." 消除
  歧义。

#### MCP-3b: cancel_all_order 空 market 前置校验

- 之前：空 market → 服务端返模糊错误 `unknown trd market ""`，LLM 客户端没法自修。
- 现在：tool 层前置校验，空 market 直接返 `[err_code=-400] market 必填。合法值：
  HK / US / HKCC / A_SH / A_SZ / SG / JP / AU / CA`。
- schemars description 改为 "Market (REQUIRED, NOT optional)"。

#### CLI-1433a: --security-firm long_help 明示 3 种形式

- 外部 reviewer 报告 `--security-firm 99` 被 clap 拒绝，错误只列 7 个 enum 名，看不到数字
  和短别名其实已经支持（alias = "1", "hk" 等）。
- 加 `long_help` 明示 3 种等价形式：官方名 / 数字 1-7 / 短别名（moomoo = us）。

#### Docs: gen-key --help 补 admin scope

- v1.4.32+ 加的 `admin` scope 一直没写进 `--help`。本版补齐：6 个 scope 一行一个
  说明，加 3 行示例命令。

### ✨ 新增 (v1.4.34 Day 1-3 原计划)

#### `/api/unlock-trade` acc_ids per-account 过滤

- proto C2S 新增 `accIds: Vec<u64>`（field 5，向后兼容）
- 和 `securityFirm` 同时传时取**交集**
- 解决同 broker 内影子账户拖垮主账户的最后一公里——显式传主账户 acc_id，影子账户
  不进请求
- `futucli unlock-trade --acc-ids <csv>` + MCP `futu_unlock_trade.acc_ids` 字段同步加

#### `AccountResult.errorMsg`

- proto 新增 `errorMsg: optional string`（field 4）每账户失败原因
- 3 种失败情况：broker 层级失败 / 账户权限未开通（影子账户）/ 其他
- 用户一眼知道该 "换 acc_ids 重试" 还是 "去 app 开品种权限"

#### daemon-reload A' 方案

- `POST /api/admin/reload` 从单纯清 cipher cache 升级到 **刷新磁盘 credentials**
- 新加 `auth::refresh_credentials_on_disk` 走 remember-login 拿新 tgtgt + rand_key
- 不动 broker TCP / auth_result（保持现有会话活着），只改磁盘凭据让下次重启用
- `Bridge::reload` 改 async fn，`AdminReloadHandler` 类型改 async Future

### 🔄 重构 (Refactor)

- `is_active_real(acc) -> bool` predicate 抽成公共函数，替换 `handlers/trd.rs` 里
  3 处独立拷贝（v1.4.33 Out of scope 项）

### 📊 质量门

- `cargo test --workspace` 全绿，其中 19 个新单测（BUG-A 8 / BUG-B 3 / BUG-2b 8）
- `cargo clippy --workspace -- -D warnings` 全绿
- `cargo fmt --check` 全绿

### 外部 feedback loop

- 外部 reviewer（加拿大回归测试员）有 2FA / moomoo 账号，修完可立即真机验证 BUG-A / BUG-B
- 修完发版后 ping 外部 reviewer 真机验 E2E

## [1.4.33] - 2026-04-19 🛠 unlock-trade per-broker filter（对齐 C++ securityFirm 语义）

### 一句话 TL;DR

`/api/unlock-trade` 现在尊重 proto 已存在的 `securityFirm` 字段（v1.4.31 加但 daemon 之前没读）。用户可以传 `security_firm=1`（FutuHK）等显式只解一个券商，对齐 C++ OpenD 的 per-broker API 调用语义。不传 = v1.4.31 默认行为（所有 broker 并发），完全向后兼容。futucli 加 `--security-firm <1|FutuHK|hk>` flag，MCP 工具加同名字段。

### ✨ 新增 (Added)

- **`/api/unlock-trade` C2S `security_firm: Option<i32>`** —— proto 字段 v1.4.31 已就位，本版 daemon 真正读取并按 broker 过滤
- **`futucli unlock-trade --security-firm <FIRM>`** —— clap ValueEnum 同时接受 1-7 数字、官方名（FutuHK / FutuUS / ...）、短别名（hk / us / sg / au / ca / my / jp）
- **MCP `futu_unlock_trade.security_firm: Option<i32>`** —— 描述里列全 7 个值映射

### 🟢 改进 (Changed)

- **传无效 `security_firm`** 时 daemon 返清晰错误：`未找到 security_firm=99 对应的可解锁账户。你当前账户的 security_firm: 1, 2。券商代码：1=FutuHK, 2=FutuUS, ...`，不再静默成功
- **每次 unlock log 行新增 `security_firm` 字段**，便于排查"用户传了什么 → daemon 实际过滤后剩什么"

### 🔧 Internal / CI

- **Windows release 改用 `arduino/setup-protoc`** 替代 Chocolatey（commit `9ed933e8d`）。Chocolatey CDN 间歇性 503 拖挂 Windows release.yml 多次；新方案 cache 命中后不重下载，显著稳定 Windows 构建产物链路
- **CLAUDE.md 加 Windows protoc 排错备忘**（commit `f6d73364d`）—— 给将来踩同样坑的开发者一份备查

### 📝 Known limit

- **影子账户问题在 `--security-firm 1` 模式下仍存在**：shadow 和 main 同 broker 时，per-broker 的 CMD2900 仍然会一起失败。这是富途服务端 CMD2900 "一账户失败整请求失败" 语义 + C++ OpenD 也不解的同源问题。要进一步细粒度需 `acc_ids` 字段，留 v1.4.34+ 候选。

### 🗑️ v1.4.32 Out of scope 回扫（CLAUDE.md 3e 流程第三次执行）

| 项 | v1.4.32 处理 | v1.4.33 状态 |
|---|---|---|
| daemon-reload 升级"真 reload"（重跑 auth + 重建 TCP） | 留 OUT | ⏭️ 继续 OUT |
| CN + HK 双 attribution 自动化回归框架 | 留 OUT | ⏭️ 继续 OUT |
| 外部 reviewer 2FA OTP 真机验证 | 留 OUT（等 外部 reviewer 账号） | ⏭️ 继续 OUT |

**新加 OUT（这版生的，下版得扫到）**：
- `acc_ids: Option<Vec<u64>>` per-account 解锁粒度（影子账户问题的最后一公里）
- 重构：daemon `UnlockTradeHandler` 中"什么算 active real account"的 predicate 在 group_accounts_by_broker 和 invalid-sf 错误路径里有 2 份独立拷贝，应抽公共函数（v1.4.32 review 提出）

## [1.4.32] - 2026-04-18 🛠 daemon 生命周期管理工具（同事 2026-04-18 提议落地）

### 一句话 TL;DR

新增 **3 个 admin 命令** `futucli daemon-{status,shutdown,reload}` + 对应
REST endpoint `/api/admin/*` + 新 `admin` scope。"出问题时快速重置"场景
从"翻日志 + kill -9"提升到"一行命令"：`daemon-status` 看登录 / broker
通道 / cipher 就绪度；`daemon-shutdown` 优雅退出让 systemd 决定重启；
`daemon-reload` 清 trade cipher 缓存，客户端重新 unlock。

### ✨ 新增 (Added) — daemon 生命周期管理 (P1 主题)

#### `Scope::Admin` 枚举 + 路由鉴权

- `futu-auth::Scope::Admin` 新 variant（string form `"admin"`）
- REST `scope_for_path` 把 `/api/admin/status|reload|shutdown` 3 条
  路径映射到 `Scope::Admin`
- **安全默认**：legacy mode（无 `--rest-keys-file`）允许通过但
  日志 WARN；scope mode 下 key 必须持 `admin` scope 才能调
- **故意不暴露给 MCP**：LLM 误触发 shutdown / reload 的 blast
  radius 太大（数十 LLM 共享一个 daemon 时一次误调就全挂）

#### `GET /api/admin/status` / `futucli daemon-status`

只读健康状态快照，响应结构化字段：

```json
{
  "version": "1.4.32",
  "login": { "online": true, "user_id": <uid>, "attribution": "Cn" },
  "platform": { "connected": true },
  "brokers": [
    { "broker_id": 1001, "name": "Futu HK", "status": "ready",
      "addr": "<broker-hk-ip>:443", "keep_alive_secs": 30 },
    { "broker_id": 1007, "name": "Futu US", "status": "ready",
      "addr": "<broker-us-ip>:443", "keep_alive_secs": 30 }
  ],
  "cache": {
    "trade_unlocked": true,
    "cached_cipher_count": 5,
    "cached_account_count": 21
  }
}
```

字段选择原则：只暴露运维真实需要的数据（登录状态 / broker 通道 / cache
就绪度），**不**暴露 `session_key` / `tgtgt` / `device_id` 等敏感凭据。

#### `POST /api/admin/shutdown` / `futucli daemon-shutdown`

触发进程优雅退出：handler 返回 200 `{"ok":true, "shutting_down_in_secs":1}`
后 spawn 异步任务 `tokio::time::sleep(1s)` + `std::process::exit(0)`。
1 秒延迟给 HTTP 响应写回 socket + 客户端收到确认的时间。

不做 drain in-flight（等待 trade 请求完成）的理由：opend 典型部署在
systemd / Docker 里，shutdown 语义就是"退出 + supervisor 决定是否重启"，
客户端自己有 timeout / retry。

#### `POST /api/admin/reload` / `futucli daemon-reload`

**MVP scope**：只清 `trd_cache.ciphers`（所有已解锁账户的 cipher）。
客户端必须重新调 `/api/unlock-trade` 才能下单。

不做的事（留给后续版本）：
- **不**重跑 HTTP auth（需要持有 plaintext login_pwd；opend 启动后即丢弃）
- **不**重建 Platform / broker TCP（v1.4.24 的 per-broker reconnect
  watcher 已能自动恢复心跳丢失；手动重建需要 push_cb 穿透太复杂）

典型场景：用户换了交易密码 / 解锁状态错乱 / "想重新来过"。

响应：

```json
{
  "ok": true,
  "ciphers_dropped": 5,
  "message": "dropped 5 trade cipher(s); call /api/unlock-trade again ..."
}
```

#### 架构：provider 注入模式

`futu-rest` **不反向依赖** `futu-gateway`。opend main 启动时构造 2 个
closure 注入到 `RestState`：

```rust
type AdminStatusProvider = Arc<dyn Fn() -> serde_json::Value + Send + Sync>;
type AdminReloadHandler = Arc<dyn Fn() -> serde_json::Value + Send + Sync>;
```

closure 捕获 `Arc<GatewayBridge>`，每次 handler 调用时返实时 JSON。
好处：admin 能力可插拔，legacy handler 完全不受影响。

### ✨ 新增 (Added) — 杂项收尾

- **`futucli acc-cash-flow --date-range <FROM..TO>`**（外部 reviewer v1.4.30 反馈
  #1 follow-up）：日期范围封装单日版循环调用，跳周末，31 天硬上限防
  bot 脚本误触服务端 rate-limit。单日版 `--date` 和范围版 `--date-range`
  互斥（clap `conflicts_with`）。
- **MCP tool description 增强 "Array hint"**（外部 reviewer v1.4.30 反馈 #2）：
  `symbols` / `acc_ids` 等数组字段 description 明确 "Array of ..." +
  具体例子 + **命名注**（"we use Rust-native snake_case across all
  MCP tools, not py-futu-api's `security_list`"）。涉及 4 个 Req
  struct：`SymbolListReq` / `FutureInfoReq` / `SuspendReq` /
  `SubAccPushReq`。

### 📊 改动量

| crate | 增 | 减 |
|---|---|---|
| `crates/futu-auth/src/scope.rs` | +8 | -1 |
| `crates/futu-gateway/src/bridge.rs` | +156 | -0 |
| `crates/futu-gateway/Cargo.toml` | +3 | -0 |
| `crates/futu-rest/src/adapter.rs` | +28 | -0 |
| `crates/futu-rest/src/auth.rs` | +14 | -0 |
| `crates/futu-rest/src/routes/admin.rs`（新） | +92 | -0 |
| `crates/futu-rest/src/routes/mod.rs` | +1 | -0 |
| `crates/futu-rest/src/server.rs` | +75 | -3 |
| `crates/futu-opend/src/main.rs` | +26 | -3 |
| `crates/futu-opend/Cargo.toml` | +2 | -0 |
| `crates/futucli/src/cli.rs` | +60 | -6 |
| `crates/futucli/src/cmd/mod.rs` | +1 | -0 |
| `crates/futucli/src/cmd/daemon.rs`（新） | +147 | -0 |
| `crates/futucli/src/cmd/trade_ext.rs` | +125 | -47 |
| `crates/futucli/Cargo.toml` | +2 | -0 |
| `crates/futu-mcp/src/tools.rs` | +28 | -5 |

**Total**: +768 / −65，16 文件。全通 `cargo fmt + clippy --workspace -- -D warnings + test --workspace`（244 passed, 0 failed）。

### 🧪 真机验证

CN 测试账号端到端验证 4 个场景：

1. **Offline mode**：daemon 启动无登录 → `daemon-status` 返
   `login.online=false`, 空 `brokers`, `trade_unlocked=false` ✓
2. **Online after login**：2 broker 通道（Futu HK 1001 / Futu US 1007）
   都 ready，`cached_account_count=21`，`trade_unlocked=false`（还没 unlock）✓
3. **After unlock 5/5**：`cached_cipher_count=5`, `trade_unlocked=true` ✓
4. **After daemon-reload**：`ciphers_dropped=5`，再 `daemon-status` 显示
   `cached_cipher_count=0`, `trade_unlocked=false` ✓
5. **daemon-shutdown**：200 响应后 1s 内进程退出，日志
   `admin shutdown: exiting process with code 0` ✓

### 📝 Known Limit

- **`daemon-reload` MVP 只清 cipher cache**，不重跑 auth / 不重建 TCP。
  下版可扩展（需要 config 穿透，复杂度中）。
- **`daemon-shutdown` 无 drain 语义**（不等 in-flight 请求完成）。真要
  精细 drain 需要 listener 进"拒新收旧"状态，当前 MVP 不做。
- **admin 能力不暴露给 MCP**：故意不加（LLM 误操作风险）。

### 🗑️ v1.4.31 Out of scope 回扫（CLAUDE.md 3e 流程第二次执行）

| 项 | v1.4.31 处理 | v1.4.32 状态 |
|---|---|---|
| daemon 管理工具（同事提议） | 新加 OUT | ✅ **本版主题**做了（`daemon-{status,shutdown,reload}`） |
| 外部 reviewer 2FA OTP 真机验证 | OUT（需 2FA 账号） | ⏭️ 继续 OUT（等 外部 reviewer 2FA 账号回归） |
| MCP Array hint | 延 v1.4.32 | ✅ **本版做**（4 个 Req struct description 增强） |
| `acc-cash-flow --date-range` | 延 v1.4.32 | ✅ **本版做**（31 天硬上限 + 跳周末） |
| 真机 CN + HK 双 attribution 回归框架 | 延 v1.4.32+ | ⏭️ 延 v1.4.33（独立 infra 工程） |
| GHCR v1.4.31 image 补 semver tag | 继续 OUT | ⏭️ 继续 OUT |
| v1.5.0 升版 | 继续 OUT | ⏭️ 继续 OUT |
| broker 通道新增 broker 运行时建连 | 继续 OUT | ⏭️ 继续 OUT（Known limit） |
| `cancel_all_order` 全市场语义 | 继续 OUT | ⏭️ 继续 OUT |

**新加 OUT（这版生的，下版得扫到）**：
- `daemon-reload` 扩展为"真正的 reload"（重跑 auth + 重建 TCP）——本版 MVP 只清 cipher，功能上够 day-to-day ops
- CN + HK attribution 自动化回归框架

## [1.4.31] - 2026-04-18 🔴 unlock-trade 架构重构（外部 reviewer v1.4.30 回归报告 3 P1 + P2 + P3 全修）

### 一句话 TL;DR

**`/api/unlock-trade` 从 "Platform channel 单请求打包所有账户" 重构为 "per-broker 并发请求 + per-account 结果"**，同时修好 moomoo 账户不能解锁（实际是通道路由错，不是密码哈希错）、支持 2FA/OTP 账户、空错误消息加自检 hint。某 CN 账号真机验证 5/5 账户（含影子账户 + moomoo broker 子账户）全部 unlock 成功。

### 🔴 修复 (Fixed) — 3 个 P1（外部 reviewer v1.4.30 回归测试发现）

#### P1-1 影子账户拉倒整个 unlock（某 CN 账号无法解锁主账户的根因）

**现象**：`/api/unlock-trade` 把 daemon 过滤后的多个"正常状态"账户全部打包进 1 个 CMD2900 请求。外部 reviewer 实测账号的账户里有 1 个"影子子账户"（`market_auth=[5]` 单一稀有编码，用户从未开通该品种权限，APP 里也看不到），服务端对其返 `result=-20416 "您没有该账户当前品种的交易权限"`——**整个请求失败，连主账户也没解锁**。下游 history-orders / place-order 全部不可用。

**修复**：改成 **per-broker 分组 + 并行 CMD2900**。
- `group_accounts_by_broker()` 按 `security_firm → broker_id` 分组（1=broker 1001 FutuHK, 2=broker 1007 FutuUS/moomoo, 3=SG, 4=AU, 5=JP, 6=CA, 7=MY）
- 每个 broker 独立发 CMD2900，互不影响
- 响应里 `ciphers[]` 和 `pswds[]` 差集 = 该 broker 失败账户
- 聚合成 `AccountResult { acc_id, success, security_firm }` 列表返回

**结果**：主账户不会被影子账户拖累；响应 schema 暴露 per-account 状态。测试账号实测 5/5 unlock 成功（含 `market_auth=[5]` shadow 账户）。

#### P1-2 moomoo 账户完全不能 unlock（外部 reviewer 实测 moomoo app 能解但 daemon 永远报"密码错误"）

**外部 reviewer 的假设**：moomoo 服务端对 pwd hash / salt / payload format 与 futunn 不同，daemon 硬编码了 futunn 算法。

**实际根因**（更底层）：**Rust 一直把 CMD2900 发到 Platform channel + Platform user_id**——应该发到 **broker channel + broker-specific customer_id**。C++ 参照：`SendTCPProto_ProtoBuf_WithAccID(uid, m_enTcpCategory = BrokerIDToTcpCategory(broker_id), 2900, req)`。moomoo 账号走 Platform channel 时服务端按 Platform uid 查不到对应 broker 的交易权限，自然返"密码错"。

**修复**：
- CMD2900 的 `broker_conn` 从 `self.brokers.get(broker_id)` 取（v1.4.8 已建好的 broker map）
- 请求时 `TrdHeader.user_id` 用 `broker_auth.customer_id`（per-broker unique）
- v1.4.26 broker IP 修复 + v1.4.8 broker channel 架构 + v1.4.31 unlock 路由对齐，三版合力把 moomoo 账户的 trade 完全通了

**结果**：测试账号的 moomoo 子账户（`security_firm=2 → broker_id=1007`）实测 unlock success=true，后续 `/api/funds` 返 `ret_type=0`。

#### P1-3 开启令牌动态密码（2FA）账户无法 unlock

**现象**：2FA 账户 unlock 时服务端返 `ret_type=-1, ret_msg="需要令牌动态密码"`（错误码内部是 `TRADE_AUTH_NEED_AUTH_TOKEN=-8`），但 daemon schema 没 OTP 字段，`futucli` 也没 `--otp` 参数。

**修复**：proto 扩展（**向后兼容**，老 Python SDK 客户端忽略新字段）：
- `Trd_UnlockTrade.C2S.secOtp` (tag 4) — OTP 明文
- `Trd_UnlockTrade.S2C.needOtp` — 服务端提示 true 时客户端重试带 OTP
- `Trd_UnlockTrade.S2C.accountResultList` — per-account 解锁状态
- 新 `AccountResult { acc_id, success, security_firm }` message

daemon 实现两阶段：
1. Phase 1: CMD2900 TradePswdAuth (密码)
2. 检测到 `result_code=-8` + `auth_pswd_sig` → Phase 2: CMD2901 AuthTradeToken (OTP + sig)

`futucli unlock-trade --otp <code>` / MCP `futu_unlock_trade` 的 `otp` 字段都已加好。

**注**：测试账号未开 2FA，schema + handler 就位但**真机 OTP 路径待 外部 reviewer 用 2FA 账号验证**。

### 🟡 修复 (Fixed) — 1 个 P2

#### P2-1 trade 接口未解锁时返回空错误消息

**现象**：`/api/history-orders`、`/api/max-trd-qtys` 未 unlock 时返回 `{ret_type: -400, ret_msg: null, s2c: null}` 三项全空，用户无任何可操作信息。

**修复**：daemon 层 `augment_empty_trade_error()` helper 在 `ret_type != 0 && ret_msg.is_empty()` 时填默认 3 项自检 hint：
```
bad request — 常见自检：
  1) 先调 /api/unlock-trade 解锁交易；
  2) acc_id 是否属于该命令支持的环境（real vs simulate）；
  3) 市场 / 账户品种权限是否开通（常见：sim 账户查 history-orders 会返 -400）。
```
客户端 `server_err()` 在前面加 `[err_code=none]` 前缀后整体呈现。

### 🟢 改进 (Changed) — 3 个 P3（文档 / schema 一致性）

- **P3-1 MCP market 参数 3 种编码说明**：`futu_get_ipo_list` / `stock_filter` / `get_price_reminder` 的 `market` 参数 schema description 标注 "Qot_Common.QotMarket enum (i32): 1=HK, 11=US, 21=SH, 22=SZ. NOTE: different from TrdMarket"；`futu_get_trading_days` 标注 "TradeDateMarket enum (i32, NOT QotMarket!)"。
- **P3-2 `futu_get_price_reminder` required 约束**：description 加 "Exactly one of symbol or market must be set"，之前 schema `required: []` 但运行时校验 `either symbol or market required`。
- **P3-3 CHANGELOG v1.4.30 数字总览**：CHANGELOG 顶部 `#### MCP +8 tool` 只是 P1 批次，实际总数 +19（33 → 52 ~100%）。v1.4.31 在 v1.4.30 段顶部加"📊 数字总览"section 消歧义。

### ✨ 新增 (Added) — futucli 补齐 py-futu-api 最后 2 个 CLI 命令

- **`futucli margin-ratio <symbols> --market HK --acc-id <id>`** — per-security 融资融券长短许可 / IM 比率 / 借券池余量 / 借券费年化率
- **`futucli order-fee <order_id_ex_csv> --market HK --acc-id <id>`** — 下单前手续费估算，分项（佣金 / 平台费 / 印花税 / 等）

backend helpers `futu_trd::misc::{get_margin_ratio, get_order_fee}` 在 v1.4.25 就有，本版只是补 CLI 连线。futucli 业务命令数 **44 → 46**（py-futu-api 对齐度 ~100%）。

### 🧹 改进 (Changed) — 重构 / 基建

- **`market_state_label` helper 抽提到 `futu-qot::types`**（减少漂移）—— 之前在 `futucli/cmd/sys.rs` + `futucli/cmd/analysis.rs` 2 处拷贝，v1.4.25 起就在慢慢发散（"加新枚举只更新一份"的隐患）。抽到公共位置 + 加 2 单测（19 proto 枚举全覆盖 + gap 值 fallback）。
- **GitHub Actions docker/* 升级 Node 24 majors**（2026-06-02 deadline，提前到位）：
  - `docker/login-action@v3 → @v4`
  - `docker/build-push-action@v6 → @v7`
  - `docker/metadata-action@v5 → @v6`
  - `docker/setup-buildx-action@v3 → @v4`
  - `docker/setup-qemu-action@v3 → @v4`
- **CLAUDE.md 发版流程加 step 3e "Out-of-scope 回扫"**：每版发版前必扫上版 session summary 的 OUT / Known-limit / Follow-up 段，对每项 triage（修了 / 继续欠 / archived）。v1.4.8 broker MVP 腐烂 17 版的教训固化进流程。v1.4.31 是此流程的第一次执行（本版 CHANGELOG 底部有回扫结果）。

### ✨ 新增 (Added) — gRPC .proto 分发（外部 reviewer 环境限制反馈）

`futu-opend-rs-X.Y.Z/examples/futu_service.proto` 加入发布 tarball。配合 grpcurl：

```bash
grpcurl --plaintext -import-path examples -proto futu_service.proto \
  -d '{"proto_id": 1001, "body": ""}' \
  localhost:33333 futu.service.FutuOpenD/Request
```

外部 reviewer v1.4.30 回归测试因为发布包不含 `.proto` + server 无 reflection 无法直接验 gRPC 路径的 `[err_code=N]` 前缀——现在可以验了。

### 📊 改动量

| 文件 | 增 | 减 |
|---|---|---|
| `proto/Trd_UnlockTrade.proto` | +20 | -2 |
| `crates/futu-gateway/src/handlers/trd.rs` | +607 | -45 |
| `crates/futu-mcp/src/tools.rs` | +84 | -12 |
| `crates/futu-mcp/src/handlers/trade.rs` | +16 | -4 |
| `crates/futu-trd/src/account.rs` | +70 | -16 |
| `crates/futucli/src/cli.rs` + `cmd/unlock.rs` | +44 | -15 |
| `CHANGELOG.md` | +7 | -0 |
| `.github/workflows/release.yml` | +3 | -0 |
| `deploy/README.dist.md` | +14 | -0 |

**Total**: +865 / -94，9 文件。全通 `cargo fmt + clippy --workspace -- -D warnings + test --workspace`（243 passed, 0 failed, +2 vs v1.4.30 baseline）。

### 🧪 真机验证（测试账号）

```
step 3c: establishing broker channels... known_brokers=2 all_brokers=2
broker TCP login succeeded broker_id=1001 broker="Futu HK" customer_id=<account> addr=<broker-hk-ip>:443
broker TCP login succeeded broker_id=1007 broker="Futu US" customer_id=<account> addr=<broker-us-ip>:443
unlock per-broker grouping: [(1001, 4), (1007, 1)] broker_count=2 total_accounts=5
sending CMD2900 TradePswdAuth per-broker broker_id=1001 security_firm=1 customer_id=<account> account_count=4
CMD2900 response broker_id=1001 result_code=0 requested=4 unlocked=4
sending CMD2900 TradePswdAuth per-broker broker_id=1007 security_firm=2 customer_id=<account> account_count=1
CMD2900 response broker_id=1007 result_code=0 requested=1 unlocked=1
```

响应 5/5 账户 `success=true`（含 `market_auth=[5]` shadow + `security_firm=2` moomoo broker 账户）。

### 📝 Known Limit

- **P1-3 OTP 真机路径**：测试账号无 2FA，schema 就位但未真机验证。外部 reviewer 用 2FA 账号测一次即可闭环。
- **`auth.moomoo.com` 直通路径** (attribution≠CN)：测试账号是 CN 归属，`--platform moomoo` 在 salt 响应后被服务端 switch 回 `auth.futunn.com`（对齐 C++ `user_attr_config.cpp` 映射）。v1.4.15 加拿大同事的 moomoo 真机测试已覆盖该路径，本版未动。

### 🗑️ v1.4.30 Out of scope 回扫（CLAUDE.md 3e 流程第一次执行）

| 项 | 状态 |
|---|---|
| GHCR v1.4.30 image 补 semver tag | ⏭️ 继续 OUT |
| v1.5.0 升版 | ⏭️ 继续 OUT（1.4.99 前小修） |
| broker 通道新增 broker 运行时建连 | ⏭️ 继续 OUT |
| `cancel_all_order` 全市场语义 | ⏭️ 继续 OUT |
| 真机 CN + HK 双 attribution 回归 | ➡️ 延 v1.4.32+ |
| `futucli margin-ratio` / `order-fee` | ✅ **本版修**（见 Added，commit `6ef0590d7`） |
| `market_state_label` helper 抽提 | ✅ **本版修**（见 Changed，commit `0f468ecf0`） |
| MCP Array hint | ➡️ 延 v1.4.32 |
| `acc-cash-flow --date-range` | ➡️ 延 v1.4.32 |
| Node 20 → 24 actions 迁移 | ✅ **本版修**（见 Changed，commit `0b71b32a5`） |
| CLAUDE.md "Out-of-scope 回扫"流程 | ✅ **本版修**（commit `0f468ecf0`，step 3e 正式写入 CLAUDE.md） |

**新加 OUT（这版生的，下版得扫到）**：
- daemon 管理工具 (`futucli daemon-reload` / `daemon-shutdown` / `daemon-status`) —— 同事 2026-04-18 提议，v1.4.32 专题做
- 外部 reviewer 用 2FA 账号真机验证 P1-3 OTP 路径

## [1.4.30] - 2026-04-18 🎯 py-futu-api 100% 覆盖里程碑

### 📊 数字总览（外部 reviewer v1.4.30 回归报告 P3-3 doc correction）

本版 MCP **共 +19 tool**（33 → 52，~61% → ~100%），下面 `#### MCP +8 tool`
只是 P1 批次（第一批 8 个）；完整版含 P1(8) + P2(futucli 补漏) + P3(系统元
数据 3) + P4(其它 11) = 19 tool 新增。具体清单见下面的 "三端覆盖矩阵"
和 `## 🎯 v1.4.30 第四批` 段。

### 🔴 修复 (Fixed)

#### BUG-2b（P2）place-order err_code 透传二次修复（外部 reviewer v1.4.29 回归测试发现）

v1.4.27 首修 BUG-2 时加了 `server_err()` helper，但逻辑是 **只在 `err_code`
非零时**才加 `[err_code=N]` 前缀。sim 下单时服务端经常返 `err_code=None`
（没填），首版逻辑会静默吞掉这个信号——用户看到的是原始
"PlaceOrder: 错误，请稍后重试或联系客服" 完全不知道是客户端代码吞了还是
服务端就这么返的。

外部 reviewer v1.4.29 回归报告实测 4/4 sim 账户下单都复现此问题。

**v1.4.30 修**：`server_err()` **永远**把 err_code 状态放 msg 前缀里：

- err_code = `None` → `[err_code=none] <ret_msg>`
- err_code = `Some(0)` → `[err_code=0] <ret_msg>`
- err_code = `Some(10001)` → `[err_code=10001] <ret_msg>`

用户现在看到 `ret_type=-1, msg=[err_code=none] PlaceOrder: ...` 就立刻
知道"服务端没给结构化错误码，这个 msg 是服务端兜底文案"，不再怀疑客户端
代码。加 4 个单元测试锁定（`err_code_none_labeled_as_none` 等）。

### 新增 (Added) —— 三端对齐 py-futu-api 54 个 user-facing 方法

#### MCP +8 tool（33 → 41，覆盖率 ~61% → ~76%）

v1.4.30 候选三批：

**#1 市场元数据 / 复权 / 自选（qot:read，5 个）**：
- `futu_get_trading_days` — 交易日列表（Python `request_trading_days`）
- `futu_get_rehab` — 复权因子（长期 K 线对齐用；Python `get_rehab`）
- `futu_get_suspend` — 停牌日（Python `get_suspend`）
- `futu_get_user_security` — 自选股分组内股票（Python `get_user_security`）
- `futu_cancel_all_order` — 全部撤单（Python `cancel_all_order`；内部
  ModifyOrder + `for_all=true`；scope = trade:real/simulate）

**#2 系统元数据（qot:read，3 个）**：
- `futu_get_global_state` — 网关全局状态（各市场开闭 / 登录状态 /
  服务器版本）
- `futu_get_user_info` — 用户信息（昵称 / 各市场行情权限 / 订阅配额 /
  历史 K 线配额）
- `futu_get_delay_statistics` — 延迟统计概要（分类 sample 数）

配套：`guard::scope_for_tool()` 一次性扩充，`all_known_tools_have_scopes`
测试白名单同步更新（严格模式，漏一个就挂 CI）。

#### futucli +13 业务命令（20 → 33，覆盖率 ~37% → ~61%）

**#1 市场元数据 / 衍生（10 个）**：
- `trading-days --market <HK|US|CN|NT|ST|JP|SG> --begin --end` — 交易日
- `rehab <symbol>` — 复权因子
- `suspend <symbols> --begin --end` — 停牌日（逗号分隔）
- `user-security <group>` — 自选股分组内股票
- `user-security-groups [--group-type <1|2|3>]` — 自选股分组列表
- `warrant [--owner] [--num 20]` — 涡轮列表（按成交量降序）
- `ipo-list --market <HK|US|CN>` — 新股 IPO
- `future-info <symbols>` — 期货合约资料
- `stock-filter --market <HK|US|CN> [--begin] [--num]` — 条件选股最小版
- `cancel-all-order <acc-id> --env <env> [--market] [--confirm]` —
  全部撤单（real 必须 `--confirm`）

**#2 系统元数据（3 个）**：
- `global-state` — 网关全局状态
- `user-info` — 用户信息
- `delay-statistics` — 延迟统计概要

#### REST +4 endpoint

- `/api/trading-days` `POST` — QotRead
- `/api/rehab` `POST` — QotRead
- `/api/suspend` `POST` — QotRead
- `/api/cancel-all-order` `POST` — TradeReal；内部 override
  `forAll=true / modifyOrderOp=Cancel / orderID=0`，限额检查走 modify-order
  同一套（market 白名单 + rate，symbol/value/side 空让细粒度检查 skip）

（ipo-list / future-info / stock-filter / user-security 的 REST endpoint
v1.4.29 之前就存在，此版新增只有上面 4 个。）

#### 新增子模块

- `crates/futu-mcp/src/handlers/reference.rs` 扩展：加 `get_trading_days`
  / `get_rehab` / `get_suspend` / `get_user_security` 4 个 handler
- `crates/futu-mcp/src/handlers/core.rs` 扩展：加 `get_global_state` /
  `get_user_info` / `get_delay_statistics` 3 个 handler
- `crates/futu-mcp/src/handlers/trade_write.rs` 扩展：加
  `cancel_all_order` handler（复用 `futu_trd::order::modify_order` 带
  `for_all=Some(true)`）
- `crates/futucli/src/cmd/sys.rs` 新文件：3 个系统元数据命令
- `crates/futucli/src/cmd/analysis.rs` 扩展：加 10 个市场元数据 /
  衍生命令
- `crates/futucli/src/cmd/trade_ext.rs` 扩展：加 `run_cancel_all_order`

### 🎯 v1.4.30 第四批（里程碑：100% py-futu-api 覆盖）

在第三批基础上再补最后 11 个 user-facing API，三端（REST / futucli /
MCP）全部对齐 py-futu-api 54 个方法（除 `verification` C++ 已弃用 +
`InitConnect` / `KeepAlive` / 推送类等内部机制）。

#### MCP +11 tool（41 → 52，覆盖率 ~76% → **~100%**）

**qot:read（9 个）**：
- `futu_get_history_kl_quota` — 历史 K 线下载配额（已用 / 剩余）
- `futu_get_holding_change` — 高管 / 机构 / 基金持股变动
- `futu_modify_user_security` — 修改自选股分组（add / del / move-out）
- `futu_get_code_change` — 股票代码变更 / 临时代码（目前港股）
- `futu_set_price_reminder` — 设置到价提醒（add / del / enable / disable /
  modify / del-all）
- `futu_get_price_reminder` — 查询到价提醒（按 symbol 或 market）
- `futu_get_option_expiration_date` — 期权到期日列表
- `futu_query_subscription` — 查询当前订阅状态
- `futu_unsubscribe` — 反订阅行情（支持 `unsub_all`）

**acc:read（2 个）**：
- `futu_sub_acc_push` — 订阅账户推送（订单 / 成交变更）
- `futu_get_acc_cash_flow` — 账户资金流水（按清算日）

#### futucli +11 业务命令（33 → 44，覆盖率 ~61% → **~100%**）

- `query-subscription`（可选 `--all-conn`）
- `unsubscribe --symbols ... --sub-types ... [--all]`
- `history-kl-quota [--detail]`
- `holding-change <symbol> --category 1|2|3 [--begin --end]`
- `modify-user-security <group> --op 1|2|3 <symbols>`
- `code-change <symbols>`
- `set-price-reminder <symbol> --op --key --type --freq --value --note`
- `price-reminder [--symbol | --market]`
- `option-expiration-date <owner> [--index-type]`
- `sub-acc-push <acc-id,acc-id,...>`
- `acc-cash-flow <acc-id> --date YYYY-MM-DD [--env --market --direction]`

#### REST +9 endpoint（全走 scope-aware auth）

- `/api/history-kl-quota` / `/api/holding-change` / `/api/modify-user-security`
  / `/api/code-change` / `/api/set-price-reminder` / `/api/price-reminder`
  / `/api/option-expiration-date` / `/api/unsubscribe` → `qot:read`
- `/api/flow-summary` → `acc:read`

#### 100% 覆盖总览

| 端 | v1.4.29 | v1.4.30 (P1) | v1.4.30 (P2 = 本批次) | 覆盖率 |
|---|---|---|---|---|
| REST | 40 | 44 | **53** | ~100% |
| futucli | 20 | 33 | **44** | ~100% |
| MCP | 33 | 41 | **52** | ~100% |

（54 - 1 verification 已废弃 - 1 InitConnect 内部 ≈ 52-53 个 user-facing。）

### 验证

- `cargo fmt --check` clean
- `cargo clippy --workspace --bins --tests -- -D warnings` 全绿
- `cargo test --workspace` **237 passed, 0 failed**
  - `all_known_tools_have_scopes` 白名单从 20 条扩到 44 条，
    `all_known_routes_have_scopes` 从 39 条扩到 53 条

## [1.4.29] - 2026-04-18

累积小修 + 补齐 v1.4.25/v1.4.26 漏补的 MCP scope 注册 + v1.4.8 起 broker
重连遗留的 commconfig 使用问题。所有改动都"小修小补"，不升 1.5。

### 修复 (Fixed)

#### 🔴 MCP scope 注册表漏补（v1.4.25+/v1.4.26+ 13 个 tool 在 scope 模式下挂）

v1.4.25 / v1.4.26 陆续加 MCP tool 时只在 `tools.rs` 加了 `#[tool]`，
忘了同步 `guard::scope_for_tool()`。`require_tool_scope` 是 **fail-closed**
的：未注册的 tool 全部返 `"unknown MCP tool"`。legacy 模式（无 keys-file
兼容路径）不受影响，但任何用 `--keys-file` 启动的 scope-mode 用户下列
tool 全部不可用：

- qot:read 7 个：`futu_get_capital_flow` / `futu_get_capital_distribution`
  / `futu_get_market_state` / `futu_get_history_kline` / `futu_get_owner_plate`
  / `futu_get_reference` / `futu_get_option_chain`
- acc:read 5 个：`futu_get_max_trd_qtys` / `futu_get_order_fee` /
  `futu_get_margin_ratio` / `futu_get_history_orders` / `futu_get_history_deals`

v1.4.29 一次性补齐，并更新 `all_known_tools_have_scopes` 测试把所有
注册 tool 列进去，以后漏 tool 测试会挂（"备忘锁"）。

#### 🟡 broker 通道重连未查 commconfig 新 IP

v1.4.24 加 broker reconnect watcher 时 hardcode `last_known_addr`。如果
commconfig 期间下发了新 `guaranteed_ip_broker[broker_id]`（运维切换 IP
池）或者原 IP 已经下线，watcher 会持续重连到失效 IP 直到放弃。v1.4.29：
reconnect watcher 每次重连前 `commconfig.load()` 查 broker 专用池，
连同 `last_known_addr` 一起组成候选列表，`connect_race` 并发尝试，拿
第一个成功的。

### 新增 (Added)

#### MCP 5 个参考数据 / 衍生证券 tool（v1.4.29 补最后一批 py-futu-api 覆盖）

- `futu_get_warrant` — 涡轮列表（按成交量降序，可选正股过滤）
- `futu_get_ipo_list` — 新股 IPO 列表（港/美/A 股按 market 过滤）
- `futu_get_future_info` — 期货合约资料（合约大小、最后交易日、交易时段）
- `futu_get_user_security_group` — 自选股分组（自定义 / 系统 / 全部）
- `futu_get_stock_filter` — 条件选股（最小参数版）

`warrant` / `stock_filter` C2S 有 20+ 过滤字段，MCP 只暴露最基础参数
（owner + num / market + begin + num）。真要按 PE / 市值 / 成交量 / Delta
等高级过滤的用户，走 REST `/api/warrant` / `/api/stock-filter` 直接传
完整 JSON body。

MCP 覆盖率：**28 → 33 tool**（~52% → ~61% Python SDK）。

### 文档 (Docs)

- `docs-site/docs/guide/mcp.md` + `mcp.en.md`：补全 v1.4.25 / v1.4.26 /
  v1.4.29 新 tool 列表（之前标题说 "19 tools" 实际已 28，本版改成
  "工具清单"不写数字）。
- GitHub Release 页补齐 v1.4.22 / v1.4.23 / v1.4.24 / v1.4.25 / v1.4.27
  / v1.4.28 六个之前 CI 只发了 tag 但没建 release page 的版本。

### 依赖升级 (Dependencies)

- **tokio-tungstenite 0.24 → 0.29** —— 0.26 把 `Message::Binary(Vec<u8>)` /
  `Message::Text(String)` 改成 `Message::Binary(Bytes)` / `Message::Text(Utf8Bytes)`。
  我们只在 `crates/futu-server/src/ws_listener.rs` 用到，一行改动（`buf.freeze().into()`
  → `buf.freeze()`）。
- **tonic 0.13 → 0.14** + **prost 0.13 → 0.14 (workspace 级)** —— 0.14
  把 `tonic_build::compile_protos` 剥离到独立 crate `tonic-prost-build`，
  生成代码依赖 `tonic-prost` / `prost 0.14`。futu-grpc 的 `build.rs` 改
  成 `tonic_prost_build::configure().compile_protos(&[...], &[...])`，
  Cargo.toml 加 `tonic-prost = "0.14"`。workspace 的 `prost` 同步升到
  0.14（涉及 futu-proto / futu-codec / futu-qot / futu-trd / futu-net 等
  所有 proto 解码点），`prost-build` 同步跟升。所有代码无需调整（prost
  0.13 → 0.14 对我们用到的 `Message::decode` / `encode_to_vec` 签名是
  完全兼容的 additive 变更）。

验证：`cargo test --workspace` 全 pass（~260+ 测试），`cargo clippy -D warnings`
全绿，`cargo fmt` clean。

## [1.4.28] - 2026-04-18

继续清理加拿大同事 v1.4.26 回归测试报告的 P3 bug + UX 改进
（见 `essentials/2026-04-18-0650-v1426-bug-report-from-ca.md`）。
v1.4.27 已修 BUG-1/2/3/4；本版修剩余 BUG-5/6/7 + UX-1。

### 修复 (Fixed)

#### 🟢 BUG-5（P3）CMD3020 fund 子账户 `result_code=3 "unknown"`

**问题**：24 个账户中 2 个固定失败：`trd_market_auth=[123]`（US_Fund）
和 `[113]`（HK_Fund）。根因是 `trd_market_to_currency` 没覆盖 fund 子
市场的 **后端原值**（13 HK_Fund / 23 US_Fund / 24 SG_Fund）和
**NN_TrdMarket 枚举值**（113 HK_Fund / 123 US_Fund / 124 SG_Fund /
125 MY_Fund / 126 JP_Fund）两套编码，fallback 到 HKD 导致服务端拒。

**修复**：`trade_query.rs::trd_market_to_currency` 完整补齐双轨值 —
fund 子市场按国别返回对应 currency（HKD/USD/SGD/MYR/JPY），默认仍
HKD 兜底。

#### 🟢 BUG-6（P3）未知 market_code WARN 降级

**问题**：启动时稳定出现 5 条 WARN `unknown market_code market_code=
182 / 200 / 263`（SG 衍生品、TSX60 指数、FTXIN9 指数），对主交易 /
行情功能无影响，但让用户以为启动异常。

**修复**：`unknown market_code` 从 WARN 降 DEBUG。未来如真需要补枚举
用 `RUST_LOG=debug` 看到完整列表。

#### 🟢 BUG-7（P3）`--audit-log` + `--json-log` 互斥改硬失败

**问题**：两个 flag 同时传时之前**静默忽略** `--audit-log` 只打 warn
到 stderr，审计文件会被创建但始终为空，用户误以为"没有审计事件发生"，
有合规事故风险。

**修复**：互斥时直接 `exit(2)` 并打印清晰二选一说明：`--json-log` 全
stderr JSONL vs `--audit-log` 仅 `target=futu_audit` 事件到单独文件。

### 新增 (Added)

#### 🟢 UX-1（P3）`/readyz` readiness probe endpoint

**问题**：daemon 启动后前 ~30-60s 内 `/api/quote` 返空 / `/api/history-kline`
报 `no backend connection`，但 `/health` 总是 200，用户看不到就绪信号。
k8s readinessProbe 没有合适端点。

**修复**：新增 `/readyz` endpoint（与 `/health` 并列，都在 bearer_auth
之外）。内部 dispatch 一次 `GET_GLOBAL_STATE`，成功 decode 出 `ret_type=0`
就返 200 "ready"；gateway 未就绪返 503。k8s readinessProbe / 负载均衡
健康检查可直接打这个端点。

**实测**：冷启动瞬间（REST 端口还没开）→ 无法连；45s 后登录就绪 →
HTTP 200 "ready"。

## [1.4.27] - 2026-04-18

基于加拿大同事 v1.4.26 端到端回归测试（40 项通过 / 7 bug / 5 doc gap）
修 4 个 P2/P3 bug + CI 基建。完整报告留存
`essentials/2026-04-18-0650-v1426-bug-report-from-ca.md`。

### 修复 (Fixed)

#### 🔴 BUG-2（P2）sim 账户 funds / 交易 API err_code 透传

**问题**：所有 sim 账户 `funds` 查询全部失败报 `missing funds in GetFunds`
（HK + US / sim_type 1 + 2 各账户族都失败）；下单失败时 `ret_msg` 只显示
服务端的"PlaceOrder: 错误，请稍后重试或联系客服"，`err_code` 被盖住，用户
无法判断参数错 / 账户锁 / 盘中限价越界等。

**修复**：
- `futu_trd::account::get_funds` — `s2c.funds` 为 None 时返空 Funds（proto
  本来就是 `optional`）+ WARN log 提示 `trd_env / acc_id / trd_market`，不再
  当成 error。real 账户响应含 funds 字段，不受影响
- 新增 `futu_trd::server_err()` helper 统一把 `ret_type/ret_msg/err_code`
  三元组汇成 `FutuError::ServerError`，msg 前缀 `[err_code=XXX]`。15 处
  `trd` crate 调用点统一用 helper：account（4 处）/ order（2 处）/ misc
  （7 处）/ query（2 处）

**实测**：sim 28701 (HK CASH) + 10848891 (HK MARGIN) `futucli funds` 从
"error: 协议解析错误" 转为正常 0.00 表格 + WARN log；real 账户（8105 主账户）
无回归（完整金额显示）。

#### 🔴 BUG-1（P2）unlock-trade 错误时自动提醒"交易密码 ≠ 登录密码"

**问题**：用户用登录密码调 `/api/unlock-trade` 时服务端返
"交易密码输入错误，您还有9次机会"。用户不知道交易密码是独立设置的，容易
连续错 10 次**锁账户**（需联系券商客服恢复）。

**修复**：`futu-rest` unlock_trade handler 在响应 `ret_type != 0` 且
`ret_msg` 包含"交易密码 / 密码错误 / 密码输入"关键词时，自动在 msg 末尾
追加：`[提示] 交易密码与登录密码独立；如未设置，先用 \`futucli set-trade-pwd\`
存入 OS keychain，重复错密码后券商会锁账户。`

**实测**：REST 实调（故意用登录密码）响应里原服务端消息后追加了完整提示。

#### 🟢 BUG-3（P3）suspend ZIP 下载日志整理

**问题**：启动时稳定出现 3 条 WARN `failed to load suspend data ...
invalid Zip archive: Could not find EOCD`（HK/US/CN 各一条），对用户无
actionable 价值，且混淆"启动有问题"的感知。

**修复**：
- HTTP 非 200 → 直接 Err，不尝试解 ZIP
- 响应前 4 字节不是 `PK\x03\x04` → 降级并 DEBUG 打印 `Content-Type` + 前
  120 字节（让运维能判断是 HTML 错误页还是真 ZIP 损坏）
- `failed to load suspend data` 从 WARN 降 DEBUG（可用 `RUST_LOG=debug` 查）

**实测**：启动日志里 3 条 WARN 全部消失。

#### 🟢 BUG-4（P3）code_change 404 日志降级

**问题**：启动时稳定出现 2 条 WARN `failed to download code ... HTTP 404`
（HK_CodeRelationship + HK_TempParTrade），因为 URL 按日期构造，周末 /
假日 CDN 无当日文件。

**修复**：下载失败时按 `HTTP 404` 区分：404 降 DEBUG（可预期的软失败，
周末/假日正常），5xx / 网络错保留 WARN（真正需关注的异常）。

**实测**：启动日志里 2 条 WARN 全部消失。

### 基建 (Infrastructure)

#### GitHub Actions 升级（彻底解决 Node.js 20 deprecation）

6 个 workflow 的 JS action 从 v5 升到最新主版本（Node.js 24 原生）：

- `actions/checkout@v5 → v6`
- `actions/upload-artifact@v5 → v7`
- `actions/download-artifact@v5 → v8`

移除 v1.4.26 为应急加的 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24="true"` env
开关。Dependabot PR #1/#2/#3 会自动关闭。

### 归档 (Archived)

- `essentials/2026-04-18-0650-v1426-bug-report-from-ca.md` — 加拿大同事
  v1.4.26 回归测试完整报告（40 项通过 / 7 bug / 5 doc gap）
- `deploy/examples/rest-curl-examples.sh` — 所有 REST POST 接口调通的
  curl 示例（随 release tarball 分发，解决同事报告里 DOC-1 的一部分）

## [1.4.26] - 2026-04-17

### 修复 (Fixed)

#### 🚨 P0 — Broker 1001 HK 真实账户 HK 主账户两周消失

**影响**：自 v1.4.8 broker 通道上线以来，凡是用户 broker_id=1001（Futu HK）
的真实账户，`futucli account` / `get_acc_list` 可能**完全不返回**——包括
资产最多的 HK 主账户、其他 disabled 子账户等。

**根因**：v1.4.8 broker 通道 MVP 用 Platform IP 建立所有 broker TCP 连接，
"让服务端 redirect"。但 broker 1001 连上某个 Platform US IP 时，**服务端
不 redirect**直接接受 conn_identity=1001 的登录，后续 CMD 2282 按
customer_id 返 **broker 1007 US 账户**——HK 账户一个没有。

**修复**：对齐 C++ `ChannelAddressManager::ParseGuaranteedIpConfig`，
commconfig `guaranteed_ip_for_conn` 下发的 **broker identity 池**
（1001/1007/1008/1009/1012/1017/1019）现在被**收集**到
`CommonConfigSnapshot.guaranteed_ip_broker`，broker 通道 CMD 1001 登录按
broker_id 查对应 IP 池，不再用错 broker 的服务端。commconfig 未下发才
fallback 到 platform_addr + LOGIN_STATUS_REDIR（老兜底路径）。

实测某 CN 账号：账户总数 13 → 21，broker 1001 从 0 real 返回 6 HK real
（含 HK 主账户 markets=HK/US/HKFUND/USFUND/JP）。详见
`essentials/2026-04-17-1634-v1426-broker-ip-fix.md`。

**CLAUDE.md 核心原则新增**一条 **"禁止硬编码服务端/配置下发可得的动态
数据"**，把这次 bug 作为反例写死，防止类似"暂时硬编码当 MVP"的思路再来一次。

#### P1 — `futucli account` 从 3 列扩到 12 字段

原 `TrdAcc` 只有 3 个字段（`trd_env` / `acc_id` / `trd_market_auth_list`），
导致 CLI 表格只有 3 列。现在对齐 `Trd_Common.TrdAcc` proto 完整 12 字段：
`acc_type` / `card_num` / `security_firm` / `sim_acc_type` / `uni_card_num`
/ `acc_status` / `acc_role` / `jp_acc_type`，futucli 表格 8 列显示
Acc ID / Card / Env / Broker / Type / Status / Role / Markets。

#### P1 — MCP trade 转发 `Protobuf 解码失败` 

`BackendTrdForwardHandler.backend_cmd_id = Some(4711/4712/4713)` 把请求
翻译到 C++ NN 内部 proto，返回的响应是 NN 格式，客户端按 FTAPI Response
decode 报 `invalid wire type` 错。修法：`backend_cmd_id = None` 时用
**原 FTAPI proto_id**（2111 / 2201 / 2202 等）直接转发后端，broker 通道
原生支持 FTAPI proto，不用翻译。涉及 `TRD_GET_MAX_TRD_QTYS` /
`TRD_GET_HISTORY_ORDER_LIST` / `TRD_GET_HISTORY_ORDER_FILL_LIST` 3 个
FTAPI。

### 新增 (Added)

#### MCP 4 个新 tool（继续对齐 py-futu-api）

- `futu_get_history_kline` — 历史 K 线，支持 rehab_type（前/后/不复权）和
  大数据量 max_count（Python `request_history_kline`）
- `futu_get_owner_plate` — 股票所属板块（行业/概念/地域）
- `futu_get_reference` — 关联证券（正股 ↔ 涡轮/期货/期权）
- `futu_get_option_chain` — 期权链，按到期日聚合 call/put 合约列表

剩余 5 个（`warrant` / `ipo_list` / `future_info` / `user_security_group`
/ `stock_filter`）留 v1.4.27，因 futu-qot 暂无 helper 或 proto 嵌套较深。

#### futucli 5 个行情分析命令

- `capital-flow` — 资金流时间序列
- `capital-distribution` — 资金分布（超大/大/中/小单）
- `market-state` — 市场状态（开盘/休市/午休/盘后）
- `owner-plate` — 股票所属板块
- `option-chain` — 期权链

#### Trading bot 教程：5 分钟起步章节

`docs-site/docs/cases/trading-bot.md` 补 **"5 分钟从零到能下第一单"** 入
门章节 —— 8 步从 keychain → setup-only SMS → 启动网关 → list account
→ unlock → place-order → 查订单/成交，跑通端到端。中英双语。

## [1.4.25] - 2026-04-17

### 新增 (Added)

#### MCP 交易 / 行情能力补齐（对齐 py-futu-api）

对照 Futu 官方 Python SDK（`FutunnOpen/py-futu-api`）54 个 user-facing
方法盘点后，本版补 **8 个** 高频 MCP tool：

**交易扩展（5 个）**：
- `futu_get_max_trd_qtys` — 下单前算最大可买/可卖（Python
  `OpenTradeContext.acctradinginfo_query`）
- `futu_get_order_fee` — 手续费明细（`order_fee_query`）
- `futu_get_margin_ratio` — 融资融券比率（`get_margin_ratio`）
- `futu_get_history_orders` — 历史订单（`history_order_list_query`）
- `futu_get_history_deals` — 历史成交（`history_deal_list_query`）

**行情分析（3 个）**：
- `futu_get_capital_flow` — 资金流向（`get_capital_flow`）
- `futu_get_capital_distribution` — 资金分布（`get_capital_distribution`）
- `futu_get_market_state` — 市场状态（`get_market_state`）

所有 tool 描述里都明确提到对应的 Python SDK method 名，方便从
py-futu-api 迁移的用户找到。

MCP 覆盖率：**20 → 28 tool**（~37% → ~52% of Python SDK 完整集）。

#### futucli 交易命令 6 件套（命令行下单 / trading bot 基础）

- `futucli place-order` — 下单（**real env 必须 `--confirm`**，防误操作；
  default env = `simulate` 防回车误触）
- `futucli modify-order` — 改单（支持 NORMAL / CANCEL / DISABLE / ENABLE /
  DELETE 5 种 op）
- `futucli cancel-order` — 撤单（modify-order 的常用快捷方式）
- `futucli history-orders` — 历史订单查询（支持 code / 时间过滤 + table/JSON
  双输出）
- `futucli history-deals` — 历史成交查询
- `futucli max-qtys` — 最大可买卖查询

futucli 覆盖率：**14 → 20 业务命令**（~26% → ~37%）。

### backend helper

- `futu_trd::misc::get_order_fee()`（v1.4.24 加过）
- `futu_trd::misc::get_margin_ratio()`（v1.4.25 新增）

### 未覆盖（v1.4.26 候选）

依然缺的 user-facing API：
- 行情类：`option_chain` / `stock_filter` / `history_kline` / `reference` /
  `owner_plate` / `warrant` / `ipo_list` / `future_info` / `user_security`
- 交易类：`cancel_all_order` / `sub_acc_push`（已有 handler 未接 tool）
- 长尾：`price_reminder` / `holding_change` / `code_change` / `rehab` 等

**三端覆盖矩阵参考** `essentials/2026-04-17-1407-api-coverage-matrix.md`。

## [1.4.24] - 2026-04-17

### 新增 (Added)

#### broker 通道断线重连（per-broker reconnect watcher）

Platform 通道 v1.4.12 起就有了"心跳退出 → 自动重连"机制，但 broker 通道
一直**没有** —— broker 心跳失败 3 次退出后，该 broker_id 就永远僵死，
只能重启 opend。v1.4.24 补齐：

- **每个成功建立的 broker 通道**都 spawn 一个 `reconnect watcher` task，
  监听 heartbeat JoinHandle
- heartbeat 退出（通常 TCP 断开的信号）→ 从 `brokers` map 移除旧 Arc
  → 用缓存的 `BrokerAuth`（broker_client_sig/key）**直接 CMD 1001 重登**
  （不走 broker_auth HTTP，因为 auth_code 是一次性的）
- 指数退避重试（3s→60s），连续 6 次失败放弃 watcher，等 Platform 通道
  整体重连时 `establish_broker_channels` 重建所有 broker
- 重连成功 → 更新 `broker_conn_meta.connect_addr`（redirect 可能切到新
  IP）→ 重启 heartbeat → 继续 watch

关键设计：broker 的 `client_sig/key` 有**约 30 分钟有效期**（对齐 C++
`broker_auth` 的 `cltsig_invalidtime`），30min 内重连可完全走缓存；超
过则必须 Platform 重连触发 HTTP auth 重新拉 `auth_code_list`。

新增 struct `BrokerConnMeta { broker_auth, connect_addr, keep_alive_secs }`
+ `GatewayBridge.broker_conn_meta: Arc<DashMap<u32, BrokerConnMeta>>`。

#### CMD 20177 运行时 broker 动态管理

v1.4.23 收到 CMD 20177 `CidStatusChangePush` 只会重拉 CMD 20176 log 新
broker_ids。v1.4.24 真的**动**这些数据：

- **移除的 broker**（当前 brokers map 有但新列表没）→ 从 `brokers` map
  + `broker_conn_meta` 删 entry（reconnect watcher 会发现 meta 缺失后
  优雅退出，conn Arc 被 drop 自动关闭 TCP）
- **新增的 broker**（新列表有但当前 brokers 没）→ **只打 WARN**：
  auth_code 一次性已用完，无法复用建新通道；需等 Platform 整体重连触发
  `establish_broker_channels`。提示用户此信号。

典型触发场景：用户在富途 App 里开了新 broker 或关闭某个 broker，服务
端 20177 → opend 自动同步。

### 架构改动

```
crates/futu-gateway/src/bridge.rs
├── pub struct BrokerConnMeta { ... }                          ← 新
├── GatewayBridge {
│     brokers: Arc<DashMap<u32, Arc<BackendConn>>>,            (v1.4.8)
│     broker_conn_meta: Arc<DashMap<u32, BrokerConnMeta>>,     ← 新 (v1.4.24)
│     ...
│   }
├── async fn establish_single_broker(...)
│     → 签名返回加 (BrokerAuth, final_addr) 供 caller 缓存       ← 改
├── async fn broker_tcp_login(...)                             ← 新
│     只做 connect + CMD 1001，不做 broker_auth HTTP
├── fn spawn_broker_reconnect_watcher(...)                     ← 新
│     heartbeat 退出后自动重连 + 更新 brokers map
└── push_cb 20177 分支：runtime broker diff + 增/删             ← 改
```

## [1.4.23] - 2026-04-17

### 新增 (Added)

#### CMD 9429 / 20177 Push Handler（对齐 C++ broker 变化推送）

Platform 通道接收服务端主动推送的两条"券商变化"信号：

**CMD 9429 `BrokerChangePush`** —— 老的"主推券商变化"信号。C++ 从
`logger.cpp:1456-1477` 的 `OnRecvBrokerChangePush` 已经**退化为只 log**
（注释 "过渡阶段，后续移除"），因为老的 9419 主推协议已废弃。我们对齐
C++ 的保守策略，也只 log 不响应。

**CMD 20177 `CidStatusChangePush`** —— 新的"cid 有效券商列表变化"信号。
对齐 C++ `FTConnBind.proto:19` + `logger.cpp:1613-1633` 的
`OnRecvValidBrokerListChangePush` —— 收到后**触发一次 CMD 20176
重拉**：

```
push_cb 收到 cmd_id=20177
  ↓
tokio::spawn → fetch_valid_broker_list(backend, uid)
  ↓
log 新的 broker_ids 列表
  ↓
（未来可扩展：重建 broker 通道。MVP 只 log，不动 broker 通道）
```

push_cb 是同步 closure，不能直接 await，所以用 `tokio::spawn` +
捕获 `SharedBackend`（ArcSwap）+ BackendConn.user_id（AtomicU32）
完成异步 reaction。

改动：
- `proto-internal/FTConnBind.proto` 加 `BrokerChangePush` +
  `CidStatusChangePush` 消息
- `crates/futu-gateway/src/bridge.rs` push_cb 加 9429 / 20177 两个分支

### 已知限制 (Known limitations)

- **broker 通道运行时动态管理** 仍未实现。v1.4.23 收到 20177 后只重拉
  20176 拿到新 broker_ids，但**不重建 broker 通道**（新增 broker 不会
  自动 connect，减少的 broker 不会断开）。这需要在 `establish_broker_channels`
  之外加运行时维护逻辑，复杂度较高，opend 场景用户开新 broker 罕见，
  MVP 暂不实现。
- **broker 通道断线重连** 目前没有。Platform 通道的重连（v1.4.12 加的
  connect_race + heartbeat）没覆盖 broker。broker 断开后需要重启 opend
  才会恢复。未来版本补。

## [1.4.22] - 2026-04-17

### 新增 (Added)

#### C++ 对齐：CMD 20176 `GetValidBrokerList`

对齐 C++ `FTLogin/.../logger.cpp:1425-1500` 的 `FetchValidBrokerList`
（"已废弃 9419 主推协议，改用 20176"）。Platform 登录后主动发一次 CMD
20176，返回的 `broker_ids` 和 HTTP auth 的 `auth_code_list` 做一致性
校验，不一致打 WARN。MVP 仍以 auth_code_list 为权威（保守策略）。

**新文件**：
- `proto-internal/FTConnBind.proto`（`GetValidBrokerListReq/Rsp`）
- `crates/futu-backend/src/valid_brokers.rs`（send + parse + diff helper
  + 3 单测）

#### `forced_ip_for_conn` 支持

对齐 C++ `address.cpp:360-400` `ParseForcedIpConfig`——CommConfig 里
另一个字段，是**单 IP 强制 + expire 时间戳**，用于紧急切换 / 灰度。
未过期时**绕过**所有 fallback（DNS / 硬编码）直接用，最高优先级。

- 新 `ForcedIpEntry { ip, port, expire_ts }` + `ForcedIpMap`
- `parse_forced_ip()` 支持 String / Object / Null 三态
- `forced_ip_for_attribution()` 判定过期
- 首登 + 重连路径都检查 forced_ip，存在时 candidate 池只留这一个
- 5 新单测（三态 + expire 边界 + attribution 分发）

IP 池优先级链（v1.4.22 完整版）：

```
forced_ip (未过期)        ← 独占
   ↓ (过期或不存在)
CommConfig guaranteed_ip  ← 官方 push
   ↓
DNS                       ← 公开域名
   ↓
Hardcoded                 ← 基线 fallback
```

#### svr_time offset 校正（TOTP）

对齐 C++ `INNBiz_SvrTime::GetSvrTimeStamp()`。`parse_auth_result` 从
authority 响应的 `result.svr_time` 取服务端时间，算出 `server - local`
offset 填到 `AuthResult.svr_time_offset`。所有 TOTP 生成（CommConfig
`/v2/conf/select_all` 的 `auth_token`）用 `local + offset`。机器时钟
偏差 > 30s 时 TOTP 不再被服务端拒，offset > 30 时打 WARN。

### 改进 (Changed)

#### `--setup-only` 提早退出

v1.4.17-v1.4.21 的 `--setup-only` 实际跑完整个 `initialize()`（step 4
拉账户、step 5 注册市场、step 6 拉市场状态、step 7 启动心跳等），~14
秒 + 多余服务端请求。v1.4.22 改成 **auth 成功 + credentials 保存后立即
return**，跳过 TCP login 及以下所有步骤。真机实测 **2.4 秒**退出。

GatewayConfig 加 `setup_only: bool` 字段，`initialize()` 在 step 1
auth 结束后识别这个 flag 短路返回空 push_rx。

## [1.4.21] - 2026-04-17

### 修复 (Fixed)

#### Bug D — CMD 1321 `conn_identify is invalid`（海外账号）

v1.4.20 真机验证 某 HK 账号（HK 账号）时发现：

```
WARN CMD1321 ConnIpRsp error result_code=1 err_msg=Some("conn_identify is invalid")
```

根因：`crates/futu-backend/src/conn_ip.rs:38` 的 `ConnIpReq.conn_identity`
字段**硬编码为 `1`（CN）**——对 HK（attribution=6）/ US（2）/ SG（3）/
AU（4）/ JP（5）账号都发 1，被服务端拒。对齐 C++ F3CLogin Dart 示例
`main.dart:383-386`：

```dart
{"user_attribution": 6, "name": "HK", ..., "conn_identity": 6}
{"user_attribution": 3, "name": "SG", ..., "conn_identity": 3}
// user_attribution → conn_identity 1:1 映射
```

修复：`fetch_conn_ip_list()` 加 `attribution: UserAttribution` 参数，
`conn_identity` 改成 `attribution.to_conn_identity()`。bridge.rs 调用点
传 `auth_result.user_attribution`。

影响：海外账号的 CMD 1321 ConnIP 推荐列表现在能正常拉取，重连路径会
收到服务端推荐的新鲜 IP（和 CommConfig 的 `guaranteed_ip_for_conn` 互补）。

#### Bug A — CommConfig `guaranteed_ip_for_conn` 解析

v1.4.20 线上实测 某 CN 账号时发现 `guaranteed_ip_for_conn parse failed
error=EOF while parsing a value at line 1 column 0`。根因：

- 代码假设 `guaranteed_ip_for_conn` 的值**总是** JSON-in-JSON 字符串
  （对齐 C++ `NNBiz_CommonConfig.cpp:141` + `toStyledString()` 的出口）
- 实际服务端返回多种形态：
  1. JSON string（C++ 路径）
  2. **直接 array**（v1.4.20 实测 某 CN 账号是这种）
  3. `null` / 空串（账号没配置 guaranteed IP）
- v1.4.20 代码对 2/3 形态都会走到 `as_str().unwrap_or("")` → 空串传给
  `from_str` → EOF 错误

修复：`parse_guaranteed_ip` 改签名接 `&serde_json::Value`，三种形态都支持
（null/空串静默返回，array 直接用，string 二次 parse）。加 `value_kind`
诊断 helper。新增 5 个单测覆盖三态 + bad input。

#### Bug B — `remember-login` 把 `code=20` 当 error 退出

服务端对过期 cached credentials 返回 `error_code=20 require_device_verify`
+ `device_verify_sig` + `phone_no`（要 SMS）—— 这是**正常流程**，不是
错误。但 v1.4.20 及之前 `remember_login` 把 `code != 0` 统统返回 Err，
外层 fallback 到 password auth 重跑一次 salt + authority。

连续两次 authority 请求（同 uid）会被服务端反刷规则命中 → 返回
**`ret_type=15 "长时间没登录"`** 拒绝，用户看到这个误导性错误难以诊断。

修复：remember_login 签名加 `verify_cb` 参数，识别 `code=20` 时直接调
`handle_device_verify` 完成 SMS 流程，不再 fallback。

#### Bug C — `ret_type=15` 错误提示不再简单归因 device_id 毒化

v1.4.20 的 `main.rs` hint 把 15 和 21 混在一起提示 "try --reset-device"，
但 15 实际有 3 种独立来源：

1. **device_id 毒化** → `--reset-device` 可解
2. **服务端反刷限流** → sleep 60 重试
3. **账号级风控** → 在富途 App 登录一次

v1.4.21 改成按这 3 类顺序提示用户一步步试。21（验证码错）单独走一条
hint。

### 文档 (Docs)

- `CLAUDE.md` 里 `ret_type=15` 的语义描述重写：区分 3 类来源 + 诊断顺序
  + 加 remember-login `code=20` fallback bug 的历史说明

## [1.4.20] - 2026-04-17

### 新增 (Added)

#### CommConfig 动态 IP 池（对齐 C++ FutuOpenD）

C++ FutuOpenD 的 `NNBiz_CommonConfig.cpp` 通过 `POST /v2/conf/select_all`
从 `api.futunn.com` / `api.moomoo.com` 拉取"公共配置"，其中
`guaranteed_ip_for_conn` 是按 identity 分组的**后台新鲜 IP 池**。当富途
换服务器 IP 时，这是全网同步的官方通道——比 DNS 更权威、比硬编码列表
更新鲜。v1.4.20 起我们对齐这个协议：

- 登录成功后主动拉取一次 CommConfig（用户 uid + TOTP auth_token）
- 解析 `conf_info.guaranteed_ip_for_conn`（JSON-in-JSON），按 identity
  1-6 映射到 `UserAttribution`
- 合并到 Platform IP 池**最前面**（优先级：CommConfig > DNS > 硬编码）
- 失败不阻塞启动，优雅 fallback 到 DNS + 硬编码

Platform IP 池优先级链（v1.4.20）：

```
CommConfig (官方 push, TOTP auth)  ←── 最新
   ↓
DNS (public domain resolution)     ←── 较新
   ↓
Hardcoded (v1.4.11 baseline)       ←── fallback
```

#### TOTP auth_token 生成（Google OTP SHA1）

- `gen_totp_sha1()` 对齐 C++ `OMBase_API_OTP.cpp:12` `GenGoogleOTPCode_SHA1`
- HMAC-SHA1 + RFC 6238 truncation，6 位数字输出
- 固定 base32 key `PEHMABDNLXIOG65U`（对应 C++ `AuthTokenKey`）
- 通过 RFC 6238 Appendix B 测试向量校验

#### 定时后台刷新

- 首登拉到的 snapshot 存进 `GatewayBridge.commconfig`（`ArcSwap` 无锁读
  写）
- `auth::commconfig::spawn_refresher` 起后台任务：睡眠 `limit_time`
  秒（clamp 到 5 分钟 – 2 小时区间）后重拉一次，失败不替换旧 snapshot
- 重连路径优先级改为 **CommConfig 缓存 → DNS → 硬编码**，长时间运行的
  opend 实例断网重连时能拿到最新 IP

改动：
- 新文件 `crates/futu-backend/src/auth/commconfig.rs`（~570 行 + 11 个单测）
- `crates/futu-backend/Cargo.toml` 加 `hmac = "0.12"` + `arc-swap` 依赖
- `crates/futu-backend/src/auth/mod.rs` 导出 `commconfig` 子模块 +
  `UserAttribution` 加 `Hash` derive（HashMap key）+ `build_http_client` 改 pub
- `crates/futu-gateway/src/bridge.rs`：
  - `GatewayBridge` 加 `commconfig: SharedCommConfig` 字段
  - 首登 Platform 池构造插 CommConfig 层 + spawn 后台刷新器
  - 重连 candidates 构造按 CommConfig → DNS → 硬编码 三级优先级

### 对齐 C++ 参照点

| C++ 文件 | 内容 |
|---|---|
| `FutuOpenD/Src/NNProtoCenter/Other/NNBiz_CommonConfig.cpp:53-87` | `PullCommonConfigV2()` URL / body / headers |
| `FutuOpenD/Src/NNProtoCenter/Other/NNBiz_CommonConfig.cpp:89-193` | `OnUpdateAllConfigCallback()` 响应解析 + 分页 |
| `FutuOpenD/Src/NNProtoCenter/Other/NNBiz_CommonConfig.cpp:42-51` | `UpdateAllConfigFromServer` 定时刷新入口 |
| `FTBasis/Src/ftbasis/utility/API/OMBase_API_OTP.cpp` | `GenGoogleOTPCode_SHA1` TOTP 算法 |
| `FTLogin/Src/ftlogin/channel/impl/address.cpp:302-358` | `ParseGuaranteedIpConfig()` identity 映射 |
| `FTLogin/Src/ftlogin/channel/impl/address.cpp:40-55` | 配置项名 `guaranteed_ip_for_conn` |

### 已知限制 (Known limitations)

- **无 broker identity 处理**：`guaranteed_ip_for_conn` 里 identity
  ≥1000 是 broker 通道 IP（Futu HK = 1001 / US = 1007 等）。本版只抓
  Platform identity 1-6；broker 仍然用 v1.4.8 的固定流程。
- **使用本机时间作为 svr_time**：TOTP 窗口 30s，机器时间偏移 > 30s 会
  被服务端拒。大部分 NTP-synced 的机器 OK，未来对齐 C++
  `INNBiz_SvrTime::GetSvrTimeStamp()` 后会更稳。

## [1.4.19] - 2026-04-17

### 新增 (Added)

#### DNS 域名解析动态 IP 池

硬编码 Platform IP 池会随富途换服务器过时。启动时对 attribution 对应的
**公开 DNS 域名** 做解析，把返回的 IP 插到 shuffled_pool 最前面（硬编码
列表作 fallback 保留）。

| Attribution | 域名 |
|---|---|
| CN | `nnconn.futunn.com` |
| HK | `hkconn.futunn.com` |
| US | `usconn.moomoo.com` |
| SG | `sgconn.moomoo.com` |
| AU | `auconn.moomoo.com` |
| JP | `jpconn.moomoo.com` |

DNS 解析 3s 超时，失败 gracefully fallback 到硬编码池（现有行为不变）。
`connect_race` 仍然拿 DNS + 硬编码合并后的前 N 个并发，和 v1.4.12 语义
兼容。

注：C++ FutuOpenD (FTNN/FTMM) 本身**不**走 DNS（靠 CommConfig 服务端 push
—— `address.cpp:159-170`）。我们加 DNS 是为了"IP 自动保鲜"，不是盲目照抄
C++。

改动：
- `crates/futu-backend/src/auth/conn_points.rs` 新增 `domain_for_attribution()`
  + `resolve_domain_ips(attr) -> Vec<(String, u16)>`
- `crates/futu-gateway/src/bridge.rs`：首登 shuffled_pool 构造 + 重连
  candidates 构造两处都先问 DNS
- 2 个新单测（domain 映射完整性 + DNS 返回格式校验）

### 改进 (Changed)

#### `Platform IP pool exhausted` 错误文案加诊断建议

v1.4.18 后 Rocky Linux 用户继续反馈 offline mode —— 实际是他腾讯云
Lighthouse 出站防火墙默认不放 9595。错误消息现在会提示：

```
ERROR gateway init failed: all Platform IPs are unreachable on port 9595.
This is almost always an outbound firewall issue on your host, NOT a Futu
server problem. Quick check:
  timeout 5 bash -c '</dev/tcp/119.29.48.17/9595'
— if this also fails (it's Tencent Cloud in Guangzhou), your host is
blocking outbound TCP 9595. Fix: open 9595 in your cloud security group ...
```

### 安全 (Security)

- **`AuthConfig` 加 `ZeroizeOnDrop`**：drop 时 `password` 字段堆内存清零，
  减小 core dump / `/proc/<pid>/mem` 读到明文的窗口。新依赖 `zeroize 1.8`
- **cargo audit 清零**（3 unmaintained + 1 CVE 全处理）：
  - 删 `atty`（RUSTSEC-2024-0375），换 stdlib `std::io::IsTerminal`
  - 升 `tabled 0.16→0.20` 连带 `tabled_derive + proc-macro-error2`
    → 清 RUSTSEC-2024-0370
  - 升 `axum-server 0.7→0.8` → 清 RUSTSEC-2025-0134
  - `.cargo/audit.toml` 记录剩余 2 条仍 allow 的 advisory（rsa 上游无修复、
    rand unsound 不影响我们用的 API），附明确理由

### 重构 (Refactor)

- 抽 `auth/parse.rs`（135 行）—— HTTP 响应解析三函数（`parse_auth_result` /
  `parse_auth_code_list` / `save_credentials_from_response`）。`auth/mod.rs`
  从 v1.4.18 的 1487 → 1369 行。auth/ 现 **7 个子模块**

### 文档 (Docs)

- `guide/auth.md` / `keys-json.md`（中英）`trade:unlock` scope 从
  "(reserved, not implemented)" 改成"MCP `futu_unlock_trade` 工具用" ——
  实际已实现（`guard.rs:61` 映射），文档写错了

## [1.4.18] - 2026-04-17

### 新增 (Added)

#### 登录密码 7 层优先级解析链（彻底堵 `ps aux` 攻击面）

同事之前提 bug report："明文密码出现在 `ps aux` / `~/.bash_history`"。
v1.4.17 前只有 `--login-pwd` / `--login-pwd-md5` / XML/TOML 明文四条路径，
都有各自的泄露面。v1.4.18 新增**组合方案**：7 层优先级，不同场景各取所需。

```
1. --login-pwd-file <path>   读文件（Docker secrets / systemd LoadCredential）
2. --login-pwd <plain>       明文 argv（会打 deprecation WARN）
3. --login-pwd-md5 <hex>     md5 argv（同样 WARN）
4. FUTU_PWD env var          环境变量
5. OS keychain               futucli set-login-pwd --account X 写入的
6. 交互式 prompt（stdin 是 tty）
7. 都没有 → 报错退出
```

**新增入口**：

- `futucli set-login-pwd --account <id>` —— 交互式 prompt（无回显不进 history）
  写 OS keychain
- `futucli clear-login-pwd --account <id>` —— 清除
- `futu-opend --login-pwd-file <path>` —— 从文件读（argv 只有路径，没有明文）

**安全增益**：

| 攻击面 | v1.4.17 `--login-pwd` | v1.4.18 keychain / file |
|---|:-:|:-:|
| `ps aux` 看到 argv | 😱 | ✅ |
| `~/.bash_history` | 😱 | ✅ |
| `/proc/<pid>/cmdline` | 😱 | ✅ |
| 配置文件 backup 泄漏 | 😱 | ✅ |

**兼容性**：

- 老用户 `--login-pwd` / `--login-pwd-md5` **仍然工作**，但启动时会打
  **WARN** 提示迁移：
  ```
  WARN ⚠️  --login-pwd passes plaintext password via argv;
       visible in `ps aux` and shell history.
       Recommended: `futucli set-login-pwd --account 12345678` ...
  ```

**Keychain 机制**：每账号一条独立条目（username = `login-password.<account>`），
所以多账号不会互相覆盖。后端：macOS Keychain / Linux Secret Service /
Windows Credential Manager。和 v1.4 的 `set-trade-pwd` 复用同一套
`futu_auth::KEYRING_SERVICE = "futu-opend-rs"` 基础设施。

**推荐部署姿势**：

```bash
# 本地长期使用
futucli set-login-pwd --account 12345678
./futu-opend --login-account 12345678 ...

# Docker
docker run -v pwd:/run/secrets/futu-pwd:ro \
  ... --login-pwd-file /run/secrets/futu-pwd

# systemd
[Service]
LoadCredential=login-pwd:/etc/futu/pwd
ExecStart=... --login-pwd-file ${CREDENTIALS_DIRECTORY}/login-pwd
```

### 新增依赖

- `keyring` 3 + `rpassword` + `atty`（futu-opend）—— 和 futucli 复用同版本
  backend features（`crypto-rust` 避免 Linux 上的 libsecret 依赖）

### 文档

- 启动速查教程加第 7 节"登录密码安全存储"，4 种部署场景的命令组合
- CLI 参考表新增 `--login-pwd-file` / `set-login-pwd` / `clear-login-pwd`
- 中英文版同步更新

## [1.4.17] - 2026-04-17

### 改进 (Changed)

#### device_id 生命周期全面升级

v1.4.16 做了 device_id 毒化的**预防**（拦截空验证码、`--device-id` 逃生），
v1.4.17 进一步做**彻底**处理：持久化 + 自动恢复 + 一键重置 + 非交互分离。

**1. 持久化随机 device_id**（对齐 C++ `FTGTW_Inner_API.cpp:198`
`GetDeviceID()`）

- 之前：`md5("futu-opend-rs-{account}")[..16]` 固定值 ——
  一旦被服务端锁定只能换 account 绕过
- 现在：首次启动随机生成 16-hex 写入
  `~/.futu-opend-rs/device-{hash}.dat`，后续启动从文件读
- `--device-id <hex>` 仍然可覆盖，且**更新**文件

**2. 统一持久化目录 `~/.futu-opend-rs/`**

- 之前：`.futu_credentials_{account}` 存在**当前工作目录** ——
  不同 cwd 启动 opend 找不到凭据，被迫重新 SMS 验证
- 现在：`~/.futu-opend-rs/credentials-{hash}.json` + `device-{hash}.dat`
  集中管理；旧 cwd 文件首次启动时**自动迁移**到新位置

**3. SMS 失败自动轮换 device_id**（bug report #3 进阶）

- 之前：用户输错验证码 → `error_code=21` → device_id 被服务端标记失败 →
  后续所有请求返回 `error_code=15 长时间没登录`，**永久锁死**
- 现在：检测到 `error_code=21` 自动清掉坏 device_id 生成新的，重新触发
  SMS 最多 2 次。服务端不再累计同 device_id 的失败
- `handle_device_verify` 现在**显式检查** `error` 字段，不再被含糊的
  codec error 吞掉

### 新增 (Added)

#### `--reset-device` flag

一键清空 `~/.futu-opend-rs/device-{hash}.dat` + `credentials-{hash}.json`，
下次启动重新生成随机 device_id 走完整首登（触发 SMS）。

```bash
./futu-opend --reset-device --login-account X --login-pwd Y ...
```

#### `--setup-only` flag

只完成首次 SMS 设备验证 + 凭据缓存就退出，**不启动任何 server**。
用于 systemd / Docker / cron 场景：

```bash
# 1. 前台终端跑一次（会触发 SMS，交互输入验证码）
./futu-opend --setup-only --login-account X --login-pwd Y --platform moomoo

# 2. 之后生产环境启动（直接走 remember-login 跳过 SMS）
./futu-opend --login-account X --login-pwd Y --platform moomoo &
```

#### 错误文案智能化

`gateway initialization failed` 时，如果错误里含 `ret_type=15/21` 或
"长时间没有登录" / "验证码错" 字样，额外提示用户尝试 `--reset-device`。

### 新增依赖

- `dirs` 6.0（获取 `~` 目录）

### 新增单测

- `account_key_stable_across_phone_format_variants` —— 确保
  `+86-xxx` 和 `xxx` 归一化后指向同一凭据文件
- `account_key_differs_by_account` —— 不同账号有不同 key
- `read_or_generate_device_id_is_persistent` —— 两次调用返回相同值
- `read_or_generate_device_id_respects_override` —— `--device-id`
  覆盖持久化

## [1.4.16] - 2026-04-17

### 新增 (Added)

#### `--device-id <hex>` 参数（bug report #3）

之前 device_id 从 account 派生（`md5("futu-opend-rs-{account}")[..16]`），
一旦该 ID 因空验证码提交被服务端锁定（`error_code=15/21`），用户只能改
account 绕过。新增 `--device-id` 参数让用户手动指定新 ID：

```bash
./futu-opend --device-id abcdef0123456789 --login-account ... --login-pwd ...
```

#### 启动时端口冲突检测（bug report #6）

多实例并行（如同时跑 futunn + moomoo）是 `--platform` 的预期场景。之前
两个实例绑同一端口（`0.0.0.0:11111` vs `127.0.0.1:11111`）会导致
futucli 连到旧实例看到错账号的数据，且**没有任何警告**。

启动时对 FTAPI / REST / gRPC / WebSocket 四类端口做 `connect_timeout`
探测：已被占用则打 WARN 日志告知用户改端口。

### 修复 (Fixed)

#### 后台模式空验证码毒化 device_id（bug report #3 + #5）

后台运行（`&` / cron / 被其他进程调用）时 stdin 不是 tty，`read_line`
立刻返回空字符串 → 空验证码被提交到服务端 → `error_code=21` →
device_id **永久降级**（后续所有请求返回 `error_code=15`，即便用户已在 App
上重新登录也无法恢复）。

修复：`prompt_input` 加 `atty::is(Stdin)` 检测：
- 非 tty 时直接报错退出，不提交空验证码
- tty 模式下用户输入空字符串也拦截，不发到服务端
- 错误信息提示用户需要前台终端运行，或使用 `--device-id` 切换新 ID

新增依赖：`atty` 0.2

## [1.4.15] - 2026-04-17

### 修复 (Fixed)

#### `--platform moomoo` 登录彻底修通

同事搭中间人代理实测发现 **`--platform moomoo` 完全不能用** 的唯一根因：
登录请求没有按所选平台切换客户端类型，导致 moomoo 登录在 salt 阶段被拒绝，
并返回类似“账号密码不匹配”的误导性错误。

正确行为：登录请求根据 `--platform` 选择对应客户端类型，和官方 OpenD 的平台选择逻辑保持一致。

修复：
- 登录配置保留平台来源，构造登录 HTTP 请求时按平台填充客户端类型
- gateway 启动参数中的 `--platform futunn` / `--platform moomoo` 会进入同一套动态选择逻辑

同事通过代理修改 client-type 后**四步认证全部通过**，确认 6 个交易账户 +
完整持仓数据正常返回。

#### salt 响应错误信息丢失（bug report 建议 #1）

之前 `auth.moomoo.com` 返回 `"result": null` + `"error": {"error_code": 2,
"error_msg": "账号密码不匹配"}` 时，我们代码丢弃了 error 对象，只报
"协议解析错误: salt: missing result" —— 用户完全无法定位。

修复：salt 解析时先检查 error 字段，有 `error_code != 0` 就把原始 error_msg
传给 `FutuError::ServerError`，用户能看到服务端实际的拒绝原因。

#### `--auth-server` 指定代理时被 attribution 自动切换覆盖（bug report 建议 #2）

之前 `--auth-server http://127.0.0.1:19998`（代理）时，salt 里返回
`user_attribution=2` 触发切到 `https://auth.moomoo.com`，绕过了用户代理。

修复：只对两个标准域名（`auth.futunn.com` / `auth.moomoo.com`）做 attribution
自动切换。非标准 URL（代理、测试环境）一律保持用户指定的地址。

## [1.4.14] - 2026-04-17

### 新增 (Added)

#### `--platform <futunn|moomoo>` CLI 标志

接着 v1.4.13 修 moomoo 手机号登录后，用户反馈还有个场景我们代码没覆盖：
**同一手机号 / 邮箱在牛牛和 moomoo 两边都注册了独立账号**（可以不同密码）。
我们默认发 salt 到 `auth.futunn.com`，结果 futunn DB 里能查到 HK 账号 →
attribution=Hk → 不切 moomoo → 登到了**错账号**（牛牛那个，非 moomoo）。

新增 `--platform` 标志让用户显式选平台：

```bash
# 牛牛账号（默认不变）
./futu-opend --login-account 12345678 --login-pwd XXX

# moomoo 账号
./futu-opend --login-account '+86-13900000000' --login-pwd XXX --platform moomoo
```

优先级：

1. `--auth-server <url>` 显式 URL（最高，给测试环境用）
2. `--platform moomoo/futunn` → auth.moomoo.com / auth.futunn.com
3. TOML / XML 里的 `platform` 字段
4. 默认 `auth.futunn.com`

日志启动时打印：

```
INFO  login credentials  account=+86-13900000000  platform=moomoo  auth_server=https://auth.moomoo.com
```

改动：

- `crates/futu-opend/src/main.rs` 新增 `Platform` enum（clap `ValueEnum` +
  serde `Deserialize`），`--platform` flag，`XmlConfig.platform` 字段，
  `RuntimeConfig.platform` 字段，以及 `merge_config` 里的解析优先级
- `deploy/examples/futu-opend.toml` 加 `platform = "moomoo"` 注释示例
- `docs-site/docs/reference/cli.md` `futu-opend` 表格加 `--platform` 行，
  更新 `--auth-server` 默认值说明

### Known issues（v1.4.13 列的继续保留）

- `+8613900000000` 区号粘着号码（无 `-` 分隔）格式无法自动拆分 ——
  需要用户输入 `+86-13900000000` 格式

## [1.4.13] - 2026-04-17

### 修复 (Fixed)

#### moomoo 手机号账号 `error_code=2 账号密码不匹配`

加拿大同事反馈 moomoo 账号（手机号 `+86-13900000000`）一直无法登录：salt
正常、tgtgt 生成、服务端能解开 tgtgt，但 `error_code=2 账号密码不匹配`。同一
密码在 moomoo App 可正常登录，说明密码本身对。

**根因**：我们把用户输入的 `+86-13900000000` **整串**当作 account 传给服务端，
但 C++ `auth_impl.cpp:267-283` `AuthByAccount` 的约定是：UI/上层把用户输入
拆成 `account="13900000000"` + `region_code="86"` 两个分开字段。服务端按
**号码本体** `13900000000` 查存的 pwd_md5，我们 tgtgt 里发的 account 是
带前缀的整串 → 服务端查不到对应的 pwd_md5 → 返回 `error_code=2`。

牛牛号（如 `12345678`）因为纯数字没前缀，不受影响，所以之前测试都没发现这个
bug。

**修复**：`crates/futu-backend/src/auth.rs` 新增 `normalize_phone_account()`
入口函数，解析 `+<区号>-<号码>` 格式：

- `+86-13900000000` → `("13900000000", Some("86"))`
- `12345678` → `("12345678", None)`  纯数字保持
- `user@example.com` → `("user@example.com", None)`  邮箱保持
- `+8613900000000`（无分隔符）→ 原样保持，不猜区号（C++ 同行为，依赖 UI 拆分）

所有后续流程使用归一化后的 account：
- **salt URL**：附 `&is_phone=true&region_no=86`，对齐 `auth_impl.cpp:1258-1261`
- **tgtgt payload**：account 字段用号码本体 `13900000000`，对齐
  `auth_cryptor.cpp:167` `CreateNewTgtgt` account 版
- **Authority POST body**：带 `"is_phone": "true"` + `"region_no": "86"`，
  对齐 `auth_impl.cpp:1681-1691`
- **凭据缓存 key**：用归一化后的 account，避免 `+86-xxx` / `xxx` 两个 key
  各存一份

已加 3 个单测（`normalize_phone_with_region_code` / 
`normalize_phone_without_separator_not_split` / 
`normalize_non_phone_account_unchanged`）。

### Known issues

- `+8613900000000`（区号粘着号码，无 `-` 分隔）格式无法自动拆分。C++
  本身也不在底层做推断，依赖上层 UI 把区号拆好。用户需要输入
  `+86-13900000000` 格式

> 注：v1.4.13 发布时曾以为 moomoo 数字 ID 和邮箱 salt 接口不支持 ——
> 后续排查（见 v1.4.15）发现真正原因是登录请求没有按平台选择正确客户端类型。
> v1.4.15 修复后，两边都应支持三种账号格式（数字 ID / 手机号 / 邮箱）。

## [1.4.12] - 2026-04-17

### 新增 (Added)

#### 并发连接竞速（对齐 C++ `ConnectStrategyAddr`）

v1.4.10 给单 IP 加超时、v1.4.11 按 attribution 选对地区的池。这版把"顺序
尝试"升级成"并发竞速"：一批同时连 3 个 IP，谁先 TCP 握手完成就用谁，其余
连接 drop 掉（tokio 自动 abort pending future）。对齐 C++
`connector.cpp:175-189` `ConnectStrategyAddr` 的 `concurrency_ip` 语义
（C++ 并发连 + 最多等 `kTimeoutConnectStrategyAddrMs=3s`）。

首屏体验：从"最差那个 IP 的 RTT（或 10s 超时）"降到"最快那个 IP 的 RTT"（
正常 <200ms）。

改动：
- `crates/futu-backend/src/conn.rs` 新增：
  - `BackendConn::establish_stream(addr, timeout)` —— 纯 TCP 连接 + nodelay，
    不 spawn 任何 task
  - `BackendConn::from_stream(stream, push_cb)` —— 从已建立的 TcpStream 构造
    完整 conn（spawn recv/send task）
  - `BackendConn::connect_race(&[addr], push_cb) -> (Self, winner_addr)` ——
    用 `FuturesUnordered` 并发 N 个 `establish_stream`，第一个 `Ok` 胜出，
    其余丢弃。每个候选独立带 10s 超时。
  - `BackendConn::connect()` 内部改成 establish + from_stream 组合
- `crates/futu-gateway/src/bridge.rs`：
  - 首登：shuffled pool 按 3 个一批 `connect_race`，失败取下一批（最多
    3 批 = 9 个 IP）；redirect 路径仍然单 IP 直连
  - 心跳后重连：取 attribution 池前 3 个（rotate 起点避免扎堆）`connect_race`
  - 删除了 v1.4.10 引入的 `MAX_CONNECT_FALLBACKS` 顺序 fallback 逻辑——
    并发竞速原生就覆盖了单 IP 失败的场景
- 新增 2 个单测：`connect_race_rejects_empty_list` +
  `connect_race_all_fail_returns_last_err`

## [1.4.11] - 2026-04-16

### 修复 (Fixed)

#### 按 `user_attribution` 选 Platform IP 池

v1.4.10 加了 connect 超时 + fallback，但 Rocky Linux 的 HK 用户升到 v1.4.10
后仍然卡：日志显示 `attribution=Hk ... connecting to backend... addr=49.234.241.94:9595`
—— 我们初始选 IP 时用的是 `conn_points::ALL`（全是 CN IP）。海外账号从 CN IP
走 TCP 本来就慢 + 部分网络环境还会被运营商干预。fallback 只是兜底，首屏还是
先踩 CN IP。

修复：补齐各地区 Platform TCP backend IP 池，按 `user_attribution` 选池。

- `crates/futu-backend/src/auth.rs` 的 `conn_points` 模块重构：
  - `CN` —— 12 个（对齐 C++ `address.cpp:498-511` `LoadHardcodeAddress()`）
  - `HK` —— 6 个 (`101.32.217.163` / `43.135.111.64` / `43.132.195.157`
    / `43.135.85.38` / `106.55.216.230` / `134.175.255.64`)
  - `US` —— 14 个（`openapi.moomoo.com` 系）
  - `SG` —— 11 个（sg.moomoo.com 系）
  - `AU` —— 2 个, `JP` —— 2 个
  - 新增 `for_attribution(attr) -> &'static [(&str, u16)]` 按归属取池
  - `ALL` 保留指向 CN 作 deprecated 兼容
- `crates/futu-gateway/src/bridge.rs`：
  - 初始 `backend_addr` 用 `for_attribution(auth_result.user_attribution)`
    随机起始 index 选（而不是从全局池抽）
  - fallback pool 也只用同一归属的池（不再混合其他地区 IP 污染）
  - 重连循环从 `get_by_region(config.region)` 切到
    `for_attribution(reconnect_auth.user_attribution)`，和首登一致

体验差异：HK/US/SG/AU/JP 账号首登直接命中本区 IP，不再先试 CN。

### Out of scope（下版迭代）

仍留到 v1.5：并发连 2-3 个 IP，谁先通用谁（对齐 C++ f3clogin
`address.cpp` 多 IP 并行探测）。

## [1.4.10] - 2026-04-16

### 修复 (Fixed)

#### 初始 backend 连接超时 + 单 IP 失败不 fallback

Rocky Linux 用户反馈 `error=网络错误: Connection timed out (os error 110)`
然后直接进 offline mode。根因有两处：

1. **`BackendConn::connect` 没超时包裹** —— `TcpStream::connect(addr).await`
   在连接不通时会等 Linux 默认 `tcp_syn_retries=6` 约 127 秒才返回
   `ETIMEDOUT`，用户等 2 分钟看到 gateway init failed。
2. **单 IP 失败直接 bubble up** —— bridge.rs 的 connect 循环失败就 `?` 抛出，
   没尝试 `conn_points` 里的其他 IP。初始 `backend_addr` 随机选，命中一个不通的
   IP 就整个 init 挂掉。

修复：
- `crates/futu-backend/src/conn.rs`：`BackendConn::connect` 用
  `tokio::time::timeout` 包 10s 超时。超时/拒绝统一返回 `FutuError::Network`
  让上层能 fallback。
- `crates/futu-gateway/src/bridge.rs`：connect 失败时从 `conn_points::ALL`
  里取下一个候选 IP 重试，最多 `MAX_CONNECT_FALLBACKS = 5` 次。重试不消耗
  login redirect 的 attempt 计数（两者独立）。

坏情况体验：从卡 2 分钟 → 50 秒（5 次 10s 超时）才进 offline mode，期间大概率
某个 IP 能通直接登录成功。

### Out of scope（下版迭代）

MVP 只做"坏 IP fallback"。下面两件更彻底的改进留到 v1.5：

- 按 `user_attribution` 选 IP 池（现在海外账号也会先试 CN IP，虽有 fallback
  但首屏慢）。需要先补 moomoo 域的 TCP backend IP 列表（C++ `address.cpp:495-740`）。
- 并发连多 IP，谁先通用谁（对齐 C++ f3clogin）。

## [1.4.9] - 2026-04-16

### 修复 (Fixed)

#### CMD 3020 账户资产查询按 broker 通道分发

v1.4.8 broker 通道上线后遗漏的一处路由修复。对齐 C++
`NNProto_Trd_Acc.cpp:988`：
`SendTCPProto_ProtoBuf_WithAccID(m_nAccID, m_enProtoCategory, NN_ProtoCmd_Trd_AccountInfoReq, req)`
—— CMD 3020 走 broker 通道不是 platform。

之前 `init_trade_data` 对所有真实账户发到 platform backend，一半 ok / 一半
`result=1 err=unknown`（发到错通道的那部分）。修复后实测 某 CN 账号 账号
`dispatched=2 skipped_no_broker=0`，两个真实账户都成功拿到资产。

改动：
- `crates/futu-gateway/src/bridge.rs` 新增 `dispatch_trade_data_queries`：
  按 `account.security_firm` 反查 `broker_id` → 选对应 `broker_conn`
- 新增 `security_firm_to_broker_id` 反向映射
- `query_account_info` API 保持不变（单账户单 conn）

### 新增 (Added)

#### broker_config() 补齐到完整 7 个 broker

v1.4.8 plan 里把 Futu AU/JP 标注 "待验证" —— 实际 C++
`env_config.cpp:41-46` 里就有明确字面值，当时偷懒没挖。v1.4.9 补齐：

| broker_id | name | auth_domain |
|---|---|---|
| 1001 | Futu HK | authority.futuhk.com |
| 1007 | Futu US | authority.us.moomoo.com |
| 1008 | Futu SG | authority.sg.moomoo.com |
| **1009** | **Futu AU** | **authority.au.moomoo.com** |
| **1012** | **Futu JP** | **authority.jp.moomoo.com** |
| **1017** | **Futu MY** | **authority.my.moomoo.com** |
| **1019** | **Futu CA** | **authority.ca.moomoo.com** |

Futu AirStar (1022) 在 C++ `broker_config.cpp:17` 没有 auth_domain，跳过。

### 其他 (Misc)

- `style`: 补跑 `cargo fmt` 修 v1.4.8 几个 commit 漏跑的格式（CI fmt-check 卡在这儿）

## [1.4.8] - 2026-04-16

### 新增 (Added) — **Broker 通道 MVP**

让 某 CN 账号 等有交易账户的用户能正确拉取账户列表（CMD 2282/2298）。
在 v1.4.7 的 Platform 登录基础上增加**券商独立 TCP 通道**。

对齐 C++ `FTLogin/Src/ftlogin/channel/impl/logger.cpp:548-558`：Platform 登录
成功后自动为 `auth_code_list` 里每个已知 broker 走一遍"broker_auth HTTP
→ TCP 连接 → CMD 1001 kCmdLoginBroker 登录"流程。

#### 新增数据结构（`crates/futu-backend/src/auth.rs`）

- `BrokerAuthCode { broker_id, auth_code, invalid_time }` — auth 响应条目
- `BrokerAuth { broker_id, customer_id, broker_client_sig, broker_client_key }` —
  broker_auth HTTP 响应解析结果
- `BrokerConfig { broker_id, name, conn_identity, auth_domain }` —
  对齐 `FTLogin/Src/ftlogin/config/impl/broker_config.cpp:9-18` 映射表
- `AuthResult` 扩展 `auth_code_list` / `rand_key` 字段
- `UserAttribution::default_broker_id()` — 按归属地派生默认 broker
  （CN/HK→Futu HK 1001，US→Futu US 1007，SG→1008，AU→1009，JP→1012）

#### 新增 broker_auth() HTTP 函数

- `POST https://{broker_auth_domain}/broker_auth/client_auth`
  body `{uid, auth_code, device_id, broker_id}`
- 响应 `broker_client_key` 用 rand_key 做 AES 解密（对齐
  `auth_impl.cpp:3434` `DecryptByRandKey`）
- broker_auth_domain：Futu HK = `authority.futuhk.com`，Futu US =
  `authority.us.moomoo.com`，Futu SG = `authority.sg.moomoo.com`
  （源 `FTLogin/Src/ftlogin/config/impl/env_config.cpp:41-43`）

#### tcp_login 通用化

- 抽出 `tcp_login_raw` 通用版，加 `cmd_id / conn_identity /
  effective_user_id / client_sig_override` 四参数，Platform 和 Broker 共用
  同一实现（对应 C++ `SendNormalLoginProtocol` 同时用于 6001/1001）
- `tcp_login` 保留作 Platform 专用快捷入口，语义不变

#### Bridge 多后端管理（`crates/futu-gateway/src/bridge.rs`）

- 新增 `brokers: Arc<DashMap<u32, Arc<BackendConn>>>` 字段
- `backend_for_cmd(cmd_id)` 分流：2282/2298 走 broker，其余走 platform
- `initialize` 新增 **Step 3c**：Platform 登录完成后并行建立
  auth_code_list 里每个已知 broker 的通道（**失败非 fatal**，per-broker
  warn 不阻塞 gateway 启动）
- `fetch_real_accounts` 改走 broker conn（原来错发在 Platform 上导致 52 字节
  ex_head + body 0 字节）

### 修复 (Fixed) — **登录链路完整重写（v1.4.7 级改动合并进 v1.4.8）**

#### 1. `ret_no_uid=true` 回归 salt URL（HTTP auth 层）

v1.4.6 的根因定位：C++ `auth_impl.cpp:1258` salt URL **始终带
`ret_no_uid=true`**，强制 uid=0 → TGTGT 用 account 版（ver=8） → Authority
body 用 `account` 字段的**一条龙**路径。v1.4.3 踩坑是因为当时 TGTGT 还是 uid
版（ver=6），三项混合状态才签名错。v1.4.6 TGTGT 已经是 account 版，但还缺
`ret_no_uid=true` + Authority body 的 account/uid 分流逻辑 → 所以一直
`error_code=2`。

**v1.4.8 修正三项一起对齐 account 路径**：
- `fetch_salt` URL 加 `ret_no_uid=true`
- `post_auth` body：`uid != 0` 写 `"uid"`，`uid == 0` 写 `"account"`
  （对齐 `auth_impl.cpp:1681-1691`）
- `handle_device_verify` 触发点从 error 对象里 parse 真实 uid
  （对齐 `auth_impl.cpp:1795 ParseJsonUint64(error, "uid", user_id_)`）

**实测效果**：CN 账号 某 CN 账号 登录成功 → error_code=2 消失 → 触发 error_code=20
正常的 SMS device verify 流程 → 拿到 client_sig/client_key。

#### 2. TCP 登录对齐 C++ logger.cpp:148-220

- **AES key 用完整 client_key**：原 v1.4.6 截取前 16 字节走 AES-128，
  实际 HTTP auth 拿到的是 32 字节 client_key（AES-256）。改用
  `aes_cbc_md5_encrypt_var` 对齐 `OMCrypt_FTAES_MD5_Encrypt(key, key_size, ...)`
- **client_ex_ver 从 1002 改成 6208**：C++ 这个字段用 `GetBuildVersion()`
  = `FTGTW_Client_Build`（`FTGTW_Version.h:6`），不是 ClientVersion(1002)
- **ReqEncryptData 补齐字段**：原 v1.4.6 只发 field 1-6，补全 12 字段：
  `host_ip`（field 7）、`conn_identity`（field 8，关键 —
  `FTConnCmn.proto:ConnIdentity` CN=1 等）、`host_port`（field 9）、
  `client_feature`（field 10，嵌套 message）、`os_name`（field 12）
- **UserAttribution::to_conn_identity()** 派生 Platform conn_identity
- **AuthResult 加 `user_attribution`** 以透传到 TCP 登录层

**实测效果**：`TCP login succeeded, got session key keep_alive=28`

#### 3. nn_codec ex_head 剥离

C++ `ProtocolHeader`（`protocol_header.cpp:45-53`）把 `body_len`
字段实际存 `ex_head_body_len = ex_head_len + body_len`，ex_head（trace
info 等）放在 header 之后、真实 body 之前。

- NNHeader 新增 `ex_head_len: u16` 字段（offset 30-32 u16 BE）
- Decoder 剥掉 ex_head，`NNFrame.body` 只暴露真实 body
- NNFrame 新增 `ex_head: Bytes` 字段 + `parse_ex_head_error()` 方法，
  服务端 body 为空时从 `FtnnExtendHead.err_info`（field 5 ErrorInfo）
  里读业务错误
- conn.rs 接收端自动 log 服务端下发的 err_info

**实测效果**：CMD 1321 ConnIP 响应由 619 字节变 418 字节（ex_head 201 字节
被剥离），protobuf 解析不再漏字段。

#### 4. remember-login 凭据解密修复

`rand_key` 不再截断到 16 字节 —— salt32 非空路径下是 32 字节，截断后解密
AES-256 加密的 `client_key` 会出 `cbc_md5_var: last_block_size > 15` 错误。
改用完整 base64 解码后的原始字节。

**实测效果**：remember-login 成功跳过 SMS 验证码。

#### 5. 心跳命令号按通道分（CMD 6003 vs CMD 1003）

对齐 C++ `channel_impl.h:62-63`：
- `kCmdHeartbeatPlatform = 6003` —— Platform 通道心跳
- `kCmdHeartbeatBroker   = 1003` —— Broker 通道心跳

v1.4.7 及以前硬编码 `CMD_HEARTBEAT = 1003` 发到 Platform 通道，服务端
返回 `code=-102 CONN can not find command service`（因为 Platform 通道
不认 1003）。

修复：`heartbeat.rs` 拆出 `start_heartbeat`（Platform, cmd=6003）
和 `start_broker_heartbeat`（Broker, cmd=1003）。Platform 通道和每个
已建立的 broker 通道各自独立起心跳任务，对齐 C++ `INNProto_Trd_KeepAlive`
per-broker 心跳语义。

#### 6. ex_head err_info "can not find command service" 降级

`code=-102 "can not find command service"` 是服务端**正常**的
"此账户/通道不支持该 cmd" 软失败信号（例如 某 CN 账号 在 Futu HK broker 上
没有授权账户时 CMD 2298 就这样返回）。conn.rs 对这种已知软失败码
降到 `debug`，其他错误保留 `warn`。

### 新增测试

- `parse_auth_code_list_extracts_entries` / `_tolerates_malformed` /
  `_missing_returns_empty`
- `broker_config_known_and_unknown`（1001/1007/1008 返回 Some，未知返回 None）
- `test_nn_codec_strips_ex_head`（手拼带 ex_head 的 wire 帧验证 Decoder 剥离）

共 191 tests passing，clippy clean。

### 文档

- CLAUDE.md "历史坑 #1" 纠正：`ret_no_uid=true` 在 account 版 TGTGT（ver=8）
  下**必须带**，v1.4.3 踩坑根因是当时 TGTGT 还是 uid 版 ver=6（三项混合状态）
- CLAUDE.md "历史坑 #2" 小端序说明：OMBinSrz 对基础类型是 memcpy host-order
- `plans/v1.4.8-broker-channel.md`（从 `~/.claude/plans/` 归档）

### Out of scope（下版迭代）

- **多 broker 并行深测**：MVP 只确保 Futu HK（1001）和 Futu US（1007），
  其他 broker 需要样本账号后续验证
- **CMD 9419/9429 FetchValidBrokerList**：C++ 还另发 TCP 请求确认有效 broker
  列表，MVP 直接信 HTTP auth 的 auth_code_list
- **CMD 20147 kCmdUpdateConnIpBroker**：broker 专用 ConnIP 刷新
- **硬编码 broker IP 表**（`address.cpp:495-740` Futu HK 独立 IP 池）：MVP
  复用 Platform IP，若服务端拒绝再补
- **Broker 断线重连**：当前只重连 Platform，broker 掉线需要单独补
- **交易命令全路由**：MVP 只路由 2282/2298，下单/撤单/资金/持仓命令后续扩

## [1.4.6] - 2026-04-16

### 深度改造 (Changed) — f3clogin 完整对齐

对照 C++ `FTLogin/Src/ftlogin/auth/impl/auth_impl.cpp` 和 `auth_cryptor.cpp`
源码，把 Rust 登录流程所有细节逐字段对齐。

#### TGTGT 构造完全重写（`auth_cryptor.cpp:135` CreateNewTgtgt account 版）

- **ver 从 2 改成 8**（账密路径正确版本；ver=2 是 uid 路径，我们不用）
- **payload 布局从 `ver + uid + ...` 改成 `ver + len(account) + account + pwd_md5 + ...`**
- **AES key 派生加 S3 步骤**：`S3 = SHA256(lowercase(hex(S2)) + salt32)`
  salt32 非空时用 S3（32 字节，AES-256）；否则兜底 S2（16 字节，AES-128）
- **rand_key 从 16 字节扩展到 32 字节**（2 个随机 u64 decimal 字符串拼接）
- **所有 u32 字段从大端改成小端**（`OMBinSrz::Srz_BasicType` memcpy host-order，
  Mac/x86/ARM 都是小端，只有带长度前缀的 buf 才走 NetOrder）

#### AES-CBC+MD5 加密库扩展（`futu-net/src/encrypt.rs`）

- 新增 `aes_cbc_md5_encrypt_var` / `aes_cbc_md5_decrypt_var` 支持可变 key 长度
  （16/24/32 字节，对应 AES-128/192/256）
- 对应 C++ `OMCrypt_FTAES_MD5_Encrypt(key, nKeyLen, ...)` 的 nbits 参数
- 用 C++ `UpdateRandKey_DomainTypeAuth_Success` 单测向量验证 AES-128 实现对齐

#### Authority POST body 补齐

- 补 `device_alias` / `device_type` / `os_ver` / `sens_state`（必填，漏一个都会
  返回 error_code=11）
- `post_auth` 函数加 `domain` 参数修掉 `AUTH_SERVER_PROD` 硬编码 bug

#### 设备 SMS 验证流程对齐

- `req_device_code` URL 补 `send_mode=0` / `is_send_no_wait=False`（★首字母大写
  是 C++ 的 Python 风格）
- `verify_device_code` body 补齐 9 字段：`uid` / `verify_mode=0` /
  `device_alias` / `sens_state`

#### salt 响应字段

- 读取 `salt32`（新增 tgtgt 派生必需）
- **移除 `ret_no_uid=true`**（v1.4.3 踩过，让服务器返 uid=0 会让 tgtgt 构造失败）

### 已知问题（Known Issue）

**CN 账号（某 CN 账号）当前仍返回 `error_code=2 "账号密码不匹配"`**。

已排查：
- ✅ payload 结构完全对齐 C++ spec（单测 `tgtgt_payload_structure_aligns_cpp_spec` 验证）
- ✅ pwd_md5 计算正确（`md5("<password>") = <md5>`，单测 golden vector 锁定）
- ✅ AES-128 实现和 C++ 完全一致（golden vector 单测验证）
- ✅ AES-256 round-trip 正确
- ✅ S2/S3 派生按 C++ `CreateS2/CreateS3` 字节对齐

**推测**：AES-256 实现细节（ftaes 库的私有 key schedule）和标准 AES-256 不完全一致，
或者有一个我们还没发现的 payload 字段细微差异。

**下一步**：等能在 C++ OpenD 源码里加 log 打印 `pwd_md5/s2/s3/tgtgt_plain/tgtgt_b64`
之后，在 Rust 侧用固定 rand_key 重现，逐字节对比定位 bug。

### 新增测试

- `tgtgt_payload_structure_aligns_cpp_spec` — TGTGT payload 结构对齐断言
- `aes_cbc_md5_var_roundtrip_128` / `_256` — AES var 版 round-trip
- `aes_cbc_md5_var_128_compat_with_old` — var 版与旧 AES-128 定长版结果完全一致
- `aes_golden_vector_update_rand_key` — 用 C++ 单测的 rand_key vector 验证

### 文档

- CLAUDE.md 大幅扩充"登录 auth 流程陷阱"章节：错误码表、HTTP headers、
  TGTGT 布局、密钥派生、POST body 字段、设备验证流程、调试手法等

## [1.4.5] - 2026-04-16

### 新增 (Added)

**海外账号支持（moomoo）—— user_attribution → auth 域名动态路由**

对齐 C++ `FTLogin/Src/ftlogin/config/impl/user_attr_config.cpp:8-15`
映射表，根据 salt 响应里的 `user_attribution` 字段动态选 auth 域名：

| attribution | 地区 | auth 域名 |
|---|---|---|
| 1 | CN | auth.futunn.com |
| 2 | US | auth.moomoo.com |
| 3 | SG | auth.moomoo.com |
| 4 | AU | auth.moomoo.com |
| 5 | JP | auth.moomoo.com |
| 6 | HK | auth.futunn.com |

**之前所有海外 moomoo 账号都完全无法登录 Rust futu-opend**（加拿大同事
反馈的"moomoo 号不能用"问题的根因）。

#### 实现机制

1. salt 请求默认发 `config.auth_server`（默认 futunn）
2. 响应里 `user_attribution` 映射到不同域名时，切到新域名重发一次 salt
3. 后续 POST `/authority/` 和设备验证都用新域名

每次请求重算域名，对齐 C++ `auth_impl.cpp:147` `GetPlatformAuthDomain`
机制。CN/HK 账号零开销（域名不变）；US/SG/AU/JP 账号多一次 salt 请求。

### 修复 (Fixed)

- **`post_auth` 硬编码 bug**：之前用 `AUTH_SERVER_PROD` 而非 `config.auth_server`，
  导致 `--auth-server` / 环境变量被静默忽略
- 现在 3 个 HTTP 函数（salt / authority / device_verify）全部接受 `domain`
  参数，domain 来源于 attribution 派生

### 变更 (Changed)

**`SavedCredentials` 格式不向后兼容**（无 `serde(default)`）：

新增必填字段 `user_attribution`。旧格式凭据（v1.4.4 及之前保存的
`.futu_credentials_*` 文件）自动作废 → 第一次升级会回落到密码登录路径，
保存新格式凭据后后续正常 remember-login。用户一次性重登无感知。

## [1.4.4] - 2026-04-16

### 修复 (Fixed)

**v1.4.3 回归修复：密码正确但报"请输入验证码"**

v1.4.3 为对齐 C++ 给 salt URL 加了 `ret_no_uid=true` 参数——但这会让服务器
返回 `uid=0`，导致后续 TGTGT 构造时用 uid=0，服务端验证失败并返回
`error_code=11 "请输入验证码"`（captcha 流程）。

去掉 `ret_no_uid=true` 恢复原行为：服务器返回真实 uid，TGTGT 签名通过，
正常进入 `error_code=20`（短信验证设备）或直接登录成功。

### 实测验证

```
某 CN 账号      → error_code=20, phone_no=152****XXXX  ✅ 进设备验证
某 HK 账号   → error_code=20, phone_no=189****XXXX  ✅ 进设备验证
```

v1.4.3 里其他 C++ 对齐修复（Client-Version 1002 / sens_state / device_alias）保留。

## [1.4.3] - 2026-04-16

### 修复 (Fixed)

**真实账号登录路径对齐 C++ f3clogin**

同事用账号 某 HK 账号 登录失败，报 `salt: missing result`。对比 C++
`FTLogin/Src/ftlogin/auth/impl/auth_impl.cpp` 源码，修复 3 处偏差：

1. **`X-Futu-Client-Version` 从 332 升到 900**——服务端对
   `user_attribution ≠ 1`（海外 / HK / 新账号）的用户要求更高版本号，
   旧版会被 `error_code=45 "当前应用版本过低"` 拒绝
2. **salt 接口 URL 加 `ret_no_uid=true` 参数**——与 C++ `GetSalt()`
   实现（auth_impl.cpp:1257）一致
3. **POST `/authority/` 请求体补 `sens_state: "true"` / `device_alias`
   字段**——C++ `Authority()` 主登接口必填

### 验证

`user_attribution=1` (CN) 账号如 某 CN 账号 不受影响（之前能登的继续能登）；
`user_attribution=6` (HK)、2-5 (US/SG/AU/JP) 账号现在 salt 能拿到，
后续 POST auth 流程对齐 C++ 请求体。

## [1.4.2] - 2026-04-16

### 修复 (Fixed)

- **`--login-pwd-md5` 实际生效**：之前参数被解析但从未传给 auth 层（字段
  标记为 `#[expect(dead_code)]`），用户只配 md5 会进 offline 模式。现在
  对齐 C++ 官方行为（`Src/FTGateway/FTGTW_Define_Key.h` 注释："密码密文,
  两个都存在优先使用密文"）：
  - `--login-pwd` 和 `--login-pwd-md5` 是"或"关系，配任一即可登录
  - 两者都给时，**优先用 md5 密文**（与 C++ 一致）
  - `AuthConfig` / `GatewayConfig` 新增 `password_is_md5: bool` 字段；
    预哈希路径跳过明文 md5 计算，验证 md5 必须是 32 位小写 hex
  - 非法 md5（长度/字符错）fail-fast 报错

### 向后兼容

配置文件（TOML / XML / CLI）字段名不变，行为对齐 C++ 官方版。原只传
`--login-pwd` 的用法不受影响。

## [1.4.1] - 2026-04-16

### 改进 (Changed)

- **安装包内容大幅完善**：从"3 个裸二进制 + 8 行 README"升级为完整的
  开箱即用分发包，新增 `examples/` 目录包含 7 个配置 / 部署模板：
  - `FutuOpenD.xml`：网关配置示例（兼容 C++ 格式，放同目录自动加载）
  - `futu-mcp.toml`：MCP server 配置（所有选项带注释）
  - `keys.json`：API Key 授权结构示例
  - `env`：环境变量文件（systemd / Docker）
  - `docker-compose.yml`：网关 + MCP Docker 编排模板
  - `futu-opend.service` / `futu-mcp.service`：systemd 服务单元
- 安装包 `README.md` 重写：包含 macOS Gatekeeper 解法（`xattr -cr`）、
  3 步快速启动、gen-key 用法、文档站链接
- 联系页移除"repo 是私仓"提示框
- 联系页"与富途官方的关系"措辞优化

### 基础设施 (Infrastructure)

- `.github/workflows/release.yml` 打包步骤更新：自动包含 `deploy/examples/`
  全部示例文件 + `deploy/README.dist.md`
- `.github/workflows/docs.yml` 改为 SSH 部署到腾讯云 VPS（原 GitHub Pages）
- VPS 安装 `deploy-release` 命令：CI 编译完自动 SSH 推 tarball
- GitHub Secret `FUTUAPI_DEPLOY_SSH_KEY` 已配置
- docs 容器 `docker run` 补齐 `/releases-host` 和 `/api-host` volume mount

## [1.4.0] - 2026-04-16

### 新增 (Added)

#### MCP HTTP 模式：OAuth2 Protected Resource Metadata（RFC 9728）

- 新端点 `GET /.well-known/oauth-protected-resource`：返回 JSON 描述
  `resource` / `bearer_methods_supported` / `scopes_supported` /
  `resource_name` / `resource_documentation`，让 MCP 客户端能自动发现
  "这个 MCP server 要 Bearer token，可声明哪些 scope"
- `/mcp` 路由的 401/403 响应会自动补 `WWW-Authenticate: Bearer
  resource_metadata="/.well-known/oauth-protected-resource"` 头（通过
  axum `middleware::from_fn`），符合 RFC 9728 §5.1
- 我们**不是**完整 OAuth 授权服务器——key 仍然由运维线下发放 +
  客户端 `Authorization: Bearer <key>` 头；metadata 仅用于让现代 MCP
  client 的自动鉴权发现流程能跑通

> 设计决策：不实现授权端点 / token 端点。Futu 的 API key 是人工配置的
> 长期凭据，没有 interactive consent 流程，也就不需要完整 OAuth server。
> RFC 9728 正是为这种"只想声明鉴权要求"的场景设计的。

#### `trade:unlock` scope 落地（MCP + keyring 跨平台密钥存储）

之前 `trade:unlock` 只是定义在 scope 枚举里、没有对应工具。v1.4 补齐：

- **新 MCP 工具 `futu_unlock_trade`**：要求 `TradeUnlock` scope；入参只有
  `unlock: bool`（默认 `true` 解锁，`false` 锁回）。**明文密码永远不进入
  LLM prompt**——服务端从以下两处自动读：
  1. OS keychain（推荐）：macOS Keychain / Linux DBus Secret Service /
     Windows Credential Manager，通过 `keyring` crate 统一接口
  2. 环境变量 `FUTU_TRADE_PWD`（container / systemd `EnvironmentFile` 场景）
- **新 futucli 子命令**：
  - `futucli set-trade-pwd`：交互式两次输入密码（rpassword 无回显），
    写入 OS keychain
  - `futucli clear-trade-pwd`：从 keychain 删除条目
- `futu-mcp` 和 `futucli` 共用 `futu_auth::KEYRING_SERVICE` /
  `KEYRING_USERNAME_TRADE_PWD` 常量，确保双边读写同一条目
- MD5 在服务端本地计算后再发给 gateway，明文不过网络

#### 核心 WS 推送防御深度：push 时刻再过一遍 scope

虽然 v1.0 的 per-message scope gate 已经在订阅请求（`QotSub` /
`TrdSubAccPush`）阶段挡住了无权 client，**无法订阅就不会收到推送**。但
为防万一（未来新增推送类型忘记加订阅门禁、或 gateway 内部状态被污染），
在 `push_*` 函数分发前也加一道 scope 检查：

- `push_qot` / `push_broadcast` / `push_notify` → 要求 `QotRead`
- `push_trd_acc` → 要求 `AccRead`
- 空 scope 集合（legacy 无 key 客户端）全放行，向后兼容
- 被过滤掉的推送打 `bump_ws_filtered(event_label, key_id)` 指标，
  和现有 REST `/ws` / gRPC `SubscribePush` 过滤计数统一

### 质量 (Quality)

- `trade_pwd` 模块 3 个单元测试用 `OnceLock<Mutex<()>>` 序列化 env 操作，
  避免 cargo test 并行时 `FUTU_TRADE_PWD` 相互覆盖
- `inject_www_authenticate` middleware + OAuth metadata handler 新加 2 个
  `tokio::test`：一个断言 RFC 9728 字段齐全，一个用 `tower::ServiceExt::oneshot`
  验证 401 才注入头、200 不注入

### 依赖 (Dependencies)

- `futu-mcp`：新增 `keyring = "3"`（apple-native / windows-native /
  linux-native-sync-persistent / crypto-rust features）+ `md5`
- `futucli`：新增 `keyring = "3"`（同上 features）
- `futu-mcp` dev-dep：新增 `tower = "0.5"`（middleware 单测用）

## [1.3.0] - 2026-04-15

**瘦身版**：GUI 下线，全平台 CLI-only。无新功能，但让 CI / Docker / 交叉
编译路径更轻。

### 移除 (Removed)

- **`futu-opend-gui` crate 整个下线** —— Slint GUI 登录界面的应用面太窄
  （真正跑 OpenD 的人几乎都是 CLI / systemd / Docker 形态，GUI 主要是早期
  开发阶段的调试入口），继续维护意义不大。所有平台都只走 CLI。

### 变更 (Changed)

- `.github/workflows/ci.yml` + `coverage.yml` 移除
  `libfontconfig1-dev` / `libxkbcommon-dev` apt install（Slint 的原生依赖，
  去掉 GUI 后不再需要）
- README 功能特性 / 快速开始 / 项目结构 三处移除 GUI 相关行
- `cargo build --workspace` 产出 3 个 binary：`futu-opend`（网关）+
  `futu-mcp`（MCP server）+ `futucli`（CLI client）—— 原本 GUI 带来的
  Linux 上 2 个系统库依赖消失，CI 更快、Docker 层更薄，交叉编译目标减少

### 升级

- 旧 `keys.json` / 启动命令 / fork 调用方都不需要改
- 曾经用 `cargo run -p futu-opend-gui` 启动的用户：改成 `futu-opend
  --login-account ... --login-pwd ...`；凭证管理现在完全靠 CLI flag / env /
  systemd `EnvironmentFile`（更安全）

测试 153 → 153（GUI crate 本身没单元测试）。clippy `-D warnings` 干净。

## [1.2.0] - 2026-04-15

**收 v1.1 已知后续**：REST/gRPC handler 层 full `CheckCtx`、futucli `--audit-log`、
`cargo llvm-cov` 接 CI。核心 WS 推送过滤复查后**不需做**（v1.0 per-message
scope gate 已经在订阅请求阶段挡住了无权 client，无法订阅就收不到推送）。
完全向后兼容 v1.1.0。

!!! danger "⚠️ Breaking change（v1.2 引入，后发现文档没标，v1.4.29 补注）"

    `--rest-token <plaintext>`（单密码字符串鉴权）**已被 `--rest-keys-file
    <path>` 替代** —— 从 v1.2 起换到 SHA-256 hash + scope + 限额的 keys.json
    模式。`--rest-token` 完全移除（不是 deprecated，是 remove）。

    **迁移**：用 `futucli gen-key --id <name> --scopes qot:read,acc:read`
    生成 keys.json，然后 `futu-opend --rest-keys-file <path>` 启动。完整
    scope 和限额说明见 [`guide/auth.md`](https://www.futuapi.com/guide/auth/)。

### 新增 (Added)

#### REST/gRPC handler 层 full CheckCtx（细粒度限额）

之前 REST/gRPC 的 trade:real 请求**只在 auth 层挂 rate + hours 全局闸门**，
keys.json 里的 `allowed_markets` / `allowed_symbols` / `max_order_value` /
`max_daily_value` / `allowed_trd_sides` 这些**细粒度限额只在 MCP 生效**。
v1.2 让 REST/gRPC 也享受同一套：

- `futu_auth::RuntimeCounters::check_full_skip_rate(...)` 新方法 —— 跑全套
  `check_and_commit` 但**跳过 rate 计数**（rate 已在 auth 层 commit，handler
  层再 commit 一次会把 rate 窗口算 2 次）。daily 仍会累加（这是真实金额额度）
- REST `routes/trd.rs::place_order`：解析 `Json<Value>` → `trd_place_order::Request`
  C2S 提取 `market` (TrdMarket enum→str) / `symbol` (market.code) /
  `order_value` (qty×price) / `trd_side` (TrdSide enum→str)，调
  `check_full_skip_rate`；失败 → `429 Too Many Requests` + JSON error
- REST `routes/trd.rs::modify_order`：ModifyOrder protobuf 给不出 symbol/qty/value
  （只有 order_id），只能做 market 白名单 + hours；symbol/value/side 留空让
  `check_full_skip_rate` 自动跳过
- gRPC `server.rs::request`：在 trade:real 通用闸门通过后按 proto_id（2202 /
  2205）prost decode body → CheckCtx → `check_full_skip_rate`
- `futu_rest::auth::bearer_auth` middleware verified `Arc<KeyRecord>` 塞
  `req.extensions_mut()`，REST handler 用 `Option<Extension<Arc<KeyRecord>>>`
  extractor 取出（legacy 模式没这个 extension → 跳过 handler 层检查保兼容）
- `futu_rest::adapter::RestState::with_auth(..., counters)` 新构造器 —— 给
  RestState 加 `counters: Arc<RuntimeCounters>` 字段，handler 层调用
- 新增 2 个 limits 测试：`check_full_skip_rate_does_not_double_count_rate`
  + `check_full_skip_rate_still_enforces_market_symbol_side_value_daily`

#### futucli `--audit-log <path>`

对齐 futu-opend / futu-mcp 已有的 `--audit-log` flag —— 让 futucli 触发的
auth / 交易事件（target = `futu_audit`）也能在客户端进程落盘到本地，跟
服务端审计互为校对：

- 新全局 flag `--audit-log <PATH>`（带扩展名 → 单文件 append；不带扩展名
  / 以 `/` 结尾 → 每日滚动 `futu-audit.log`）
- main.rs 用 `tracing-subscriber::Registry` 多层注册：主 fmt layer 写 stderr，
  audit JSONL layer 用 `filter_fn(meta.target() == "futu_audit")` 过滤目标
  事件
- WorkerGuard 持有到 main 返回，避免 tracing-appender 后台线程丢事件

#### `cargo llvm-cov` 接 CI

- 新 `.github/workflows/coverage.yml`：单独 workflow，**只在 main push +
  手动触发**时跑（不挂 PR job 卡 review）
- 用 `taiki-e/install-action@cargo-llvm-cov` 装 cargo-llvm-cov，
  `dtolnay/rust-toolchain@stable` + `llvm-tools-preview`
- `cargo llvm-cov --workspace --tests --lcov --output-path lcov.info` 出
  lcov 格式上传 artifact（保留 14 天）；`--summary-only` 控制台显示总览
- `--ignore-filename-regex 'target/.*|tests/.*'` 排除 build script 生成的
  protobuf 代码和 integration tests 自身

### 调研结论 (Investigated, Not Done)

#### 核心 WS 推送按 client scope 过滤 —— 不做

复查后发现 v1.0 的 per-message scope gate **已间接覆盖**：

- 客户端必须先发 `QOT_SUB`(3001) / `TRD_SUB_ACC_PUSH`(2008) 等订阅请求
  才能收到对应推送
- 这些订阅请求会在 `ws_process_requests` 被 v1.0 加的 scope gate 拦截 ——
  无 acc:read 的 key 订阅 trade 类推送会被直接丢弃（不响应）
- 服务端 `push.rs` 的 `push_notify` / `push_trd_acc` / `push_qot` 是按
  SubscriptionManager 查表后**定向**推送（不是无差别广播）
- 既然客户端**无法登记订阅**，就不会被推送

如果要做"防御深度"（防 handler bug 在推送时泄漏），可在 push 路径加冗余
scope 检查；但 v1.2 这个版本评估认为不必要

### 变更 (Changed)

- `futu_rest::adapter::RestState` 新增 `counters` 字段 + `with_auth` 构造器；
  原 `with_key_store` 内部用 `Arc::new(RuntimeCounters::new())` 占位（保留
  签名不破坏 fork）
- `futu_rest::auth::bearer_auth` middleware 现在会把 verified `Arc<KeyRecord>`
  塞 request extensions，下游 handler 可用 `Extension<Arc<KeyRecord>>` 取
- `futu_grpc::Cargo.toml` 新增 `futu-proto` 依赖（prost decode 下单 body）

### 升级

- 旧 `keys.json` / 启动命令 / fork 调用方都不需要改
- handler 层 full check 是**新增的护栏**，不会让原本能通过的请求被拒（market/
  symbol/side 的 reject 只发生在 keys.json 配了对应白名单的场景）
- handler 层 + auth 层都跑限额 ⇒ rate 不重复计（用 `check_full_skip_rate`），
  但 **daily 会累加** —— 这是符合预期的（daily 才是真实金额额度，无论从
  REST/gRPC/MCP 哪条路径都要计入同一个 key 的当日总额）

## [1.1.0] - 2026-04-15

**v1.0 收口版**：把 v1.0 留下的 3 个"已知后续"做完，再加运维 / CI / 文档
追齐。完全向后兼容 v1.0.0。

### 新增 (Added)

#### MCP HTTP transport：Authorization header → per-call key 自动识别

v1.0 加了 HTTP transport，但 per-call key 还得在 tool args 里塞 `api_key`
字段。v1.1 让 HTTP 模式下 `Authorization: Bearer <token>` header 自动作为
override：

- 3 个交易 handler 加 `req_ctx: RequestContext<RoleServer>` 参数（rmcp 的
  `FromContextPart` 框架原生支持）
- 新 `tools::http_bearer_token(ctx)` helper：从 `ctx.extensions.get::<http::request::Parts>()`
  取 `Authorization: Bearer ...`
- 优先级：**tool args `api_key` > HTTP Bearer header > startup `FUTU_MCP_API_KEY`**
- stdio 模式下 ctx.extensions 没有 Parts，header_token = None，自动回落
- 多 LLM 共享同一 MCP server 时各自带自己的 key，audit / 限额 / scope 各
  记各的

#### gRPC SubscribePush 按 scope 过滤推送

对齐 REST `/ws` v0.9 加的 push filter —— 之前 gRPC 流式推送握手过 `qot:read`
后什么都收得到，现在按 client key 的 scope 过滤：

- 新 `scope_for_event(event_type)`：`trade` → `acc:read`，其他 → `qot:read`
- send loop 里过滤掉 client 不持有的 scope；过滤掉的事件计 metrics counter
  `futu_ws_filtered_pushes_total{required_scope, key_id}`
- legacy 模式（authed=None）给"全 scope"集合让全部放行（向后兼容）

#### REST `/health` 端点

- `GET /health` → 200 OK + body `"ok"`，挂在 bearer_auth middleware 之外
- 故意做得很轻：只验证 axum 还能 schedule 任务返回响应；不查网关 / DB
  （那是 readiness 的活）
- 给 LB / k8s liveness probe 用；Dockerfile 的 HEALTHCHECK 也指向这里

#### Dockerfile + systemd unit

- 仓库根加 `Dockerfile`：多 stage build（rust:1.83 builder → debian:bookworm-slim
  runtime），非 root 用户 `futu:futu`，HEALTHCHECK 走 `/health`，包含
  `futu-opend` / `futu-mcp` / `futucli` 三个 binary
- `deploy/systemd/futu-opend.service` + `futu-mcp.service`：
  - 凭证从 `/etc/futu-opend/env` `EnvironmentFile=` 读，避免 `ps` 暴露
  - 运行用户 `futu:futu`，`NoNewPrivileges` / `ProtectSystem=strict` /
    `ReadWritePaths=/var/log/futu /var/lib/futu` 一系列 systemd 加固
  - `Restart=on-failure`，`LimitNOFILE=65535`

#### 文档

- `README.md` 加 v1.0+ 章节：四条入口护栏 / `--ws-keys-file` / `/metrics`
  + `/health` 端点 / MCP HTTP transport 用法 / Docker + systemd 部署
- `docs/migration-v1.0.md`（覆盖 v0.9 → v1.0 → v1.1 的 fork / 集成方需
  改的 API 变更）：
  - REST/gRPC `start_with_auth` 签名加 `counters` 参数
  - REST `bearer_auth` 的 State 类型从 `Arc<KeyStore>` 改成 `AuthState`
  - 核心 WS `--ws-keys-file` 用法
  - MCP HTTP transport + per-call key 优先级 + JSON 例子

### 修复 (Fixed)

- CI workflow `cargo test` 缺 `--tests` —— 之前 integration tests
  （如 REST 的 `auth_e2e.rs`）实际上不会被 picked up
- 全工程 `cargo fmt --all` 一遍，CI 里 `fmt --check` 终于会过

### 已知后续（v1.2 候选）

- 核心 WS 推送（不是请求）按 scope 过滤 —— 目前 WS 收到的所有 push 都直接
  转发，没看 client scope。建议给 WS key 配 `allowed_markets` 当软限制
- REST/gRPC handler 层跑 full `CheckCtx`：market/symbol/value/side 的细
  粒化检查目前只在 MCP 生效
- `cargo llvm-cov` 接 CI 出覆盖率报告

## [1.0.0] - 2026-04-15

**v1.0 里程碑**：把 v0.9.0 结尾三个"已知后续"一次收口 —— **核心 WS 握手鉴权
+ per-message scope**、**gRPC / REST 的限额护栏打通**、**MCP 支持 HTTP transport**。
至此 REST / gRPC / 核心 WS / MCP 四条入口的鉴权、scope、限额、审计、metrics
全线对齐，且所有限额计数都跑在一套共享 `Arc<RuntimeCounters>` 上。

**完全向后兼容 v0.9.0**：未改 `keys.json` 格式 / protobuf / HTTP 路由；新功能
全是 opt-in CLI flag。

### 新增 (Added)

#### 核心 WS（Futu SDK 用的 binary WebSocket）握手鉴权 + per-message scope

之前核心 WS（`crates/futu-server::ws_listener`）零鉴权，任何人连上去都能
下单。v1.0 把 REST / gRPC 的 scope + 限额模型移植过来：

- `futu_auth::scope_for_proto_id(u32) -> Option<Scope>` —— gRPC 和 WS 共用的
  proto_id → scope 映射（把 `futu-grpc::auth::scope_for_proto` 提到
  futu-auth，gRPC 改成转发一行）
- `ClientConn` 加 `key_id: Option<String>` + `scopes: HashSet<Scope>` 字段；
  TCP listener 填空 = legacy 放行（向后兼容）
- `ws_listener.rs`:
  - `accept_async` → `accept_hdr_async`：握手回调里读 `?token=` 或
    `Authorization: Bearer <token>`，调 `KeyStore::verify` 拿 `KeyRecord`；
    过期 / 缺 `qot:read` 在握手阶段就拒（HTTP 401 / 403 + JSON body）
  - `ws_process_requests` 加 scope gate：按 proto_id 查 needed scope，不匹配
    → 直接丢弃请求 + `futu_auth::audit::reject`；`trade:real` 多跑一次
    `check_and_commit` 挂 rate + hours 闸门
  - limits 走 `KeyStore::get_by_id(key_id)` 取最新快照 —— SIGHUP 重载 keys.json
    后改 scope / 收紧限额立刻对 WS 生效（对齐 v0.8.0 的 MCP 行为）
- 新 `WsServer::with_auth(..., key_store, counters)` 入口；原 `WsServer::new()`
  等价于 `with_auth(None, None)`，保持旧调用方能继续编
- futu-opend：新 CLI flag `--ws-keys-file <path>`；启动时传 `shared_counters`
- `extract_ws_token` + 7 个单测（query / Bearer header / 空串 / 非 Bearer 等）

#### gRPC 限额护栏（之前 v0.7.1 遗漏）

gRPC 在 v0.7-v0.9 只做 scope 检查，完全没跑 `check_and_commit` —— 拿
trade:real 的 key 可以从 gRPC 侧绕过所有限额。

- `FutuGrpcService::with_auth(..., counters)` 新构造器；`request()` 里
  `trade:real` scope 通过后跑 check_and_commit（CheckCtx 留空只挂 rate + hours）
- 限额拒 → `Status::resource_exhausted`（对应 HTTP 429）+ audit reject
- `start_with_auth(..., counters)` 签名新增 counters 参数

#### REST 限额护栏（之前也没跑 check_and_commit）

REST 原先也只有 scope 检查。v1.0 让 REST 和 gRPC 用同一套护栏：

- 新 `futu_rest::auth::AuthState { key_store, counters }` middleware state
- `bearer_auth` 中 `trade:real` scope 通过后跑 check_and_commit，失败返回
  `429 Too Many Requests` + JSON body
- `limits.rs` 市场白名单加"空串跳过"pattern：auth 层不解析 body，`CheckCtx`
  里 market/symbol/value/side 全空，靠 rate + hours 两项做全局闸门；细粒化
  检查留给下游 handler（MCP 已做，REST/gRPC handler 层后续版本）
- 新 e2e 测试 `trade_real_hits_rate_limit_at_auth_layer`：max=2/min 的 key
  第 3 单拿 429 + 错误里含 "rate limit"

#### 共享 `Arc<RuntimeCounters>` wiring

v0.8.0 时 REST / gRPC / MCP 各自新建 `RuntimeCounters` —— 同一把 key 从
不同接口发请求，rate 窗口各看各的。v1.0 把 counters 从 futu-opend main 统
一下发：

- main.rs 创建 `shared_counters = Arc::new(RuntimeCounters::new())`
- REST / gRPC / WS 三条服务启动时都传入这份
- `futu_rest::server::start_with_auth` 和 `futu_grpc::server::start_with_auth`
  签名增加 counters 参数（新增，不破坏旧调用方 —— `build_router` 等便利函数
  默认给 `RuntimeCounters::new()`）
- 结果：同 key 的 rate limit / 日累计跨接口一致生效
- MCP 是独立进程，仍有自己的 counters 实例（如要跨进程聚合，将来用
  Prometheus scrape + 汇总）

#### MCP streamable HTTP transport

之前 MCP 只支持 stdio —— 一个 LLM 客户端启子进程连自己专属的 MCP server。
v1.0 加 HTTP 模式，一个 MCP server 能接多客户端 + 暴露 `/metrics`：

- `rmcp` feature 加 `transport-streamable-http-server`，新增 `axum = "0.8"`
  dev+prod 依赖
- 新 CLI flag `--http-listen <addr>`（支持 `:port` 或 `host:port`），不传
  则 stdio（默认 / 向后兼容）
- `serve_http()`：axum 0.8 router，`/mcp` `nest_service`
  `StreamableHttpService`（`LocalSessionManager::default()` 做 in-memory
  session 管理），`/metrics` 独立挂 Prometheus 文本输出
- FutuServer 现在 `Clone` 实现给 rmcp 的 service factory 用（ServerState
  内 Arc 共享，clone 廉价）
- MCP 启动时也 install 全局 `MetricsRegistry`，audit hook 的 counter bump
  起作用；`/metrics` 端点直接读
- per-call 切 key 仍然走 tool args 的 `api_key` 字段（v0.9.0 加的，与 stdio
  一致）

### 变更 (Changed)

- `futu_rest::auth::bearer_auth` 的 State 类型从 `Arc<KeyStore>` 改为
  `AuthState`（包装 key_store + counters）—— 调用方需要用 `AuthState::new`
  构造
- `futu_grpc::server::start_with_auth` 签名加 `counters` 参数
- `futu_rest::server::start_with_auth` 签名加 `counters` 参数
- `futu_grpc::auth::scope_for_proto` 改成一行 wrapper，真正逻辑移到
  `futu_auth::scope_for_proto_id`
- `ClientConn` 新字段 `key_id` / `scopes`（TCP listener 和老 WS 构造都
  填 None / 空集 = legacy 放行）

### 已知后续

本版本**没做**但有价值的点（用户可以提 issue 催）：

- **MCP HTTP 里 Authorization header → per-call key 自动识别**：
  v1.0 只做传输层切换，per-call key 依然走 tool args `api_key`。要让 HTTP
  header 自动转成 per-call override，每个 trade handler 得加
  `RequestContext<RoleServer>` 参数读 Extensions，19 个 tool 改动面大，
  留给 v1.1 做统一的 rmcp middleware
- **REST/gRPC handler 层的 full CheckCtx**：
  auth 层只做 rate + hours 粗粒度；要让 market/symbol/value/side 也在 REST
  下单路由生效，需要在 `trd::place_order` 里解析 body 后再跑一次
  `check_and_commit`。MCP 已经是这么做的
- **Core WS: InitConnect AES 加密 + scope 联动**：
  握手鉴权和 per-message scope 都基于 HTTP header；InitConnect 之后的 AES
  body 加解密流程未动，和 scope 正交

### 升级

- 旧 `keys.json` 无需改动
- 旧 futu-opend 启动命令无需改动（不加 `--ws-keys-file` 就是 legacy）
- 自己调 `futu_rest::server::start_with_auth` / `futu_grpc::server::start_with_auth`
  的 fork：签名多了一个 `counters: Arc<RuntimeCounters>` 参数，传 `Arc::new(RuntimeCounters::new())` 即可
- 自己调 `futu_rest::auth::bearer_auth` 做测试：包 `AuthState::new(store, counters)`
  当 middleware state

## [0.9.0] - 2026-04-15

本版本三件事一起做：**WS 推送按 scope 过滤** / **Prometheus `/metrics`**
/ **MCP 交易工具 per-call api_key 覆盖**。前两块补观察性和 v0.7.1 推过
的护栏漏网之鱼；第三块让同一个 MCP 进程可以服务多个租户，各自带自己的
key 做限额 / 审计，不用起多个 futu-mcp。

**完全向后兼容 v0.8.0**：未改 keys.json 格式 / CLI flag / protobuf /
HTTP 路由；`/metrics` 路径是新增，`api_key` 字段是可选新增。

### 新增 (Added)

#### WS 推送按 scope 过滤（修 v0.7.1 延的"WS per-message 护栏"）

之前 REST `/ws` 握手 `qot:read` 通过后，客户端就能收到**所有**推送事件
——包括 `trade` 类（账户交易回报）。拿到 `qot:read`-only 的 bot key 能
旁路看到其他账户的成交记录，属于越权泄漏。

- 新 `WsPushScope` enum + `required_scope()`：
  - `Quote` → `qot:read`（行情）
  - `Notify` → `qot:read`（通用通知）
  - `Trade` → `acc:read`（账户交易回报，需账户读权限）
- 每条 `WsPushEvent` 带 `required_scope` 字段（`#[serde(skip)]` 不发给
  客户端，只用于服务端过滤）
- WS 连接握手时把 `KeyRecord.scopes` 传给 send_task，过滤掉 client
  不持有 scope 的事件；legacy 模式（`KeyStore::empty()`）给全 scope
  集合照旧广播
- 过滤掉的推送记一次 counter `futu_ws_filtered_pushes_total`，看得出
  "这个 key 订阅了但 scope 不对"的配置错误
- 核心 WS（`crates/futu-server::ws_listener`，Futu 原 binary WS）未动，
  留给 v1.0 做 auth 握手 bolt-on 时一起收口

#### `/metrics` Prometheus 端点

- 新 `futu_auth::metrics` 模块 + 全局 `OnceLock<Arc<Registry>>`
- 三类 counter：
  - `futu_auth_events_total{iface, outcome, key_id}` —— auth 和交易事件分桶
  - `futu_auth_limit_rejects_total{iface, key_id, reason}` —— 限额拒按
    reason 大类（rate / daily / per_order / market / symbol / side /
    hours / other）
  - `futu_ws_filtered_pushes_total{required_scope, key_id}` —— WS 按
    scope 过滤掉的推送
- `futu_auth::audit::{reject,allow,trade}` 在写 JSONL 日志的同时 bump
  counter，保持日志流和数值面板一致
- `classify_limit_reason(reason)` 把 `limits.rs` 的拒绝文案映射到固定
  的 reason 桶（新增拒绝类型时要同步这里，否则会落到 `"other"`）
- REST `/metrics` 路由挂在 `bearer_auth` middleware **之后** ——
  middleware 对非 `/api/*` 路径全放行，所以 `/metrics` 无需 token
  （运维用 firewall / bind 127.0.0.1 控访问）
- Prometheus text exposition 0.0.4 格式手写，不引入 `prometheus` crate
  依赖（counter 够用，以后真要 histogram/summary 再换）
- futu-opend `main` 启动时 `install()` 全局 registry；futu-mcp 是独立
  进程暂不挂 HTTP，但 audit hook 仍会计数（将来加 transport 就能暴露）
- `all_known_limit_reasons_classified`（文档里称测试锁）由 counter 名
  固定 + `classify_limit_reason` 单测保障

#### MCP 交易工具 per-call API key 覆盖

场景：一个 MCP 进程被多个 LLM agent 共用，每次调用带自己 key，各自
在 audit/限额里分开记。之前只能 `FUTU_MCP_API_KEY` 启动时锁死一把。

- `PlaceOrderReq` / `ModifyOrderReq` / `CancelOrderReq` 新增可选字段
  `api_key: Option<String>`（`#[serde(default, skip_serializing_if =
  "Option::is_none")]`，schemars description 说明用途）
- 读工具不加这个字段 —— 读场景多租户收益小，保持 API 简洁
- `guard::require_trading` 加参数 `override_key: Option<&str>`：
  - `Some("xxx")` 非空 → `key_store.verify(xxx)` 实时拿 record，
    失败**直接拒绝**（不回落到 startup key，否则攻击者塞任何字串都能
    "升级"到 startup key 的 scope）
  - `Some("")` → 当 None 处理
  - `None` → 回落到 startup `state.authed_key`（SIGHUP-aware fresh lookup）
- `emit_trade_outcome` 的 `key_id` 也按 override 解析 —— audit 里记
  "本次下单实际用的哪把 key"，多租户审计分得开
- legacy 模式（未配 keys.json）下 `override_key` 被忽略（"信任所有
  调用方"的配置，覆盖没意义）
- 5 个单测覆盖：无 override / override 有效 / override 无效拒 /
  空串当 None / override scope 不够拒

### 变更 (Changed)

- `guard::require_trading` 签名加一个 `override_key: Option<&str>` 参数
  —— 所有调用点已更新为 `req.api_key.as_deref()`

### 升级

- 无需改 `keys.json`，无需改 CLI flag
- 添加新 API 路由时：`/metrics` 已占掉 `/metrics` 路径名
- Prometheus 抓取：`curl http://<rest-addr>/metrics` 无需 token
- fork 维护者：加新限额类型要同步更新 `futu_auth::metrics::classify_limit_reason()`
  否则会落到 `"other"` 桶

### 已知后续

- 核心 WS（`futu-server::ws_listener`）仍无 auth，留给 v1.0
- MCP 没自己的 `/metrics` endpoint（走 stdio transport），将来加 HTTP
  transport 时一起做
- gRPC 目前不共享 `RuntimeCounters` 也不走 `check_and_commit()`，限额
  只在 REST 和 MCP 生效；gRPC 护栏收口需要单独一批 commit

## [0.8.0] - 2026-04-15

本版本聚焦 **MCP 护栏对齐 REST**：v0.7.1 给 REST 加的 fail-closed scope 注册表、
rate limit 覆盖、trade 审计，在 MCP 侧被一并补齐。MCP 是 LLM agent 最直接的
攻击面，v0.7.1 后它和 REST 护栏力度不一致，这版抹平。

另外改了 MCP 的 key 读取方式，让它对 `SIGHUP` 热重载真正有效：之前改 keys.json
里某个 key 的 scope / 限额 / expires_at 必须重启 futu-mcp，现在 reload 完立刻
生效。REST / gRPC 本来就是如此。

**完全向后兼容 v0.7.1**：没改 keys.json 格式，没改 CLI flag，没改 protobuf / HTTP 路由。

### 新增 (Added)

#### MCP 中央化 tool→scope 注册表（`guard::scope_for_tool`）

对应 REST 的 `scope_for_path()` + `all_known_routes_have_scopes` 测试锁：

- 新 `ToolScope` enum：`Read(Scope)`（只读工具的 scope 静态确定）/ `Trade`
  （交易工具运行时按 `env=real/simulate` 派发到 `TradeReal` / `TradeSimulate`）
- `scope_for_tool(tool: &str) -> Option<ToolScope>` 枚举全部 19 个工具；
  未登记的返回 `None` → handler 直接 reject `"unknown MCP tool"`
- 所有只读 handler 从 `require_scope(tool, Scope::X)` 改为 `require_tool_scope(tool)`，
  scope 决定权集中到注册表，不再散落在 19 个 handler 里
- `all_known_tools_have_scopes` 单元测试 = 备忘锁：新加 `#[tool]` 忘了更注册表
  会挂
- `unknown_tool_fails_closed` 测试：未登记的名字 fail-closed 拒

#### MCP `modify_order` / `cancel_order` 进 rate limiter

之前这俩传 `None` ctx 到 `require_trading()`，**直接跳过全部限额**：

- 后果：拿到 `trade:real` scope 的 key 可以 spray 改单 / 撤单而不触发
  `max_orders_per_minute`。单次下单被挡死的 key 能一分钟刷几百次 cancel。
- 现在传 `CheckCtx { market, symbol: "", order_value: None, trd_side: None }`
  ，让 market 白名单 / 时段 / 速率 照常生效；symbol / 单笔 / 日累计 / side
  这几项在 `limits.rs` 里已改成"空字段 skip"，自动绕过
- `futu_auth::limits` 的 `symbol_whitelist` 检查对齐 `trd_side` 的 None-skip
  pattern：空字符串跳过（对应"改单 / 撤单给不出 symbol"的语义）
- 新增 3 个测试：`symbol_whitelist_skipped_when_ctx_symbol_is_empty` /
  `rate_limit_counts_mutations_with_empty_symbol` / MCP 端覆盖

#### MCP 交易 success/failure 审计（`guard::emit_trade_outcome`）

- `place_order` / `modify_order` / `cancel_order` handler 返回后，解析 JSON：
  含 `error` 字段 → `outcome="failure"` + 错误文案 reason；否则 `"success"`；
  非 JSON → `"unknown"`
- 事件走 `futu_auth::audit::trade()`，字段：`iface=mcp / tool / key_id /
  args_hash / outcome / reason`
- 之前只有 pre-execution 的 `"request"` 事件，审计链路不完整 —— 攻击者通过
  key 的权限下了单，审计里看不到是否真的成交

#### `KeyStore::get_by_id(id)` + MCP SIGHUP-aware

- `KeyStore` 新增 `get_by_id(id) -> Option<Arc<KeyRecord>>`，从当前 ArcSwap
  快照按 id 查 KeyRecord（不做 expiry / machine 校验，调用方自理）
- MCP `guard` 每次请求都通过 `current_authed_key()` 拿最新记录：
  - 之前：启动时 `KeyStore::verify(plaintext)` 把 KeyRecord 快照到
    `ServerState.authed_key`，后面 scope / 限额 / 过期检查全部读这个快照
  - 现在：`state.authed_key` 里的 id 用来每次向 `key_store` 做 `get_by_id`
    fresh lookup，scope / limits / expires_at 取当前文件里最新版
  - 结果：SIGHUP 重载后，改 scope / 收紧限额 / 吊销 key 立刻生效，不用重启
- `remove_key` 把某 id 从 keys.json 删掉后 `get_by_id` 返回 None →
  MCP guard 视为"key revoked"直接拒，audit 写 `reason="key revoked"`
- REST / gRPC 本来就是每请求查 KeyStore，SIGHUP-aware 天然成立；这次只补齐
  MCP 的行为差距
- 新增测试 `get_by_id_reflects_reload`：reload 前看老 scope、reload 后看新 scope、
  remove_key 后 get_by_id 返回 None

### 变更 (Changed)

- MCP tools.rs 的 `self.require_scope(tool, Scope::X)` 调用全部改为
  `self.require_tool_scope(tool)`，scope 不再在 handler 里硬编码

### 修复 (Fixed)

- **MCP 改单 / 撤单绕过 rate limit**（v0.7.1 引入的实际 bypass，上文已述）
- **MCP 吊销 key 后旧进程仍可用**：通过 SIGHUP-aware fresh lookup 消除

### 升级

- 无需改 `keys.json`，无需改 CLI flag
- 如果你维护 fork：有新加 MCP `#[tool]` 的 commit，必须同步更新
  `crates/futu-mcp/src/guard.rs::scope_for_tool()`，否则 `all_known_tools_have_scopes`
  测试会挂（这正是"备忘锁"的目的）

## [0.7.1] - 2026-04-14

本版本围绕 **agent / LLM 场景的生产可用性**：在 v0.7.0 API Key 基础上补齐
审计、速率限制、fail-closed 路由、机器绑定和端到端测试五块，让运维能把
keys.json 拿到 production 真的跑起来。**完全向后兼容 v0.7.0**：旧 keys.json
不需改动就能直接加载（新增字段都是 `Option<T>` + `#[serde(default)]`）。

### 新增 (Added)

#### 速率限制 + 交易方向白名单（per-key）

`futu_auth::Limits` 新增两个可选字段，`KeyRecord` 同步新增，
`futucli gen-key` 透出对应 flag：

- `max_orders_per_minute: Option<u32>`：60s 滑动窗口下单次数上限。
  挡"单笔金额小 + 日累计没超"场景下的 spray-and-pray（例如
  `max_order_value=50` 的 key 一分钟刷几千单）。
  新加 `RuntimeCounters.rates: DashMap<key_id, VecDeque<timestamp>>`，
  check_and_commit 顺序：白名单 → 时间窗 → 单笔 → **速率** → 日累计。
- `allowed_trd_sides: Option<HashSet<String>>`：交易方向白名单。
  典型用法 `--allowed-trd-sides SELL` → 只让平仓 bot 卖；值 `BUY` /
  `SELL` / `SELL_SHORT` / `BUY_BACK`。**改单 / 撤单路径不校验**（CheckCtx.trd_side=None
  时自动跳过），避免误伤运维操作。
- `futucli list-keys` 表格加 `LIMITS` 列（总宽 150），格式 `rate=3/m,sell,ord=50k`

#### REST 路由 fail-closed scope 映射

`scope_for_path()` 从"未知 `/api/*` 回落到 `QotRead`"改成**显式列表 + 未知拒绝**：

- 之前：前缀匹配 → `qot:read`；后果是如果以后加了个写接口 `/api/transfer-money`
  但忘改 auth 这里，它会被静默当成 qot:read 放行
- 现在：三个常量数组（QOT 27 条 / ACC 11 条 / TRADE 3 条）全量枚举，
  不在表中的 `/api/*` 返回 `None`，middleware 回 `404` + `audit reject`
- 新增 `all_known_routes_have_scopes` 测试："备忘锁"：新加路由忘了更 auth.rs 会挂

#### 审计日志 JSONL 输出（`futu-auth::audit` + `--audit-log`）

- 新模块 `futu_auth::audit`：统一的审计事件发射 helper
  - `TARGET = "futu_audit"` 常量，供 `tracing-subscriber` 按 target 过滤
  - `reject(iface, endpoint, key_id, reason)` / `allow(iface, endpoint, key_id, scope)` /
    `trade(iface, tool, key_id, args_hash, outcome, reason)` 三个 helper
  - `open_writer(path)` 启发式：有扩展名 → 单文件 append；目录 / 以 `/` 结尾 / 无扩展名 → 每日滚动 `futu-audit.log`
- **所有接口已统一切换**：gRPC auth / REST auth middleware / WebSocket 握手 / MCP 工具（含下单 trade 事件）
  全部从散落的 `tracing::warn!` 改为 `futu_auth::audit::{reject,allow,trade}`
- 新增 CLI flag：
  - `futu-opend --audit-log <PATH>` —— 写到 JSONL 文件或每日滚动目录
  - `futu-mcp --audit-log <PATH>` —— 同上（MCP 走 stdio transport，常规日志仍在 stderr）
  - 与 `--json-log` 互斥：若都传，`--audit-log` 被忽略并 warn（json-log 已把全部事件写成 JSON）
- 字段固定：`iface` / `endpoint` / `key_id` / `outcome` / `reason` / `args_hash` / `scope` —— 方便 `jq`、DuckDB 后处理
- `tracing-appender` non-blocking writer，`WorkerGuard` 保留到 main 返回防止 flush 丢事件

#### 软机器绑定（`futu-auth::machine`）

- `KeyRecord.allowed_machines: Option<Vec<String>>`：把 key 限定到若干台机器
  - `None`（默认）→ 不启用，任何机器可用（向后兼容 v0.7.0 早期 key）
  - `Some(vec![fp, ...])` → 只允许列出的机器
  - `Some(vec![])` → 冻结（用于临时禁用某 key 而不删）
- 指纹公式：`SHA-256("futu-machine-bind:v1:" || key_id || ":" || raw_machine_id)`
  - key_id 混入 → 同台机器上不同 key 的指纹不同，防横向关联
  - raw_machine_id 来源：Linux `/etc/machine-id`、macOS `IOPlatformUUID`（ioreg）
- `KeyStore::verify()` 在 plaintext 匹配后自动调用 `check_machine()`；
  不过返回 `None` 并走 `tracing::warn` 审计（含 key_id + error）
- `futucli machine-id` / `futucli machine-id --for-key <id>` 打印本机 id / 指纹
- `futucli gen-key --bind-this-machine` + `--bind-machines <fp1,fp2>` 组合使用
- **强度声明**：这是软绑定，攻击者登上机器就能读到 machine-id 伪造指纹；
  能挡住 keys.json 整体复制到别的机器这种意外泄漏；真要强绑定走 TPM/Secure Enclave（未来版本）

#### `futucli bind-key` 就地编辑机器绑定

- 不走 "revoke + regen"（那会换 plaintext，所有客户端得重配），而是原地改 keys.json
- 支持 4 个动作：
  - 追加（默认）：`--this-machine` 或 `--machines fp1,fp2` 加进现有白名单（去重）
  - 替换：`--replace` 配合上面任一，用新指纹覆盖整个白名单
  - 清除：`--clear` 把 `allowed_machines` 置 None（解除绑定，任何机器可用）
  - 冻结：`--freeze` 把 `allowed_machines` 置 `[]`（任何机器都不过，用于临时禁用）
- 三种修改互斥（clippy `conflicts_with_all` 校验），忘记改完 SIGHUP 会有提示
- `store::update_key(path, id, closure)` 新 atomic-rename helper，其他元数据修改也能复用

#### `futucli list-keys` 增加 BOUND 列

- `*` → 未绑定（任何机器可用）
- `FROZEN` → 空列表（冻结中）
- `N machine(s)` → 白名单长度
- v0.7.1 后表格总宽 150，新增 `LIMITS` 列（`rate=/m,sides,ord=`）

#### REST 鉴权端到端集成测试

- 新 `crates/futu-rest/tests/auth_e2e.rs`：用 `tower::ServiceExt::oneshot`
  驱动迷你 axum app + 真 `bearer_auth` middleware，覆盖 8 个场景
  （legacy / 缺 token / 假 token / 错 scope / 对 scope / 未知路径 / 过期 key /
  非 /api 路径）。不依赖 Futu 网关即可验证鉴权链路。

## [0.7.0] - 2026-04-14

本版本引入**API Key 授权系统**作为 agent / LLM / 多租户场景下 `--enable-trading`
两级开关的升级路径。所有现代接口（REST / gRPC / WebSocket / MCP）统一复用
同一份 `keys.json`，`futucli gen-key` 一站式生成。向后完全兼容：不配置 keys
时保持旧行为（REST/gRPC 全开 + warn、MCP 回退 `--enable-trading`）。

### 新增 (Added)

#### API Key 授权系统（新 crate `futu-auth`）

- **5 个 Scope**：`qot:read` / `acc:read` / `trade:simulate` / `trade:real` / `trade:unlock`
- **KeyStore**：keys.json 加载 + SHA-256 hash 常量时间比对 + 过期 + id 去重
- **限额**：单笔金额、日累计（UTC 日滚 Mutex 保护）、市场/品种白名单、
  时间窗口（服务器本地时区、支持跨午夜 `22:00-04:00`）、过期时间

#### 各接口的 Bearer Token 接入

- **`futu-mcp`**：`--keys-file` + `FUTU_MCP_API_KEY` 环境变量；
  每个工具前置 scope 守卫；下单走 scope + 限额 + 审计（args_hash）；
  未配 keys 时回退 `--enable-trading` / `--allow-real-trading` 两级开关
- **`futu-rest`**：`--rest-keys-file` + `Authorization: Bearer` header；
  axum middleware 按路由前缀映射 scope；
  未配 keys 时保持旧行为全开（启动 warn）
- **`futu-grpc`**：`--grpc-keys-file` + `authorization: Bearer` metadata；
  按 proto_id 区间映射 scope（3xxx → qot:read / 2xxx 账户只读 → acc:read /
  2005/2202/2205/2237 → trade:real）；
  `SubscribePush` 流式 RPC 要求 `qot:read`；未配 keys 时全开
- **REST `/ws` WebSocket**：`?token=<plaintext>` 查询参数或 `Authorization: Bearer`
  header；浏览器因不能设自定义 header 优先用 query；握手阶段校验 scope（qot:read）；
  未配 keys 时直接放行

#### SIGHUP 热重载

- REST + gRPC + MCP 三个服务都支持 `kill -HUP <pid>` 重载 keys.json
- 失败保留旧 keys 继续服务，不中断运行

#### `futucli gen-key`

- 生成 32 字节随机 plaintext（hex 64 字符），SHA-256 存盘，atomic rename + 0o600 权限
- 支持 `--scopes` / `--expires Nd/Nh/Nm|RFC3339` / `--allowed-markets` /
  `--allowed-symbols` / `--max-order-value` / `--max-daily-value` /
  `--hours-window` / `--note`
- 明文只打印一次到 stdout，附带 Claude Desktop config 模板

#### 审计

- 所有 scope 命中 / 拒绝都走 `tracing`，字段包括 key_id / tool / 路径 /
  拒绝原因；交易工具额外记录 args_short_hash（不含明文敏感字段）

### 文档

- `docs/migration-v0.7.md`：v0.6 → v0.7 迁移指南（不启用 keys 场景 + scope 模式）
- `plans/deployment-modes.md`：单进程 vs opend+bridged 双形态部署设计备忘
- README / current-status 补充 API Key 使用与向后兼容说明

## [0.6.0] - 2026-04-14

本版本新增两个直接面向终端用户与 LLM 的客户端：**futucli**（命令行 + REPL）
和 **futu-mcp**（Model Context Protocol stdio server）。网关本体协议与语义保持不变。

### 新增 (Added)

#### futucli — 命令行客户端（新 crate `futucli`）
- 单次子命令模式，覆盖行情 + 账户只读 + 交易解锁：
  - 行情：`ping` / `quote` / `snapshot` / `sub` / `kline` / `orderbook` /
    `ticker` / `rt` / `static` / `broker` / `plate-list` / `plate-stocks`
  - 账户：`account` / `funds` / `position` / `order` / `deal`
  - 解锁：`unlock-trade`（支持 `--lock` / `--from-stdin`，
    密码优先级：`--from-stdin` > `FUTU_TRADE_PWD` > tty 无回显输入；
    MD5 本地计算，不过 LLM / MCP）
- 输出格式：`-o table`（默认）/ `-o json`（聚合数组）/ `-o jsonl`（逐行）
- `--gateway` 可用 `FUTU_GATEWAY` 环境变量覆盖
- **交互式 REPL（`futucli repl`）**：
  - 共享一条 FutuClient 长连接，避免每条命令重建 TCP / AES 握手
  - `rustyline` 行编辑 + 历史持久化（`~/.cache/futucli/history`）
  - `ExternalPrinter` 让订阅推送在 prompt 上方打印、不打断输入；
    非 tty 环境（pipe / 重定向）自动降级到 stderr
  - REPL 专属命令：`help` / `exit` / `reconnect` / `subs` / `sub` / `unsub`
  - 其他所有子命令通过共享 `cli::dispatch` 调度，与外层 `futucli` 语义一致

#### futu-mcp — Model Context Protocol server（新 crate `futu-mcp`）
- **stdio transport**（`rmcp::transport::stdio`），直接由 Claude Code /
  Claude Desktop / Cursor 等 MCP 客户端 spawn
- **19 个工具**：
  - 行情只读（11）：`futu_ping` / `futu_get_quote` / `futu_get_snapshot` /
    `futu_get_kline` / `futu_get_orderbook` / `futu_get_ticker` /
    `futu_get_rt` / `futu_get_static_info` / `futu_get_broker` /
    `futu_list_plates` / `futu_plate_stocks`
  - 账户只读（5）：`futu_list_accounts` / `futu_get_funds` /
    `futu_get_positions` / `futu_get_orders` / `futu_get_deals`
  - 交易写（3）：`futu_place_order` / `futu_modify_order` / `futu_cancel_order`
- **两级开关**保护交易写工具：
  - 默认关闭：必须 `--enable-trading` 才注册下单路径
  - `--enable-trading` 单独使用时仅允许 `env=simulate`
  - `--allow-real-trading` 才放通真实账户（启动日志 warn 提醒）
- **密码永不经过 MCP / LLM**：解锁交易必须用 `futucli unlock-trade` 带外执行，
  解锁状态在 gateway 进程级 `TrdCache` 中共享，重启失效
- 所有交易工具每次调用走 `tracing::warn!` 审计日志
- `schemars` 自动从 Rust 请求类型生成 JSON Schema

### 文档
- README 增补客户端工具链章节（futucli / futu-mcp 使用示例 + Claude Desktop 配置）
- 项目结构图添加 `futucli` / `futu-mcp` crate

---

## [0.5.0] - 2026-04-14

首个公开发布版本。在 0.1.x 开发迭代积累的基础上，新增 REST / gRPC / GUI 三大对外接口，
整理项目结构，发布可对外分发的二进制。

### 新增 (Added)

#### REST API（新 crate `futu-rest`）
- **41 个 HTTP 接口**，覆盖系统 3 个 + 行情 24 个 + 交易 14 个
- 通用 `proto_id/JSON` 适配器，复用现有 `RequestRouter`，无需为每个接口重复编码
- CORS 全开放，支持浏览器跨域直连
- **WebSocket 推送 `/ws`**：
  - `tokio::sync::broadcast` 通道分发
  - 三种推送类型：`quote`（行情） / `trade`（交易） / `notify`（广播）
  - JSON 格式：`{type, proto_id, sec_key?, sub_type?, acc_id?, body_b64}`

#### gRPC 服务（新 crate `futu-grpc`）
- 通用 `Request(FutuRequest) returns (FutuResponse)` 单一 RPC
- `SubscribePush` 流式推送，实时接收行情/交易/广播
- 采用 proto_id + raw bytes 模式，避免为 54 个 FTAPI proto 逐一生成 tonic service
- 客户端断开或广播器关闭自动结束 stream
- 虚拟 `conn_id` 从 20_000_000 起（REST 从 10_000_000），便于区分请求来源

#### GUI（新 crate `futu-opend-gui`）
- 基于 **Slint** 的图形化登录与状态界面
- **多语言支持**：英文 / 简体中文 / 繁體中文，运行时切换
- 监听 IP 与 API 端口配置（支持 `0.0.0.0` / `127.0.0.1` / 其他）
- **短信验证码对话框**：新设备绑定流程的 GUI 交互
- 默认字体 `Hiragino Sans GB`（修复中文显示为方块的问题）

#### 推送分发基础设施
- `futu_server::push::ExternalPushSink` trait：外部模块挂载点
- `PushDispatcher` 支持 `Vec<Arc<dyn ExternalPushSink>>` 多接收器并行
- 推送分发统一出口：TCP + WebSocket + gRPC 三路同时投递
- `WsBroadcaster` 与 `GrpcPushBroadcaster` 均实现 `ExternalPushSink`

### 变更 (Changed)

- CLI 参数 `--api-port` 重命名为 `--port`（保留 `--api-port` 作为别名向后兼容）
- 新增 CLI 参数：`--rest-port` / `--grpc-port`
- XML 配置新增字段：`port` / `rest_port` / `grpc_port`，`api_port` 仍被接受
- Protobuf 类型自动派生 `serde::Serialize` / `Deserialize`，供 REST JSON 使用

### 修复 (Fixed)

- 客户端断开时清理连接池和订阅关系（此前残留导致内存缓慢增长）
- 重连后新心跳退出能再次触发重连（修复无限重试链路）
- 股票列表定期同步 + `BasicQot` 推送合并 bit 1/5
- GUI 中文显示为方块（默认字体配置）
- Slint 密码输入框 binding loop（移除多余 `height` 绑定）
- `#[serde(default)]` 意外应用到 enum 导致 90 处编译错误（改用 `message_attribute`）

### 删除 (Removed)

- 项目根目录下的全部 C++ 源码副本：`Src/` / `Doc/` / `OM/` / `Proj/` / `Script/` / `Config/` / `3rd/` / `CHANGES.txt`
- 共约 **2400 个文件、86 万行代码**
- C++ 参考源码迁移至外部路径 `/Users/leaf/ai-lab/o-src/FutuOpenD/`

---

## 0.4.x 及更早（未正式发布）

早期开发迭代未维护详细 changelog，主要完成内容如下：

### 核心协议与网络
- FTAPI TCP 协议完整实现（44 字节帧头、AES-128 ECB、SHA1 明文校验）
- 后端 NN 协议对接（AES-CBC-MD5 加密、序列号匹配、Push/Reply 分发）
- 自动重连（`ArcSwap` 原子替换连接引用，handler 无感知切换）
- 动态 IP 发现（CMD 1321），移除硬编码 region 配置

### 认证
- 账密登录（明文密码 + MD5）
- 设备绑定 + 短信验证码（CLI `stdin` / GUI 对话框二选一）
- RSA 加密 InitConnect 支持
- 心跳重连 + 无限重试

### 行情
- 订阅：`Qot_Sub` → CMD 6211（按市场分组 + ORDER_BOOK/BROKER 独立拆分）
- 推送：CMD 6212 `QuotePush` 解码 → 按 bit 分发 `Qot_Update*`
  - 覆盖 bit：`PRICE` / `ORDER_BOOK` / `TICK` / `TIME_SHARING` / `KLINE_*`
- 所有 `Get*` 接口：`BasicQot` / `KL` / `OrderBook` / `Broker` / `Ticker` / `RT` / `Snapshot` / `StaticInfo` / `PlateSet` / `PlateSecurity` / `Reference` / `OwnerPlate` / `OptionChain` / `Warrant` / `CapitalFlow` / `CapitalDistribution` / `UserSecurity` / `StockFilter` / `IpoList` / `FutureInfo` / `MarketState` / `RequestHistoryKL`
- 行情权限缓存（CMD 6024）
- 股票列表定期同步
- 代码变更缓存（HTTP 下载的 CodeRelation + CodeTemp）

### 交易
- 账户：`GetAccList` / `UnlockTrade` / `SubAccPush`
- 资金持仓：`GetFunds` / `GetPositions` / `GetMaxTrdQtys` / `GetMarginRatio`
- 订单：`PlaceOrder` / `ModifyOrder` / `GetOrders` / `GetOrderFills` / `GetHistoryOrders` / `GetHistoryOrderFills` / `GetOrderFee`
- 交易通知重查（CMD 4716）→ `UpdateOrder` / `UpdateOrderFill` 推送
- 订单更新按 `order_ids` / `order_fill_ids` 精准推送

### 服务端
- `RequestRouter` 请求路由
- `SubscriptionManager` 订阅管理（行情 + 交易账户 + 通知）
- `PushDispatcher` 三种推送模式
- `ClientConn` 客户端连接（AES 加密帧 + keepalive）
- WebSocket 监听器（TCP 协议级别）
- Telnet 管理端口
- `GatewayMetrics` 监控指标（Prometheus 风格）
- 频率限制 + 回放检测

### 系统
- `GetGlobalState` / `GetUserInfo` / `GetDelayStatistics`
- 多语言支持（`chs` / `cht` / `en`）
- 日志分级（`--log-level`）
- Ctrl+C 优雅关闭

---

[Unreleased]: #unreleased
[0.7.0]: #070---2026-04-14
[0.6.0]: #060---2026-04-14
[0.5.0]: #050---2026-04-14
