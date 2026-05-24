# CHANGELOG — ecommerce-product-investigator

> 版本变更记录、验证结果和已知痛点摘要。详细实施步骤见 GitHub Issues。

---

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
