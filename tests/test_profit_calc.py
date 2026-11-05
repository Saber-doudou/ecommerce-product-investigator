"""profit_calc.py 单元测试 — 国内/跨境利润计算、敏感度分析、边界值"""

import pytest
from datetime import datetime
from profit_calc import (
    calc_domestic, calc_crossborder,
    check_commission_staleness,
    COMMISSION_REF_DATE,
)


class TestCalcDomestic:
    """calc_domestic() — 国内版利润计算"""

    def test_basic_profit(self):
        r = calc_domestic(purchase_price=80, selling_price=159, shipping=8, commission_rate=0.05)
        assert r["采购价"] == 80
        assert r["售价"] == 159
        assert r["平台扣点"] == pytest.approx(7.95)
        assert r["总成本"] == pytest.approx(95.95)
        assert r["利润"] == pytest.approx(63.05)
        assert "敏感度分析" in r

    def test_platform_auto_commission(self):
        """--platform 自动匹配佣金率"""
        r = calc_domestic(purchase_price=80, selling_price=100, platform="jd")
        assert r["平台扣点率"] == "5.0%"

    def test_taobao_no_commission(self):
        r = calc_domestic(purchase_price=80, selling_price=100, platform="taobao")
        assert r["平台扣点率"] == "0.0%"
        assert r["平台扣点"] == 0

    def test_zero_selling_price(self):
        r = calc_domestic(purchase_price=80, selling_price=0)
        assert r["利润率"] == "0.0%"
        assert r["利润"] == -80.0

    def test_negative_profit(self):
        r = calc_domestic(purchase_price=100, selling_price=50, commission_rate=0.05)
        assert r["利润"] < 0

    def test_sensitivity_analysis(self):
        r = calc_domestic(purchase_price=80, selling_price=159, shipping=8, commission_rate=0.05)
        sa = r["敏感度分析"]
        assert "当前" in sa
        assert "售价 +10%" in sa
        assert "售价 -10%" in sa
        assert "最坏场景（售价 -10% + 采购价 +10%）" in sa

        # 当前利润应约 63.05
        assert sa["当前"]["利润"] == pytest.approx(63.05, abs=0.1)

        # 最坏场景利润应低于当前
        worst = sa["最坏场景（售价 -10% + 采购价 +10%）"]
        assert worst["利润"] < sa["当前"]["利润"]


class TestCalcCrossborder:
    """calc_crossborder() — 跨境版利润计算"""

    def test_basic_profit(self):
        r = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.2,
            selling_price_usd=24.99, shipping_usd=1.5,
            fba_fee=5.5, commission_rate=0.15,
        )
        assert r["模式"] == "跨境"
        assert r["采购价(CNY)"] == 50
        assert r["采购价(USD)"] == pytest.approx(6.94, abs=0.01)
        assert r["单位硬性成本"] > 0
        assert r["单件利润"] > 0

    def test_exchange_buffer(self):
        """汇率浮动备用金 3% 被正确计入"""
        r = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.2,
            selling_price_usd=24.99, shipping_usd=1.5,
            fba_fee=5.5, commission_rate=0.15,
            exchange_buffer=0.03,
        )
        # 采购价 USD ≈ 6.94，buffer ≈ 6.94 × 0.03 ≈ 0.21
        assert r["汇率浮动备用金(USD)"] == pytest.approx(0.21, abs=0.01)

    def test_break_even_price(self):
        r = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.2,
            selling_price_usd=24.99, shipping_usd=1.5,
            fba_fee=5.5, commission_rate=0.15,
        )
        # 保本售价 = 单位硬性成本 / (1 - 0.15)
        expected = r["单位硬性成本"] / 0.85
        assert r["保本售价"] == pytest.approx(expected, abs=0.01)

    def test_zero_buffer(self):
        r = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.2,
            selling_price_usd=24.99, shipping_usd=1.5,
            fba_fee=5.5, commission_rate=0.15,
            exchange_buffer=0,
        )
        assert r["汇率浮动备用金(USD)"] == 0

    def test_german_vat(self):
        """德国市场自动推断 19% VAT"""
        r = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.2,
            selling_price_usd=24.99, commission_rate=0.15,
            tax_rate=0.19,
        )
        assert r["税率"] == "19.0%"
        assert r["税金"] == pytest.approx(24.99 * 0.19, abs=0.01)

    def test_sensitivity_analysis(self):
        r = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.2,
            selling_price_usd=24.99, shipping_usd=1.5, fba_fee=5.5,
        )
        sa = r["敏感度分析"]
        assert "当前" in sa
        assert "售价 +10%" in sa
        assert "汇率 +5%（人民币贬值）" in sa
        assert "采购价 +10%" in sa
        assert "最坏场景（售价 -10% + 人民币升值5%）" in sa

        # 最坏场景利润应远低于当前
        worst = sa["最坏场景（售价 -10% + 人民币升值5%）"]
        assert worst["利润"] < sa["当前"]["利润"]


