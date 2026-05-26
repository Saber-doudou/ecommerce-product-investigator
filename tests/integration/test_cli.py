"""集成测试 — CLI 端到端执行（不依赖外部 API）"""
import subprocess
import json
import sys
import os

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
PROFIT_CALC = os.path.join(SCRIPTS_DIR, "profit_calc.py")


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

    def test_sensitivity_in_output(self):
        code, stdout, stderr = _run(
            "crossborder",
            "--purchase-price-cny", "100", "--exchange-rate", "7.2",
            "--selling-price-usd", "25.00", "--format", "table",
        )
        assert code == 0, f"exit={code} stderr={stderr}"
        assert "敏感度分析" in stdout
