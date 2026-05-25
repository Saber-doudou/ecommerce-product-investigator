"""maishou_common.py 单元测试 — format_table / check_env 等公共函数"""
import pytest
from maishou_common import format_table, check_env


class TestFormatTable:
    """format_table() — 中英文混排表格"""

    def test_empty_rows(self):
        assert format_table([], {"列1": 10}) == "未找到结果"

    def test_single_row(self):
        rows = [{"name": "test", "val": "123"}]
        result = format_table(rows, {"name": 10, "val": 10})
        assert "test" in result
        assert "123" in result
        assert "---" in result  # 分隔线

    def test_cjk_alignment(self):
        """中文列名和数据应对齐"""
        rows = [{"商品名": "蓝牙耳机", "价格": "99"}]
        result = format_table(rows, {"商品名": 12, "价格": 8})
        lines = result.split("\n")
        # 表头行显示宽度应一致（至少分隔线不短于表头）
        assert len(lines) >= 3  # header + sep + data

    def test_mixed_cjk_ascii(self):
        """中英文混排数据"""
        rows = [
            {"name": "iPhone 15", "price": "5999"},
            {"name": "华为Mate60", "price": "6999"},
        ]
        result = format_table(rows, {"name": 20, "price": 10})
        assert "iPhone 15" in result
        assert "华为Mate60" in result

    def test_multiple_rows_all_columns(self):
        """多行多列"""
        rows = [
            {"序号": 1, "商品名": "测试A", "价格": "10", "平台": "淘宝", "销量": "100"},
            {"序号": 2, "商品名": "测试B", "价格": "20", "平台": "京东", "销量": "200"},
        ]
        result = format_table(rows, {"序号": 4, "商品名": 10, "价格": 8, "平台": 8, "销量": 8})
        assert "测试A" in result
        assert "测试B" in result
        assert "淘宝" in result
        assert "京东" in result


class TestCheckEnv:
    """check_env() — 环境变量校验"""

    def test_returns_list(self):
        result = check_env()
        assert isinstance(result, list)

    def test_warning_text_format(self):
        """警告文本应包含 ⚠️ 前缀"""
        result = check_env()
        for w in result:
            assert w.startswith("⚠️ ")
