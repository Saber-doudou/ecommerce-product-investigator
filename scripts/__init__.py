"""ecommerce-product-investigator scripts package — 版本号从 SKILL.md 自动同步"""
import logging
import re
from pathlib import Path

_logger = logging.getLogger(__name__)
_version_file = Path(__file__).parent.parent / "SKILL.md"
if _version_file.exists():
    _match = re.search(r"^version:\s*(.+)$", _version_file.read_text(encoding="utf-8"), re.MULTILINE)
    if _match:
        __version__ = _match.group(1).strip()
    else:
        _logger.warning("SKILL.md 缺少 version 字段，__version__ 回退为 0.0.0")
        __version__ = "0.0.0"
else:
    _logger.warning("SKILL.md 不存在，__version__ 回退为 0.0.0")
    __version__ = "0.0.0"
