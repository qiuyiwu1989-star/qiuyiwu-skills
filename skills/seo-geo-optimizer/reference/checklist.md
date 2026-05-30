# SEO + GEO 完整检查清单

## P0 · 致命

- [ ] **HTTPS** — 没 SSL = AI 抓取意愿 < 10%
- [ ] **正文嵌进 HTML**（非 JS 渲染） — JS 渲染 = LLM 几乎不抓
- [ ] **robots.txt** 存在并明确允许 LLM bot
- [ ] **sitemap.xml** 存在且每个 URL 可访问
- [ ] **每页有 `<title>` 和 `<meta name="description">`**
- [ ] **canonical URL** 每页自指
- [ ] **html lang 属性** 明确（zh-CN / en）

## P1 · 重要

- [ ] **JSON-LD 结构化数据**
  - 首页：WebSite + (Book / Organization / Person 视类型)
  - 文章页：Article（含 author + publisher + datePublished）
- [ ] **Open Graph meta**（og:title / og:description / og:image / og:url）
- [ ] **Twitter Card**（summary_large_image）
- [ ] **viewport meta** 移动端必备
- [ ] **OG image 用 PNG**（SVG 微信/X 不识别）
- [ ] **页面加载 < 2s**（gzip + 长缓存）
- [ ] **llms.txt** 给 LLM 的极简导览

## P2 · 加分

- [ ] **RSS feed** 给订阅者和 LLM Reader
- [ ] **font-display:swap** Google Fonts 自带
- [ ] **resource hints**（preconnect / dns-prefetch）
- [ ] **statics 长缓存**（CSS/JS 30d，图片 7d，HTML 1h）
- [ ] **Brotli 压缩** 比 gzip 再小 20%（nginx_module_brotli）

## P3 · 数据 / 营销

- [ ] **百度统计**（中国流量必备）
- [ ] **GSC** Google Search Console 提交 sitemap
- [ ] **百度搜索资源平台** 提交 sitemap
- [ ] **Necotagger / Bing Webmaster Tools** 提交

## 验证方法

### 模拟搜索引擎抓取

```bash
curl -A "Mozilla/5.0 (compatible; Googlebot/2.1)" "$URL"
```

### 模拟 LLM 抓取

```bash
curl -A "GPTBot/1.0" "$URL" | head -100
curl -A "ClaudeBot/1.0" "$URL" | head -100
curl -A "PerplexityBot/1.0" "$URL" | head -100
```

### 验证 JSON-LD

把 HTML 粘到 https://search.google.com/test/rich-results

### 验证 OG meta

把 URL 粘到 https://developers.facebook.com/tools/debug/

### 速度

```bash
python3 scripts/speed_check.py "$URL"
```

或用 https://pagespeed.web.dev/

## 中国独特考虑

1. **百度统计**而不是 Google Analytics（GA 在国内卡）
2. **Baiduspider** 必须显式 Allow
3. **Bytespider** 字节豆包 / 抖音搜索的关键
4. **网页打开速度**：从中国大陆访问海外节点慢，**国内服务器 + 国内 CDN** 是关键
5. **DNS**：腾讯云 DNSPod 比 Cloudflare 在国内更稳

## 红线（千万别做）

- ❌ 不要 noindex 整个网站（很多人误改 default 模板）
- ❌ 不要 disallow `/`（robots.txt 写错位置就 GG）
- ❌ 不要把 meta keywords 塞 30 个词（被反作弊降权）
- ❌ 不要把 OG image 写成本地文件路径（必须绝对 URL）
- ❌ 不要在不同页面用相同 canonical（会被合并到一个）
- ❌ 不要用 client-side redirect 当 SEO 重定向（用 301）
