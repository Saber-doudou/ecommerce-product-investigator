"""maishou_search.py 单元测试 — detail() 函数各种场景"""
import pytest
from unittest.mock import patch, AsyncMock

from maishou_search import detail


class TestDetail:
    """detail() — 商品详情获取"""

    @pytest.mark.asyncio
    async def test_full_success(self):
        """两个 API 都正常返回"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search._retry_post", new=AsyncMock()) as mock_rp:
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
            with patch("maishou_search._retry_post", new=AsyncMock()) as mock_rp:
                mock_rp.return_value = ({}, "请求失败（已重试）: timeout")
                result = await detail("123", 2)
                assert result.startswith("❌")
                assert "请求失败" in result
                assert mock_rp.call_count == 1  # 第一次就返回错误，不再调第二次

    @pytest.mark.asyncio
    async def test_target_url_fails_non_fatal(self):
        """TARGET_URL 失败不应阻断，仍返回部分数据"""
        with patch("maishou_search.get_session", new=AsyncMock()):
            with patch("maishou_search._retry_post", new=AsyncMock()) as mock_rp:
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
            with patch("maishou_search._retry_post", new=AsyncMock()) as mock_rp:
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
            with patch("maishou_search._retry_post", new=AsyncMock()) as mock_rp:
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
            with patch("maishou_search._retry_post", new=AsyncMock()) as mock_rp:
                mock_rp.side_effect = [
                    ({"data": {"title": "json test"}}, None),
                    ({"data": {}}, None),
                ]
                result = await detail("111", 1, format="json")
                assert result.startswith("{")
                assert "json test" in result
