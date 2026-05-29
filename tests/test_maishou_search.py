"""maishou_search.py 单元测试 — detail() + search_products() 函数各种场景"""
import pytest
from unittest.mock import patch, AsyncMock

from maishou_search import detail, search_products


_MOCK_ITEMS = [
    {"goodsId": "1001", "sourceType": 2, "title": "蓝牙耳机 Pro", "shopName": "数码旗舰店",
     "originalPrice": "299.00", "actualPrice": "199.00", "couponPrice": "189.00",
     "commission": "10.00", "monthSales": "5000+", "picUrl": "http://x.com/1.jpg"},
    {"goodsId": "1002", "sourceType": 2, "title": "无线充电器", "shopName": "配件专营",
     "originalPrice": "99.00", "actualPrice": "79.00", "couponPrice": None,
     "commission": "5.00", "monthSales": "1200+", "picUrl": "http://x.com/2.jpg"},
    {"goodsId": "1003", "sourceType": 2, "title": "USB-C 数据线", "shopName": "线材之家",
     "originalPrice": "39.90", "actualPrice": "29.90", "couponPrice": "24.90",
     "commission": "2.00", "monthSales": "8000+", "picUrl": "http://x.com/3.jpg"},
]


class TestDetail:
    """detail() — 商品详情获取"""

    @pytest.mark.asyncio
    async def test_full_success(self):
        """两个 API 都正常返回"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.retry_post", new=AsyncMock()) as mock_rp:
                mock_rp.side_effect = [
                    ({"data": {"title": "蓝牙耳机 Pro", "price": "199"}}, None),
                    ({"data": {"appUrl": "https://x.com/item/123", "kl": "￥ABC123"}}, None),
                ]
                result = await detail("123", 2)
                assert "蓝牙耳机 Pro" in result
                assert mock_rp.call_count == 2

    @pytest.mark.asyncio
    async def test_detail_api_fails(self):
        """第一步 DETAIL_URL 失败（重试后仍失败）"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.retry_post", new=AsyncMock()) as mock_rp:
                mock_rp.return_value = ({}, "请求失败（已重试）: timeout")
                result = await detail("123", 2)
                assert result.startswith("❌")
                assert "请求失败" in result
                assert mock_rp.call_count == 1  # 第一次就返回错误，不再调第二次

    @pytest.mark.asyncio
    async def test_target_url_fails_non_fatal(self):
        """TARGET_URL 失败不应阻断，仍返回部分数据"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.retry_post", new=AsyncMock()) as mock_rp:
                mock_rp.side_effect = [
                    ({"data": {"title": "测试商品"}}, None),
                    ({}, "获取分享链接失败"),
                ]
                result = await detail("123", 2)
                assert "测试商品" in result
                # 不应包含 ❌ 错误（非致命）
                assert not result.startswith("❌")

    @pytest.mark.asyncio
    async def test_field_extraction(self):
        """字段提取正确性：购买链接、复制口令"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.retry_post", new=AsyncMock()) as mock_rp:
                mock_rp.side_effect = [
                    ({"data": {"title": "test item"}}, None),
                    ({"data": {"appUrl": "tb.cn/abc", "kl": "copy-me"}}, None),
                ]
                result = await detail("456", 1)
                assert "tb.cn/abc" in result
                assert "copy-me" in result

    @pytest.mark.asyncio
    async def test_yaml_format_default(self):
        """默认输出 YAML 格式"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.retry_post", new=AsyncMock()) as mock_rp:
                mock_rp.side_effect = [
                    ({"data": {"title": "yaml test"}}, None),
                    ({"data": {}}, None),
                ]
                result = await detail("789", 1)
                assert "商品标题" in result  # YAML 有中文 key

    @pytest.mark.asyncio
    async def test_json_format(self):
        """--format json 输出 JSON"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.retry_post", new=AsyncMock()) as mock_rp:
                mock_rp.side_effect = [
                    ({"data": {"title": "json test"}}, None),
                    ({"data": {}}, None),
                ]
                result = await detail("111", 1, format="json")
                assert result.startswith("{")
                assert "json test" in result


class TestSearchProducts:
    """search_products() — 商品搜索"""

    @pytest.mark.asyncio
    async def test_csv_format(self):
        """CSV 格式输出正确性"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.search_api", new=AsyncMock()) as mock_api:
                mock_api.return_value = (_MOCK_ITEMS, None)
                result = await search_products("蓝牙", format="csv")
                assert "goodsId" in result
                assert "蓝牙耳机 Pro" in result
                assert "无线充电器" in result

    @pytest.mark.asyncio
    async def test_table_format(self):
        """Table 格式输出正确性（含 CJK 对齐）"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.search_api", new=AsyncMock()) as mock_api:
                mock_api.return_value = (_MOCK_ITEMS, None)
                result = await search_products("蓝牙", format="table")
                assert "蓝牙耳机 Pro" in result
                assert "199" in result  # actualPrice
                assert "数码旗舰店" in result

    @pytest.mark.asyncio
    async def test_json_format(self):
        """JSON 格式输出字段完整性"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.search_api", new=AsyncMock()) as mock_api:
                mock_api.return_value = (_MOCK_ITEMS, None)
                result = await search_products("蓝牙", format="json")
                assert result.startswith("[")
                assert "goodsId" in result
                assert "蓝牙耳机 Pro" in result

    @pytest.mark.asyncio
    async def test_empty_result(self):
        """空结果处理"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.search_api", new=AsyncMock()) as mock_api:
                mock_api.return_value = ([], None)
                result = await search_products("不存在的商品", format="csv")
                assert "查询结果为空" in result or result == "未找到结果"

    @pytest.mark.asyncio
    async def test_empty_result_json(self):
        """空结果 JSON 格式"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.search_api", new=AsyncMock()) as mock_api:
                mock_api.return_value = ([], None)
                result = await search_products("不存在", format="json")
                assert "error" in result

    @pytest.mark.asyncio
    async def test_api_error(self):
        """API 错误处理"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.search_api", new=AsyncMock()) as mock_api:
                mock_api.return_value = ([], "网络超时")
                result = await search_products("蓝牙", format="csv")
                assert "网络超时" in result or "❌" in result

    @pytest.mark.asyncio
    async def test_limit_truncation(self):
        """limit 截断"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search.search_api", new=AsyncMock()) as mock_api:
                mock_api.return_value = (_MOCK_ITEMS, None)
                result = await search_products("蓝牙", limit=1, format="json")
                data = __import__("json").loads(result)
                assert len(data) == 1
                assert data[0]["goodsId"] == "1001"
