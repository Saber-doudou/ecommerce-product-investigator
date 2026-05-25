"""ecommerce-product-investigator scripts package — 版本号从 SKILL.md 自动同步"""
import re
from pathlib import Path

_version_file = Path(__file__).parent.parent / "SKILL.md"
if _version_file.exists():
    _match = re.search(r"^version:\s*(.+)$", _version_file.read_text(encoding="utf-8"), re.MULTILINE)
    __version__ = _match.group(1).strip() if _match else "0.0.0"
else:
    __version__ = "0.0.0"
