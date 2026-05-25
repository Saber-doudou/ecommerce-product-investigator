---
name: ecommerce-product-investigator
version: 0.4.0
description: 电商选品调研（国内+跨境双模式）。支持京东/淘宝/拼多多/1688/Amazon/Shopee/TikTok Shop/Temu。快速模式/完整调研/单点查询/监测模式。
agent_created: true
---

# ecommerce-product-investigator

电商选品调研工具，**双模式自动路由**：根据用户输入自动判断国内/跨境电商，无需手动切换。

**内置双引擎**：
1. **全网比价（买手引擎）** — 调 API 快速扫描淘宝/京东/拼多多/抖音/快手/1688
2. **深度调研（CDP 引擎）** — 登录态直读商品详情页，获取完整规格参数和用户评价

---

## 平台路由（自动判断）

| 用户意图信号 | 路由目标 | 判断依据 |
|:---|:---|:---|
| 京东/淘宝/拼多多/1688/闲鱼 + 产品词 | **国内模式** | 平台域名或中文平台名 |
| Amazon/ASIN/Shopee/TikTok Shop/跨境/FBA | **跨境模式** | 平台域名或跨境关键词 |
| 直接丢链接 | **根据域名自动判断** | jd.com/taobao.com → 国内；amazon.com → 跨境 |
| 模糊（如"帮我看这个品"） | **追问目标市场和平台** | 无法判断时主动澄清 |

---

## 工作模式总览

| 用户意图 | 模式 | 说明 |
|:---|:---|:---|
| 丢链接或只有 1-2 个商品 | **快速模式** | 国内版：直接分析链接；跨境版：快速扫描产品基本面 |
| 做购买决策或深度选品 | **完整调研模式** | 国内版：买手+CDP 双引擎；跨境版：4 阶段深度分析 |
| 只算利润或查单项数据 | **单点查询** | 利润测算 / BSR 查询 / 竞品比价 |
| 持续跟踪品类数据变化 | **监测模式** | 增量报告，标注变化 |

---

## 快速模式（用户丢链接即分析）

**触发**：用户直接发来商品 URL，或只有 1-2 个商品需快速决策。

### 国内版流程

```
用户发来链接 → 识别平台 → 优先买手 API 获取基础数据 → WebFetch 补充 → 轻量版输出
```

> 💡 买手 API 或 WebFetch 能拿到足够信息就不启动 CDP。30 秒内出结果。用户看完说"帮我对比其他平台"时自动升级到完整模式。

### 跨境版流程

```
用户提供关键词/ASIN → maishou_price.py（采购成本）+ Web Search（竞品价格/Review） → 1 页纸摘要
```

### 输出格式（轻量版）

```markdown
## 快速分析：<商品名>
| 字段 | 值 |
|------|-----|
| 平台 | XX |
| 价格 | ¥XXX |
| 关键参数 | XXX、XXX |
| 好评率 | XX%（X条） |
| 数据来源 | 买手API / WebFetch / 商品页 |

### AI 简评
- 优势/注意/适合人群
### 💡 建议：[推荐/可考虑/不推荐] — 理由
```

---

## 完整调研 — 国内版

**前置收集**（省 Token）：先问用户「① 有没有商品 URL？② 平时习惯在哪个平台购物？」

| 用户回复 | 处理 |
|:---:|:---|
| 有 URL | 跳过买手搜索，直接 CDP |
| 无 URL + 有偏好平台 | 买手 API 先搜该平台 |
| 无 URL + 无偏好 | source=0 全平台搜索 |

### 买手引擎：全网快速比价

```bash
python scripts/maishou_search.py search --source=<0-10> --keyword='<商品名>'
# source: 0=全部 1=淘宝 2=京东 3=拼多多 4=苏宁 5=唯品会 6=考拉 7=抖音 8=快手 10=1688
```

买手 API 失败 → 直接降级到 CDP 引擎手动搜索，不阻塞流程。

### CDP 引擎：深度调研

> 详细操作见 `references/domestic-guide.md` 和 `references/cdp-setup.md`

**前置（合并为一步）**：端口预检 → 启动浏览器（如需要）→ 登录验证

```bash
# 端口预检（9222 已被占用则直接复用）
curl -s http://localhost:9222/json > /dev/null 2>&1 && echo "PORT_IN_USE" || echo "PORT_FREE"
```

**核心 4 阶段**：
1. **链接解析**：有 URL 直接导航，无 URL 则平台搜索
2. **参数获取**：Route B（登录页直读）→ Route D（ZOL 等第三方站）→ Route A（API）→ Route C（多模态图片）→ browser-use 兜底
   > ⚠️ 京东新页面规格参数为异步渲染，直接走 Route D（ZOL），不要在 Route B 上浪费 token
3. **评价获取**：快速摘要模式（默认）或完整深度模式（用户要求时）
4. **AI 选品分析**：综合排名（首选/次选/预算之选）+ 避坑提示 + 性价比分析

---

## 完整调研 — 跨境版

> 详细操作见 `references/crossborder-guide.md` 和 `references/platform-guide.md`

**4 阶段引擎**：
1. **前置收集**：产品关键词/ASIN + 目标市场（默认 US）+ 目标平台（默认 Amazon）
2. **数据采集**：API（maishou_price.py）→ CDP → Web Search，采集竞品价格/Review/BSR/利润链
3. **深度分析**：市场吸引力 + 竞争格局 + 利润可行性 + 风险因素，含确认门
4. **报告生成**：按 `references/output-template.md` 输出，明确建议（做/不做/需验证）

