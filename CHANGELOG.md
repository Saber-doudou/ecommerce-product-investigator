# CHANGELOG — ecommerce-product-investigator

> 📦 **本文档面向用户**，记录每个版本的功能变更、修复和已知问题。
> 交付流程与审查记录请查阅 `delivery-summary.md`。历史版本归档见 `references/changelog-archive.md`。

---

## [0.5.7] — 2026-11-06

### 修复（第三轮复审 P3 收口）
- **P3-1 零销量显示**：两处销量列由空值兜底短路改为直传，交由 `format_table` 统一处理 `None`；数字 `0` 不再被吞成空白（0 销量是有意义信号）
- **P3-2 尾注日期**：README 与 docs 的两处尾注统一到 2026-11-06
- **P3-3 错误可观测性**：API 错误日志级别提为 ERROR；CLI 在 stdout 输出与写文件完成后以退出码 2 结束，空结果仍为 0，只读 stdout 的自动化可区分「请求失败」与「没有结果」；补 caplog 断言守护日志不退化；SKILL.md 契约同步写明退出码
- **自检**：J7 扩容为「JSON 契约与错误可观测性」，守护退出码 / 错误标志 / caplog，项数仍 **78**
- **P3-4 口径**：`wc -l` 为 489、`count(NL)+1` 为 490，属叙述口径差，全文以 489 行为准，不单独发版

### 测试
- **148 passed**（用例数不变，1 个既有用例加强为 caplog 断言）

## [0.5.6] — 2026-11-06

### 修复（独立复审 v0.5.5 后的小补丁）
- **N1 新回归**：`scripts/__init__.py` 的版本正则由误写的 `//s*` 修回标准空白匹配，`scripts.__version__` 恢复与 SKILL.md 同步（此前恒为 0.0.0 并伴随假警告）
- **N2 格式回归**：CDP 端口决策表中间的引用行移到表格下方，`PORT_FREE` 不再掉出表格
- **R1 / R2 / R5 文档残留**：README 与 docs 的流程示例改回 API + Web Search 主链（CDP 仅在必要时启用）；归档头的旧版本数声明改为与现状一致；docs 环境变量措辞与 README 对齐
- **R3 空值**：`format_table()` 统一 `None` 到空串，并去掉两处传参前的 `str(None)` 包装，销量列不再显示字符串 `None`
- **R4 JSON 契约**：`--format json` 统一恒为数组，空结果 / API 错误返回 `[]`，错误原因走日志；SKILL.md 增加显式契约声明
- **nit**：删重复断言；`_sanitize_category()` 补 Windows 保留名防护
- **自检扩容**：新增 J5（`__version__` 一致性）、J6（Markdown 表格完整性 + 自测）、J7（JSON 数组契约），75 至 **78 项**

### 测试
- **148 passed**（用例数不变，2 个既有用例断言随契约更新并加强）

## [0.5.5] — 2026-11-05

### 修复（v0.5.4 逐条销账复核后的补漏）
- **P2-1 做实**：`--platform` 的 `choices` 改由 `commission-rates.yaml` 动态生成（v0.5.4 条目曾超前声明，实际仍是硬编码）；YAML 加载失败时不设 choices，由运行时显式报错退出 2
- **P2-7 做实**：清理 `maishou_search.py` 残留的 `import aiohttp`；AST 全仓扫描另清 `monitor_store.py` 的 `os` / `Any` 与 5 个测试文件共 6 处历史未使用导入，全仓归零
- **P2-9 做实**：`format_csv()` 删除仅供测试注入的 `output` 死参数，对应用例改写为「Windows CSV 无隔行空行」回归
- **P2-12 复核**：`requirements-dev.txt` 本就只有 pytest 两项，审查所述「混入 aiohttp/PyYAML」未复现，不改动文件，如实留痕
- **自检扩容**：`check_ecommerce_20261105.py` 新增 J 组 4 项常驻断言守护补漏项，总数 75 项

### 测试
- **148 passed**（用例数不变，1 个用例改写为等价有效断言）

## [0.5.4] — 2026-11-05

