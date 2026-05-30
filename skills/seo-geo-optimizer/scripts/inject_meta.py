#!/usr/bin/env python3
"""
给单个 HTML 注入 canonical / OG / Twitter / JSON-LD meta
（已存在的会被替换；缺的会加在 </head> 之前）

用法:
  python3 inject_meta.py <html_file> <meta.json>

meta.json 格式:
  {
    "title": "页面标题",
    "description": "搜索结果描述",
    "canonical": "https://example.com/this-page",
    "ogImage": "https://example.com/og.png",
    "siteName": "站点名",
    "ogType": "article",          # 或 website / book
    "twitterCard": "summary_large_image",
    "author": "作者名",
    "jsonld": { ... schema.org 对象 ... }
  }
"""
import json
import re
import sys
from pathlib import Path


def upsert_meta(html: str, attr: str, name: str, content: str) -> str:
    """更新或插入 <meta {attr}="{name}" content="{content}">"""
    pat = re.compile(rf'<meta\s+{attr}=["\']{re.escape(name)}["\'][^>]*>', re.I)
    new_tag = f'<meta {attr}="{name}" content="{content}">'
    if pat.search(html):
        return pat.sub(new_tag, html, count=1)
    return html.replace("</head>", f"    {new_tag}\n</head>", 1)


def upsert_link_canonical(html: str, href: str) -> str:
    pat = re.compile(r'<link\s+rel=["\']canonical["\'][^>]*>', re.I)
    new_tag = f'<link rel="canonical" href="{href}">'
    if pat.search(html):
        return pat.sub(new_tag, html, count=1)
    return html.replace("</head>", f"    {new_tag}\n</head>", 1)


def upsert_title(html: str, title: str) -> str:
    pat = re.compile(r"<title[^>]*>[^<]*</title>", re.I)
    new = f"<title>{title}</title>"
    if pat.search(html):
        return pat.sub(new, html, count=1)
    return html.replace("</head>", f"    {new}\n</head>", 1)


def inject_jsonld(html: str, jsonld) -> str:
    """如果还没有 application/ld+json，加一段"""
    if 'application/ld+json' in html:
        return html  # 不动已有的
    blob = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False) + "</script>"
    return html.replace("</head>", f"    {blob}\n</head>", 1)


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    fp = Path(sys.argv[1])
    cfg = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    html = fp.read_text(encoding="utf-8")

    if cfg.get("title"):
        html = upsert_title(html, cfg["title"])
    if cfg.get("description"):
        html = upsert_meta(html, "name", "description", cfg["description"])
    if cfg.get("canonical"):
        html = upsert_link_canonical(html, cfg["canonical"])
    if cfg.get("author"):
        html = upsert_meta(html, "name", "author", cfg["author"])

    # OG
    if cfg.get("title"):
        html = upsert_meta(html, "property", "og:title", cfg["title"])
    if cfg.get("description"):
        html = upsert_meta(html, "property", "og:description", cfg["description"])
    if cfg.get("canonical"):
        html = upsert_meta(html, "property", "og:url", cfg["canonical"])
    if cfg.get("ogImage"):
        html = upsert_meta(html, "property", "og:image", cfg["ogImage"])
    if cfg.get("ogType"):
        html = upsert_meta(html, "property", "og:type", cfg["ogType"])
    if cfg.get("siteName"):
        html = upsert_meta(html, "property", "og:site_name", cfg["siteName"])
    if cfg.get("locale"):
        html = upsert_meta(html, "property", "og:locale", cfg["locale"])

    # Twitter
    html = upsert_meta(html, "name", "twitter:card", cfg.get("twitterCard", "summary_large_image"))
    if cfg.get("title"):
        html = upsert_meta(html, "name", "twitter:title", cfg["title"])
    if cfg.get("description"):
        html = upsert_meta(html, "name", "twitter:description", cfg["description"])
    if cfg.get("ogImage"):
        html = upsert_meta(html, "name", "twitter:image", cfg["ogImage"])

    # JSON-LD
    if cfg.get("jsonld"):
        html = inject_jsonld(html, cfg["jsonld"])

    fp.write_text(html, encoding="utf-8")
    print(f"✓ {fp.name} 已注入 meta")


if __name__ == "__main__":
    main()
