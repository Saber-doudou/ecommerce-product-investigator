# ecommerce-product-investigator 交付总结

> 面向审查与交付流程。用户版变更记录见 `CHANGELOG.md`。

---

## v0.5.6 独立复审小补丁（2026-11-06）

独立复审确认 v0.5.5 修复主体成立，但查出 1 个新回归、1 个格式回归、5 项残留与 1 项复审方误报。本轮收掉 N1 / N2 / R1 至 R5，另清 2 个 nit；R4 采用「JSON 恒为数组 + 错误走日志」而非仅注明差异。版本升 0.5.6 保证一号一 tree，自检扩容至 78 项。复审报告见 `技能治理-20261030/ecommerce-product-investigator-v0.5.5复审报告-20261106.md`，销账明细见结算报告 §14。

## v0.5.5 严格审查逐条销账补漏（2026-11-05）

v0.5.4 发布后按 46 项清单逐条机械复核：43 项直接通过、3 项为我方核对断言写窄（复核为已修）、3 项确属漏修（P2-1 / P2-7 / P2-9）、1 项审查结论未复现（P2-12）。补修 3 项、订正 v0.5.4 的两处超前声明、全仓未使用导入清零。升 0.5.5 以保证一个版本号只对应一份 tree。**148 passed**，自检扩容至 75 项全绿，双副本零分叉。逐条销账见结算报告 §13。

## v0.5.4 严格审查收口（2026-11-05）

外部严格审查查出 46 项问题（P0 5 / P1 21 / P2 20）。逐条复现核实后分四批修复：代码侧堵崩溃与错数、统一规则口径、补健壮性与 18 个边界用例、清文档矛盾。**148 passed**，仓库与安装副本零分叉，自检脚本同步扩容。审查报告见 `技能治理-20261030/ecommerce-product-investigator-严格审查报告-20261105.md`，修复明细见同目录结算报告 §13。

## v0.5.3 收口自检与代码闭环（2026-11-05）

按「全部做完 + 自检」指令收口 v0.5.2 全部残留：代码侧移除硬编码费率副本与静默降级，补 5 个守卫用例（**130 passed**）；文档侧消除自相矛盾并统一 0.5.3；安装副本同步零分叉。穷尽核对清单与自检结果见本次交付的收口自检报告。远端发布走 Git Data API 通道（git 通道当日不可达）。

## v0.5.2 文档治理与分支合并（2026-11-05）

按 darwin-skill 流程执行：基线 73.1（full_test）→ 终版见优化结算报告。本轮只改文档与版本控制层，铁律 5 条 / 利润公式 / references 规则内容 / 顶层结构 / 代码实现一律未动。远端只保留 main，回滚点为 backup-premerge-main-20261105 与 backup-premerge-master-20261105 两个 tag。pytest 125 passed。

## v0.5.1 审查报告残余优化

基于 Saber_lily 审查报告 v0.5.0 | 2026-05-29

### TL;DR

审查报告 v0.5.0 **7/7 条残余建议全部实施**（2 P2 + 5 P3）。新增 1 个文件、修改 4 个文件。测试数 95→125。

### 交付概览

| 维度 | 数值 |
|:---|:---|
| **P2 修复** | 2/2 ✅ |
| **P3 优化** | 5/5 ✅ |
| **新增文件** | 1 个 |
| **修改文件** | 4 个 |
| **单元测试** | 125 个全部通过（+30） |

### 文件变更清单

| 文件 | 变更 | 说明 |
|:---|:---:|:---|
| `scripts/monitor_store.py` | 🔧 | P2-1 通用字段增删检测 + P3-5 价格格式兼容 + warning |
| `scripts/profit_calc.py` | 🔧 | P3-3 tax_rate 0-1 范围校验 + P3-4 MARKET_TAX 从 YAML 加载 |
| `references/commission-rates.yaml` | 🔧 | P3-4 新增 market_tax 段（US/DE/JP/UK） |
| `tests/test_monitor_store.py` | ➕ | P2-2 25 个单元测试（读写/对比/安全/格式化） |
| `tests/integration/test_cli.py` | 🔧 | P3-6 maishou_price CLI 5 个集成测试 |
| `delivery-summary.md` | 🔧 | P3-7 精简，历史版本汇总为表格 |

### 审查报告 v0.5.0 最终状态

| 优先级 | 总数 | 已采纳 |
|:---:|:---:|:---:|
| P2 | 2 | 2 ✅ |
| P3 | 5 | 5 ✅ |

---

## v0.5.0 优化报告全量实施

基于 Saber_lily 优化建议报告 v0.4.5 | 2026-05-29

