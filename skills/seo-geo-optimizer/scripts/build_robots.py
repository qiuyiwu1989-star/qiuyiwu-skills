#!/usr/bin/env python3
"""
生成 robots.txt · 内置主流 LLM bot 白名单

用法:
  python3 build_robots.py <config.json>

config 格式:
  {
    "baseUrl": "https://example.com/",
    "allow": ["/"],
    "disallow": ["/admin/", "/private/"],
    "sitemap": "https://example.com/sitemap.xml"   # 可选, 不写则自动推
  }
"""
import json
import sys
from pathlib import Path

LLM_BOTS = [
    ("GPTBot",         "OpenAI ChatGPT crawler"),
    ("ChatGPT-User",   "OpenAI inline browsing"),
    ("OAI-SearchBot",  "OpenAI search"),
    ("anthropic-ai",   "Anthropic data collection"),
    ("ClaudeBot",      "Anthropic Claude search"),
    ("PerplexityBot",  "Perplexity AI"),
    ("Google-Extended","Google Bard / Gemini training"),
    ("Bingbot",        "Bing (and Copilot)"),
    ("Baiduspider",    "百度搜索"),
    ("YandexBot",      "Yandex"),
    ("Applebot",       "Apple"),
    ("Bytespider",     "字节豆包/抖音"),
    ("Amazonbot",      "Amazon Alexa"),
    ("DuckDuckBot",    "DuckDuckGo"),
]


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    base = cfg["baseUrl"].rstrip("/")
    allow = cfg.get("allow", ["/"])
    disallow = cfg.get("disallow", [])
    sitemap = cfg.get("sitemap") or f"{base}/sitemap.xml"
    site_name = cfg.get("siteName", "")

    lines = []
    lines.append(f"# {site_name} — 欢迎搜索引擎和 LLM 抓取" if site_name else "# 欢迎搜索引擎和 LLM 抓取")
    lines.append("# 全部内容静态化，无需执行 JS")
    lines.append("")
    lines.append("User-agent: *")
    for a in allow:
        lines.append(f"Allow: {a}")
    for d in disallow:
        lines.append(f"Disallow: {d}")
    lines.append("")
    lines.append("# 明确允许主流 LLM 抓取")
    for bot, _comment in LLM_BOTS:
        lines.append(f"User-agent: {bot}")
        for a in allow:
            lines.append(f"Allow: {a}")
        lines.append("")
    lines.append(f"Sitemap: {sitemap}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
