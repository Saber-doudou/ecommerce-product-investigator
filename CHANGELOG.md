# CHANGELOG — ecommerce-product-investigator

> 版本变更记录、验证结果和已知痛点摘要。详细实施步骤见 GitHub Issues。

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

## [0.4.2] — 2026-05-25

### 修复（P1 — 审查报告 v0.4.0）
- **提取 _retry_post()**：maishou_common.py 新增通用 POST 重试函数，search_api() 和 detail() 均复用，消除 20+ 行重复重试代码

### 优化（P2）
- **敏感度列宽动态计算**：profit_calc.py format_output() 根据实际内容 display_width 动态计算列宽，长 CJK 场景名不再被截断
- **conftest.py**：统一 tests/ sys.path 设置，新增测试无需重复写 import 路径
- **requirements-dev.txt**：pytest + pytest-asyncio 开发依赖

### 测试
- **test_maishou_common.py**（+7）：format_table 空/单行/CJK/多列测试 + check_env 测试
- **test_maishou_search.py**（+6）：detail() 全成功/API失败/非致命降级/字段提取/YAML/JSON 格式
- 测试总数 33 → 46，全部通过

---

## [0.4.1] — 2026-05-25

### 修复（P0 — 审查报告 v0.4.0）
- **profit_calc.py 佣金敏感度**：国内版新增扣点率 ±2pp 场景，跨境版新增佣金率 ±2pp 场景
- **跨境最坏场景命名**："汇率 -5%" → "人民币升值5%"，与 variations 命名一致，消除歧义

### 修复（P1）
- **_display_width 导入规范**：maishou_price.py 直接从 text_utils 导入 display_width，不再跨模块导入下划线前缀符号
- **SKILL.md 补文档**：maishou_search.py 用法示例补充 --output 参数

### 优化（P2）
- **crossborder-guide.md**：US 示例后补充 DE 市场（19% VAT）对比示例，展示 VAT 对利润的巨大影响
- **delivery-summary.md**：修正版本号残留文字（v0.3.6 → v0.4.1）

### 测试
- test_profit_calc.py 同步更新最坏场景命名断言
- 全部 33 个测试通过

---

## [0.4.0] — 2026-05-25

### 修复（P0 — 审查报告 v0.3.5）
- **maishou_price.py 字段映射**：price→actualPrice/originalPrice, sales→monthSales, shop→shopName，修复价格列为空的 Bug
- **crossborder-guide.md 利润示例**：补汇率浮动备用金 $0.21，与代码逻辑一致
- **_fmt_table CJK 宽度**：len()→_display_width()，中文商品名表格不再错位

### 修复（P1）
- **profit_calc.py 敏感度行 CJK 对齐**：{extra:<40}→_pad_str_local
- **提取 text_utils.py**：消除 maishou_common/profit_calc 间 35 行重复代码
- **maishou_search.py func 参数**：删除未使用的 func=None，main() 过滤 kwargs
- **delivery-summary.md**：更新到 v0.4.0
- **CHANGELOG _EnvProxy**：0.3.4 条目加"已在 0.3.5 移除"注记

### 优化（P2）
- **单元测试**：新增 33 个用例（test_profit_calc.py + test_text_utils.py），pytest 全通过
- **print→logging**：全部脚本警告统一走 logging 模块
- **maishou_search.py --output**：搜索结果支持文件输出
- **佣金率过期提醒**：COMMISSION_REF_DATE 超 6 个月自动 warn
- **SKILL.md frontmatter**：description 精简（~200→~100 字符）

## [0.3.5] — 2026-05-24

### 架构重构
- **search_api() 公共函数**：`maishou_common.py` 新增统一搜索 API，`maishou_search.py` 和 `maishou_price.py` 改为调用公共函数，消除参数不一致
- **profit_calc.py 敏感度分析参数化**：提取 `_sensitivity()` 和 `_worst_case()` 通用函数，代码量减少 ~60%，新增维度只需一行配置
- **清理模块级别变量**：删除 `INVITE_CODE`/`OPENID`/`HEADERS_APP`/`_EnvProxy`/`_warn_deprecated`，所有调用方改为函数动态获取

