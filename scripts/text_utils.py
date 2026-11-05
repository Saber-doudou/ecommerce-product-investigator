# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
text_utils.py - 中英文混排文本工具（零外部依赖）

提供 CJK 显示宽度计算和字符串填充，解决终端表格中英文对齐问题。
"""

import unicodedata


def _char_width(ch: str) -> int:
    """单字符显示宽度：display_width 与 pad_str 截断共用同一口径。"""
    cp = ord(ch)
    if (0x1F300 <= cp <= 0x1F9FF or 0x2600 <= cp <= 0x26FF
            or 0x2700 <= cp <= 0x27BF or 0xFE00 <= cp <= 0xFE0F
            or unicodedata.east_asian_width(ch) in ("W", "F")):
        return 2
    return 1


def display_width(s: str) -> int:
    """计算终端显示宽度；None/空值按 0 处理，避免上游 null 字段崩溃。"""
    if s is None:
        return 0
    return sum(_char_width(ch) for ch in str(s))


def pad_str(s: str, width: int, align: str = "<") -> str:
    """按显示宽度填充字符串，解决中英文混排对齐问题

    Args:
        s: 原始字符串
        width: 目标显示宽度
        align: 对齐方式 "<" 左对齐 | ">" 右对齐 | "^" 居中

    Returns:
        填充后的字符串（超宽时截断并以 … 结尾）
    """
    dw = display_width(s)
    if dw >= width:
        result = ""
        cur = 0
        for ch in s:
            chw = _char_width(ch)
            if cur + chw > width:
                remaining = width - cur
                if remaining >= 1:
                    result += "\u2026"  # …
                break
            result += ch
            cur += chw
        return result
    padding = width - dw
    if align == "<":
        return s + " " * padding
    elif align == ">":
        return " " * padding + s
    else:  # "^" center
        left = padding // 2
        right = padding - left
        return " " * left + s + " " * right
