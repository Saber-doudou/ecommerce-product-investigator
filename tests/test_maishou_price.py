# test_maishou_price.py — 跨境采购比价引擎单元测试
# 对应审查报告 P1-4: maishou_price.py 零测试覆盖
import pytest
import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

# conftest.py 已统一 sys.path


# ── format_csv 测试 ──

class TestFormatCsv:
    """format_csv 纯函数测试（不依赖外部服务）"""

    def test_normal_data(self):
        """正常数据输出 CSV 格式"""
        results = [
            {"title": "手机支架A", "price": "12.99", "platform": "淘宝", "shop": "店铺1", "sales": "1000", "url": ""},
            {"title": "手机支架B", "price": "9.99", "platform": "拼多多", "shop": "店铺2", "sales": "500", "url": ""},
        ]
        from maishou_price import format_csv
        output = format_csv(results)
        assert "title" in output  # CSV 有表头
        assert "手机支架A" in output
        assert "手机支架B" in output
        assert "淘宝" in output
        assert "拼多多" in output

    def test_empty_results(self):
        """空结果返回提示"""
        from maishou_price import format_csv
        output = format_csv([])
        assert output == "未找到结果"

    def test_partial_fields(self):
        """部分字段缺失时仍可正常输出"""
        results = [
            {"title": "测试商品", "price": "", "platform": "京东", "shop": "", "sales": "", "url": ""},
        ]
        from maishou_price import format_csv
        output = format_csv(results)
        assert "测试商品" in output

    def test_custom_output_buffer(self):
        """自定义 buffer 模式不返回字符串"""
        results = [
            {"title": "测试", "price": "1.0", "platform": "1688", "shop": "", "sales": "10", "url": ""},
        ]
        from maishou_price import format_csv
        buf = io.StringIO()
        ret = format_csv(results, output=buf)
        assert ret == ""
        assert "测试" in buf.getvalue()


# ── search_single_source 测试 ──

@pytest.mark.asyncio
class TestSearchSingleSource:
    """search_single_source 异步函数测试"""

    @pytest.fixture
    def mock_session(self):
        """创建 mock aiohttp session"""
        return MagicMock()

    @patch("maishou_price.search_api")
    async def test_success(self, mock_search_api, mock_session):
        """正常返回商品列表"""
        mock_search_api.return_value = (
            [
                {"title": "商品A", "actualPrice": "12.99", "monthSales": "100", "shopName": "店A"},
                {"title": "商品B", "actualPrice": "9.99", "monthSales": "200", "shopName": "店B"},
            ],
            None,  # no error
        )
        from maishou_price import search_single_source
        results = await search_single_source(mock_session, "测试", src=1, limit=10)
        assert len(results) == 2
        assert results[0]["title"] == "商品A"
        assert results[0]["price"] == "12.99"
        assert results[0]["platform"] == "淘宝"
        assert results[0]["sales"] == "100"
        assert results[0]["shop"] == "店A"

    @patch("maishou_price.search_api")
    async def test_api_error(self, mock_search_api, mock_session):
        """API 返回错误时返回空列表"""
        mock_search_api.return_value = ([], "API 内部错误")
        from maishou_price import search_single_source
        results = await search_single_source(mock_session, "测试", src=1, limit=10)
        assert results == []

    @patch("maishou_price.search_api")
    async def test_empty_result(self, mock_search_api, mock_session):
        """API 正常但无商品"""
        mock_search_api.return_value = ([], None)
        from maishou_price import search_single_source
        results = await search_single_source(mock_session, "罕见关键词", src=1, limit=10)
        assert results == []

    @patch("maishou_price.search_api")
    async def test_original_price_fallback(self, mock_search_api, mock_session):
        """actualPrice 为空时回退到 originalPrice"""
        mock_search_api.return_value = (
            [{"title": "商品", "originalPrice": "19.99", "monthSales": "", "shopName": ""}],
            None,
        )
        from maishou_price import search_single_source
        results = await search_single_source(mock_session, "测试", src=2, limit=10)
        assert results[0]["price"] == "19.99"

    @patch("maishou_price.search_api")
    async def test_unknown_source_map(self, mock_search_api, mock_session):
        """未注册的 platform 编号也能处理"""
        mock_search_api.return_value = (
            [{"title": "商品", "actualPrice": "5.0", "monthSales": "", "shopName": ""}],
            None,
        )
        from maishou_price import search_single_source
        results = await search_single_source(mock_session, "测试", src=99, limit=10)
        assert results[0]["platform"] == "平台99"


# ── search_price 测试 ──

@pytest.mark.asyncio
class TestSearchPrice:
    """search_price 异步函数测试"""

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @patch("maishou_price.get_session")
    @patch("maishou_price.search_single_source")
    async def test_single_source(self, mock_single, mock_get_session, mock_session):
        """source > 0 时只查询单个平台"""
        mock_get_session.return_value = mock_session
        mock_single.return_value = [
            {"title": "商品", "price": "10", "platform": "京东", "url": "", "sales": "50", "shop": "京东店"},
        ]
        from maishou_price import search_price
        results = await search_price("测试", source=2, limit=10)
        assert len(results) == 1
        assert results[0]["platform"] == "京东"

    @patch("maishou_price.get_session")
    @patch("maishou_price.search_single_source")
    async def test_all_sources(self, mock_single, mock_get_session, mock_session):
        """source=0 时并发查询全部平台（4个）"""
        mock_get_session.return_value = mock_session

        async def mock_return(session, keyword, src, limit, page=1):
            return [{"title": f"商品-{src}", "price": "10", "platform": str(src),
                     "url": "", "sales": "10", "shop": f"店-{src}"}]

        mock_single.side_effect = mock_return
        from maishou_price import search_price
        results = await search_price("测试", source=0, limit=10)
        assert len(results) == 4  # 4 个平台各 1 条

    @patch("maishou_price.get_session")
    @patch("maishou_price.search_single_source")
    async def test_exception_handling(self, mock_single, mock_get_session, mock_session):
        """并发中某个平台抛异常不阻塞其他平台"""
        mock_get_session.return_value = mock_session

        async def mixed_return(session, keyword, src, limit, page=1):
            if src == 2:
                raise RuntimeError("模拟异常")
            return [{"title": f"商品-{src}", "price": "10", "platform": str(src),
                     "url": "", "sales": "10", "shop": f"店-{src}"}]

        mock_single.side_effect = mixed_return
        from maishou_price import search_price
        # source=0 时查询 4 个平台，京东(src=2)抛异常，其他 3 个正常
        results = await search_price("测试", source=0, limit=10)
        assert len(results) == 3  # 京东异常被捕获，其余 3 平台正常
