#!/usr/bin/env python3
"""
对 JS 渲染站做静态预渲染 · 让爬虫和 LLM 也能读到完整内容

依赖:
  pip install playwright
  playwright install chromium

用法:
  python3 prerender_js_site.py <urls.txt> <out_dir>

urls.txt 每行一个 URL（或一个 URL + tab + 文件名）

输出:
  <out_dir>/<slug>.html · 完全渲染后的静态 HTML
"""
import re
import sys
from pathlib import Path


def slugify(url: str) -> str:
    """URL → 简短文件名"""
    s = re.sub(r"^https?://[^/]+/?", "", url).strip("/")
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", s).strip("-")
    return s or "index"


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 需要先装 playwright: pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(1)

    urls_file = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for line in urls_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            url, fname = line.split("\t", 1)
        else:
            url, fname = line, slugify(line) + ".html"
        entries.append((url, fname))

    print(f"将渲染 {len(entries)} 个页面到 {out_dir}/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for url, fname in entries:
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (compatible; Prerender/1.0)",
                viewport={"width": 1280, "height": 800},
            )
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
                # 等所有动态内容
                page.wait_for_timeout(800)
                # 注入 noindex + canonical 提示
                html = page.content()
                out_path = out_dir / fname
                out_path.write_text(html, encoding="utf-8")
                size_kb = out_path.stat().st_size // 1024
                print(f"  ✓ {url} → {fname} ({size_kb} KB)")
            except Exception as e:
                print(f"  ✗ {url}  错误: {e}")
            finally:
                ctx.close()
        browser.close()

    print(f"\n✓ 完成 · 部署 {out_dir}/ 后，记得在 sitemap 里改用静态 URL")


if __name__ == "__main__":
    main()