### 修复（严格审查收口，共 46 项）
- **P0（5）**：空标题崩溃；佣金率达到 100% 时保本售价误算为 0 元；跨境采集优先级在 6 个文件里 4 种写法；输出模板把佣金税金算进单位硬性成本导致二次扣减；JP/UK 市场对比数字错误
- **P1（21）**：佣金率范围校验与费率来源标记、售价 0 的利润率、跨境 JSON Infinity、费率过期边界、详情接口返回码、.env BOM 与行内注释、品类名路径穿越、BSR 变化描述丢失、429 等待与重试口径、CSV 空行、空值结构、说明书凭据措辞、环境变量必要性、平台数、版本范围声明、未闭合粗体、失效域名
- **P2（20）**：非法 JSON 友好退出、price=None、0 基线、同日增量、字符宽度口径共用、未使用导入清理（部分，见 0.5.5 补漏）、缺失 SKILL.md 的版本告警、pytest 配置去重、compatibility 精确化、平台数、合法 JSON 示例、人类安装命令、python3/taskkill/端口说明、历史表标题等
- **测试质量**：修正 2 个「假通过」断言；新增 18 个边界回归用例，覆盖空值 / BOM / 费率边界 / 非法 JSON / 路径穿越 / 0 基线 / CSV 落盘 / 固定返回结构

### 测试
- 测试数 130 至 **148 passed**

## [0.5.3] — 2026-11-05

### 修复（P0：文档与实现不一致）
- **移除硬编码费率副本**：`scripts/profit_calc.py` 删除 `_DEFAULT_*` 四组内存费率表，费率唯一事实源为 `references/commission-rates.yaml`。文件缺失 / PyYAML 缺失 / 解析失败 / 数据不完整均抛 `CommissionRatesError`，CLI 显式报错并以退出码 2 停止，不再静默降级输出利润
- **未知平台 / 未知市场不再套默认值**：`calc_domestic()` / `calc_crossborder()` 遇未知键抛 `ValueError` 并列出可用值
- **费率过期检测可注入日期**：`check_commission_staleness(today=...)`，消除测试随日历推移失效的时间炸弹
- **命令路径补齐**：安装依赖命令中的残留相对路径改用 `${CODEBUDDY_SKILL_DIR}`
- **文档自洽**：环境变量表不再指向已失效的凭据入口；README 删「代码自动 fallback」过期描述；合规边界收进 `SKILL.md` 单点；docs 说明书修乱码 / 编号跳号 / 过期参数 / 示意数字标注 / 范围符；待优化项 OPT-1 标记已实现
- **安装副本同步**至 0.5.3，与仓库零分叉（含 `docs/` 与 `.gitignore`）

### 测试
- 测试数 125 至 **130 passed**（新增 5 个守卫用例：费率文件缺失、费率错误阻断计算、未知平台、未知市场、过期阈值）

## [0.5.2] — 2026-11-05

### 文档与可用性（不改变任何业务规则）
- 分支合并：master(v0.5.1 代码) 合入 main，远端仅保留 main；保留 main 侧 .gitignore 与 docs 说明书改进
- frontmatter：description 补 Use when 场景与触发词；新增 compatibility 声明运行时依赖
- 命令路径：16 处脚本命令改用 ${CODEBUDDY_SKILL_DIR} 占位符并补全局基准声明，修复非技能目录 CWD 下必失败
- 事实校验锚：新增端点 / 凭据语义 / 端点版本 / 费率 / 限流的可复制核法与解释器自检；api-limits.md 补最后校验日期
- references：按需加载参考补齐 9 件入口（api-limits.md / commission-rates.yaml / changelog-archive.md）
- README：修正过期命令参数、补 --data、删除悬空的「SKILL.md 合规提醒章节」引用；徽章与版本记录对齐 0.5.2 / 125 tests
- 测试：125 passed（未新增用例）

## [0.5.1] — 2026-05-29

### 修复（P2）
- **diff_snapshot 通用字段增删检测**：除 4 个固定字段外，自动检测新增/移除的自定义字段
- **monitor_store 单元测试**：新增 `tests/test_monitor_store.py`，25 个用例覆盖 save/load/diff/sanitize/list/format

### 优化（P3）
- **tax_rate 范围校验**：`calc_crossborder()` 添加税率 0-1 范围校验，非法值抛出 ValueError
- **MARKET_TAX 配置化**：市场税率从 `profit_calc.py` 硬编码迁移到 `commission-rates.yaml` 的 `market_tax` 段
- **价格格式兼容**：`diff_snapshot()` 价格对比兼容 `[100, 200]` 平面列表格式，非预期格式输出 warning
- **maishou_price 集成测试**：新增 5 个 CLI 端到端测试（help/参数解析/格式校验）
- **delivery-summary 精简**：历史版本汇总为表格，约精简 40%

### 测试
- 测试数 95 → 125（+25 monitor_store 单元 + 5 maishou_price 集成）

---

## [0.5.0] — 2026-05-29

