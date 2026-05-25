# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
text_utils.py - 中英文混排文本工具（零外部依赖）

提供 CJK 显示宽度计算和字符串填充，解决终端表格中英文对齐问题。
"""

import unicodedata


def display_width(s: str) -> int:
    """计算字符串的终端显示宽度（CJK 字符占 2 列，ASCII 占 1 列）"""
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


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
            chw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
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
