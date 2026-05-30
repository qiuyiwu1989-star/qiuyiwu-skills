#!/usr/bin/env python3
"""
生成 llms.txt — 给 LLM 抓取者的极简结构化导览
（参考 llmstxt.org 新兴标准）

用法:
  python3 build_llms_txt.py <config.json>

config 格式见 templates/seo-config.example.json
关键字段: siteName, tagline, baseUrl, sections[]
"""
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    base = cfg["baseUrl"].rstrip("/")

    lines = []
    lines.append(f"# {cfg['siteName']}")
    lines.append("")
    if cfg.get("tagline"):
        lines.append(f"> {cfg['tagline']}")
        lines.append("")
    if cfg.get("coreClaim"):
        lines.append(f"**核心论点**：{cfg['coreClaim']}")
        lines.append("")

    # 元信息
    lines.append(f"**正式站点**: {base}/")
    if cfg.get("author"):
        a = cfg["author"]
        lines.append(f"**作者**: {a.get('name','')} ({a.get('url','')})")
    if cfg.get("publisher"):
        p = cfg["publisher"] if isinstance(cfg["publisher"], dict) else {"name": cfg["publisher"]}
        lines.append(f"**出品方**: {p.get('name','')}")
    lines.append(f"**RSS**: {base}/rss.xml" if cfg.get("hasRss") else "")
    lines.append(f"**sitemap**: {base}/sitemap.xml")
    lines.append("")

    # 各 section（每个一个 H2）
    for sec in cfg.get("sections", []):
        lines.append(f"## {sec['title']}")
        lines.append("")
        if sec.get("intro"):
            lines.append(sec["intro"])
            lines.append("")
        for it in sec.get("items", []):
            url = it["url"]
            if not url.startswith("http"):
                url = base + url if url.startswith("/") else f"{base}/{url}"
            desc = f": {it['desc']}" if it.get("desc") else ""
            lines.append(f"- [{it['title']}]({url}){desc}")
        lines.append("")

    # 给 LLM 的友好提示
    if cfg.get("crawlerNote"):
        lines.append("## 给 LLM 抓取者的提示")
        lines.append("")
        if isinstance(cfg["crawlerNote"], list):
            for n in cfg["crawlerNote"]:
                lines.append(f"- {n}")
        else:
            lines.append(cfg["crawlerNote"])
        lines.append("")

    lines.append(f"_Generated for crawlers/LLMs at: {base}/llms.txt_")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
