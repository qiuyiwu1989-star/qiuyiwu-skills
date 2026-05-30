# 实战补充：从 qiuyiwu.com/ai-cognition 项目踩到的新坑

> 这是 2025 年做 AI 思维与认知卡片站时新积累的经验，对 SEO + 数据统计 + 预渲染都有补充。
> 配合 `SKILL.md` 主流程用，遇到对应情况查这份。

---

## 1. PWA Service Worker `CACHE_VERSION` 必须随部署同步 bump

**症状**：部署了新版 CSS / JS / HTML，老访客（之前装过 PWA / 注册过 SW 的）仍看旧站。

**真因**：SW 拦截 fetch，shell 缓存里仍是旧版本的 index.html、styles.css。即使你 bump 了 `?v=` 查询字符串，SW 已缓存的 HTML 还是引用旧 `?v=`。

**修法**：每次部署，**sw.js 顶部的 `CACHE_VERSION` 也要 +1**：

```javascript
const CACHE_VERSION = "v349-1";  // ← 每次部署同步 bump
const SHELL_CACHE = `your-app-shell-${CACHE_VERSION}`;
const ASSET_CACHE = `your-app-assets-${CACHE_VERSION}`;
// ...
```

SW 的 `activate` 事件会自动删掉旧缓存，新版本立刻生效。

**预防**：在部署脚本里**自动**从 `?v=` 提取版本号写入 sw.js（一次性消除整类问题）：

```bash
# 部署脚本片段
VER=$(grep -oE "v=[0-9a-z-]+" index.html | head -1 | sed 's/v=//')
sed -i "s/const CACHE_VERSION = \".*\"/const CACHE_VERSION = \"$VER\"/" sw.js
```

---

## 2. Python 预渲染脚本：替换函数体不要用 `[^}]*`

**症状**：跑预渲染 / 注入脚本后，目标 JS 文件语法报错。整个 app.js 无法解析 → 网站首页所有动态内容（卡片、过滤栏、五阶模型）全部消失。

**真因**：

```python
# ❌ 错的写法
re.sub(
    r'function cardHref\(card\)\s*\{[^}]*\}',
    new_fn, src, count=1
)
```

`[^}]*` 只匹配「非 `}`」字符。但模板字符串里的 `${expr}` 包含 `}`，正则会**提前截断**：

```javascript
// 原函数体
return `./card.html?id=${encodeURIComponent(card.id)}`;
//                                          ↑ 这里有 }
```

匹配在 `${encodeURIComponent(card.id)}` 那个 `}` 就停了，新函数插进去，老函数 `` `;\n}` 尾巴**留在文件里当垃圾**。

**修法**：用「大括号配对解析器」找完整函数：