### 新增功能
- **.env 自动加载**：`maishou_common.py` 自动读取项目根目录 `.env` 文件（手动解析，无额外依赖）
- **跨境版按市场自动推断税率**：`--market` 参数指定 US/DE/JP/UK 时自动设置对应 VAT 税率（0%/19%/10%/20%）
- **最坏场景综合敏感度**：国内版（售价 -10% + 采购价 +10%）和跨境版（售价 -10% + 汇率 -5%）
- **search_api() 内置重试**：统一 2 次重试 + 3 秒延迟，消除两个脚本各自实现
- **敏感度分析 extra 显示**：汇率/采购价变动场景自动附带采购价(USD)换算

### 修复
- **profit_calc.py 表格中文对齐**：使用 CJK 宽度感知的 `_pad_str_local` 替代 `{k:<16}`，输出不再错位
- **PEP 723 清理**：移除 `maishou_search.py`/`maishou_price.py` 中 `argparse` 标准库依赖声明
- **--keyword 改为 required=True**：防止遗漏参数时静默搜索空关键词
- **format_table 截断精度**：剩余宽度不足时正确处理 `…`（U+2026）占位
- **移除未使用的 import**：`maishou_price.py` 移除 `OPENID`

### 文档
- **CHANGELOG 补充**：0.3.4 条目
- **README 版本记录**：补 0.3.4
- **__init__.py 自动版本同步**：从 SKILL.md 动态读取版本号
- **domestic-guide.md**：补充国内平台税率说明（含跨境进口场景）
- **SOURCE_MAP**：标注 9 号平台保留未使用
- **敏感度场景命名统一**：`变量 +幅度` 格式（如 "售价 +10%"、"汇率 +5%（人民币贬值）"）

## [0.3.4] — 2026-05-24

### 修复（P0）
- **环境变量 import 时固化**：`maishou_common.py` 的 `INVITE_CODE`/`OPENID`/`HEADERS_APP` 改为函数动态获取，支持运行时 `.env` 加载。通过 `_EnvProxy` 代理保持向后兼容
  > 注：`_EnvProxy` 已在 0.3.5 中移除。
- **search API 请求格式统一**：`maishou_search.py` 从 `data={}`(Form) 改为 `json={}`，与 `maishou_price.py` 一致
- **API 响应结构兼容**：两个脚本对 search 接口响应添加双向解析 fallback（`data.list` / `data` 数组）

### 修复（P1）
- **format_table 中文对齐**：使用 `unicodedata.east_asian_width` 计算 CJK 字符显示宽度
- **跨境版采购价敏感度**：`profit_calc.py` `calc_crossborder()` 添加采购价 ±10% 敏感度分析
- **detail() pop 改 get**：不修改原始数据
- **detail() 失败返回统一**：返回错误字符串而非不可序列化的列表

### 优化（P2）
- **佣金率添加参考日期**：`COMMISSION_REF_DATE = "2026-05"`
- **添加 .env.example**：列出所有必需环境变量
- **SKILL.md 添加依赖说明**：`pip install -r scripts/requirements.txt`
- **domestic-guide.md 日期修正**："2025年后" → "2025年起（截至2026年5月）"

## [0.3.3] — 2026-05-23

### 文档修正
- **CHANGELOG 结构重组**：将 0.3.2 条目下两批修复分别归入 0.3.1 和 0.3.2

---

## [0.3.1] — 2026-05-22

### 修复（P0）
- **SESSION 全局变量 BUG**：`maishou_search.py` 的 `async with ... as SESSION` 创建局部变量导致全局 SESSION 为 None，改为显式赋值 + `try/finally` 关闭
- **search() 返回值统一**：空结果时返回统一错误格式（JSON 模式返回 `{"error": msg}`，其他返回 `❌ msg`）
- **INVITE_CODE 校验**：`maishou_search.py` 的 `main()` 中添加 `MAISHOU_API_KEY` 环境变量校验

### 修复（P1）
- **API 错误日志**：`maishou_price.py` 的 `search_single_source` 在 code != 200 时打印错误信息
- **运费敏感度分析**：`profit_calc.py` 国内版敏感度分析添加运费 ±20% 场景
- **--limit 参数**：`maishou_search.py` 添加 `--limit` 参数，与 `maishou_price.py` 一致

### 优化（P2）
- **公共模块提取**：新建 `maishou_common.py`，统一 session 管理、headers、API 端点、环境变量校验
- **两个脚本重构**：`maishou_search.py` 和 `maishou_price.py` 改为导入 `maishou_common`，消除重复代码
- **SKILL.md 补充**：添加环境变量说明、agent-browser 工具说明、`--limit` 使用示例
- **requirements.txt**：补充 browser-use 可选依赖注释

