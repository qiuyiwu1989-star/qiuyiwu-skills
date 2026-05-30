#!/usr/bin/env python3
"""
给一组 HTML 批量注入缺失的默认 meta（canonical/description/OG/Twitter）
- 从 <title> 自动提取标题
- 从文件路径推导 canonical
- 用 seo-config.json 提供的 ogImage + siteName 作 fallback
- 幂等：已有的 meta 不动

用法:
  python3 bulk_default_meta.py <project_dir> <seo-config.json>

config 字段:
  baseUrl       (必)
  siteName      (必)
  ogImage       (必)
  author { name }   描述末尾
"""
import json
import re
import sys
from pathlib import Path


def extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    return m.group(1).strip() if m else ""


def has_meta(html: str, attr: str, name: str) -> bool:
    return bool(re.search(rf'<meta[^>]*{attr}=["\']{re.escape(name)}["\']', html, re.I))


def has_canonical(html: str) -> bool:
    return bool(re.search(r'<link[^>]*rel=["\']canonical["\']', html, re.I))


def file_to_url(file_path: Path, project_dir: Path, base_url: str) -> str:
    rel = file_path.relative_to(project_dir).as_posix()
    if rel.endswith("/index.html"):
        rel = rel[:-len("index.html")]
    if rel == "index.html":
        rel = ""
    return f"{base_url.rstrip('/')}/{rel}"


def inject_block(html: str, block: str) -> str:
    """在 </head> 之前插入一段 meta 块"""
    return html.replace("</head>", f"{block}\n</head>", 1)


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    project_dir = Path(sys.argv[1]).expanduser().resolve()
    cfg = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    base = cfg["baseUrl"].rstrip("/")
    site_name = cfg.get("siteName", "")
    og_image = cfg.get("ogImage", "")
    author = (cfg.get("author") or {}).get("name", "")

    htmls = [p for p in project_dir.rglob("*.html") if not any(part.startswith(".") for part in p.parts)]
    counts = {"injected": 0, "skipped": 0, "no </head>": 0}

    for h in htmls:
        text = h.read_text(encoding="utf-8")
        if "</head>" not in text:
            counts["no </head>"] += 1
            continue

        title = extract_title(text)
        if not title:
            continue
        canonical = file_to_url(h, project_dir, base)
        desc_default = f"{title} —— {cfg.get('tagline', site_name)[:120]}"

        new_blocks = []

        # canonical
        if not has_canonical(text):
            new_blocks.append(f'    <link rel="canonical" href="{canonical}">')

        # description
        if not has_meta(text, "name", "description"):
            new_blocks.append(f'    <meta name="description" content="{desc_default}">')

        # OG
        if not has_meta(text, "property", "og:title"):
            new_blocks.append(f'    <meta property="og:title" content="{title}">')
        if not has_meta(text, "property", "og:description"):
            new_blocks.append(f'    <meta property="og:description" content="{desc_default}">')
        if not has_meta(text, "property", "og:url"):
            new_blocks.append(f'    <meta property="og:url" content="{canonical}">')
        if not has_meta(text, "property", "og:image"):
            if og_image:
                new_blocks.append(f'    <meta property="og:image" content="{og_image}">')
        if not has_meta(text, "property", "og:type"):
            new_blocks.append(f'    <meta property="og:type" content="article">')
        if not has_meta(text, "property", "og:site_name") and site_name:
            new_blocks.append(f'    <meta property="og:site_name" content="{site_name}">')
        if not has_meta(text, "property", "og:locale"):
            new_blocks.append(f'    <meta property="og:locale" content="zh_CN">')

        # Twitter
        if not has_meta(text, "name", "twitter:card"):
            new_blocks.append(f'    <meta name="twitter:card" content="summary_large_image">')
        if not has_meta(text, "name", "twitter:title"):
            new_blocks.append(f'    <meta name="twitter:title" content="{title}">')
        if not has_meta(text, "name", "twitter:description"):
            new_blocks.append(f'    <meta name="twitter:description" content="{desc_default}">')
        if not has_meta(text, "name", "twitter:image") and og_image:
            new_blocks.append(f'    <meta name="twitter:image" content="{og_image}">')

        # author
        if not has_meta(text, "name", "author") and author:
            new_blocks.append(f'    <meta name="author" content="{author}">')

        if new_blocks:
            new_text = inject_block(text, "\n".join(new_blocks))
            h.write_text(new_text, encoding="utf-8")
            counts["injected"] += 1
            print(f"  injected {len(new_blocks)} meta in {h.relative_to(project_dir)}")
        else:
            counts["skipped"] += 1

    print()
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
