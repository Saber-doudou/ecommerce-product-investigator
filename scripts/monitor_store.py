# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
monitor_store.py - 电商选品监测数据持久化

支持按品类+日期保存快照、读取上次快照对比、输出增量变化。

使用方法:
    # 保存快照
    python monitor_store.py save --category "电脑机箱" --data '{"prices": [...], "bsr": 1234}'

    # 读取上次快照
    python monitor_store.py load --category "电脑机箱"

    # 对比增量变化
    python monitor_store.py diff --category "电脑机箱" --data '{"prices": [...], "bsr": 2345}'

    # 列出所有监测品类
    python monitor_store.py list

存储路径:
    默认 ~/.ecom-investigator/monitor/<category>/YYYY-MM-DD.json
    可通过 --store-dir 自定义
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_STORE_DIR = Path.home() / ".ecom-investigator" / "monitor"


def _sanitize_category(category: str) -> str:
    """将品类名转为安全的目录名"""
    return category.strip().replace("/", "_").replace("\\", "_").replace(" ", "_")


def _store_dir(store_root: Path, category: str) -> Path:
    return store_root / _sanitize_category(category)


def save_snapshot(category: str, data: dict, store_root: Path | None = None) -> dict:
    """保存当前快照。

    Args:
        category: 品类名
        data: 监测数据（dict，可包含任意字段）
        store_root: 存储根目录，默认 ~/.ecom-investigator/monitor/

    Returns:
        {"status": "ok", "path": str, "date": str}
    """
    root = store_root or DEFAULT_STORE_DIR
    cat_dir = _store_dir(root, category)
    cat_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    file_path = cat_dir / f"{today}.json"

    snapshot = {
        "category": category,
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    return {"status": "ok", "path": str(file_path), "date": today}


def load_latest(category: str, store_root: Path | None = None) -> dict | None:
    """读取最近一次快照。

    Args:
        category: 品类名
        store_root: 存储根目录

    Returns:
        dict 快照数据，无历史时返回 None
    """
    root = store_root or DEFAULT_STORE_DIR
    cat_dir = _store_dir(root, category)

    if not cat_dir.exists():
        return None

    snapshots = sorted(
        [f for f in cat_dir.glob("*.json") if not f.name.startswith(".")],
        reverse=True,
    )
    if not snapshots:
        return None

    with open(snapshots[0], encoding="utf-8") as f:
        return json.load(f)


def diff_snapshot(
    category: str,
    current_data: dict,
    store_root: Path | None = None,
    save: bool = True,
) -> dict:
    """对比上次快照，输出增量变化。

    Args:
        category: 品类名
        current_data: 当前数据
        store_root: 存储根目录
        save: 是否同时保存当前数据为新快照（默认 True）

    Returns:
        {"category": str, "previous_date": str|None, "changes": [...], "is_first": bool}
    """
    previous = load_latest(category, store_root)
    changes: list[dict] = []
    is_first = previous is None

    if save:
        save_result = save_snapshot(category, current_data, store_root)
    else:
        save_result = {}

    if is_first:
        return {
            "category": category,
            "previous_date": None,
            "is_first": True,
            "changes": [{"field": "_first_run", "message": "首次监测，无历史数据对比"}],
        }

    prev_data = previous.get("data", {})

    # 价格变化（如果 data 中有 prices 字段）
    if "prices" in current_data and "prices" in prev_data:
        prev_prices = prev_data["prices"]
        curr_prices = current_data["prices"]
        if isinstance(prev_prices, list) and isinstance(curr_prices, list):
            prev_avg = sum(p.get("price", 0) for p in prev_prices) / len(prev_prices) if prev_prices else 0
            curr_avg = sum(p.get("price", 0) for p in curr_prices) / len(curr_prices) if curr_prices else 0
            if curr_avg != prev_avg:
                diff_pct = (curr_avg - prev_avg) / prev_avg * 100 if prev_avg else 0
                direction = "↑" if diff_pct > 0 else "↓"
                changes.append({
                    "field": "price",
                    "previous": round(prev_avg, 2),
                    "current": round(curr_avg, 2),
                    "delta": round(curr_avg - prev_avg, 2),
                    "delta_pct": f"{direction} {abs(diff_pct):.1f}%",
                })

    # 竞品数量变化
    if "competitor_count" in current_data and "competitor_count" in prev_data:
        prev_count = prev_data["competitor_count"]
        curr_count = current_data["competitor_count"]
        if prev_count != curr_count:
            direction = "↑" if curr_count > prev_count else "↓"
            changes.append({
                "field": "competitor_count",
                "previous": prev_count,
                "current": curr_count,
                "delta": curr_count - prev_count,
                "delta_pct": f"{direction} {abs(curr_count - prev_count)}",
            })

    # 排行榜/BSR 变化
    if "bsr" in current_data and "bsr" in prev_data:
        prev_bsr = prev_data["bsr"]
        curr_bsr = current_data["bsr"]
        if prev_bsr != curr_bsr:
            direction = "↑" if curr_bsr > prev_bsr else "↓"  # BSR ↑ = 排名下降
            changes.append({
                "field": "bsr",
                "previous": prev_bsr,
                "current": curr_bsr,
                "delta": curr_bsr - prev_bsr,
                "description": f"排名{'下降' if curr_bsr > prev_bsr else '上升'} {direction} {abs(curr_bsr - prev_bsr)}",
            })

    # Review/评价数量变化
    if "review_count" in current_data and "review_count" in prev_data:
        prev_rev = prev_data["review_count"]
        curr_rev = current_data["review_count"]
        if prev_rev != curr_rev:
            changes.append({
                "field": "review_count",
                "previous": prev_rev,
                "current": curr_rev,
                "delta": curr_rev - prev_rev,
                "delta_pct": f"+{curr_rev - prev_rev}" if curr_rev > prev_rev else str(curr_rev - prev_rev),
            })

    # 通用字段对比：对 data 中所有标量字段进行对比
    for key in current_data:
        if key in ("prices", "competitor_count", "bsr", "review_count"):
            continue  # 已单独处理
        if key not in prev_data:
            continue
        curr_val = current_data[key]
        prev_val = prev_data[key]
        if isinstance(curr_val, (int, float, str)) and isinstance(prev_val, (int, float, str)):
            if curr_val != prev_val:
                try:
                    if isinstance(curr_val, (int, float)) and isinstance(prev_val, (int, float)):
                        delta = curr_val - prev_val
                        pct = delta / prev_val * 100 if prev_val else 0
                        changes.append({
                            "field": key,
                            "previous": prev_val,
                            "current": curr_val,
                            "delta": round(delta, 2),
                            "delta_pct": f"{'+' if delta > 0 else ''}{pct:.1f}%",
                        })
                    else:
                        changes.append({
                            "field": key,
                            "previous": prev_val,
                            "current": curr_val,
                            "delta": "changed",
                        })
                except (TypeError, ValueError):
                    pass

    if not changes:
        changes.append({"field": "_no_change", "message": "各项数据与上次相比无明显变化"})

    return {
        "category": category,
        "previous_date": previous.get("date"),
        "is_first": False,
        "changes": changes,
        "saved": save_result,
    }


def list_categories(store_root: Path | None = None) -> list[str]:
    """列出所有监测品类"""
    root = store_root or DEFAULT_STORE_DIR
    if not root.exists():
        return []
    return sorted(
        d.name for d in root.iterdir()
        if d.is_dir() and any(d.glob("*.json"))
    )


def format_changes(diff_result: dict) -> str:
    """将 diff 结果格式化为可读文本"""
    lines = []
    lines.append(f"\n📊 监测对比 — {diff_result['category']}")
    lines.append(f"{'─' * 50}")

    if diff_result.get("is_first"):
        lines.append("🆕 首次监测，已保存基准数据")
        return "\n".join(lines)

    prev_date = diff_result.get("previous_date", "?")
    lines.append(f"对比基准：{prev_date}")
    lines.append("")

    for change in diff_result.get("changes", []):
        field = change.get("field", "")
        if field == "_no_change":
            lines.append("✅ 各项数据与上次相比无明显变化")
        elif field == "_first_run":
            lines.append("🆕 首次监测，已保存基准数据")
        elif "delta_pct" in change:
            if "description" in change:
                lines.append(f"  {change['field']}: {change['description']}")
            else:
                lines.append(
                    f"  {change['field']}: {change['previous']} → {change['current']} "
                    f"({change['delta_pct']})"
                )
        else:
            lines.append(f"  {change['field']}: {change['previous']} → {change['current']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="电商选品监测数据持久化工具")
    subparsers = parser.add_subparsers(dest="command")

    # save
    save_parser = subparsers.add_parser("save", help="保存快照")
    save_parser.add_argument("--category", required=True, help="品类名")
    save_parser.add_argument("--data", required=True, help="监测数据（JSON 字符串）")
    save_parser.add_argument("--store-dir", help="存储根目录")

    # load
    load_parser = subparsers.add_parser("load", help="读取最近快照")
    load_parser.add_argument("--category", required=True, help="品类名")
    load_parser.add_argument("--store-dir", help="存储根目录")

    # diff
    diff_parser = subparsers.add_parser("diff", help="对比增量变化")
    diff_parser.add_argument("--category", required=True, help="品类名")
    diff_parser.add_argument("--data", required=True, help="当前数据（JSON 字符串）")
    diff_parser.add_argument("--store-dir", help="存储根目录")
    diff_parser.add_argument("--no-save", action="store_true", help="不保存当前数据")

    # list
    list_parser = subparsers.add_parser("list", help="列出所有监测品类")
    list_parser.add_argument("--store-dir", help="存储根目录")

    args = parser.parse_args()

    store_root = Path(args.store_dir) if getattr(args, "store_dir", None) else None

    if args.command == "save":
        data = json.loads(args.data)
        result = save_snapshot(args.category, data, store_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "load":
        result = load_latest(args.category, store_root)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "未找到历史快照"}, ensure_ascii=False))
            sys.exit(1)
    elif args.command == "diff":
        data = json.loads(args.data)
        result = diff_snapshot(args.category, data, store_root, save=not args.no_save)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()  # 空行分隔
        print(format_changes(result))
    elif args.command == "list":
        categories = list_categories(store_root)
        if categories:
            for c in categories:
                print(f"  📂 {c}")
        else:
            print("  (无监测记录)")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
