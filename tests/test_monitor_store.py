"""monitor_store.py 单元测试 — 监测数据持久化功能"""
import json
import tempfile
import os
from pathlib import Path

import pytest

from monitor_store import (
    save_snapshot,
    load_latest,
    diff_snapshot,
    _sanitize_category,
    list_categories,
    format_changes,
)


@pytest.fixture
def temp_store():
    """创建临时存储目录"""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestSaveAndLoad:
    """save_snapshot + load_latest 读写正确性"""

    def test_save_and_load_roundtrip(self, temp_store):
        data = {"prices": [{"price": 100}, {"price": 200}], "bsr": 1234}
        result = save_snapshot("电脑机箱", data, store_root=temp_store)
        assert result["status"] == "ok"
        assert result["date"] is not None
        assert os.path.exists(result["path"])

        loaded = load_latest("电脑机箱", store_root=temp_store)
        assert loaded is not None
        assert loaded["category"] == "电脑机箱"
        assert loaded["data"] == data

    def test_load_nonexistent_category(self, temp_store):
        result = load_latest("nonexistent", store_root=temp_store)
        assert result is None

    def test_save_overwrites_same_day(self, temp_store):
        """同一天多次保存，load_latest 返回最新的"""
        data1 = {"bsr": 100}
        data2 = {"bsr": 200}
        save_snapshot("test_cat", data1, store_root=temp_store)
        save_snapshot("test_cat", data2, store_root=temp_store)

        loaded = load_latest("test_cat", store_root=temp_store)
        assert loaded["data"] == data2


class TestDiffSnapshot:
    """diff_snapshot 对比逻辑"""

    def test_first_run(self, temp_store):
        data = {"prices": [{"price": 100}], "bsr": 500}
        result = diff_snapshot("test_cat", data, store_root=temp_store)
        assert result["is_first"] is True
        assert result["previous_date"] is None
        assert any(c["field"] == "_first_run" for c in result["changes"])

    def test_no_change(self, temp_store):
        data = {"prices": [{"price": 100}], "bsr": 500}
        save_snapshot("test_cat", data, store_root=temp_store)
        result = diff_snapshot("test_cat", data, store_root=temp_store, save=False)
        assert result["is_first"] is False
        assert any(c["field"] == "_no_change" for c in result["changes"])

    def test_price_change(self, temp_store):
        baseline = {"prices": [{"price": 100}, {"price": 200}]}
        current = {"prices": [{"price": 120}, {"price": 220}]}
        save_snapshot("test_cat", baseline, store_root=temp_store)
        result = diff_snapshot("test_cat", current, store_root=temp_store, save=False)
        price_changes = [c for c in result["changes"] if c["field"] == "price"]
        assert len(price_changes) == 1
        assert price_changes[0]["previous"] == 150.0  # avg of 100,200
        assert price_changes[0]["current"] == 170.0   # avg of 120,220

    def test_price_format_flat_list(self, temp_store):
        """兼容 [100, 200] 格式的价格列表"""
        baseline = {"prices": [100, 200]}
        current = {"prices": [120, 220]}
        save_snapshot("test_cat", baseline, store_root=temp_store)
        result = diff_snapshot("test_cat", current, store_root=temp_store, save=False)
        price_changes = [c for c in result["changes"] if c["field"] == "price"]
        assert len(price_changes) == 1
        assert price_changes[0]["previous"] == 150.0
        assert price_changes[0]["current"] == 170.0

    def test_bsr_change(self, temp_store):
        baseline = {"bsr": 500}
        current = {"bsr": 300}
        save_snapshot("test_cat", baseline, store_root=temp_store)
        result = diff_snapshot("test_cat", current, store_root=temp_store, save=False)
        bsr_changes = [c for c in result["changes"] if c["field"] == "bsr"]
        assert len(bsr_changes) == 1
        assert "排名上升" in bsr_changes[0]["description"]

    def test_review_count_change(self, temp_store):
        baseline = {"review_count": 100}
        current = {"review_count": 150}
        save_snapshot("test_cat", baseline, store_root=temp_store)
        result = diff_snapshot("test_cat", current, store_root=temp_store, save=False)
        rev_changes = [c for c in result["changes"] if c["field"] == "review_count"]
        assert len(rev_changes) == 1
        assert rev_changes[0]["delta"] == 50

    def test_competitor_count_change(self, temp_store):
        baseline = {"competitor_count": 10}
        current = {"competitor_count": 15}
        save_snapshot("test_cat", baseline, store_root=temp_store)
        result = diff_snapshot("test_cat", current, store_root=temp_store, save=False)
        comp_changes = [c for c in result["changes"] if c["field"] == "competitor_count"]
        assert len(comp_changes) == 1

    def test_custom_field_change(self, temp_store):
        baseline = {"conversion_rate": 0.05}
        current = {"conversion_rate": 0.07}
        save_snapshot("test_cat", baseline, store_root=temp_store)
        result = diff_snapshot("test_cat", current, store_root=temp_store, save=False)
        cr_changes = [c for c in result["changes"] if c["field"] == "conversion_rate"]
        assert len(cr_changes) == 1
        assert cr_changes[0]["previous"] == 0.05
        assert cr_changes[0]["current"] == 0.07

    def test_field_added(self, temp_store):
        """新增字段应被检测"""
        baseline = {"bsr": 500}
        current = {"bsr": 500, "new_field": "hello"}
        save_snapshot("test_cat", baseline, store_root=temp_store)
        result = diff_snapshot("test_cat", current, store_root=temp_store, save=False)
        added = [c for c in result["changes"] if c["delta"] == "新增"]
        assert len(added) == 1
        assert added[0]["field"] == "new_field"
        assert added[0]["current"] == "hello"

    def test_field_removed(self, temp_store):
        """移除字段应被检测"""
        baseline = {"bsr": 500, "old_field": "bye"}
        current = {"bsr": 500}
        save_snapshot("test_cat", baseline, store_root=temp_store)
        result = diff_snapshot("test_cat", current, store_root=temp_store, save=False)
        removed = [c for c in result["changes"] if c["delta"] == "移除"]
        assert len(removed) == 1
        assert removed[0]["field"] == "old_field"
        assert removed[0]["previous"] == "bye"

    def test_save_false_does_not_persist(self, temp_store):
        """save=False 时不保存当前快照"""
        data = {"bsr": 500}
        save_snapshot("test_cat", data, store_root=temp_store)
        new_data = {"bsr": 600}
        diff_snapshot("test_cat", new_data, store_root=temp_store, save=False)
        loaded = load_latest("test_cat", store_root=temp_store)
        # 应仍是 baseline
        assert loaded["data"]["bsr"] == 500


