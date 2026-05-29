# CHANGELOG — ecommerce-product-investigator

> 📦 **本文档面向用户**，记录每个版本的功能变更、修复和已知问题。
> 交付流程与审查记录请查阅 `delivery-summary.md`。历史版本归档见 `references/changelog-archive.md`。

---

## [0.5.0] — 2026-05-29

### 修复（P1）
- **Session 锁初始化提前**：`_SESSION_LOCK` 改为模块加载时初始化为 `asyncio.Lock()`，消除 `close_session()` 无锁保护竞态窗口
- **佣金率数据外部化**：新增 `references/commission-rates.yaml`，非开发者可直接修改 YAML 文件更新佣金率。代码自动 fallback 到硬编码默认值
- **快速模式编号式升级提示**：快速模式输出末尾追加 1️⃣2️⃣3️⃣4️⃣ 编号选项，Agent 识别编号即可路由升级
- **监测模式数据持久化**：新增 `scripts/monitor_store.py`，支持按品类+日期保存快照、增量对比、自动标注变化。存储路径 `~/.ecom-investigator/monitor/`

### 优化（P2）
- **CSV 空行保护**：`search_products()` CSV 分支添加 `if not rows` 防御
- **利润计算输入校验**：`calc_domestic()`/`calc_crossborder()` 入口校验负值，CLI 层友好报错
- **Emoji 宽度计算修复**：`text_utils.py` `display_width()` 对 Emoji/符号范围硬编码为 2 列
- **敏感度新增保本售价维度**：国内版敏感度分析新增"保本售价"场景，直观展示盈亏平衡点
- **跨境 CDP 默认不启用**：`crossborder-guide.md` Stage 2 调整采集优先级（API → Web Search → CDP🧪），CDP 标注为实验性
- **前置收集智能跳过**：SKILL.md 新增决策表，用户输入包含 URL/平台名/多链接时跳过对应追问
- **CHANGELOG 归档**：历史版本移入 `references/changelog-archive.md`，主文件保留最近 3 版本
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
| OPT-1 | 配置文件支持：佣金率、默认市场等可配置化（JSON/YAML） | P1 | ⬜ 待实现 |
| OPT-2 | 类型注解完善：补充函数参数和返回值类型注解 | P2 | ⬜ 待实现 |
| OPT-3 | 错误处理标准化：统一错误码体系（ErrorCode enum） | P2 | ⬜ 待实现 |

> 已评估但不采纳：缓存机制（skill无状态不适合）、速率控制（已有降级链）、日志系统（过度工程）、代码结构重构（成本高收益低）、API文档（SKILL.md即文档）
