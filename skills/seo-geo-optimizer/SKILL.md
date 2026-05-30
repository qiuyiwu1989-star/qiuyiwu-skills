---
name: seo-geo-optimizer
description: 把任意网站升级到"搜索引擎友好 + LLM 抓取友好 + 速度 < 2s"的完整工具包。当用户说"做 SEO / GEO 优化 / 让大模型能读到我的站 / 加百度统计 / 加 sitemap / 加 robots / 加 llms.txt / 让我的站被搜索到"时触发。无论是静态站还是有 JS 渲染的站，都能用。
---

# /seo-geo-optimizer — SEO + GEO 一站式优化

把任意网站（无论是 ai-revolution 这样的开源专著、企业官网、产品落地页还是个人博客）升级到：

- ✅ **搜索引擎可索引**（sitemap / robots / canonical / JSON-LD）
- ✅ **LLM 可抓取**（llms.txt / 静态 HTML 正文 / OG meta / 明确白名单 LLM bot）
- ✅ **速度 < 2s**（gzip / 长缓存 / 字体优化 / 资源 preload）
- ✅ **统计就位**（百度统计自动注入到所有 HTML）

> 这是从 qiuyiwu.com/ai-revolution/ 项目里萃取出来的实战经验。
> 全部脚本独立可跑，可单独执行也可一键全套。

---

## 何时触发

用户说出下面任何一个意图时：

- "做 SEO 优化"
- "让我的站被搜索到"
- "让大模型 / ChatGPT / Claude / Perplexity 能读到"
- "加百度统计"
- "加 sitemap / robots / llms.txt"
- "网站速度太慢"
- "审计一下我的站"
- "做 GEO（生成引擎优化）"

---

## 调用流程（agent 视角）

收到上述意图时：

1. **先 audit**：跑 `audit.py <project_dir>` 看现状
2. **看清缺什么**：output 是一张 ✅/❌ 清单
3. **按需补齐**：每一项缺失，调对应脚本
4. **核心：如果是 JS 渲染站**，必须预渲染（爬虫看不到 JS 渲染的内容）
5. **最后**：跑一次 `audit.py` 确认全绿

---

## 工具集

### 🔍 `audit.py` —— 单文件审计

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/audit.py <project_dir> [base_url]
```

扫描项目目录，输出清单：

```
✅ HTTPS（curl 测试）
✅ sitemap.xml
❌ robots.txt（缺）
❌ llms.txt（缺）
✅ canonical URL
✅ JSON-LD（Book schema）
✅ Open Graph
❌ 百度统计（缺）
⚠️  index.html 包含 fetch() — 可能是 JS 渲染站，爬虫看不到内容
✅ gzip 已开启
✅ 速度: 0.45s
```

---

### 📊 `inject_baidu.py` —— 一键注入百度统计

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/inject_baidu.py <dir> <hm_id>
```

- `dir`: 要扫的目录（找所有 `*.html`）
- `hm_id`: 百度统计的 ID（hm.js?HM_ID 那个）

行为：
- 给所有 HTML 在 `</head>` 之前注入百度统计 snippet
- 已有的不重复（按 hm.baidu.com 关键字检测）

---

### 🗺 `build_sitemap.py` —— 生成 sitemap.xml

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/build_sitemap.py <config.json> > sitemap.xml
```

`config.json` 格式：

```json
{
  "baseUrl": "https://example.com/",
  "pages": [
    { "url": "/", "priority": 1.0, "changefreq": "weekly" },
    { "url": "/about", "priority": 0.5 },
    { "url": "/blog/post-1", "priority": 0.8, "changefreq": "monthly" }
  ]
}
```

---

### 🤖 `build_robots.py` —— 生成 robots.txt

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/build_robots.py <config.json> > robots.txt
```

输出含**所有主流 LLM bot 白名单**：GPTBot / ClaudeBot / PerplexityBot / Google-Extended / Bingbot / Baiduspider / Bytespider 等。

`config.json`：

```json
{
  "baseUrl": "https://example.com/",
  "allow": ["/"],
  "disallow": ["/admin/", "/scripts/", "/private/"],
  "sitemap": "https://example.com/sitemap.xml"
}
```

---

### 🧠 `build_llms_txt.py` —— 生成 llms.txt（LLM 友好导览）

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/build_llms_txt.py <config.json> > llms.txt
```

`config.json`：

```json
{
  "siteName": "示例站",
  "tagline": "一句话核心论点",
  "baseUrl": "https://example.com",
  "sections": [
    {
      "title": "全部文章",
      "items": [
        { "url": "/blog/1", "title": "标题", "desc": "一句话描述" }
      ]
    }
  ],
  "crawlerNote": "本站全部内容已静态化，无需执行 JS 即可抓取。"
}
```

参考 [llmstxt.org](https://llmstxt.org)。

---

### 📚 `build_jsonld_articles.py` —— 批量给章节/文章页注入 Article schema

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/build_jsonld_articles.py <project_dir> <seo-config.json>
```

最适合**书型项目**：一本书 N 章，每章一个 HTML。脚本会：

- 从 seo-config.json 的 `sections[*].items` 提取所有 URL
- 把 URL 映射到本地 `<project>/<path>/index.html` 或 `.html`
- 从已有的 `<meta>` 抽取 title / description / canonical / article:section
- 估算正文字数（中文字符）
- 注入完整 `Article` JSON-LD（含 author, publisher, isPartOf:Book, articleSection, wordCount）
- 幂等 —— 已有 JSON-LD 的页面跳过

