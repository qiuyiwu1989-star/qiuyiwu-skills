#!/usr/bin/env python3
"""
批量给一组 HTML 注入 schema.org Article JSON-LD
- 从每个 HTML 自动提取已有的 og:title / og:description / canonical / article:section / article:author
- 估算字数（中文字符）
- 写入 <script type="application/ld+json"> 到 </head> 之前
- 幂等：已有 application/ld+json 的页面跳过

用法 1（按 seo-config.json 的 sections 跑）:
  python3 build_jsonld_articles.py <project_dir> <seo-config.json>

用法 2（直接给 HTML 列表）:
  python3 build_jsonld_articles.py <html1> <html2> ...

config 必须有：
  - siteName       书名
  - baseUrl        基础 URL
  - author { name, url }
  - publisher { name, logo? }
  - ogImage        默认 cover 图

config 可选：
  - bookName       isPartOf 书名（默认 siteName）
  - datePublished  日期
  - inLanguage     语言（默认 zh-CN）
"""
import json
import re
import sys
from pathlib import Path
from datetime import date


def extract_meta(html: str, attr: str, name: str) -> str:
    m = re.search(
        rf'<meta\s+{attr}=["\']{re.escape(name)}["\']\s+content=["\']([^"\']+)["\']',
        html, re.I,
    )
    return m.group(1) if m else ""


def extract_canonical(html: str) -> str:
    m = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html, re.I)
    return m.group(1) if m else ""


def extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    return m.group(1).strip() if m else ""


def count_chinese(html: str) -> int:
    # 去 script/style
    body = re.search(r"<body[^>]*>(.+?)</body>", html, re.S | re.I)
    if not body:
        return 0
    txt = body.group(1)
    txt = re.sub(r"<script.*?</script>", "", txt, flags=re.S | re.I)
    txt = re.sub(r"<style.*?</style>", "", txt, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", "", txt)
    return sum(1 for c in txt if "一" <= c <= "鿿")


def has_jsonld(html: str) -> bool:
    return 'application/ld+json' in html


def build_jsonld(html: str, cfg: dict, page_url_hint: str = "") -> dict:
    title = extract_meta(html, "property", "og:title") or extract_title(html)
    desc = extract_meta(html, "property", "og:description") or extract_meta(html, "name", "description")
    canonical = extract_canonical(html) or page_url_hint
    section = extract_meta(html, "property", "article:section") or ""
    author_in_html = extract_meta(html, "property", "article:author")
    image = extract_meta(html, "property", "og:image") or cfg.get("ogImage", "")
    wc = count_chinese(html)

    author = cfg.get("author") or {"name": author_in_html or "未知"}
    if isinstance(author, str):
        author = {"name": author}
    publisher = cfg.get("publisher") or author
    if isinstance(publisher, str):
        publisher = {"name": publisher}

    book_name = cfg.get("bookName") or cfg.get("siteName") or ""
    date_pub = cfg.get("datePublished") or date.today().strftime("%Y")
    in_lang = cfg.get("inLanguage", "zh-CN")

    obj = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "url": canonical,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": image,
        "inLanguage": in_lang,
        "wordCount": wc,
        "author": {"@type": "Person", "name": author["name"], **({"url": author["url"]} if author.get("url") else {})},
        "publisher": {
            "@type": "Organization",
            "name": publisher["name"],
            **({"logo": {"@type": "ImageObject", "url": publisher["logo"]}} if publisher.get("logo") else {}),
        },
        "datePublished": date_pub,
    }
    if section:
        obj["articleSection"] = section
    if book_name:
        obj["isPartOf"] = {"@type": "Book", "name": book_name, "url": cfg.get("baseUrl", "")}
    return obj


def inject(html_path: Path, cfg: dict, page_url_hint: str = "", dry: bool = False) -> str:
    html = html_path.read_text(encoding="utf-8")
    if has_jsonld(html):
        return "skipped (already has JSON-LD)"
    if "</head>" not in html:
        return "skipped (no </head>)"
    jsonld = build_jsonld(html, cfg, page_url_hint)
    blob = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False) + "</script>"
    new_html = html.replace("</head>", f"    {blob}\n</head>", 1)
    if not dry:
        html_path.write_text(new_html, encoding="utf-8")
    return f"injected (wc={jsonld['wordCount']})"


def resolve_url_to_path(project_dir, base_url, url):
    """seo-config 的 /ch01/ 类 URL → 对应 HTML 文件路径"""
    rel = url.lstrip("/")
    # 处理 base 前缀（如 baseUrl 是 https://x.com/ai-education，URL 是 /ch01/ → 文件在 project/ch01/index.html）
    candidates = [
        project_dir / rel / "index.html",
        project_dir / (rel.rstrip("/") + ".html") if not rel.endswith(".html") else project_dir / rel,
        project_dir / rel,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    # 模式 1：第 2 个参数是 json → config 模式
    if len(args) >= 2 and args[1].endswith(".json") and Path(args[1]).is_file():
        project_dir = Path(args[0]).expanduser().resolve()
        cfg = json.loads(Path(args[1]).read_text(encoding="utf-8"))
        base = cfg.get("baseUrl", "").rstrip("/")

        # 收集所有 sections 里的 item URL
        items = []
        for sec in cfg.get("sections", []):
            for it in sec.get("items", []):
                items.append(it)
        # 也加上 pages（去重）
        seen = {it["url"] for it in items}
        for p in cfg.get("pages", []):
            if p["url"] not in seen:
                items.append(p)
                seen.add(p["url"])

        counts = {}
        for it in items:
            url = it["url"]
            page_path = resolve_url_to_path(project_dir, base, url)
            full_url = base + url if url.startswith("/") else f"{base}/{url}"
            if not page_path:
                result = f"skipped (file not found for {url})"
            else:
                result = inject(page_path, cfg, page_url_hint=full_url)
            counts[result] = counts.get(result, 0) + 1
            print(f"  {result:40s} {url}")
        print()
        for k, v in counts.items():
            print(f"  {k}: {v}")

    else:
        # 模式 2：HTML 文件列表（需要配置文件先放好）
        cfg_path = Path("seo-config.json")
        if not cfg_path.is_file():
            print("当前目录下没有 seo-config.json", file=sys.stderr)
            sys.exit(1)
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        for arg in args:
            p = Path(arg)
            if not p.is_file():
                print(f"  skipped (not found) {arg}")
                continue
            print(f"  {inject(p, cfg)}  {arg}")


if __name__ == "__main__":
    main()