### TL;DR

优化报告 v0.4.5 **15/19 条建议已采纳**（4 P1 + 11 P2）。新增 5 个文件、修改 10 个文件。测试数 74→95。

### 交付概览

| 维度 | 数值 |
|:---|:---|
| **P1 修复** | 4/4 ✅ |
| **P2 优化** | 11/12 ✅ |
| **P3 推迟** | 2 项（SKILL.md 分层 / 远期功能） |
| **新增文件** | 5 个 |
| **修改文件** | 10 个 |
| **单元测试** | 95 个全部通过（+21） |

### 文件变更清单

| 文件 | 说明 |
|:---|:---|
| `scripts/maishou_common.py` | P1-3.1 Session 锁初始化提前 + 并发安全 |
| `scripts/profit_calc.py` | P1-3.2 YAML 佣金率加载 + P2-3.4 输入校验 + P2-3.6 保本售价维度 |
| `scripts/text_utils.py` | P2-3.5 Emoji 宽度硬编码修复 |
| `scripts/maishou_search.py` | P2-3.3 CSV 空行保护 |
| `scripts/monitor_store.py` | ➕ P1-4.2 监测模式数据持久化 |
| `references/commission-rates.yaml` | ➕ P1-3.2 佣金率外部化配置文件 |
| `references/api-limits.md` | ➕ P2-5.3 API 限流文档 |
| `references/changelog-archive.md` | ➕ P2-5.1 CHANGELOG 历史归档 |
| `references/crossborder-guide.md` | P2-4.3 跨境 CDP 默认不启用 |
| `SKILL.md` | P1-4.1 快速模式升级提示 + P1-4.2 监测存储文档 + P2-4.4 智能跳过规则 |
| `CHANGELOG.md` | P2-5.1 归档精简 + v0.5.0 条目 |
| `delivery-summary.md` | P2-5.2 职责标注 + v0.5.0 增量记录 |
| `tests/test_maishou_search.py` | P2-6.1 search_products() 7 个测试 |
| `tests/integration/test_cli.py` | P2-6.2 集成测试扩展 12 用例 |
| `tests/test_maishou_common.py` | P2-6.3 并发安全 2 个测试 |

### 优化报告 v0.4.5 最终状态

| 优先级 | 总数 | 已采纳 | 推迟 |
|:---:|:---:|:---:|:---:|
| P1 | 4 | 4 ✅ | 0 |
| P2 | 12 | 11 ✅ | 0 |
| P3 | 2 | 0 | 2 ⏸️ |

---

## v0.4.5 增量修复

基于 Saber_lily 审查报告 v0.4.4 + 优化建议报告 + 自查 | 2026-05-27

### TL;DR

审查报告 v0.4.4 全部建议已采纳（2 P1 + 5 P2），优化报告 2/12 采纳，自查修复 3 处。测试 67→74。

### 文件变更

| 文件 | 说明 |
|:---|:---|
| `scripts/maishou_common.py` | P1-1 docstring + P1-2 close_session 锁同步 |
| `pyproject.toml` | P2-1 元数据补充 |
| `README.md` | P2-2 徽章 + 测试数 68→74 |
| `references/crossborder-guide.md` | P2-3 JP/UK 市场 + 跨境 CDP 验证状态表 |
| `scripts/profit_calc.py` | P2-4 税率 ±2pp 敏感度 |
| `CONTRIBUTING.md` | ➕ P2-5 贡献指南 |
| `tests/test_profit_calc.py` | 自查 5 个边界条件测试 |
| `SKILL.md` | 自查 快速模式模板补字段 |

---

## 历史版本汇总（v0.4.0 起，节选）

| 版本 | 日期 | 审查基线 | 修复 | 测试数 | 关键变更 |
|:---|:---|:---|:---:|:---:|:---|
| v0.4.4 | 05-26 | v0.4.3 | 12 项（P0x1 P1x2 P2x7 Archx3） | 67 | logger 修复、SensitivityVariation dataclass、集成测试框架 |
| v0.4.2 | 05-25 | v0.4.0 延后 | 5 项（P1x1 P2x4） | 46 | _retry_post 提取、detail() 测试、敏感度列宽动态计算 |
| v0.4.1 | 05-25 | v0.4.0 | 6 项（P0x2 P1x2 P2x2） | 33 | 佣金敏感度修正、最坏场景命名、DE VAT 示例 |
| v0.4.0 | 05-25 | v0.3.5 | 14 项（P0x3 P1x5 P2x6） | 33 | text_utils 消除重复、CJK 对齐、logging 规范化 |