```python
def replace_function(src, fn_name, new_body):
    m = re.search(rf'function {re.escape(fn_name)}\([^)]*\)\s*\{{', src)
    if not m: return src
    start = m.start()
    i = m.end() - 1  # 指向 `{`
    depth, in_str, sc, esc, in_tpl = 0, False, None, False, False
    while i < len(src):
        c = src[i]
        if esc: esc = False
        elif c == '\\' and (in_str or in_tpl): esc = True
        elif in_str:
            if c == sc: in_str = False
        elif in_tpl:
            if c == '`': in_tpl = False
            elif c == '$' and i + 1 < len(src) and src[i+1] == '{':
                # 跳过模板插值 ${...}
                j = i + 2; d = 1
                while j < len(src) and d > 0:
                    if src[j] == '{': d += 1
                    elif src[j] == '}': d -= 1
                    j += 1
                i = j; continue
        elif c in ('"', "'"):
            in_str = True; sc = c
        elif c == '`':
            in_tpl = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return src[:start] + new_body + src[i+1:]
        i += 1
    return src
```

**预防**：任何脚本改完 JS 后立刻跑 `node --check file.js`，不通过就 abort。

---

## 3. 详情页预渲染：写 HTML 模板时，路径要相对深度

**症状**：预渲染的 `/card/L4-022.html` 在浏览器打开后，CSS / JS / 图片都 404。

**真因**：模板 card.html 在站根，引用是 `./styles.css`。复制到子目录 `/card/L4-022.html` 后，`./styles.css` 解析成 `/card/styles.css` — 不存在。

**修法**：预渲染脚本生成子目录文件时，把所有 `src="./xxx"` / `href="./xxx"` 转成 `../xxx`：

```python
def fix_paths(m):
    attr, val = m.group(1), m.group(2)
    if val.startswith("./") and not val.startswith("./card/"):
        return f'{attr}="../{val[2:]}"'
    return m.group(0)
out = re.sub(r'(src|href)="(\./[^"]+)"', fix_paths, out)
# 还要修 hash 链接
out = out.replace('href="#top"', 'href="../index.html#top"')
out = out.replace('href="#cards"', 'href="../index.html#cards"')
# 等等
```

---

## 4. 内部链接函数也要换路径

光做了预渲染不够 —— **内部链接（`cardHref()` 这类）也要指向新路径**，不然爬虫沿用旧 query-string URL，新文件没人去。

```javascript
// 旧
function cardHref(card) {
  return `./card.html?id=${encodeURIComponent(card.id)}`;
}

// 新（预渲染路径）
function cardHref(card) {
  return `./card/${encodeURIComponent(card.id)}.html`;
}
```

**同时 sitemap 也要重写**，把所有详情 URL 换成新路径。

---

## 5. 百度爬虫连 JS 注入的 `<title>` 都看不到

**坑**：以为给 SPA 加了 `document.title = '...'` 就行 — Google 能看（运行 JS），但**百度几乎不跑 JS**，看到的还是 HTML 里的初始 title。

**修法**：每张预渲染的 HTML 文件里**写死专属 title / description / canonical**。JS 端的 `document.title` 注入仍然保留（用户切路由用），但**别指望它给 SEO 加分**。

```html
<title>L4-022 · AI+健康的第一性原理 | AI 思维与认知</title>
<meta name="description" content="AI+健康的第一性原理，是用 AI 把..." />
<link rel="canonical" href="https://qiuyiwu.com/ai-cognition/card/L4-022.html" />
```

---

## 6. 5 大引擎验证 meta 集合（一次性占位，等 token 来填）

放 `</head>` 注释状态里，用户拿到 token 后取消注释填值：

```html
<!-- 站长平台验证 — 拿到验证字符串后替换 content 值 -->
<!-- <meta name="baidu-site-verification" content="codeva-XXXX" /> -->
<!-- <meta name="google-site-verification" content="XXXX" /> -->
<!-- <meta name="msvalidate.01" content="XXXX" /> -->
<!-- <meta name="sogou_site_verification" content="XXXX" /> -->
<!-- <meta name="360-site-verification" content="XXXX" /> -->
```

各引擎注册地址：

| 引擎 | 站长平台 |
|------|----------|
| 百度 | https://ziyuan.baidu.com/ |
| Google | https://search.google.com/search-console |
| Bing | https://bing.com/webmasters |
| Sogou | https://zhanzhang.sogou.com/ |
| 360 | https://zhanzhang.so.com/ |

---

## 7. FAQ schema — GEO 杀手锏

让 LLM（ChatGPT / Claude / Perplexity / 豆包 / Kimi）能引用你的核心定义。每个核心问题写 80-150 字的"可被一句话引用"的答案：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "什么是 <核心概念>？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "<80-150 字定义，要能被 LLM 一句话引用>"
      }
    }
    // 5-10 个
  ]
}
</script>
```

每张详情页加 Article + BreadcrumbList，首页加 FAQPage + WebSite。

---

## 8. GA4 + 百度统计**两套并存**才稳

国内 GA4 经常被网络 / 拦截器干扰；境外用户百度统计触达差。最佳实践：**两套都装，事件双发**：

```javascript
window.track = function(eventName, params = {}) {
  // GA4
  if (typeof gtag === 'function') {
    try { gtag('event', eventName, params); } catch (_) {}
  }
  // 百度
  if (typeof _hmt !== 'undefined') {
    try {
      const category = params.category || eventName.split('_')[0] || 'event';
      const label = params.label || params.id || params.card_id || '';
      _hmt.push(['_trackEvent', category, eventName, String(label), Number(params.value) || 0]);
    } catch (_) {}
  }
};
```

详细做法见 `~/.claude/skills/web-analytics/SKILL.md`。

---

## 9. 部署后必做的 3 件事

不然就算所有代码都对，搜索引擎一周内都不会来：

1. **百度站长平台 → 普通收录 → API 推送**：把 sitemap.xml 里所有 URL POST 给百度
2. **Google Search Console → Sitemaps → 提交** sitemap.xml
3. **微信公众号文章末尾固定加站点链接**（国内最高质量的免费外链）

百度主动推送脚本：

```bash
# scripts/baidu_push.py
import re, urllib.request, sys, os
SITE = os.environ["BAIDU_SITE"]          # https://yoursite.com
TOKEN = os.environ["BAIDU_PUSH_TOKEN"]   # 站长平台拿
urls = re.findall(r"<loc>([^<]+)</loc>",
                  open(sys.argv[1]).read())
payload = "\n".join(urls).encode()
url = f"http://data.zz.baidu.com/urls?site={SITE}&token={TOKEN}"
req = urllib.request.Request(url, data=payload,
        headers={"Content-Type":"text/plain"}, method="POST")
print(urllib.request.urlopen(req).read().decode())
```

跑：`BAIDU_PUSH_TOKEN=xxx python3 baidu_push.py sitemap.xml`

---

## 10. 部署后 24h 验证清单

每次大改完，curl 抓一遍生产环境核对：

```bash
SITE="https://your.site"
echo "── 1. cache 版本 ──"
curl -s $SITE/ | grep -o "v=[0-9a-z-]*" | head -1

echo "── 2. SW 版本同步 ──"
curl -s $SITE/sw.js | grep CACHE_VERSION

echo "── 3. 关键页 HTTP ──"
curl -s -o /dev/null -w "%{http_code}  %{size_download}B  /\n"               $SITE/
curl -s -o /dev/null -w "%{http_code}  %{size_download}B  /sitemap.xml\n"    $SITE/sitemap.xml
curl -s -o /dev/null -w "%{http_code}  %{size_download}B  /sw.js\n"          $SITE/sw.js
curl -s -o /dev/null -w "%{http_code}  %{size_download}B  /manifest.json\n"  $SITE/manifest.json

echo "── 4. 详情页静态化 ──"
curl -s $SITE/card/L4-022.html | grep -c "<h1"     # 应 > 0
curl -s $SITE/card/L4-022.html | grep -c "<p>"     # 应 > 5

echo "── 5. 结构化数据 ──"
curl -s $SITE/ | grep -c "application/ld+json"   # 首页应 2+

echo "── 6. JS 语法 ──"
curl -s "$SITE/app.js" > /tmp/check.js
node --check /tmp/check.js && echo "✓ JS 语法 OK"
```

任何一项异常 → 回滚 / 修复。

---

## 配套：把数据统计也做了

SEO 让搜索引擎找到你，统计让你知道**谁来了 / 看了什么 / 转化了多少**。两件事一起做：

→ `~/.claude/skills/web-analytics/SKILL.md`

里面有：
- 百度统计 + GA4 + GTM 三套模板
- 7 个核心事件埋点代码（card_view / outbound / scroll_depth / pwa_install 等）
- 双发 `window.track()` helper

---

## 速查：常见症状 → 哪一章

| 症状 | 看哪一章 |
|------|----------|
| 部署完老访客没看到新版 | 1 — SW CACHE_VERSION |
| 改 JS 后整页空白 | 2 — 替换函数体 |
| 子目录 HTML 资源 404 | 3 — 路径相对深度 |
| 新预渲染 URL 没有流量 | 4 — 内部链接 |
| 百度后台一直没收录 | 5、6、9 — 静态 title + 验证 + 主动推送 |
| LLM 不引用你 | 7 — FAQ schema |
| 数据统计不准 | 8 — GA4 + 百度并存 |
| 部署后不知道对不对 | 10 — 24h 验证清单 |
