#!/usr/bin/env python3
"""
从 seo-config.json 生成 sitemap.xml

用法:
  python3 build_sitemap.py <config.json> [> output.xml]

config 格式见 templates/seo-config.example.json
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    base = cfg["baseUrl"].rstrip("/")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for p in cfg.get("pages", []):
        url = p["url"]
        if not url.startswith("http"):
            url = base + url if url.startswith("/") else f"{base}/{url}"
        lastmod = p.get("lastmod", today)
        changefreq = p.get("changefreq", "monthly")
        priority = p.get("priority", 0.5)
        lines.append(
            f"  <url><loc>{url}</loc>"
            f"<lastmod>{lastmod}</lastmod>"
            f"<changefreq>{changefreq}</changefreq>"
            f"<priority>{priority}</priority></url>"
        )
    lines.append("</urlset>")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