## [0.3.2] — 2026-05-22

### 修复（P0）
- **环境变量名统一**：脚本 `MAISHOU_INVITE_CODE` → `MAISHOU_API_KEY`，与文档对齐
- **detail() 错误处理**：`getTargetUrl` 请求添加 try/except 保护
- **detail() 认证 header**：`goods/detail` 和 `getTargetUrl` 请求添加 openid/version header
- **汇率浮动备用金**：`profit_calc.py` 跨境版公式补回 `exchange_buffer` 项，默认 3%

### 修复（P1）
- **SKILL.md**：快速模式输出表格格式修正
- **output-template.md**：补充模板3（监测报告）和模板4（单点查询）
- **cdp-setup.md**：补充 macOS/Linux 浏览器检测和启动命令
- **platform-guide.md**：删除重复采购价层级表，改为引用 crossborder-guide.md
- **maishou_price.py**：添加 OPENID 启动校验和请求重试逻辑
- **README**：更新过时信息（目录树/待验证事项/日期）
- **LICENSE**：添加 MIT LICENSE 文件

### 优化（P2）
- **maishou_price.py**：移除内部重复 `import json`
- **SKILL.md**：frontmatter 补充触发词（产品调研/市场调研/FBA利润等 10 个）
- **crossborder-guide.md**：补充确认门话术示例
- **profit_calc.py**：跨境版添加 `--platform` 快捷参数（amazon/shopee/tiktok/temu）
- **maishou_price.py**：综合搜索改为 `asyncio.gather` 并发查询

---

## [0.3.0] — 2026-05-21

### 变更
- **SKILL.md 精简**：955 行 → 214 行（Tier1/Tier2/Tier3 渐进式加载）
- **合并 CDP 文件**：`cdp-reference.md` 合并入 `cdp-setup.md`，删除重复文件
- **新建 crossborder-guide.md**：跨境 4 阶段引擎、单点查询、监测模式从 SKILL.md 拆分
- **frontmatter 规范化**：version 改为语义化 `0.3.0`，description 精简
- **域名修正**：删除 `openapi.maishou.com` 过时引用，统一为 `appapi.maishou88.com`

### 修复
- **maishou_search.py 6 项修复**：enumerate 替代 walrus、添加超时/重试/OPENID 校验/--format 支持
- **maishou_price.py source 映射**：1688=10（原错误为 4），去掉不支持的闲鱼，修正 sources 列表
- **统一 source 编号**：SKILL.md + 两个脚本 source 编号一致

### 新增
- `scripts/requirements.txt`：aiohttp>=3.9, PyYAML>=6.0

---

## [beta2] — 2026-05-20

### 新增
- 跨境模式（Amazon/Shopee/TikTok Shop/Temu）4 阶段引擎
- 平台自动路由、监测模式、输出结构化模板
- 降级链体系（API→CDP→Web Search→手动）+ 精度标注
- 利润计算公式纠正（佣金/税金基于售价）
- domestic-guide.md、platform-guide.md、output-template.md、fallback-guide.md、cdp-setup.md

### 验证
- ✅ `appapi.maishou88.com` 返回 HTTP 200
- ❌ `openapi.maishou.com` HTTP 000（域名无效，已修正）
- ❌ Amazon 503 / Shopee 连接失败（被墙，降级到 Web Search）

---

## [beta1] — 2026-05-19

### 新增
- P0 AI 选品分析层（首选/次选/预算之选）、P2 快速模式、合规提醒、browser-use 兜底

## [beta0] — 2026-05-18

### 核心功能
- CDP 浏览器连接、买手 API 全网比价、四路线数据提取（B>D>A>C）

---

## 已知痛点摘要

| # | 痛点 | 状态 |
|---|------|------|
| P0-1 | 京东新页面异步渲染，规格参数无法 snapshot 读取 | ⬜ Route D 降级 |
| P0-2 | browser-use 速度慢成本高 | ⬜ 仅兜底 |
| P0-3 | 验证码拦截 | ⬜ 提示用户手动 |
| P1-1 | 买手 API 不支持得物/闲鱼 | ⬜ CDP 手动搜索 |
| P1-2 | Firefox 不支持 CDP | ⬜ 文档已说明 |

> 完整待解决项和路线图见 GitHub Issues。
