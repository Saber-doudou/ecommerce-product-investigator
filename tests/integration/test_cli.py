"""集成测试 — CLI 端到端执行（不依赖外部 API）"""
import subprocess
import json
import sys
import os
import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
PROFIT_CALC = os.path.join(SCRIPTS_DIR, "profit_calc.py")
MONITOR_STORE = os.path.join(SCRIPTS_DIR, "monitor_store.py")
MAISHOU_SEARCH = os.path.join(SCRIPTS_DIR, "maishou_search.py")
MAISHOU_PRICE = os.path.join(SCRIPTS_DIR, "maishou_price.py")


def _run(*args):
    """运行 profit_calc.py 子进程，返回 (returncode, stdout, stderr)"""
    result = subprocess.run(
        [sys.executable, PROFIT_CALC] + list(args),
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return result.returncode, result.stdout, result.stderr


class TestDomesticCLI:
    """国内版 CLI 端到端测试"""

    def test_basic_table_output(self):
        code, stdout, stderr = _run(
            "domestic", "--purchase-price", "80", "--selling-price", "159", "--shipping", "8"
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "国内" in stdout
        assert "利润" in stdout

    def test_json_output(self):
        code, stdout, stderr = _run(
            "domestic", "--purchase-price", "80", "--selling-price", "159", "--format", "json"
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        data = json.loads(stdout)
        assert data["模式"] == "国内"
        assert "利润" in data
        assert "敏感度分析" in data

    def test_platform_inference(self):
        """--platform pdd 应自动推断佣金率 ~0.6%"""
        code, stdout, stderr = _run(
            "domestic", "--purchase-price", "80", "--selling-price", "159", "--platform", "pdd"
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "0.6%" in stdout

    def test_sensitivity_in_output(self):
        code, stdout, stderr = _run(
            "domestic", "--purchase-price", "100", "--selling-price", "200", "--format", "table"
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "敏感度分析" in stdout


class TestCrossBorderCLI:
    """跨境版 CLI 端到端测试"""

    def test_basic_table_output(self):
        code, stdout, stderr = _run(
            "crossborder",
            "--purchase-price-cny", "80", "--exchange-rate", "7.2",
            "--selling-price-usd", "29.99", "--shipping-usd", "3.5",
            "--fba-fee", "4.2",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "跨境" in stdout
        assert "利润" in stdout

    def test_json_output(self):
        code, stdout, stderr = _run(
            "crossborder",
            "--purchase-price-cny", "80", "--exchange-rate", "7.2",
            "--selling-price-usd", "29.99", "--format", "json",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        data = json.loads(stdout)
        assert data["模式"] == "跨境"
        assert "保本售价" in data
        assert "敏感度分析" in data

    def test_market_tax_inference(self):
        """--market DE 应自动推断 19% VAT"""
        code, stdout, stderr = _run(
            "crossborder",
            "--purchase-price-cny", "80", "--exchange-rate", "7.2",
            "--selling-price-usd", "29.99", "--market", "DE",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "19.0%" in stdout

    def test_platform_inference(self):
        """--platform shopee 应自动推断佣金率 ~6%"""
        code, stdout, stderr = _run(
            "crossborder",
            "--purchase-price-cny", "80", "--exchange-rate", "7.2",
            "--selling-price-usd", "29.99", "--platform", "shopee",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "6.0%" in stdout

    def test_combined_platform_market_inference(self):
        """--platform shopee --market DE 应同时推断佣金率 6% + VAT 19%"""
        code, stdout, stderr = _run(
            "crossborder",
            "--purchase-price-cny", "80", "--exchange-rate", "7.2",
            "--selling-price-usd", "29.99",
            "--platform", "shopee", "--market", "DE",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "6.0%" in stdout, "应推断 shopee 佣金率 6%"
        assert "19.0%" in stdout, "应推断 DE VAT 19%"

    def test_sensitivity_in_output(self):
        code, stdout, stderr = _run(
            "crossborder",
            "--purchase-price-cny", "100", "--exchange-rate", "7.2",
            "--selling-price-usd", "25.00", "--format", "table",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "敏感度分析" in stdout


class TestInputValidation:
    """输入校验测试"""

    def test_domestic_negative_purchase_price(self):
        """采购价不能为负数"""
        code, stdout, stderr = _run(
            "domestic", "--purchase-price", "-80", "--selling-price", "159"
        )
        assert code != 0

    def test_domestic_negative_selling_price(self):
        """售价不能为负数"""
        code, stdout, stderr = _run(
            "domestic", "--purchase-price", "80", "--selling-price", "-159"
        )
        assert code != 0

    def test_crossborder_negative_exchange_rate(self):
        """汇率不能为 0 或负数"""
        code, stdout, stderr = _run(
            "crossborder",
            "--purchase-price-cny", "80", "--exchange-rate", "0",
            "--selling-price-usd", "29.99",
        )
        assert code != 0


class TestNewFeatures:
    """v0.5.0 新功能集成测试"""

    def test_break_even_in_domestic_output(self):
        """国内版应输出保本售价"""
        code, stdout, stderr = _run(
            "domestic", "--purchase-price", "80", "--selling-price", "159",
            "--format", "json",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        data = json.loads(stdout)
        assert "保本售价" in data
        assert data["保本售价"] > 0

    def test_break_even_in_sensitivity(self):
        """敏感度分析应包含保本售价场景"""
        code, stdout, stderr = _run(
            "domestic", "--purchase-price", "80", "--selling-price", "159",
            "--format", "json",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        data = json.loads(stdout)
        scenarios = list(data["敏感度分析"].keys())
        assert any("保本售价" in s for s in scenarios)


class TestMonitorStoreCLI:
    """监测模式 CLI 测试"""

    def _run_monitor(self, *args):
        result = subprocess.run(
            [sys.executable, MONITOR_STORE] + list(args),
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return result.returncode, result.stdout, result.stderr

    def test_save_and_load(self, tmp_path):
        store = str(tmp_path / "monitor")
        import time
        cat = f"test_category_{int(time.time())}"
        data = '{"prices": [{"price": 100}, {"price": 200}], "bsr": 1234}'

        # save
        code, stdout, stderr = self._run_monitor(
            "save", "--category", cat, "--data", data, "--store-dir", store
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        result = json.loads(stdout)
        assert result["status"] == "ok"

        # load
        code, stdout, stderr = self._run_monitor(
            "load", "--category", cat, "--store-dir", store
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        result = json.loads(stdout)
        assert result["category"] == cat
        assert "data" in result

    def test_diff_first_run(self, tmp_path):
        store = str(tmp_path / "monitor")
        import time
        cat = f"test_diff_{int(time.time())}"
        data = '{"prices": [{"price": 100}], "bsr": 500}'

        code, stdout, stderr = self._run_monitor(
            "diff", "--category", cat, "--data", data, "--store-dir", store
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "首次监测" in stdout or "_first_run" in stdout

    def test_diff_with_change(self, tmp_path):
        store = str(tmp_path / "monitor")
        import time
        cat = f"test_diff_change_{int(time.time())}"

        # save baseline
        self._run_monitor(
            "save", "--category", cat,
            "--data", '{"prices": [{"price": 100}], "bsr": 500}',
            "--store-dir", store,
        )

        # diff with new data
        code, stdout, stderr = self._run_monitor(
            "diff", "--category", cat,
            "--data", '{"prices": [{"price": 120}], "bsr": 600}',
            "--store-dir", store,
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        # should detect price change
        assert "price" in stdout.lower() or "首次" not in stdout

    def test_list(self, tmp_path):
        store = str(tmp_path / "monitor")
        code, stdout, stderr = self._run_monitor("list", "--store-dir", store)
        assert code == 0, f"exit={code} stderr={stderr}"


class TestSearchCLIHelp:
    """maishou_search.py CLI 基本测试"""

    def _run_search(self, *args):
        result = subprocess.run(
            [sys.executable, MAISHOU_SEARCH] + list(args),
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return result.returncode, result.stdout, result.stderr

    def test_help_output(self):
        code, stdout, stderr = self._run_search("--help")
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "search" in stdout
        assert "detail" in stdout

    def test_search_missing_keyword(self):
        """缺少 --keyword 时应报错"""
        code, stdout, stderr = self._run_search("search", "--source", "2")
        assert code != 0

    def test_detail_missing_id(self):
        """缺少 --id 时应报错"""
        code, stdout, stderr = self._run_search("detail", "--source", "2")
        assert code != 0


class TestMaishouPriceCLI:
    """maishou_price.py CLI 端到端测试（不依赖 API）"""

    def _run_price(self, *args):
        result = subprocess.run(
            [sys.executable, MAISHOU_PRICE] + list(args),
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return result.returncode, result.stdout, result.stderr

    def test_help_output(self):
        code, stdout, stderr = self._run_price("--help")
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "source" in stdout
        assert "format" in stdout

    def test_missing_keyword(self):
        """缺少 positional keyword 时应报错"""
        code, stdout, stderr = self._run_price("--source", "2")
        assert code != 0

    def test_invalid_format(self):
        """无效 --format 值应报错"""
        code, stdout, stderr = self._run_price("test_keyword", "--format", "xml")
        assert code != 0

    def test_valid_format_args(self):
        """--format json/table/csv 应能被解析（即使 API 失败也先验证参数解析）"""
        # 只测试参数解析阶段不报错，不依赖 API 成功
        for fmt in ("table", "json", "csv"):
            code, stdout, stderr = self._run_price("test_keyword", "--format", fmt)
            # API 失败会导致非零退出码，但参数解析本身不应报错
            # 验证不是 argparse 错误（argparse 错误含 "usage:"）
            assert "usage:" not in stderr.lower(), f"format={fmt} 参数解析失败: {stderr}"

    def test_limit_and_page_parsed(self):
        """--limit 和 --page 参数应能被解析"""
        code, stdout, stderr = self._run_price(
            "test_keyword", "--limit", "5", "--page", "2", "--format", "json"
        )
        assert "usage:" not in stderr.lower(), f"参数解析失败: {stderr}"
