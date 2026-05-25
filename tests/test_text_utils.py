"""text_utils.py 单元测试 — CJK 宽度计算、截断、对齐"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from text_utils import display_width, pad_str


class TestDisplayWidth:
    """display_width() — 计算终端显示宽度"""

    def test_ascii(self):
        assert display_width("hello") == 5
        assert display_width("123") == 3

    def test_cjk(self):
        assert display_width("你好") == 4
        assert display_width("中文测试") == 8

    def test_mixed(self):
        assert display_width("hello你好") == 9  # 5 + 4
        assert display_width("价格$10") == 7     # 4(价格) + 1($) + 2(10)

    def test_empty(self):
        assert display_width("") == 0

    def test_special_chars(self):
        """全角符号算 2 宽，半角算 1"""
        assert display_width("，。！") == 6  # 全角标点


class TestPadStr:
    """pad_str() — 按显示宽度填充"""

    def test_left_align_short(self):
        result = pad_str("hi", 5, "<")
        assert result == "hi   "  # 2 chars + 3 spaces
        assert display_width(result) == 5

    def test_left_align_cjk(self):
        result = pad_str("你好", 6, "<")
        assert result == "你好  "  # 4 cols + 2 spaces
        assert display_width(result) == 6

    def test_right_align(self):
        result = pad_str("hi", 5, ">")
        assert result == "   hi"

    def test_center_align(self):
        result = pad_str("ab", 6, "^")
        assert display_width(result) == 6
        # "  ab  " — left=2 right=2
        assert result.startswith("  ")
        assert result.endswith("  ")

    def test_truncate_ascii(self):
        """ASCII 在宽度边界截断，不添加省略号"""
        result = pad_str("hello world", 7, "<")
        assert display_width(result) <= 7
        assert result == "hello w"

    def test_truncate_cjk(self):
        """CJK 截断到奇数宽度时添加 …"""
        result = pad_str("很长很长的标题名称", 5, "<")
        assert display_width(result) <= 5
        assert result == "很长…"

    def test_no_truncate_when_exact(self):
        result = pad_str("abcd", 4, "<")
        assert result == "abcd"

    def test_no_truncate_when_shorter(self):
        result = pad_str("ab", 4, "<")
        assert result == "ab  "


class TestPadStrEdgeCases:
    """pad_str 边界情况"""

    def test_single_char_width_1(self):
        result = pad_str("a", 1, "<")
        assert result == "a"

    def test_single_char_width_2(self):
        result = pad_str("中", 2, "<")
        assert result == "中"

    def test_width_zero(self):
        result = pad_str("abc", 0, "<")
        assert display_width(result) == 0