class TestSanitizeCategory:
    """_sanitize_category 路径安全"""

    def test_normal_category(self):
        assert _sanitize_category("电脑机箱") == "电脑机箱"

    def test_spaces_to_underscores(self):
        assert _sanitize_category("gaming case") == "gaming_case"

    def test_slashes_replaced(self):
        assert _sanitize_category("a/b/c") == "a_b_c"
        assert _sanitize_category("a\\b") == "a_b"

    def test_trailing_spaces_stripped(self):
        assert _sanitize_category("  hello  ") == "hello"


class TestListCategories:
    """list_categories 功能"""

    def test_empty_store(self, temp_store):
        assert list_categories(store_root=temp_store) == []

    def test_with_categories(self, temp_store):
        save_snapshot("cat_a", {"bsr": 1}, store_root=temp_store)
        save_snapshot("cat_b", {"bsr": 2}, store_root=temp_store)
        cats = list_categories(store_root=temp_store)
        assert sorted(cats) == ["cat_a", "cat_b"]


class TestFormatChanges:
    """format_changes 格式化输出"""

    def test_first_run_message(self):
        result = {"category": "test", "is_first": True, "changes": []}
        output = format_changes(result)
        assert "首次监测" in output

    def test_no_change_message(self):
        result = {
            "category": "test", "is_first": False, "previous_date": "2026-05-28",
            "changes": [{"field": "_no_change", "message": "各项数据无明显变化"}],
        }
        output = format_changes(result)
        assert "无明显变化" in output

    def test_field_added_message(self):
        result = {
            "category": "test", "is_first": False, "previous_date": "2026-05-28",
            "changes": [{"field": "new_metric", "current": 42, "delta": "新增"}],
        }
        output = format_changes(result)
        assert "新字段" in output

    def test_field_removed_message(self):
        result = {
            "category": "test", "is_first": False, "previous_date": "2026-05-28",
            "changes": [{"field": "old_metric", "previous": 99, "delta": "移除"}],
        }
        output = format_changes(result)
        assert "已移除" in output

    def test_with_price_change(self):
        result = {
            "category": "test", "is_first": False, "previous_date": "2026-05-28",
            "changes": [{
                "field": "price", "previous": 100.0, "current": 120.0,
                "delta": 20.0, "delta_pct": "↑ 20.0%",
            }],
        }
        output = format_changes(result)
        assert "120.0" in output
        assert "↑" in output
