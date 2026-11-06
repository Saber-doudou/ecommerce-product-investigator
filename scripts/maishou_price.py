# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""
maishou_price.py - 跨境选品采购价查询脚本
使用买手 API (maishou88.com) 查询国内平台价格，为跨境卖家提供采购成本参考

使用方法:
    python maishou_price.py "手机支架" --source 0 --format table
    python maishou_price.py "蓝牙耳机" --source 1 --limit 10 --format csv

参数说明:
    keyword   : 搜索关键词
    --source  : 平台选择 (0=综合 1=淘宝 2=京东 3=拼多多 10=1688)
    --limit   : 每个平台返回的结果数量 (默认 10)
    --page    : 分页页码 (默认 1)
    --format   : 输出格式 (table/json/csv, 默认 table)
    --output   : 输出文件路径 (可选，不指定则输出到终端)
"""

import io
import csv
import json
import asyncio
import logging
import sys
import aiohttp
import argparse

logger = logging.getLogger(__name__)

from maishou_common import (
    SOURCE_MAP,
    get_session, close_session, check_env, format_table,
    search_api, first_present,
)

from text_utils import display_width

# 全部平台失败时置为本轮错误原因；部分失败不阻断（退出码仍为 0）。
_LAST_ERROR = None


async def search_single_source(
    session: aiohttp.ClientSession,
    keyword: str, src: int, limit: int, page: int = 1,
    errors: list[str] | None = None,
) -> list[dict]:
    """搜索单个平台（errors 由调用方传入，避免模块级状态跨调用残留）"""
    items, error = await search_api(session, keyword, src, page=page, limit=limit)
    if error:
        if errors is not None:
            errors.append(f"{SOURCE_MAP.get(src, src)}: {error}")
        logger.warning("平台 %s 查询失败: %s", SOURCE_MAP.get(src, src), error)
        return []

    return [
        {
            "title": item.get("title") or "",
            "price": first_present(item.get("actualPrice"), item.get("originalPrice")),
            "platform": SOURCE_MAP.get(src, f"平台{src}"),
            "url": "",  # API 不直接返回购买链接，需通过 detail 接口获取
            "sales": item.get("monthSales"),
            "shop": item.get("shopName") or "",
        }
        for item in items[:limit]
    ]


async def search_price(keyword: str, source: int = 0, limit: int = 10, page: int = 1) -> list[dict]:
    """
    使用买手 API 搜索商品（并发查询多平台）

    Args:
        keyword: 搜索关键词
        source: 平台 (0=综合 1=淘宝 2=京东 3=拼多多 10=1688)
        limit: 每个平台返回的结果数量
        page: 分页页码 (默认 1)

    Returns:
        商品列表 [{"title", "price", "platform", "url", ...}]
    """
    global _LAST_ERROR
    _LAST_ERROR = None
    errors: list[str] = []
    session = await get_session()

    if source == 0:
        sources = [1, 2, 3, 10]  # 淘宝、京东、拼多多、1688
    else:
        sources = [source]

    # 并发查询所有平台
    tasks = [search_single_source(session, keyword, src, limit, page, errors) for src in sources]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    # 展平结果
    results = []
    for item in results_nested:
        if isinstance(item, list):
            results.extend(item)
        elif isinstance(item, Exception):
            errors.append(str(item))
            logger.warning("并发查询异常: %s", item)

    if len(errors) >= len(sources):
        _LAST_ERROR = "; ".join(errors)
        logger.error("全部平台查询失败: %s", _LAST_ERROR)

    return results


def format_csv(results: list[dict]) -> str:
    """格式化 CSV 输出，返回 CSV 文本（\n 行终止符，避免 Windows 隔行空行）"""
    if not results:
        return "未找到结果"

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["title", "price", "platform", "shop", "sales", "url"], lineterminator="\n")
    writer.writeheader()
    for r in results:
        writer.writerow(r)

    return buf.getvalue()


async def main():
    global _LAST_ERROR
    _LAST_ERROR = None
    for warning in check_env():
        logger.warning(warning)

    try:
        parser = argparse.ArgumentParser(description="跨境选品采购价查询")
        parser.add_argument("keyword", help="搜索关键词")
        parser.add_argument("--source", type=int, default=0, help="平台 (0=综合 1=淘宝 2=京东 3=拼多多 10=1688)")
        parser.add_argument("--limit", type=int, default=10, help="每个平台返回的结果数量（--source 0 时为每平台上限）")
        parser.add_argument("--page", type=int, default=1, help="分页页码")
        parser.add_argument("--format", choices=["table", "json", "csv"], default="table", help="输出格式")
        parser.add_argument("--output", help="输出文件路径 (可选)")
        args = parser.parse_args()

        print(f"🔍 搜索: {args.keyword}  (平台={args.source}, 数量={args.limit}, 分页={args.page})", file=sys.stderr)
        results = await search_price(args.keyword, args.source, args.limit, args.page)
        if _LAST_ERROR:
            print(f"❌ 查询失败: {_LAST_ERROR}", file=sys.stderr)
        else:
            print(f"✅ 找到 {len(results)} 条结果\n", file=sys.stderr)

        # 表格输出使用公共 format_table
        def _fmt_table(res):
            if not res:
                return "未找到结果"
            title_width = max(20, max(display_width(r.get("title") or "") for r in res))
            columns = {"序号": 4, "商品名": title_width, "价格": 10, "平台": 8, "销量": 10}
            display_rows = [
                {"序号": i, "商品名": r.get("title") or "", "价格": r["price"], "平台": r["platform"], "销量": r.get("sales")}
                for i, r in enumerate(res, 1)
            ]
            return format_table(display_rows, columns)

        if args.format == "table":
            print(_fmt_table(results))
        elif args.format == "json":
            output = json.dumps(results, ensure_ascii=False, indent=2)
            print(output)
        elif args.format == "csv":
            text = format_csv(results)
            # 只保证一个结尾换行，避免 CSV 尾部多出空行
            sys.stdout.write(text if text.endswith("\n") else text + "\n")

        # 写入文件
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                if args.format == "json":
                    json.dump(results, f, ensure_ascii=False, indent=2)
                elif args.format == "csv":
                    f.write(format_csv(results))
                else:
                    f.write(_fmt_table(results))
            print(f"\n📁 结果已保存到: {args.output}", file=sys.stderr)
    finally:
        await close_session()
    if _LAST_ERROR:
        sys.exit(2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    asyncio.run(main())
