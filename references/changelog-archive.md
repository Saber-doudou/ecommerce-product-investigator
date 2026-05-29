# CHANGELOG 历史归档

> v0.4.3 之前的历史版本记录，主 CHANGELOG.md 仅保留最近 3 个版本。

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

---

## [0.3.5] — 2026-05-24

### 架构重构
- **search_api() 公共函数**：`maishou_common.py` 新增统一搜索 API
- **profit_calc.py 敏感度分析参数化**：提取 `_sensitivity()` 和 `_worst_case()` 通用函数
- **清理模块级别变量**：删除 `_EnvProxy` 等，改为函数动态获取

### 新增功能
- **.env 自动加载**、**跨境版按市场推断税率**、**最坏场景综合敏感度**、**search_api() 内置重试**

### 修复
- profit_calc.py 表格中文对齐、PEP 723 清理、--keyword required=True、format_table 截断精度

---

## [0.3.4] — 2026-05-24

### 修复（P0）
- **环境变量 import 时固化**：改为函数动态获取
- **search API 请求格式统一**：Form → JSON
- **API 响应结构兼容**：双向解析 fallback

---

## [0.3.3] — 2026-05-23

### 文档修正
- CHANGELOG 结构重组

---

## [0.3.2] — 2026-05-22

### 修复（P0）
- 环境变量名统一、detail() 错误处理/认证 header、汇率浮动备用金

### 优化（P1/P2）
- 快速模式输出格式修正、output-template 补模板、cdp-setup 补命令、platform-guide 去重复、maishou_price 加校验和重试、LICENSE 文件

---

## [0.3.1] — 2026-05-22

### 修复（P0/P1）
- SESSION 全局变量 BUG、search() 返回值统一、INVITE_CODE 校验、API 错误日志、运费敏感度、--limit 参数

### 优化（P2）
- 公共模块 maishou_common.py 提取、双脚本重构

---

## [0.3.0] — 2026-05-21

- **SKILL.md 精简** 955→214 行、合并 CDP 文件、新建 crossborder-guide.md、frontmatter 规范化、域名修正
- maishou_search.py 6 项修复、maishou_price.py source 映射修正

---

## [beta2] — 2026-05-20

- 跨境模式 4 阶段引擎、平台自动路由、监测模式、降级链体系、利润公式纠正

## [beta1] — 2026-05-19

- P0 AI 选品分析层、P2 快速模式、browser-use 兜底

## [beta0] — 2026-05-18

- CDP 浏览器连接、买手 API 全网比价、四路线数据提取