class TestEdgeCases:
    """边界值和异常输入"""

    def test_domestic_zero_shipping(self):
        r = calc_domestic(purchase_price=80, selling_price=159, commission_rate=0.05)
        assert r["运费"] == 0

    def test_domestic_purchase_greater_than_selling(self):
        """采购价 > 售价 → 亏损，利润率为负"""
        r = calc_domestic(purchase_price=200, selling_price=100, commission_rate=0.05)
        assert r["利润"] < 0
        # 利润率是负值（200 采购 + 5 扣点 = 205 成本，卖 100，亏损 105，利润率 -105%）
        assert r["利润"] == pytest.approx(-105, abs=0.1)

    def test_domestic_large_numbers(self):
        """大数值不溢出，利润计算正确"""
        r = calc_domestic(purchase_price=99999, selling_price=150000, commission_rate=0.05)
        assert r["利润"] == pytest.approx(150000 - 99999 - 7500, abs=1)

    def test_domestic_100_percent_commission(self):
        """100% 佣金率 → 利润可以正确计算（极端的业务逻辑测试，不验证合理性）"""
        r = calc_domestic(purchase_price=80, selling_price=159, commission_rate=1.0)
        assert r["平台扣点"] == 159
        assert r["利润"] == pytest.approx(159 - 80 - 159, abs=0.01)

    def test_domestic_zero_purchase_price(self):
        """采购价为 0 → 利润 = 售价 - 运费 - 扣点"""
        r = calc_domestic(purchase_price=0, selling_price=159, shipping=8, commission_rate=0.05)
        assert r["采购价"] == 0
        assert r["利润"] == pytest.approx(159 - 8 - 7.95, abs=0.01)

    def test_crossborder_high_commission(self):
        """高佣金率下利润为负"""
        r = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.2,
            selling_price_usd=10, commission_rate=0.30,
        )
        assert r["单件利润"] < 0

    def test_crossborder_zero_price(self):
        """售价为 0 → 极端亏损"""
        r = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.2,
            selling_price_usd=0, commission_rate=0.15,
        )
        assert r["单件利润"] < 0
        # 保本售价应 > 0（成本不为零）
        assert r["保本售价"] > 0

    def test_crossborder_large_numbers(self):
        """大数值不溢出"""
        r = calc_crossborder(
            purchase_price_cny=999999, exchange_rate=7.2,
            selling_price_usd=9999, fba_fee=500, shipping_usd=1000,
            commission_rate=0.15,
        )
        assert isinstance(r["单件利润"], float)
        assert r["单位硬性成本"] > 0

    def test_crossborder_strong_rmb(self):
        """人民币升值（汇率下降）→ 采购成本上升 → 利润下降"""
        r_strong = calc_crossborder(
            purchase_price_cny=50, exchange_rate=6.5,
            selling_price_usd=24.99, commission_rate=0.15,
        )
        r_weak = calc_crossborder(
            purchase_price_cny=50, exchange_rate=7.5,
            selling_price_usd=24.99, commission_rate=0.15,
        )
        assert r_strong["单件利润"] < r_weak["单件利润"]


class TestCommissionStaleness:
    """check_commission_staleness() — 佣金率过期检测（注入固定日期，避免时间炸弹）"""

    def test_not_stale_when_recent(self):
        warnings = check_commission_staleness(today=datetime(2026, 5, 1))
        assert len(warnings) == 0

    def test_returns_list(self):
        assert isinstance(check_commission_staleness(), list)

    def test_stale_after_threshold(self):
        warnings = check_commission_staleness(today=datetime(2027, 5, 1))
        assert len(warnings) == 1
        assert "已过 12 个月" in warnings[0]


class TestCommissionRatesGuard:
    """v0.5.3：费率数据不可用或入参越界时必须显式报错，禁止静默降级"""

    def test_missing_rates_file_raises(self, monkeypatch, tmp_path):
        import profit_calc
        monkeypatch.setattr(profit_calc, "__file__", str(tmp_path / "fake.py"))
        with pytest.raises(profit_calc.CommissionRatesError, match="费率文件不存在"):
            profit_calc._load_commission_rates()

    def test_rates_error_stops_calculation(self, monkeypatch):
        import profit_calc
        monkeypatch.setattr(profit_calc, "_RATES_ERROR", "模拟费率不可用")
        with pytest.raises(profit_calc.CommissionRatesError, match="禁止在无费率数据"):
            profit_calc.calc_domestic(80, 159, commission_rate=0.05)

    def test_unknown_domestic_platform_raises(self):
        with pytest.raises(ValueError, match="未知平台"):
            calc_domestic(purchase_price=80, selling_price=159, platform="unknown")

    def test_unknown_crossborder_market_raises(self):
        with pytest.raises(ValueError, match="未知市场"):
            calc_crossborder(purchase_price_cny=80, exchange_rate=7.2,
                             selling_price_usd=29.99, market="XX")
