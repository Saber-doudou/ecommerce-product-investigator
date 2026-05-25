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
    --limit   : 返回结果数量 (默认 10)
    --page    : 分页页码 (默认 1)
    --format   : 输出格式 (table/json/csv, 默认 table)
    --output   : 输出文件路径 (可选，不指定则输出到终端)
"""

import io
import csv
import json
import asyncio
import logging
import aiohttp
import argparse

logger = logging.getLogger(__name__)

from maishou_common import (
    SEARCH_URL, SOURCE_MAP, TIMEOUT,
    get_openid, get_headers_app,
    get_session, close_session, check_env, format_table,
    search_api,
)

from text_utils import display_width


async def search_single_source(
    session: aiohttp.ClientSession,
    keyword: str, src: int, limit: int, page: int = 1
) -> list[dict]:
    """搜索单个平台"""
    items, error = await search_api(session, keyword, src, page=page, limit=limit)
    if error:
        logger.warning("平台 %s 查询失败: %s", SOURCE_MAP.get(src, src), error)
        return []

    return [
        {
            "title": item.get("title", ""),
            "price": item.get("actualPrice") or item.get("originalPrice") or "",
            "platform": SOURCE_MAP.get(src, f"平台{src}"),
            "url": "",  # API 不直接返回购买链接，需通过 detail 接口获取
            "sales": item.get("monthSales", ""),
            "shop": item.get("shopName", ""),
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
    session = await get_session()

    if source == 0:
        sources = [1, 2, 3, 10]  # 淘宝、京东、拼多多、1688
    else:
        sources = [source]

    # 并发查询所有平台
    tasks = [search_single_source(session, keyword, src, limit, page) for src in sources]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    # 展平结果
    results = []
    for item in results_nested:
        if isinstance(item, list):
            results.extend(item)
        elif isinstance(item, Exception):
            logger.warning("并发查询异常: %s", item)

    return results


def format_csv(results: list[dict], output: io.StringIO | None = None) -> str:
    """格式化 CSV 输出"""
    if not results:
        return "未找到结果"

    buf = output or io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["title", "price", "platform", "shop", "sales", "url"])
    writer.writeheader()
    for r in results:
        writer.writerow(r)

    return buf.getvalue() if output is None else ""


async def main():
    for warning in check_env():
        logger.warning(warning)

    try:
        parser = argparse.ArgumentParser(description="跨境选品采购价查询")
        parser.add_argument("keyword", help="搜索关键词")
        parser.add_argument("--source", type=int, default=0, help="平台 (0=综合 1=淘宝 2=京东 3=拼多多 10=1688)")
        parser.add_argument("--limit", type=int, default=10, help="返回结果数量")
        parser.add_argument("--page", type=int, default=1, help="分页页码")
        parser.add_argument("--format", choices=["table", "json", "csv"], default="table", help="输出格式")
        parser.add_argument("--output", help="输出文件路径 (可选)")
        args = parser.parse_args()

        print(f"🔍 搜索: {args.keyword}  (平台={args.source}, 数量={args.limit}, 分页={args.page})")
        results = await search_price(args.keyword, args.source, args.limit, args.page)
        print(f"✅ 找到 {len(results)} 条结果\n")

        # 表格输出使用公共 format_table
        def _fmt_table(res):
            if not res:
                return "未找到结果"
            title_width = max(20, max(display_width(r["title"]) for r in res))
            columns = {"序号": 4, "商品名": title_width, "价格": 10, "平台": 8, "销量": 10}
            display_rows = [
                {"序号": i, "商品名": r["title"], "价格": r["price"], "平台": r["platform"], "销量": str(r.get("sales", ""))}
                for i, r in enumerate(res, 1)
            ]
            return format_table(display_rows, columns)

        if args.format == "table":
            print(_fmt_table(results))
        elif args.format == "json":
            output = json.dumps(results, ensure_ascii=False, indent=2)
            print(output)
        elif args.format == "csv":
            output = format_csv(results)
            print(output)

        # 写入文件
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                if args.format == "json":
                    json.dump(results, f, ensure_ascii=False, indent=2)
                elif args.format == "csv":
                    f.write(format_csv(results))
                else:
                    f.write(_fmt_table(results))
            print(f"\n📁 结果已保存到: {args.output}")
    finally:
        await close_session()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    asyncio.run(main())
