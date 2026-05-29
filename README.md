# ecommerce-product-investigator

![Tests](https://img.shields.io/badge/tests-95%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Version](https://img.shields.io/badge/version-0.5.0-orange)

电商平台商品调研与选品分析工具（**国内电商 + 跨境电商双模式**）。

- **国内版**：通过 CDP 连接用户已登录的浏览器，提取商品参数/规格/价格/评价，生成 AI 购买建议。支持京东、淘宝、拼多多、闲鱼、1688。
- **跨境版**：帮跨境卖家做产品深度调研与选品决策（Amazon/Shopee/TikTok Shop/Temu），支持竞品分析/利润测算/BSR 查询/差评分析。

提供 **4 种工作模式**：快速模式 / 完整调研 / 单点查询 / 监测模式。

---

## 功能特性

| 国内电商 | 跨境电商 |
|:---|:---|
| ✅ 全网比价（买手引擎，支持 9 大平台） | ✅ 选品分析（市场吸引力/竞争格局/利润可行性） |
| ✅ CDP 深度调研（登录态直读商品页） | ✅ 利润测算（FBA 利润链、保本售价计算） |
| ✅ 4 路线参数提取（B > D > A > C） | ✅ BSR 排名趋势分析 |
| ✅ 中差评分析（好评/中评/差评筛选） | ✅ Review 分析（总量/评分分布/差评关键词） |
| ✅ AI 选品分析层（首选/次选/预算之选） | ✅ 监测模式（持续跟踪品类数据变化） |
| ✅ 价格趋势参考（什么值得买/慢慢买） | ✅ 平台差异速查（Amazon/Shopee/TikTok/Temu） |
| ✅ 降级链 + 精度标注（🟢高/🟡中/🟠低/🔴手动） | ✅ 降级链 + 精度标注（同国内版） |

---

## 快速开始

### 国内模式（购买决策）

**场景**：想买一个电脑机箱，对比 5 款。

```
用户：「帮我对比这几款电脑机箱：
https://item.jd.com/100012345678.html
https://item.taobao.com/item.htm?id=123456789」
```

**工作流程**：
1. 前置收集：确认偏好平台（京东）→ 跳过买手搜索，直接 CDP
2. CDP 引擎阶段 1-4：链接解析 → 参数获取（Route D: ZOL）→ 评价获取 → AI 选品分析
3. 输出：商品对比表 + AI 推荐排名 + 购买建议

### 跨境模式（选品决策）

**场景**：想做 Action Figure 品类，深度分析值不值得做。

```
用户：「我想做 Action Figure 这个品类，深度分析一下值不值得做」
```

**工作流程**：
1. 前置收集：确认目标市场（US）、平台（Amazon）、预算（$5000）
2. Stage 2 采集：CDP 抓取 TOP20 竞品 + API 价格 + Search 补充
3. Stage 3 分析：市场吸引力/头部集中度/利润率（18-22%）/风险
4. Stage 4 报告：建议可做但需差异化定位，避开通用款红海

---

## 安装

1. 将本 skill 放到 WorkBuddy 工作空间的 `.workbuddy/skills/` 目录：
   ```
   .workbuddy/skills/ecommerce-product-investigator/
   ├── SKILL.md                      # 技能定义（Agent 入口）
   ├── CHANGELOG.md                  # 最近 3 版本变更记录
   ├── README.md                     # 本文件
   ├── CONTRIBUTING.md               # 贡献指南
   ├── pyproject.toml                # 项目元数据与依赖
   ├── scripts/
   │   ├── maishou_common.py         # 公共模块（session/headers/API/重试）
   │   ├── maishou_search.py         # 国内比价搜索
   │   ├── maishou_price.py          # 跨境采购参考价
   │   ├── profit_calc.py            # 利润计算器（国内+跨境）
   │   ├── text_utils.py             # 中文对齐 & Emoji 宽度工具
   │   ├── monitor_store.py          # 监测模式数据持久化
   │   └── requirements.txt          # 运行时依赖
   ├── references/
   │   ├── domestic-guide.md         # 国内平台参数提取规则
   │   ├── crossborder-guide.md      # 跨境 4 阶段引擎详解
   │   ├── platform-guide.md         # 跨境平台差异速查
   │   ├── output-template.md        # 输出模板（4 种场景）
   │   ├── fallback-guide.md         # 降级链与精度标注
   │   ├── cdp-setup.md              # CDP 浏览器配置指南
   │   ├── api-limits.md             # API 限流规则与状态码处理
   │   ├── commission-rates.yaml     # 佣金率数据（可直接编辑）
   │   └── changelog-archive.md      # 历史版本归档
   └── tests/                        # 95 个测试用例
   ```

2. 安装依赖（如需使用脚本）：
   ```bash
   pip install -r scripts/requirements.txt
   ```

3. 配置环境变量（跨境模式可选）：
   ```bash
   export MAISHOU_API_KEY="your_api_key"
   export MAISHOU_OPENID="your_open_id"
   ```

4. **注册 skill**（WorkBuddy 环境必须）：
   ```bash
   ima_skill_create -d /path/to/.workbuddy/skills/ecommerce-product-investigator
   ```

---

## 脚本说明

### `scripts/maishou_search.py`（国内比价）

基于 `maishou88.com` API，全网比价。

```bash
# 搜索商品（全部平台）
python scripts/maishou_search.py search --source=0 --keyword='电脑机箱'

# 搜索指定平台（source: 1=淘宝 2=京东 3=拼多多 7=抖音 10=1688）
python scripts/maishou_search.py search --source=2 --keyword='电脑机箱'

# 获取商品详情
python scripts/maishou_search.py detail --source=2 --id='100012345678'
```

### `scripts/maishou_price.py`（跨境采购参考）

基于 `appapi.maishou88.com` API，获取国内采购参考价。

```bash
python scripts/maishou_price.py --keyword "Action Figure" --format json --limit 10
```

### `scripts/profit_calc.py`（利润计算器）

国内 + 跨境双模式利润计算，支持敏感度分析和保本售价。

```bash
# 国内利润计算
python scripts/profit_calc.py domestic --purchase 50 --selling 99 --shipping 5 --platform jd

# 跨境利润计算
python scripts/profit_calc.py crossborder --purchase 30 --selling 29.99 --exchange 7.2 --market US --platform amazon
```

### `scripts/monitor_store.py`（监测模式持久化）

按品类 + 日期保存快照，支持增量对比和变化标注。存储路径 `~/.ecom-investigator/monitor/`。

```bash
python scripts/monitor_store.py save --category "action-figure" --data '{"items": [...]}'
python scripts/monitor_store.py diff --category "action-figure"
python scripts/monitor_store.py list
```

---

## 参考文档

| 文件 | 用途 | 何时读取 |
|:---|:---|:---|
| `references/domestic-guide.md` | 国内平台参数提取规则（京东/淘宝/拼多多/1688/闲鱼） | 国内模式参数提取时 |
| `references/crossborder-guide.md` | 跨境 4 阶段引擎、单点查询、监测模式详解 | 跨境模式深度调研时 |
| `references/platform-guide.md` | 跨境平台差异速查（Amazon/Shopee/TikTok Shop/Temu） | 跨境报告输出前 |
| `references/output-template.md` | 输出模板（快速扫描/深度报告/单点查询/监测报告） | 输出报告时 |
| `references/fallback-guide.md` | 降级链（API→Web Search→CDP🧪→手动）+ 精度标注 | 数据采集出错时 |
| `references/cdp-setup.md` | CDP 浏览器自动化配置指南 | 需要连接本地浏览器时 |
| `references/api-limits.md` | API 限流规则、状态码处理策略 | 调用频率受限时 |
| `references/commission-rates.yaml` | 各平台佣金率数据（可直接编辑，代码自动 fallback） | 需要更新佣金率时 |
| `references/changelog-archive.md` | v0.4.3 之前的历史版本记录 | 查阅旧版本变更时 |

---

## 利润计算公式

### 国内版

```
利润 = 售价 - (采购价 + 运费 + 平台扣点)
```

### 跨境版

```
单位硬性成本 = 采购价 + 头程运费 + FBA费 + 采购价×汇率浮动备用金
保本售价 = 单位硬性成本 ÷ (1 - 平台佣金率 - 税率)
利润 = 售价 - 单位硬性成本 - 售价×(平台佣金率 + 税率)
```

⚠️ **关键纠正**：平台佣金和税金都是**基于售价**扣除，不是基于成本。用成本算佣金会导致定价偏低、实际亏钱。

---

## 合规提醒

### ✅ 可以做

- 采集**公开可见**的商品名称、价格、参数
- 通过官方 API 获取授权范围内的数据
- 自己店铺的数据自由分析
- 控制频率、遵守 robots.txt

### ❌ 不要做

- 绕过验证码/登录墙抓取**非公开数据**
- 高频批量爬取导致**平台服务器压力**
- 抓取其他商家**后台运营数据**
- 将采集数据**转售或做未授权营销**

> 💡 详见 SKILL.md「合规提醒」章节。

---

## 版本记录

| 版本 | 日期 | 核心变更 |
|:---:|:---|:---|
| **0.5.0** | 2026-05-29 | Session 锁竞态修复、佣金率外部化(YAML)、监测模式持久化(monitor_store.py)、快速模式编号升级提示、API 限流文档；测试 74→95 |
| **0.4.5** | 2026-05-27 | Session 锁同步、pyproject.toml PEP 621、README 徽章、CONTRIBUTING 贡献指南、JP/UK 市场示例；测试 67→74 |
| **0.4.4** | 2026-05-26 | logger NameError 修复、跨境 tax/commission 自动推断、SensitivityVariation dataclass、pytest.ini、集成测试；测试 58→67 |
| **0.4.2** | 2026-05-25 | 提取 retry_post() 公共函数、敏感度列宽动态计算、conftest.py 统一路径；测试 33→46 |
| **0.4.1** | 2026-05-25 | 佣金敏感度 ±2pp、跨境最坏场景命名修正、DE 市场 VAT 示例 |
| **0.4.0** | 2026-05-25 | 字段映射修复、提取 text_utils.py 消除重复代码、33 个单元测试；print→logging |
| **0.3.5** | 2026-05-24 | 架构重构：search_api() 公共函数、敏感度参数化、.env 自动加载、市场自动税率 |
| **0.3.0** | 2026-05-21 | SKILL.md 精简、CDP 文件合并、crossborder-guide 拆出 |
| **beta0** | 2026-05-18 | 初始版本：CDP 浏览器连接、买手 API 比价、四路线数据提取 |

> 完整变更记录见 [CHANGELOG.md](CHANGELOG.md)，历史版本归档见 [changelog-archive.md](references/changelog-archive.md)。

---

## 引擎验证状态

| 引擎 | 状态 | 说明 |
|:---|:---|:---|
| 买手 API（国内比价） | ✅ 已验证 | 淘宝/京东/拼多多/抖音/1688 全平台可用 |
| CDP（国内深度调研） | ✅ 已验证 | 登录态直读京东/淘宝商品页 |
| API + Web Search（跨境） | ✅ 已验证 | 主力数据路径 |
| CDP（跨境境外站） | 🧪 实验性 | Amazon/Shopee 等境外站访问未充分验证，降级为备选 |

> 详见 `references/crossborder-guide.md` 验证状态表。

---

## 许可证

MIT License

---

*Last updated: 2026-05-29 (v0.5.0)*
