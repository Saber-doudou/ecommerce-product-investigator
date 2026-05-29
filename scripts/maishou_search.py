# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp", "PyYAML"]
# ///
"""
maishou_search.py - 国内电商全网比价脚本
基于买手 88 API (appapi.maishou88.com) 查询国内平台商品价格、店铺、销量

使用方法:
    python maishou_search.py search --source=0 --keyword='电脑机箱'
    python maishou_search.py search --source=2 --keyword='电脑机箱' --limit 10 --format json
    python maishou_search.py detail --source=2 --id='100012345678'

参数说明:
    search  : 搜索商品
      --keyword  : 搜索关键词（必填）
      --source   : 平台 (0=全部 1=淘宝 2=京东 3=拼多多 4=苏宁 5=唯品会 6=考拉 7=抖音 8=快手 10=1688)
      --page     : 分页 (默认 1)
      --limit    : 返回数量限制 (默认 0=不限)
      --format   : 输出格式 (csv/table/json, 默认 csv)
    detail  : 获取商品详情
      --id       : 商品ID (goodsId)
      --source   : 平台编号 (同上)
      --format   : 输出格式 (yaml/json, 默认 yaml)
"""
import io
import csv
import json
import yaml
import asyncio
import logging
import aiohttp
import argparse

logger = logging.getLogger(__name__)

from maishou_common import (
    SEARCH_URL, DETAIL_URL, TARGET_URL,
    SOURCE_MAP, TIMEOUT,
    get_invite_code, get_openid, get_headers_app,
    get_session, close_session, check_env, format_table,
    search_api, retry_post,
)


async def search_products(keyword: str, source: int = 0, **kwargs) -> str:
    """搜索商品，返回格式化的结果字符串"""
    session = await get_session()
    items, error = await search_api(
        session, keyword, source,
        page=kwargs.get("page", 1),
        limit=kwargs.get("limit", 0),
    )

    if error:
        fmt = kwargs.get("format", "csv")
        return json.dumps({"error": error}, ensure_ascii=False) if fmt == "json" else f"❌ {error}"

    if not items:
        msg = "查询结果为空"
        return json.dumps({"error": msg}, ensure_ascii=False) if kwargs.get("format") == "json" else f"❌ {msg}"

    rows = [
        {
            "idx": i,
            "goodsId": v.get("goodsId"),
            "source": v.get("sourceType"),
            "title": v.get("title"),
            "shopName": v.get("shopName"),
            "originalPrice": v.get("originalPrice"),
            "actualPrice": v.get("actualPrice"),
            "couponPrice": v.get("couponPrice"),
            "commission": v.get("commission"),
            "monthSales": v.get("monthSales"),
            "picUrl": v.get("picUrl"),
        }
        for i, v in enumerate(items, 1)
    ]

    limit = kwargs.get("limit", 0)
    if limit > 0:
        rows = rows[:limit]

    fmt = kwargs.get("format", "csv")
    if fmt == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2)
    elif fmt == "table":
        columns = {"#": 4, "商品名": 40, "价格": 10, "销量": 10, "店铺": 20}
        display_rows = []
        for r in rows:
            display_rows.append({
                "#": r["idx"],
                "商品名": r.get("title", ""),
                "价格": str(r.get("actualPrice") or r.get("originalPrice") or "?"),
                "销量": str(r.get("monthSales", "")),
                "店铺": (r.get("shopName") or ""),
            })
        return format_table(display_rows, columns)
    else:  # csv
        if not rows:
            return "未找到结果"
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for item in rows:
            writer.writerow(item)
        text = output.getvalue()
        output.close()
        return text


async def detail(id: str, source: int, **kwargs) -> str:
    """获取商品详情"""
    session = await get_session()

    params = {
        "goodsId": str(id),
        "sourceType": str(source),
        "inviteCode": get_invite_code(),
        "supplierCode": "",
        "activityId": "",
        "isShare": "1",
        "token": "",
    }

    # 第一步：获取商品详情
    data, error = await retry_post(
        session, DETAIL_URL,
        {**params, "keyword": "", "usageScene": 5},
    )
    if error:
        return f"❌ {error}"
    detail_data = (data.get("data") or {}) if isinstance(data, dict) else {}

    # 第二步：获取分享链接（非致命，失败只警告）
    data2, err2 = await retry_post(
        session, TARGET_URL,
        {**params, "isDirectDetail": 0},
    )
    info = (data2.get("data") or {}) if isinstance(data2, dict) else {}
    if err2:
        logger.warning("获取分享链接失败，部分数据可能缺失: %s", err2)
    elif not info and isinstance(data2, dict) and data2.get("message"):
        logger.warning("获取分享链接失败: %s", data2.get("message"))

    result = {
        "商品标题": detail_data.get("title", ""),
        "购买链接": info.get("appUrl") or info.get("schemaUrl"),
        "复制口令": info.get("kl"),
        "商品详情": detail_data,
    }

    fmt = kwargs.get("format", "yaml")
    if fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    return yaml.dump(result, allow_unicode=True, sort_keys=False)


async def main():
    for warning in check_env():
        logger.warning(warning)
    if not get_invite_code():
        logger.warning("MAISHOU_API_KEY 未设置，detail 模式将无法正常工作")

    try:
        parser = argparse.ArgumentParser(
            description="国内电商全网比价（基于买手88 API）"
        )
        parsers = parser.add_subparsers()

        search_parser = parsers.add_parser("search")
        search_parser.add_argument("--keyword", required=True, help="搜索关键词")
        search_parser.add_argument(
            "--source", type=int, default=0,
            help="平台 (0=全部 1=淘宝 2=京东 3=拼多多 4=苏宁 5=唯品会 6=考拉 7=抖音 8=快手 10=1688)"
        )
        search_parser.add_argument("--page", type=int, default=1, help="分页")
        search_parser.add_argument("--limit", type=int, default=0, help="返回结果数量限制 (默认 0=不限)")
        search_parser.add_argument(
            "--format", choices=["csv", "table", "json"], default="csv",
            help="输出格式 (默认 csv)"
        )
        search_parser.add_argument("--output", help="输出文件路径 (可选)")
        search_parser.set_defaults(func=search_products)

        detail_parser = parsers.add_parser("detail")
        detail_parser.add_argument("--id", required=True, help="商品ID (goodsId)")
        detail_parser.add_argument(
            "--source", type=int, default=1,
            help="平台 (1=淘宝 2=京东 3=拼多多 4=苏宁 5=唯品会 6=考拉 7=抖音 8=快手 10=1688)"
        )
        detail_parser.add_argument(
            "--format", choices=["yaml", "json"], default="yaml",
            help="输出格式 (默认 yaml)"
        )
        detail_parser.add_argument("--output", help="输出文件路径 (可选)")
        detail_parser.set_defaults(func=detail)

        args = parser.parse_args()
        if hasattr(args, "func"):
            kwargs = {k: v for k, v in vars(args).items() if k not in ("func", "output")}
            output_text = str(await args.func(**kwargs))
            print(output_text)
            if getattr(args, "output", None):
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output_text)
                print(f"\n📁 结果已保存到: {args.output}")
        else:
            parser.print_help()
    finally:
        await close_session()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    asyncio.run(main())
