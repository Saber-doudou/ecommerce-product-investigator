# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
profit_calc.py - 电商利润计算器（国内版 + 跨境版）

使用方法:
    # 国内版
    python profit_calc.py domestic --purchase-price 80 --selling-price 159 --shipping 8 --commission-rate 0.05

    # 跨境版
    python profit_calc.py crossborder --purchase-price-cny 80 --exchange-rate 7.2 --selling-price-usd 29.99 --shipping-usd 3.5 --fba-fee 4.2 --commission-rate 0.15 --exchange-buffer 0.03

    # JSON 输出
    python profit_calc.py domestic --purchase-price 80 --selling-price 159 --format json
"""

import argparse
import json
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from text_utils import display_width as _display_width, pad_str as _pad_str_local


# 国内平台佣金参考（截至 2026-05，请以平台官方最新费率为准）
DOMESTIC_COMMISSION = {
    "jd": 0.05,      # 京东 POP 约 3-8%
    "tmall": 0.05,   # 天猫约 2-5%
    "taobao": 0.00,  # 淘宝基础无佣金
    "pdd": 0.006,    # 拼多多 0.6% 支付手续费
    "1688": 0.03,    # 1688 约 2-5%
}
COMMISSION_REF_DATE = "2026-05"
_COMMISSION_STALENESS_MONTHS = 6


def check_commission_staleness() -> list[str]:
    """检查佣金率是否过期，返回警告列表"""
    warnings = []
    try:
        ref = datetime.strptime(COMMISSION_REF_DATE, "%Y-%m")
        now = datetime.now()
        months = (now.year - ref.year) * 12 + (now.month - ref.month)
        if months > _COMMISSION_STALENESS_MONTHS:
            warnings.append(
                f"⚠️ 佣金率参考日期为 {COMMISSION_REF_DATE}（已过 {months} 个月），"
                f"请确认 DOMESTIC_COMMISSION / CROSSBORDER_COMMISSION 仍为最新费率"
            )
    except ValueError:
        pass
    return warnings

# 跨境平台佣金参考（截至 2026-05，请以平台官方最新费率为准）
CROSSBORDER_COMMISSION = {
    "amazon": 0.15,
    "shopee": 0.06,   # 5% + 1% payment fee
    "tiktok": 0.06,   # 5% + 1% payment fee
    "temu": 0.05,     # 补贴期
}

# 按市场自动推断税率（不指定 --tax-rate 时生效）
MARKET_TAX = {"US": 0.0, "DE": 0.19, "JP": 0.10, "UK": 0.20}


# ── 敏感度分析工具 ──

def _sensitivity(calc_fn, base_kwargs: dict, variations: list[tuple]) -> dict:
    """
    通用敏感度分析。

    Args:
        calc_fn: 计算函数 (**kwargs) -> (profit: float, rate: float)
        base_kwargs: 基准参数字典
        variations: [(场景名, 变动参数名, 值, 显示字段名, 额外显示[, is_absolute]), ...]
                    - 值: 默认为乘数（如 1.10 表示 +10%）
                    - is_absolute (可选 bool): True 时使用绝对值替换, 而非乘法
                    - 额外显示 为 dict 或 None

    Returns:
        {场景名: {显示字段: 值, "利润": float, "利润率": str}}
    """
    results = {}
    for var in variations:
        name = var[0]
        param = var[1]
        value = var[2]
        display_field = var[3]
        extra = var[4] if len(var) > 4 else None
        is_absolute = var[5] if len(var) > 5 else False

        kw = dict(base_kwargs)
        kw[param] = value if is_absolute else kw[param] * value
        profit, rate = calc_fn(**kw)
        entry = {"利润": round(profit, 2), "利润率": f"{rate:.1f}%"}
        entry[display_field] = round(kw[param], 2)
        if extra:
            entry.update(extra)
        results[name] = entry
    return results


def _worst_case(calc_fn, base_kwargs: dict, scenarios: list[dict]) -> dict:
    """
    最坏场景综合敏感度：同时调整多个参数。

    Args:
        calc_fn: 计算函数
        base_kwargs: 基准参数字典
        scenarios: [{场景名: str, params: {参数: 乘数}, display: {显示字段: 值}}]

    Returns:
        {场景名: {利润, 利润率, ...}}
    """
    results = {}
    for s in scenarios:
        kw = dict(base_kwargs)
        for param, mult in s["params"].items():
            kw[param] = kw[param] * mult
        profit, rate = calc_fn(**kw)
        entry = {"利润": round(profit, 2), "利润率": f"{rate:.1f}%"}
        entry.update(s.get("display", {}))
        results[s["name"]] = entry
    return results


# ── 国内版 ──

def calc_domestic(purchase_price, selling_price, shipping=0, commission_rate=None, platform=None):
    """国内版利润计算。

    Args:
        purchase_price: 采购价（元）
        selling_price: 售价（元）
        shipping: 运费（元），默认 0
        commission_rate: 佣金率（小数，如 0.05=5%），优先于 platform
        platform: 平台标识（jd/tmall/taobao/pdd/1688），自动推断佣金率

    Returns:
        dict: 包含利润、利润率、敏感度分析等字段
    """
    if commission_rate is None and platform:
        commission_rate = DOMESTIC_COMMISSION.get(platform.lower(), 0.05)
    elif commission_rate is None:
        commission_rate = 0.05

    commission = selling_price * commission_rate
    total_cost = purchase_price + shipping + commission
    profit = selling_price - total_cost
    profit_rate = profit / selling_price * 100 if selling_price > 0 else 0

    def _calc(pp, sp, sh, cr):
        comm = sp * cr
        total = pp + sh + comm
        p = sp - total
        r = p / sp * 100 if sp > 0 else 0
        return p, r

    base = {"pp": purchase_price, "sp": selling_price, "sh": shipping, "cr": commission_rate}
    variations = [
        ("售价 +10%", "sp", 1.10, "售价", None),
        ("当前",     "sp", 1.00, "售价", None),
        ("售价 -10%", "sp", 0.90, "售价", None),
        ("运费 +20%", "sh", 1.20, "运费", None),
        ("运费 -20%", "sh", 0.80, "运费", None),
        ("采购价 +10%", "pp", 1.10, "采购价", None),
        ("采购价 -10%", "pp", 0.90, "采购价", None),
        ("扣点率 +2pp", "cr", commission_rate + 0.02, "扣点率", {"扣点率%": f"{(commission_rate + 0.02)*100:.1f}%"}, True),
        ("扣点率 -2pp", "cr", max(0, commission_rate - 0.02), "扣点率", {"扣点率%": f"{max(0, commission_rate - 0.02)*100:.1f}%"}, True),    ]

    sensitivity = _sensitivity(_calc, base, variations)

    # 最坏场景：售价 -10% + 采购价 +10%
    worst = _worst_case(_calc, base, [
        {"name": "最坏场景（售价 -10% + 采购价 +10%）",
         "params": {"sp": 0.90, "pp": 1.10},
         "display": {"售价": round(selling_price * 0.90, 2), "采购价": round(purchase_price * 1.10, 2)}},
    ])

    return {
        "模式": "国内",
        "采购价": purchase_price,
        "运费": shipping,
        "平台扣点率": f"{commission_rate*100:.1f}%",
        "平台扣点": round(commission, 2),
        "总成本": round(total_cost, 2),
        "售价": selling_price,
        "利润": round(profit, 2),
        "利润率": f"{profit_rate:.1f}%",
        "敏感度分析": {**sensitivity, **worst},
    }


# ── 跨境版 ──

def calc_crossborder(
    purchase_price_cny, exchange_rate, selling_price_usd,
    shipping_usd=0, fba_fee=0, commission_rate=0.15, tax_rate=0, market="US",
    exchange_buffer=0.03,
):
    """跨境版利润计算。

    Args:
        purchase_price_cny: 采购价（人民币元）
        exchange_rate: 汇率（1 USD = ? CNY）
        selling_price_usd: 售价（美元）
        shipping_usd: 头程运费（美元），默认 0
        fba_fee: FBA/平台物流费（美元），默认 0
        commission_rate: 佣金率（小数），默认 0.15
        tax_rate: 税率（小数），默认 0
        market: 目标市场（US/DE/JP/UK），用于自动推断 tax_rate
        exchange_buffer: 汇率浮动备用金比例（默认 0.03=3%）

    Returns:
        dict: 包含保本售价、利润、利润率、敏感度分析等字段
    """
    purchase_price_usd = purchase_price_cny / exchange_rate
    buffer = purchase_price_usd * exchange_buffer
    unit_cost = purchase_price_usd + shipping_usd + fba_fee + buffer
    # 保本售价
    divisor = 1 - commission_rate - tax_rate
    break_even_price = unit_cost / divisor if divisor > 0 else float("inf")

    # 实际利润
    commission = selling_price_usd * commission_rate
    tax = selling_price_usd * tax_rate
    profit = selling_price_usd - unit_cost - commission - tax
    profit_rate = profit / selling_price_usd * 100 if selling_price_usd > 0 else 0

    def _calc(pp_cny, ex_r, sp_usd, ship, fba, cr, tr, eb):
        pp_usd = pp_cny / ex_r
        buf = pp_usd * eb
        uc = pp_usd + ship + fba + buf
        comm = sp_usd * cr
        t = sp_usd * tr
        p = sp_usd - uc - comm - t
        r = p / sp_usd * 100 if sp_usd > 0 else 0
        return p, r

    base = {
        "pp_cny": purchase_price_cny, "ex_r": exchange_rate,
        "sp_usd": selling_price_usd, "ship": shipping_usd,
        "fba": fba_fee, "cr": commission_rate,
        "tr": tax_rate, "eb": exchange_buffer,
    }

    variations = [
        ("售价 +10%", "sp_usd", 1.10, "售价", None),
        ("当前",     "sp_usd", 1.00, "售价", None),
        ("售价 -10%", "sp_usd", 0.90, "售价", None),
        ("汇率 +5%（人民币贬值）", "ex_r", 1.05, "汇率", {"采购价(USD)": round(purchase_price_cny / (exchange_rate * 1.05), 2)}),
        ("汇率 -5%（人民币升值）", "ex_r", 0.95, "汇率", {"采购价(USD)": round(purchase_price_cny / (exchange_rate * 0.95), 2)}),
        ("运费 +20%", "ship", 1.20, "运费", None),
        ("运费 -20%", "ship", 0.80, "运费", None),
        ("FBA费 +20%", "fba", 1.20, "FBA费", None),
        ("FBA费 -20%", "fba", 0.80, "FBA费", None),
        ("采购价 +10%", "pp_cny", 1.10, "采购价(CNY)", {"采购价(USD)": round(purchase_price_cny * 1.10 / exchange_rate, 2)}),
        ("采购价 -10%", "pp_cny", 0.90, "采购价(CNY)", {"采购价(USD)": round(purchase_price_cny * 0.90 / exchange_rate, 2)}),
        ("佣金率 +2pp", "cr", commission_rate + 0.02, "佣金率", {"佣金率%": f"{(commission_rate + 0.02)*100:.1f}%"}, True),
        ("佣金率 -2pp", "cr", max(0, commission_rate - 0.02), "佣金率", {"佣金率%": f"{max(0, commission_rate - 0.02)*100:.1f}%"}, True),    ]

    sensitivity = _sensitivity(_calc, base, variations)

    # 最坏场景：售价 -10% + 汇率 +5%（人民币贬值）
    ex_down_5 = exchange_rate * 0.95
    worst = _worst_case(_calc, base, [
        {"name": "最坏场景（售价 -10% + 人民币升值5%）",
         "params": {"sp_usd": 0.90, "ex_r": 0.95},
         "display": {"售价": round(selling_price_usd * 0.90, 2), "汇率": round(ex_down_5, 2)}},
    ])

    return {
        "模式": "跨境",
        "目标市场": market,
        "汇率": exchange_rate,
        "采购价(CNY)": purchase_price_cny,
        "采购价(USD)": round(purchase_price_usd, 2),
        "汇率浮动备用金(USD)": round(buffer, 2),
        "头程运费(USD)": shipping_usd,
        "FBA费(USD)": fba_fee,
        "单位硬性成本": round(unit_cost, 2),
        "平台佣金率": f"{commission_rate*100:.1f}%",
        "税率": f"{tax_rate*100:.1f}%",
        "保本售价": round(break_even_price, 2),
        "实际售价": selling_price_usd,
        "平台佣金": round(commission, 2),
        "税金": round(tax, 2),
        "单件利润": round(profit, 2),
        "利润率": f"{profit_rate:.1f}%",
        "敏感度分析": {**sensitivity, **worst},
    }


# ── 输出格式化 ──

def format_output(result, fmt="table"):
    if fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)

    lines = []
    lines.append(f"\n{'='*50}")
    lines.append(f"  {result['模式']}利润计算")
    lines.append(f"{'='*50}")

    skip_keys = {"模式", "敏感度分析"}
    for k, v in result.items():
        if k not in skip_keys:
            lines.append(f"  {_pad_str_local(k, 20)} {v}")

    # 敏感度分析
    sensitivity = result.get("敏感度分析", {})
    if sensitivity:
        # 动态计算列宽：根据实际内容的最大显示宽度 + 2 余量
        scenario_width = max(
            max(_display_width(s) for s in sensitivity.keys()),
            12,
        ) + 2
        # 确保列宽不低于最小内容宽度
        scenario_width = max(scenario_width, 14)

        extra_width = max(
            max(
                _display_width(" ".join(
                    f"{k} {v}" for k, v in data.items()
                    if k not in ("利润", "利润率")
                ))
                for data in sensitivity.values()
            ),
            20,
        ) + 2
        extra_width = max(extra_width, 22)

        lines.append(f"\n  {'─'*max(40, scenario_width)}")
        lines.append(f"  📊 敏感度分析")
        lines.append(f"  {'─'*max(40, scenario_width)}")
        for scenario, data in sensitivity.items():
            profit_v = data.get("利润", "?")
            rate_v = data.get("利润率", "?")
            # 提取关键显示字段（不含内部字段）
            extra = " ".join(
                f"{k} {v}" for k, v in data.items()
                if k not in ("利润", "利润率")
            )
            line = f"  {_pad_str_local(scenario, scenario_width)}  {_pad_str_local(extra, extra_width)}  利润 {_pad_str_local(str(profit_v), 10)}  利润率 {rate_v}"
            lines.append(line)

    lines.append(f"{'='*50}\n")
    return "\n".join(lines)


def main():
    for warning in check_commission_staleness():
        logger.warning(warning)

    parser = argparse.ArgumentParser(description="电商利润计算器（国内版 + 跨境版）")
    subparsers = parser.add_subparsers(dest="mode")

    # 国内版
    dom = subparsers.add_parser("domestic", help="国内版利润计算")
    dom.add_argument("--purchase-price", type=float, required=True, help="采购价（元）")
    dom.add_argument("--selling-price", type=float, required=True, help="售价（元）")
    dom.add_argument("--shipping", type=float, default=0, help="运费（元）")
    dom.add_argument("--commission-rate", type=float, help="平台扣点率（如 0.05=5%%），不指定则根据 --platform 自动设置")
    dom.add_argument("--platform", choices=["jd", "tmall", "taobao", "pdd", "1688"], help="平台（自动设置扣点率）")
    dom.add_argument("--format", choices=["table", "json"], default="table", help="输出格式")

    # 跨境版
    cb = subparsers.add_parser("crossborder", help="跨境版利润计算")
    cb.add_argument("--purchase-price-cny", type=float, required=True, help="采购价（人民币）")
    cb.add_argument("--exchange-rate", type=float, required=True, help="汇率（1 USD = ? CNY）")
    cb.add_argument("--selling-price-usd", type=float, required=True, help="售价（美元）")
    cb.add_argument("--shipping-usd", type=float, default=0, help="头程运费（美元）")
    cb.add_argument("--fba-fee", type=float, default=0, help="FBA/平台物流费（美元）")
    cb.add_argument("--commission-rate", type=float, help="平台佣金率（如 0.15=15%%），不指定则根据 --platform 自动设置")
    cb.add_argument("--platform", choices=["amazon", "shopee", "tiktok", "temu"], help="跨境平台（自动设置佣金率）")
    cb.add_argument("--exchange-buffer", type=float, default=0.03, help="汇率浮动备用金比例（如 0.03=3%%）")
    cb.add_argument("--tax-rate", type=float, default=None, help="税率（如 0.19=19%% VAT），不指定则根据 --market 自动推断")
    cb.add_argument("--market", default="US", help="目标市场（US/DE/JP/UK）")
    cb.add_argument("--format", choices=["table", "json"], default="table", help="输出格式")

    args = parser.parse_args()

    if args.mode == "domestic":
        result = calc_domestic(
            purchase_price=args.purchase_price,
            selling_price=args.selling_price,
            shipping=args.shipping,
            commission_rate=args.commission_rate,
            platform=args.platform,
        )
    elif args.mode == "crossborder":
        commission_rate = args.commission_rate
        if commission_rate is None and args.platform:
            commission_rate = CROSSBORDER_COMMISSION.get(args.platform, 0.15)
        elif commission_rate is None:
            commission_rate = 0.15

        tax_rate = args.tax_rate
        if tax_rate is None:
            tax_rate = MARKET_TAX.get(args.market, 0.0)

        result = calc_crossborder(
            purchase_price_cny=args.purchase_price_cny,
            exchange_rate=args.exchange_rate,
            selling_price_usd=args.selling_price_usd,
            shipping_usd=args.shipping_usd,
            fba_fee=args.fba_fee,
            commission_rate=commission_rate,
            tax_rate=tax_rate,
            market=args.market,
            exchange_buffer=args.exchange_buffer,
        )
    else:
        parser.print_help()
        sys.exit(1)

    print(format_output(result, fmt=args.format))


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    main()
