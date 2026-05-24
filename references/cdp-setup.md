# CDP 浏览器自动化设置指南

本指南说明如何连接本地浏览器进行数据采集。CDP（Chrome DevTools Protocol）能获取最完整的页面数据，但需要本地浏览器支持。

---

## 前置条件

### 1. 浏览器要求

需要 Chrome 或 Chromium 内核浏览器，版本 ≥ 90。

> ⚠️ **Firefox 用户注意**：agent-browser 的 `--cdp` 基于 Chrome DevTools Protocol，**不支持 Firefox**。如需使用本技能，请改用 Edge/Chrome/Brave/Vivaldi 等 Chromium 内核浏览器。

### 2. 浏览器检测命令

**Windows (Git Bash)**：
```bash
for path in \
  "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  "/c/Program Files/Microsoft/Edge/Application/msedge.exe" \
  "/c/Program Files/Google/Chrome/Application/chrome.exe" \
  "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
  "/c/Users/$USER/AppData/Local/Google/Chrome/Application/chrome.exe" \
  "/c/Users/$USER/AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe" \
  "/c/Users/$USER/AppData/Local/Vivaldi/Application/vivaldi.exe"; do
  [ -f "$path" ] && echo "✓ $(basename ${path%.exe}) → $path" || true
done
```

**Windows (PowerShell)**：
```powershell
$paths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe"
)
foreach ($p in $paths) { if (Test-Path $p) { Write-Output "✓ 找到: $p" } }
```

**macOS**：
```bash
# 浏览器检测
for name in "Google Chrome" "Microsoft Edge" "Brave Browser" "Vivaldi"; do
  [ -d "/Applications/$name.app" ] && echo "✓ $name"
done
```

**Linux**：
```bash
# 浏览器检测
which google-chrome chromium-browser microsoft-edge brave-browser vivaldi 2>/dev/null
```

---

## 启动带 CDP 的浏览器

浏览器需要以远程调试模式启动。如果浏览器已在运行，需要先**完全退出**再以调试模式重启，否则端口不会生效。

| 浏览器 | 典型路径 | 启动命令 |
|:---:|:---|:---|
| **Edge** | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` | `& "..." --remote-debugging-port=9222` |
| **Chrome** | `C:\Program Files\Google\Chrome\Application\chrome.exe` | 同上 |
| **Chrome（用户级）** | `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe` | 同上 |
| **Brave** | `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe` | 同上 |
| **Vivaldi** | `%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe` | 同上 |
| **Opera** | `%LOCALAPPDATA%\Programs\Opera\opera.exe` | 同上（注意不是launcher.exe） |

**PowerShell 完整启动命令示例**：
```powershell
# Edge
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222

# Chrome
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# Brave
& "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9222
```

**macOS 启动命令**：
```bash
# Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 &

# Edge
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222 &

# Brave
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --remote-debugging-port=9222 &
```

**Linux 启动命令**：
```bash
# Chrome
google-chrome --remote-debugging-port=9222 &

# Chromium
chromium-browser --remote-debugging-port=9222 &

# Edge
microsoft-edge --remote-debugging-port=9222 &
```

---

## 端口预检

### 端口状态检测

```bash
# 检查 CDP 端口是否就绪（基础检查）
curl -s http://localhost:9222/json/version | head -5
```

成功输出示例：
```json
{
    "Browser": "Chrome/120.0.6099.109",
    "Protocol-Version": "1.3"
}
```

### 端口状态决策表

| 端口状态 | 处理方式 |
|:---:|:---|
| PORT_IN_USE（9222被占用 + 返回JSON） | ✅ 直接复用，跳过启动步骤 |
| PORT_IN_USE（9222被非浏览器占用） | 尝试备选端口（9223/9224） |
| PORT_FREE（9222空闲） | 继续启动浏览器流程 |

### 备选端口

```bash
for port in 9223 9224; do
  curl -s http://localhost:$port/json > /dev/null 2>&1 && echo "PORT_IN_USE:$port" || echo "PORT_FREE:$port"
done
```

如果所有端口都不可用，提示用户关闭占用 9222 的程序，或手动指定端口。

---

## 快速启动检查清单

在执行 CDP 采集前，按此清单逐项确认：

- [ ] 浏览器已安装且版本 ≥ 90
- [ ] 浏览器**完全退出**后以 `--remote-debugging-port=9222` 重新启动
- [ ] `curl -s http://localhost:9222/json/version` 返回 JSON（而非 Connection refused）
- [ ] 目标平台已手动登录（如需登录态）
- [ ] 未开过多标签页（建议 ≤ 5 个，避免内存溢出）

任一项失败 → 跳过 CDP，降级到 Web Search。详见 `fallback-guide.md`。

---

## 登录验证

部分数据需要登录态。CDP 复用浏览器 profile：

1. 先在浏览器中**手动登录**目标平台
2. 然后再启动调研——CDP 会继承登录态
3. 验证登录状态：用 CDP 打开目标页面，检查是否跳转到登录页

```bash
# 快速检查当前打开的标签页
curl -s http://localhost:9222/json | python3 -c "
import json, sys
tabs = json.load(sys.stdin)
for t in tabs:
    print(f'{t.get(\"title\",\"?\")} → {t.get(\"url\",\"?\")[:60]}')
"
```

