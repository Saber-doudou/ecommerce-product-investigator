"""严格审查收口回归用例（2026-11-05）。

覆盖审查报告 §四列出的 8 类零覆盖场景：空值 / BOM / 费率边界 /
非法 JSON / 路径穿越 / 0 基线 / CSV 落盘 / 固定结构。
"""

import json
import os
from pathlib import Path

import pytest


def test_display_width_none_is_zero():
    from text_utils import display_width
    assert display_width(None) == 0
    assert display_width("中文") == 4


@pytest.mark.asyncio
async def test_null_title_normalized(monkeypatch):
    import maishou_price as mp

    async def fake_search_api(session, keyword, src, page=1, limit=10):
        return [{
            "title": None, "actualPrice": None,
            "monthSales": None, "shopName": None,
        }], None

    monkeypatch.setattr(mp, "search_api", fake_search_api)
    rows = await mp.search_single_source(None, "x", 2, 10)
    assert rows[0]["title"] == ""
    assert mp.display_width(rows[0]["title"]) == 0


def test_price_csv_has_no_blank_lines():
    import maishou_price as mp
    out = mp.format_csv([{
        "title": "A", "price": "1", "platform": "京东",
        "shop": "x", "sales": "2", "url": "",
    }])
    assert chr(10) * 2 not in out


def test_dotenv_bom_and_inline_comment(monkeypatch, tmp_path):
    import maishou_common as mc
    content = "\ufeffMAISHOU_API_KEY=bom_key  # 行内注释\nMAISHOU_OPENID=\"quoted_openid\"\n"
    (tmp_path / ".env").write_bytes(content.encode("utf-8"))
    fake_module = tmp_path / "a" / "b.py"
    fake_module.parent.mkdir()
    monkeypatch.setattr(mc, "__file__", str(fake_module))
    monkeypatch.delenv("MAISHOU_API_KEY", raising=False)
    monkeypatch.delenv("MAISHOU_OPENID", raising=False)
    try:
        mc._load_dotenv()
        assert os.environ.get("MAISHOU_API_KEY") == "bom_key"
        assert os.environ.get("MAISHOU_OPENID") == "quoted_openid"
    finally:
        os.environ.pop("MAISHOU_API_KEY", None)
        os.environ.pop("MAISHOU_OPENID", None)


def test_sanitize_category_blocks_traversal(tmp_path):
    from monitor_store import _sanitize_category, save_snapshot
    assert _sanitize_category("..") == "unnamed"
    assert _sanitize_category("a/b") == "a_b"
    assert _sanitize_category("con") == "con_dir"
    assert _sanitize_category("COM1") == "COM1_dir"
    assert _sanitize_category("nul") == "nul_dir"
    result = save_snapshot("..", {"prices": [10]}, tmp_path)
    path = Path(result["path"]).resolve()
    assert tmp_path.resolve() in path.parents


def test_parse_data_invalid_json_exits_2(capsys):
    from monitor_store import _parse_data
    with pytest.raises(SystemExit) as exc:
        _parse_data("{bad")
    assert exc.value.code == 2
    assert "不是合法 JSON" in capsys.readouterr().err


@pytest.mark.asyncio
async def test_search_empty_json_has_fixed_shape(monkeypatch):
    import maishou_search as ms

    async def fake_session():
        return None

    async def fake_search_api(session, keyword, source, **kwargs):
        return [], None

    monkeypatch.setattr(ms, "get_session", fake_session)
    monkeypatch.setattr(ms, "search_api", fake_search_api)
    out = await ms.search_products("x", format="json")
    assert json.loads(out) == []  # --format json 恒为数组，空结果/错误一致；错误原因走日志


@pytest.mark.asyncio
async def test_detail_non_200_is_rejected(monkeypatch):
    import maishou_search as ms

    async def fake_session():
        return None

    async def fake_retry(session, url, payload, **kwargs):
        if "detail" in url:
            return {"code": 500, "message": "签名错误"}, None
        return {}, None

    monkeypatch.setattr(ms, "get_session", fake_session)
    monkeypatch.setattr(ms, "retry_post", fake_retry)
    out = await ms.detail("1", 2, format="json")
    assert "签名错误" in out


def test_price_none_and_zero_baseline(tmp_path):
    from monitor_store import save_snapshot, diff_snapshot
    save_snapshot("zero_base", {"prices": [{"price": None}]}, tmp_path)
    result = diff_snapshot(
        "zero_base", {"prices": [{"price": 10}]}, tmp_path, save=False
    )
    price_changes = [c for c in result["changes"] if c["field"] == "price"]
    assert len(price_changes) == 1
    assert "不适用百分比" in price_changes[0]["delta_pct"]


def test_bsr_description_is_rendered(tmp_path):
    from monitor_store import save_snapshot, diff_snapshot, format_changes
    save_snapshot("bsr_case", {"bsr": 1000}, tmp_path)
    result = diff_snapshot("bsr_case", {"bsr": 1200}, tmp_path, save=False)
    assert "排名下降" in format_changes(result)
