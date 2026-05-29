# 买手 88 API 限流与速率控制

> 本文档记录买手 88 API（`appapi.maishou88.com`）已知的限流规则和最佳实践。

## 已知限流行为

| 维度 | 当前了解 | 来源 |
|:---|:---|:---|
| 请求频率 | 未公开发布具体 QPS 限制 | 实测观察 |
| 并发连接 | 建议 ≤ 3 并发请求 | 实测经验 |
| 429 处理 | 等待 30 秒后重试 1 次 | `fallback-guide.md` |

> ⚠️ 以上为经验数据，非官方 SLA。买手 88 未公开限流文档。

## 代码中的重试策略

`maishou_common.py` 的 `retry_post()` 函数：

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `max_attempts` | 2 | 最多尝试 2 次（1 次原始 + 1 次重试） |
| 重试间隔 | 3 秒 | `asyncio.sleep(3)` |
| 触发条件 | `ClientError` / `TimeoutError` / `JSONDecodeError` | 网络层或解析错误 |

## 状态码处理策略

| 状态码 | 含义 | 代码行为 | 建议 |
|:---|:---|:---|:---|
| 200 | 成功 | 正常解析 | - |
| 429 | 限流 | `raise_for_status()` 抛出 `ClientResponseError`，进入重试逻辑 | 如果遇到持续 429，降低请求频率至 1 req/s |
| 5xx | 服务端错误 | 同上，进入重试 | 重试后仍失败则降级到 Web Search |
| 4xx（非 429） | 客户端错误 | 同上 | 检查 API Key 和参数 |

## 最佳实践

1. **并发控制**：`maishou_price.py` 综合搜索使用 `asyncio.gather` 多平台并发，平台数上限由 `sources` 列表控制（当前 5 个平台）
2. **失败降级**：买手 API 失败不阻塞流程，降级到 CDP 或 Web Search
3. **请求间隔**：连续多次调用同一接口时，建议间隔 ≥ 1 秒
4. **环境变量**：确保 `MAISHOU_API_KEY` 和 `MAISHOU_OPENID` 正确设置——未授权请求也可能返回异常状态码

## 待补充

- [ ] 官方限流文档链接（如有）
- [ ] 429 响应头中的 `Retry-After` 信息
- [ ] `maishou_common.py` 中添加可配置的请求间隔参数
