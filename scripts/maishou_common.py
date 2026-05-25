# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""
maishou_common.py - 买手 88 API 公共模块
提供共享的 session 管理、headers、API 端点和工具函数。
"""

import os
import json
import asyncio
from pathlib import Path
import aiohttp

from text_utils import display_width as _display_width, pad_str as _pad_str

# ── 自动加载 .env 文件 ──
def _load_dotenv():
    """自动加载项目根目录的 .env 文件（如果存在），不引入 python-dotenv 依赖"""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ.setdefault(key, value)

_load_dotenv()

# ── 环境变量（函数动态获取，避免 import 时固化） ──
def get_invite_code() -> str:
    """动态获取 MAISHOU_API_KEY，支持运行时 .env 加载后设置"""
    return os.getenv("MAISHOU_API_KEY") or ""


def get_openid() -> str:
    """动态获取 MAISHOU_OPENID，支持运行时 .env 加载后设置"""
    return os.getenv("MAISHOU_OPENID") or ""




def get_headers_app() -> dict:
    """每次调用动态获取 openid，确保运行时设置的环境变量生效"""
    return {
        **HEADERS_BASE,
        aiohttp.hdrs.USER_AGENT: "MaiShouApp/3.7.7 (iPhone; iOS 17.0; Scale/3.00)",
        "openid": get_openid(),
        "version": "3.7.7",
    }


# ── 常量 ──
API_BASE = "https://appapi.maishou88.com"
API_SHARE_BASE = "https://msapi.maishou88.com"
SEARCH_URL = f"{API_BASE}/api/v1/homepage/searchList"
DETAIL_URL = f"{API_BASE}/api/v3/goods/detail"
TARGET_URL = f"{API_SHARE_BASE}/api/v1/share/getTargetUrl"

SOURCE_MAP = {1: "淘宝", 2: "京东", 3: "拼多多", 4: "苏宁", 5: "唯品会", 6: "考拉", 7: "抖音", 8: "快手", 10: "1688"}  # 9 号保留未使用

TIMEOUT = aiohttp.ClientTimeout(total=30)

HEADERS_BASE = {
    aiohttp.hdrs.ACCEPT: "application/json",
    aiohttp.hdrs.REFERER: "https://www.google.com/",
    aiohttp.hdrs.USER_AGENT: "Mozilla/5.0 AppleWebKit/537 Chrome/120 Safari/537",
}



# ── Session 管理 ──
_SESSION: aiohttp.ClientSession | None = None


async def get_session() -> aiohttp.ClientSession:
    """懒加载单例 session"""
    global _SESSION
    if _SESSION is None or _SESSION.closed:
        _SESSION = aiohttp.ClientSession(headers=HEADERS_BASE, timeout=TIMEOUT)
    return _SESSION


async def close_session():
    """关闭全局 session"""
    global _SESSION
    if _SESSION and not _SESSION.closed:
        await _SESSION.close()
        _SESSION = None


# ── 工具函数 ──
def check_env():
    """启动时校验环境变量，打印警告"""
    warnings = []
    if not get_openid():
        warnings.append("⚠️ MAISHOU_OPENID 未设置，可能影响搜索结果")
    if not get_invite_code():
        warnings.append("⚠️ MAISHOU_API_KEY 未设置，商品详情接口可能受限")
    return warnings


def format_table(rows: list[dict], columns: dict[str, int]) -> str:
    """
    通用表格格式化（支持中英文混排对齐）

    Args:
        rows: 数据行
        columns: {列名: 列宽} 字典
    """
    if not rows:
        return "未找到结果"

    lines = []
    # 表头
    header_parts = [_pad_str(col, width) for col, width in columns.items()]
    header = "  ".join(header_parts)
    # 分隔线按显示宽度算
    sep = "-" * _display_width(header)
    lines.append(header)
    lines.append(sep)

    for r in rows:
        parts = []
        for col, width in columns.items():
            val = str(r.get(col, ""))
            parts.append(_pad_str(val, width))
        lines.append("  ".join(parts))

    return "\n".join(lines)


# ── 统一搜索 API ──
async def search_api(
    session: aiohttp.ClientSession,
    keyword: str,
    source: int = 0,
    page: int = 1,
    limit: int = 0,
) -> tuple[list[dict], str | None]:
    """
    统一的买手 88 搜索 API 调用，供 maishou_search.py 和 maishou_price.py 共用。

    Args:
        session: aiohttp session
        keyword: 搜索关键词
        source: 平台编号 (0=全部 1=淘宝 2=京东 3=拼多多 10=1688 ...)
        page: 分页页码
        limit: 返回数量限制 (0=不限)

    Returns:
        (items: list[dict], error: str | None)
    """
    payload = {
        "isCoupon": 0,
        "keyword": str(keyword),
        "openid": get_openid(),
        "order": "desc",
        "page": page,
        "pddListId": "",
        "sort": "",
        "sourceType": str(source),
        "user_id": "",
    }
    if limit > 0:
        payload["limit"] = limit

    for attempt in range(2):
        try:
            resp = await session.post(
                SEARCH_URL,
                headers=get_headers_app(),
                json=payload,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            data = await resp.json(encoding="utf-8-sig")

            if data.get("code") == 200:
                raw = data.get("data")
                # 双向兼容：data 直接是数组，或 data.list / data.items
                if isinstance(raw, list):
                    items = raw
                elif isinstance(raw, dict):
                    items = raw.get("list") or raw.get("items") or []
                else:
                    items = []
                return items, None
            else:
                msg = data.get("message", f"API 返回异常 code={data.get('code')}")
                return [], msg
        except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
            if attempt == 0:
                await asyncio.sleep(3)
            else:
                return [], f"请求失败（已重试）: {e}"

    return [], "未知错误"