### 修复（P1）
- **Session 锁初始化提前**：`_SESSION_LOCK` 改为模块加载时初始化为 `asyncio.Lock()`，消除 `close_session()` 无锁保护竞态窗口
- **佣金率数据外部化**：新增 `references/commission-rates.yaml`，非开发者可直接修改 YAML 文件更新佣金率。代码自动 fallback 到硬编码默认值（v0.5.3 起已移除该回退，见 0.5.3 条目）
- **快速模式编号式升级提示**：快速模式输出末尾追加 1️⃣2️⃣3️⃣4️⃣ 编号选项，Agent 识别编号即可路由升级
- **监测模式数据持久化**：新增 `scripts/monitor_store.py`，支持按品类+日期保存快照、增量对比、自动标注变化。存储路径 `~/.ecom-investigator/monitor/`

### 优化（P2）
- **CSV 空行保护**：`search_products()` CSV 分支添加 `if not rows` 防御
- **利润计算输入校验**：`calc_domestic()`/`calc_crossborder()` 入口校验负值，CLI 层友好报错
- **Emoji 宽度计算修复**：`text_utils.py` `display_width()` 对 Emoji/符号范围硬编码为 2 列
- **敏感度新增保本售价维度**：国内版敏感度分析新增"保本售价"场景，直观展示盈亏平衡点
- **跨境 CDP 默认不启用**：`crossborder-guide.md` Stage 2 调整采集优先级（API → Web Search → CDP🧪），CDP 标注为实验性
- **前置收集智能跳过**：SKILL.md 新增决策表，用户输入包含 URL/平台名/多链接时跳过对应追问
- **CHANGELOG 归档**：历史版本移入 `references/changelog-archive.md`，主文件保留最近若干版本（完整列表见本文件）
- **delivery-summary 职责分离**：CHANGELOG 面向用户、delivery-summary 面向审查流程，各自头部标注范围
- **API 限流文档**：新增 `references/api-limits.md`，记录限流规则、状态码处理策略

### 测试
- **search_products() 单元测试**：新增 7 个用例（CSV/Table/JSON/空结果/API错误/Limit截断）
- **集成测试扩展**：新增 12 个用例（输入校验/新功能验证/监测存储CLI/搜索CLI）
- **并发安全测试**：新增 2 个用例（并发 session 创建/关闭）
- 测试总数 74 → 95（+21），全部通过

---

## [0.4.5] — 2026-05-27

### 修复（P1 — 审查报告 v0.4.4）
- **get_session() docstring 不准确**：文档声称"3 次重试"但实际重试逻辑在 retry_post() 中。更新 docstring 准确描述行为
- **close_session() 缺乏锁同步**：直接操作 _SESSION 全局变量未使用 _SESSION_LOCK，存在竞态条件。添加锁同步逻辑

### 优化（P2 — 审查报告 v0.4.4）
- **pyproject.toml 元数据补充**：添加 authors、license、readme、repository、keywords、classifiers，符合 PEP 621 规范
- **README.md 徽章**：添加 Tests/Python/Version 状态徽章
- **crossborder-guide.md 市场示例**：补充 JP（10%）和 UK（20%）市场利润对比表
- **profit_calc.py 敏感度扩展**：新增税率 ±2pp 敏感度维度
- **CONTRIBUTING.md**：新增贡献指南（开发环境、测试、代码风格、PR 流程）

### 优化（P2）
- **crossborder-guide.md 验证状态说明**：新增跨境引擎验证状态表，标注 CDP 境外站为"未验证"，推荐 API + WebSearch 主力路径（采纳 saberlily 优化报告）
- **test_profit_calc.py 边界测试增强**：新增 5 个边界测试（采购>售价/大数值/100%佣金/采购价为0/跨境售价为0），覆盖极端输入场景（采纳 saberlily 优化报告）

### 测试
- 测试总数 67 → 74（+7），全部通过

---

## [0.4.4] — 2026-05-26

### 修复（P0 — 审查报告 v0.4.3）
- **maishou_common.py logger 未定义**：`_load_dotenv()` 内 `logger.debug()` 引用未定义变量导致 NameError。添加 `import logging` 和 `logger = logging.getLogger(__name__)`

### 修复（P1）
- **calc_crossborder() market 参数未使用**：函数签名声明 `market="US"` 但内部不推断 tax_rate。现在 `tax_rate=None`（默认）时自动从 MARKET_TAX 推断。同时新增 `platform` 参数支持自动推断佣金率（与 calc_domestic 行为统一）