### 采购价参考

```bash
python scripts/maishou_price.py "关键词" --format json
# --source: 0=综合 1=淘宝 2=京东 3=拼多多 10=1688
```

> ⚠️ 买手价不是工厂出厂价，利润测算时用买手价 × 0.8 作为采购成本估算。

---

## 单点查询

用户只想算利润或查单项数据时，不走完整流程：

| 场景 | 操作 |
|:---|:---|
| 利润测算 | 给定采购价+售价，计算利润链 |
| BSR 查询 | 给定 ASIN 查排名 |
| 竞品比价 | 给定关键词查 TOP10 价格 |

---

## 监测模式

对已确认关注的品类做持续跟踪，每次对比上次数据标注变化。重点关注：新竞品、价格波动、Review 增速。

---

## 利润计算公式

### 国内版
```
利润 = 售价 - (采购价 + 运费 + 平台扣点)
```

```bash
# 手动指定扣点率
python scripts/profit_calc.py domestic --purchase-price 80 --selling-price 159 --shipping 8 --commission-rate 0.05

# 快捷用法（自动匹配平台扣点率）
python scripts/profit_calc.py domestic --purchase-price 80 --selling-price 159 --shipping 8 --platform jd
```

### 跨境版
```
单位硬性成本 = 采购价 + 头程运费 + FBA费 + 采购价×汇率浮动备用金
保本售价 = 单位硬性成本 ÷ (1 - 平台佣金率 - 税率)
利润 = 售价 - 单位硬性成本 - 售价×(平台佣金率 + 税率)
```

```bash
# 手动指定佣金率
python scripts/profit_calc.py crossborder --purchase-price-cny 80 --exchange-rate 7.2 --selling-price-usd 29.99 --shipping-usd 3.5 --fba-fee 4.2 --commission-rate 0.15

# 快捷用法（自动匹配平台佣金率）
python scripts/profit_calc.py crossborder --purchase-price-cny 80 --exchange-rate 7.2 --selling-price-usd 29.99 --shipping-usd 3.5 --fba-fee 4.2 --platform amazon --market US
```

⚠️ 平台佣金和税金均**基于售价**扣除，不是基于成本。用成本算佣金会导致定价偏低。

---

## 铁律（5 条）

1. **CDP 引擎必须先提示用户登录** — 不可跳过，未登录数据不完整
2. **买手引擎是加速器不是必选项** — 失败了不影响最终结果，CDP 能兜底
3. **降级不阻塞流程** — 同一方案失败 ≤2 次即降级，宁可用 80% 数据出报告
4. **缺失字段标注"未检索到"** — 绝不猜测填充，每个字段标注数据来源和精度
5. **跨境利润计算** — 佣金和税金基于售价，使用前务必确认公式正确性

---

## 环境变量

> 💡 首次使用前需安装依赖：`pip install -r scripts/requirements.txt`

| 变量名 | 必要性 | 说明 |
|:---|:---|:---|
| `MAISHOU_API_KEY` | 必须 | 买手 88 API 邀请码，从 maishou88.com 获取 |
| `MAISHOU_OPENID` | 必须 | 买手 88 用户 OpenID，从 maishou88.com 获取 |

> 💡 设置方式：`export MAISHOU_API_KEY="your_key"` 或写入 `.env` 文件。可参考 `.env.example` 模板。

### 注册 skill（WorkBuddy 环境必须）

将 skill 目录放到 `.workbuddy/skills/` 后，必须执行以下命令使变更生效：

```bash
ima_skill_create -d /path/to/.workbuddy/skills/ecommerce-product-investigator
```

> ⚠️ 修改任何 skill 文件后都需要重新执行此命令，否则变更不会生效。

## agent-browser 工具

本 skill 大量使用 `agent-browser --cdp 9222` 命令，这是 **WorkBuddy 环境内置的 CLI 工具**，用于通过 CDP 协议操作浏览器。非 WorkBuddy 环境可使用 `playwright`/`puppeteer` 替代。

---

## 内置脚本

### `scripts/maishou_search.py`（国内比价）

基于买手 88 API（`appapi.maishou88.com` ✅ 已验证）。

```bash
python scripts/maishou_search.py search --source=0 --keyword='<商品名>'
python scripts/maishou_search.py search --source=2 --keyword='<商品名>' --limit 10 --format json
python scripts/maishou_search.py detail --source=2 --id='<goodsId>'
```

### `scripts/maishou_price.py`（跨境采购参考）

```bash
python scripts/maishou_price.py "关键词" --format json
python scripts/maishou_price.py "关键词" --limit 10
```

环境变量：`MAISHOU_API_KEY`（必须）、`MAISHOU_OPENID`（必须）

---

## 按需加载参考

以下文档不在 SKILL.md 中，需要时用 Read 读取：

| 何时读取 | 文件 |
|:---|:---|
| 需要连接本地浏览器采集数据 | `references/cdp-setup.md` |
| 国内平台参数提取规则、Route B/D/A/C 详解 | `references/domestic-guide.md` |
| 跨境 4 阶段引擎、单点查询、监测模式详解 | `references/crossborder-guide.md` |
| 数据采集出错、需要降级方案 | `references/fallback-guide.md` |
| 需要按模板格式输出报告 | `references/output-template.md` |
| 涉及跨境平台规则和差异 | `references/platform-guide.md` |
| 项目说明、合规提醒、快速开始 | `README.md` |