示例输出：

```
  injected (wc=6111)                /ch01/
  injected (wc=6242)                /ch02/
  ...
  injected: 16
  skipped (already has JSON-LD): 1
```

---

### 🚀 `bulk_default_meta.py` —— 批量给一组 HTML 补默认 meta

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/bulk_default_meta.py <project_dir> <seo-config.json>
```

最适合：项目里有 N 个零散 HTML（着陆页、单页应用的多个入口），只有 5 个手工写过 OG 完整 meta，剩下 11 个缺。它会：

- 自动从 `<title>` 提取标题
- 从文件路径反推 canonical URL
- 用 `seo-config.json` 的 `ogImage` / `siteName` / `tagline` 兜底
- 缺什么补什么（已有的不动）
- 一次性补齐：canonical / description / og:* / twitter:* / author

实战：ai-transformation 16 页（5 有 / 11 缺）→ 一行命令后 16/16 全绿。

---

### 💉 `inject_meta.py` —— 给 HTML 加 canonical / OG / Twitter / JSON-LD

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/inject_meta.py <html_file> <config.json>
```

`config.json`：

```json
{
  "title": "页面标题",
  "description": "页面描述（搜索结果显示，~120 字）",
  "canonical": "https://example.com/this-page",
  "ogImage": "https://example.com/og-cover.png",
  "siteName": "站点名",
  "type": "article",
  "author": "作者名",
  "jsonld": { "@context": "https://schema.org", "@type": "Article", ... }
}
```

---

### ⚡ `speed_check.py` —— 速度体检

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/speed_check.py <url1> [url2] ...
```

- 每个 URL 跑 3 次 curl
- 报告：总时间 / 大小（含 gzip）/ TTFB
- 标红超过 2 秒的

---

### 🔥 `prerender_js_site.py` —— JS 渲染站静态化（最关键）

如果 audit 报告 "JS 渲染" 警告，必须跑这个。

```bash
python3 ~/.claude/skills/seo-geo-optimizer/scripts/prerender_js_site.py <urls.txt> <out_dir>
```

- 用 headless Chrome（playwright）抓每个 URL 完全渲染后的 HTML
- 保存到 `<out_dir>/<slug>.html`
- 爬虫和 LLM 抓这些静态文件 = 抓到完整内容

> 依赖：需要本机装 playwright (`pip install playwright && playwright install chromium`)

---

## 一键工作流（最常用）

对一个有 HTML 文件的项目，跑下面这套：

```bash
SKILL=~/.claude/skills/seo-geo-optimizer
PROJ=/path/to/your/project
BASE=https://your.site/

# 1. audit 当前状态
python3 $SKILL/scripts/audit.py $PROJ $BASE

# 2. 写一个 seo-config.json（位于项目根）
# 包含：siteName, baseUrl, pages[], llmsSections, baiduHmId, ogImage 等

# 3. 全套生成（脚本会按 seo-config.json 自动跑）
python3 $SKILL/scripts/build_sitemap.py $PROJ/seo-config.json > $PROJ/sitemap.xml
python3 $SKILL/scripts/build_robots.py $PROJ/seo-config.json > $PROJ/robots.txt
python3 $SKILL/scripts/build_llms_txt.py $PROJ/seo-config.json > $PROJ/llms.txt
python3 $SKILL/scripts/inject_baidu.py $PROJ <hm_id>

# 4. 再 audit 一遍，确认全绿
python3 $SKILL/scripts/audit.py $PROJ $BASE
```

---

## 设计原则

- **每个脚本独立** — 想用哪个就跑哪个，不强制框架
- **配置统一** — 同一个 `seo-config.json` 喂给所有生成类脚本
- **幂等** — 重复运行不会产生重复内容
- **模板可改** — `templates/` 里都是纯文本模板，按自己品牌调
- **零依赖（默认）** — 都是 Python stdlib；只有预渲染需要 playwright
- **专为中文站优化** — 百度统计、Baiduspider、中文 SEO 模式都内置

---

## 配置模板

参考 `templates/seo-config.example.json`，复制改值即可。

## 完整检查清单

参考 `reference/checklist.md`。

## LLM bot 白名单参考

参考 `reference/llm-bots.txt`。

---

## 最佳实践（提醒 agent）

1. **JS 渲染站是 GEO 杀手** — Google 部分能爬，但 ChatGPT/Claude/Perplexity 几乎不爬 JS。检测到 `fetch()` 在主入口就必须预渲染。
2. **百度统计 hm_id 是公开的** —— 但不要把 hm_id 写死在 skill 里，从配置读。
3. **llms.txt 是新东西** —— 还没成标准，但越来越多 LLM 开始读。投资成本极低，回报递增。
4. **不要把 `data/` 整个 disallow** —— 但要 disallow `data/stats.json` 这类用户数据。
5. **结构化数据要写对类型** —— 书是 Book，文章是 Article，组织是 Organization；混用会被搜索引擎降权。
6. **每章 canonical 必须自指** —— 避免重复内容惩罚。
7. **OG image 优先 PNG**，SVG 部分微信、X 客户端不识别。
8. **测速基准：HTML < 0.5s, 完整页面 < 2s**（用 `speed_check.py`）。