**登录墙探测（一次性）**：
```bash
# 打开目标网站并检测登录状态
agent-browser --cdp 9222 open "https://<目标网站>"
agent-browser --cdp 9222 wait --load networkidle
agent-browser --cdp 9222 snapshot -i | grep -E "你好，请登录|登录|规格参数|¥|价格|评价"
```
- 看到用户名 + 规格参数 + 价格 → ✅ 登录态有效
- 看到"登录""请登录" → ⚠️ 提醒用户完成登录
- 空白/验证页/重定向 → 换 CDP 方式或检查浏览器

---

## agent-browser 常用 CDP 命令速查

### 页面导航与等待
```bash
agent-browser --cdp 9222 open <URL>
agent-browser --cdp 9222 wait --load networkidle       # 等待网络空闲
agent-browser --cdp 9222 wait --load domcontentloaded  # 等待DOM加载
```

### 数据获取
```bash
agent-browser --cdp 9222 get title
agent-browser --cdp 9222 get url
agent-browser --cdp 9222 snapshot -i      # 交互元素版（推荐）
agent-browser --cdp 9222 snapshot         # 完整版（含非交互文本）
```

### 页面操作
```bash
agent-browser --cdp 9222 click @eN        # 点击元素（N为snapshot -i返回的ref编号）
agent-browser --cdp 9222 scroll down 2000 # 向下滚动
agent-browser --cdp 9222 scroll up 500    # 向上滚动
```

### 多标签页管理
```bash
agent-browser --cdp 9222 tab              # 列出所有标签页
agent-browser --cdp 9222 tab 2            # 切换到标签页2
agent-browser --cdp 9222 tab new <URL>    # 新标签页打开
agent-browser --cdp 9222 tab close 2      # 关闭标签页2
```

### 截图
```bash
agent-browser --cdp 9222 screenshot <path>
agent-browser --cdp 9222 screenshot --full <path>   # 全页截图
```

### 执行 JavaScript
```bash
cat <<'EOF' | agent-browser --cdp 9222 eval --stdin
(() => {
  // 你要执行的 JS 代码
  return document.title;
})()
EOF
```

---

## 多商品调研流程

```bash
# 1. 打开第一个商品标签页
agent-browser --cdp 9222 open "https://item.jd.com/<SKU1>.html"

# 2. 提取数据...

# 3. 新标签页打开第二个商品
agent-browser --cdp 9222 tab new "https://item.jd.com/<SKU2>.html"

# 4. 提取数据...

# 5. 反复切换标签页
agent-browser --cdp 9222 tab 1   # 回到商品1
agent-browser --cdp 9222 tab 2   # 回到商品2

# 6. 处理完清理
agent-browser --cdp 9222 tab close 2
```

---

## 第三方数据源速查表

| 来源 | 用途 | 示例 URL |
|:---:|:---|:---|
| ZOL（中关村在线） | 参数、评价 | `detail.zol.com.cn`, `wap.zol.com.cn` |
| 什么值得买 | 测评、评价、历史价格 | `www.smzdm.com` |
| 太平洋电脑网 | 参数 | `product.pconline.com.cn` |
| 天极网 | 参数 | `product.yesky.com` |
| NGA | 论坛讨论 | `bbs.nga.cn` |
| Chiphell | 高端玩家论坛 | `www.chiphell.com` |
| 小红书 | 用户真实体验 | `www.xiaohongshu.com` |

---

## 常见问题 FAQ

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| Connection refused | 浏览器未以调试模式启动 | 完全退出浏览器后加 `--remote-debugging-port=9222` 重启 |
| 端口被占用 | 已有实例在使用 9222 | `taskkill /F /IM chrome.exe` 或换端口 9223/9224 |
| "元素已失效" | 页面变化后 ref 过期 | 重新 snapshot 再操作 |
| 登录态丢失 | 使用了新的 user-data-dir | 每次用同一个 user-data-dir，或复用默认 profile |
| 页面加载超时 | 网络慢或页面过重 | 增加等待时间，或降级到 web search |
| 反爬验证码 | 频繁请求触发风控 | 降低请求频率，加入随机延迟 |
| 规格表空白 | 未点击展开 / 京东异步渲染 | 先点击"规格参数"tab 再读取；京东直接走 ZOL 参数页 |
| 评价只有好评 | 默认好评排序 | 手动切换筛选到"中评""差评"tab |
| 图片参数不可读 | 参数在 CSS 背景图里 | 下载图片后多模态 LLM 读取；京东不适用 |
| 页面跳转到验证页 | 需要登录或被反爬 | 检查浏览器登录状态 |
| Firefox 不支持 CDP | 协议不兼容 | 换 Edge/Chrome/Brave 等 Chromium 浏览器 |
| 页面加载慢 | 网络问题或懒加载 | 使用 `wait --load networkidle` + 适当 `sleep` |

---

## 降级处理

当 CDP 连接失败时，不要卡在重试上。参考 `fallback-guide.md` 切换到备选采集方式。

> 💡 **核心原则**：CDP 能拿到最完整的页面数据，但连接失败时不要阻塞流程，立即降级到搜索模式，因为用户等的是分析结果不是技术日志。