### 优化（P2 — 审查报告 v0.4.3）
- **`_retry_post` → `retry_post`**：去掉下划线前缀，明确跨模块共享语义
- **导入风格统一**：`_display_width` → `display_width`，与 text_utils.py 导出和 maishou_price.py 一致
- **测试冗余 sys.path**：test_profit_calc.py 和 test_text_utils.py 移除手动 sys.path.insert（conftest.py 已统一处理）
- **多余空行**：maishou_common.py PEP 8 规范化
- **pytest 配置**：新增 pytest.ini，配置 `asyncio_mode = strict`，消除弃用警告
- **variations 列表格式**：`]` 移到独立行，便于 diff 和阅读
- **pyproject.toml**：新增项目配置文件，定义元数据、依赖和 pytest 配置

### 架构改进（Arch — 审查报告 v0.4.3）
- **SensitivityVariation dataclass**：替代 6 元素位置元组，字段语义明确，新增维度不易出错
- **推断逻辑统一**：calc_crossborder() 内部统一处理 commission_rate（platform → 佣金率）和 tax_rate（market → 税率）推断，CLI 层不再预解析
- **集成测试**：新增 `tests/integration/test_cli.py`（8 用例），覆盖国内/跨境 CLI 端到端、平台推断、市场税率推断

### 测试
- 测试总数 58 → 67（+9），全部通过（58 单元 + 9 集成）

---

## [0.4.3] — 2026-05-26

### 修复（P0 — 审查报告 v0.4.2）
- **±2pp 佣金敏感度乘数→绝对值**：`_sensitivity()` 新增 `is_absolute` 参数，扣点率/佣金率 ±2pp 场景改用绝对值增量而非乘数。修复非默认佣金率平台（拼多多 0.6%、淘宝 0%）敏感度结果严重偏差的问题

### 修复（P1）
- **`--id required=True`**：maishou_search.py detail 子命令 --id 标记为必填
- **docstring 补充 Args**：calc_domestic() 和 calc_crossborder() 补全参数文档
- **京东佣金率文档一致**：domestic-guide.md 新增代码默认值与自营实际差异的警告
- **`_retry_post()` 日志加 URL**：重试日志记录目标 URL 便于排查

### 优化（P2）
- **`__init__.py` fallback**：版本号解析失败时回退到 "0.0.0"
- **`_load_dotenv()` 改进**：支持 `export KEY=VALUE` 格式；格式错误行输出行号日志
- **delivery-summary.md 层级统一**：三个版本交付记录标题层级一致化
- **Session 锁**：get_session() 加 `asyncio.Lock` 双重检查，防止并发创建泄漏
- **format_output() 下限保护**：敏感度列宽计算加最小宽度保护

### 文档
- **crossborder-guide.md**：DE 市场 VAT 计算公式补充说明
- **domestic-guide.md**：京东自营佣金实际 vs 代码默认值差异警告

### 测试
- **test_maishou_price.py**（+12）：format_csv 4 用例 + search_single_source 5 用例 + search_price 3 用例
- 测试总数 46 → 58，全部通过

---

---

> 📦 v0.4.2 及更早版本的历史记录已归档至 `references/changelog-archive.md`。

## 已知痛点摘要

| # | 痛点 | 状态 |
|---|------|------|
| P0-1 | 京东新页面异步渲染，规格参数无法 snapshot 读取 | ⬜ Route D 降级 |
| P0-2 | browser-use 速度慢成本高 | ⬜ 仅兜底 |
| P0-3 | 验证码拦截 | ⬜ 提示用户手动 |
| P1-1 | 买手 API 不支持得物/闲鱼 | ⬜ CDP 手动搜索 |
| P1-2 | Firefox 不支持 CDP | ⬜ 文档已说明 |

> 完整待解决项和路线图见 GitHub Issues。

---

## 待优化项（来源：saberlily 优化报告 2026-05-27）

| # | 建议 | 优先级 | 状态 |
|---|------|--------|------|
| OPT-1 | 配置文件支持：佣金率、默认市场等可配置化（JSON/YAML） | P1 | ✅ 已实现（v0.5.0，见 `references/commission-rates.yaml`） |
| OPT-2 | 类型注解完善：补充函数参数和返回值类型注解 | P2 | ⬜ 待实现 |
| OPT-3 | 错误处理标准化：统一错误码体系（ErrorCode enum） | P2 | ⬜ 待实现 |

> 已评估但不采纳：缓存机制（skill无状态不适合）、速率控制（已有降级链）、日志系统（过度工程）、代码结构重构（成本高收益低）、API文档（SKILL.md即文档）
