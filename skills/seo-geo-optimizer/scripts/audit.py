#!/usr/bin/env python3
"""
SEO + GEO 体检：扫描项目目录，输出清单 + 修复建议

用法:
  python3 audit.py <project_dir> [base_url]

例:
  python3 audit.py /var/www/site https://site.com/
"""
import json
import re
import subprocess
import sys
from pathlib import Path


GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def line(status, label, detail=""):
    icon = {"ok": f"{GREEN}✅", "warn": f"{YELLOW}⚠️ ", "miss": f"{RED}❌", "info": f"{DIM}·"}[status]
    detail_str = f" {DIM}{detail}{RESET}" if detail else ""
    print(f"  {icon}{RESET}  {label}{detail_str}")


def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def file_has(path: Path, *patterns: str) -> bool:
    if not path.exists():
        return False
    txt = read(path)
    return all(pat.lower() in txt.lower() for pat in patterns)


def find_html_files(root: Path):
    return [p for p in root.rglob("*.html") if not any(part.startswith(".") for part in p.parts)]


def audit(project_dir: str, base_url: str = ""):
    root = Path(project_dir).expanduser().resolve()
    if not root.is_dir():
        print(f"{RED}错误：{root} 不是目录{RESET}")
        sys.exit(1)

    print(f"\n{BOLD}🔍 SEO + GEO 体检{RESET}  {DIM}{root}{RESET}\n")

    # ============ 文件级 ============
    print(f"{BOLD}┌─ 关键文件{RESET}")

    if (root / "sitemap.xml").exists():
        urls = read(root / "sitemap.xml").count("<loc>")
        line("ok", "sitemap.xml", f"{urls} 个 URL")
    else:
        line("miss", "sitemap.xml 缺", "→ 跑 build_sitemap.py")

    if (root / "robots.txt").exists():
        rb = read(root / "robots.txt")
        llm_bots = sum(1 for b in ("GPTBot", "ClaudeBot", "PerplexityBot", "Bytespider") if b in rb)
        if llm_bots >= 2:
            line("ok", "robots.txt", f"含 {llm_bots} 个 LLM bot 白名单")
        else:
            line("warn", "robots.txt 存在但缺 LLM 白名单", "→ 重新跑 build_robots.py")
    else:
        line("miss", "robots.txt 缺", "→ 跑 build_robots.py")

    if (root / "llms.txt").exists():
        sz = (root / "llms.txt").stat().st_size
        line("ok", "llms.txt", f"{sz // 1024} KB")
    else:
        line("miss", "llms.txt 缺（LLM 抓取友好关键文件）", "→ 跑 build_llms_txt.py")

    if (root / "rss.xml").exists() or (root / "feed.xml").exists():
        line("ok", "RSS feed")
    else:
        line("info", "RSS feed 无", "可选")

    # ============ HTML 级 ============
    print(f"\n{BOLD}┌─ HTML 检查{RESET}")

    htmls = find_html_files(root)
    if not htmls:
        line("miss", "找不到 HTML 文件")
        return
    line("info", f"扫到 {len(htmls)} 个 HTML 文件")

    # 拿一个代表样本（仅用于 viewport / html lang 这类 site-wide 判断）
    candidates = [h for h in htmls if "admin" not in str(h) and "scripts" not in str(h)]
    rep = candidates[0] if candidates else htmls[0]
    rep_txt = read(rep)

    # 全量统计每个 HTML 的 meta 覆盖度（不再只看 1 个代表样本）
    def count_pages_with(pattern, *additional):
        n = 0
        for h in htmls:
            t = read(h)
            if pattern.search(t) and all(a in t for a in additional):
                n += 1
        return n

    pat_canon = re.compile(r'<link[^>]*rel=["\']canonical["\']', re.I)
    pat_desc = re.compile(r'<meta[^>]*name=["\']description["\']', re.I)

    n_canon = count_pages_with(pat_canon)
    n_desc = count_pages_with(pat_desc)
    n_og = sum(1 for h in htmls if "og:title" in read(h) and "og:image" in read(h))
    n_tw = sum(1 for h in htmls if "twitter:card" in read(h))

    def meta_status(label, n, total, miss_hint=""):
        if n == total:
            line("ok", label, f"{n}/{total} 页")
        elif n >= total * 0.7:
            line("warn", f"{label} 大部分覆盖", f"{n}/{total} → 仍有 {total-n} 页缺")
        else:
            line("miss", f"{label} 缺", f"{n}/{total} → {miss_hint}")

    meta_status("canonical URL",     n_canon, len(htmls), "用 inject_meta.py 批量加")
    meta_status("meta description",  n_desc, len(htmls))
    meta_status("Open Graph",        n_og, len(htmls), "微信/X 分享需要")
    meta_status("Twitter Card",      n_tw, len(htmls), "可选但推荐")

    # JSON-LD
    jsonld_count = sum(1 for h in htmls if 'application/ld+json' in read(h))
    if jsonld_count >= len(htmls) * 0.5:
        line("ok", f"JSON-LD 结构化数据", f"{jsonld_count}/{len(htmls)} 页")
    elif jsonld_count > 0:
        line("warn", f"JSON-LD 部分缺", f"只有 {jsonld_count}/{len(htmls)} 页")
    else:
        line("miss", "JSON-LD 全缺", "→ inject_meta.py 加 Article/Book/WebSite")

    # viewport
    has_vp = '<meta name="viewport"' in rep_txt or "<meta name='viewport'" in rep_txt
    line("ok" if has_vp else "miss", "viewport meta（移动端）")

    # language
    has_lang = re.search(r'<html[^>]*lang=', rep_txt, re.I)
    line("ok" if has_lang else "miss", "html lang 属性")

    # 百度统计
    baidu_count = sum(1 for h in htmls if "hm.baidu.com" in read(h))
    if baidu_count == len(htmls):
        line("ok", "百度统计", f"已覆盖 {len(htmls)}/{len(htmls)} 页")
    elif baidu_count > 0:
        line("warn", "百度统计部分覆盖", f"{baidu_count}/{len(htmls)} → 跑 inject_baidu.py 补齐")
    else:
        line("miss", "百度统计未安装", "→ 跑 inject_baidu.py <dir> <hm_id>")

    # ============ JS 渲染检测（GEO 杀手） ============
    print(f"\n{BOLD}┌─ JS 渲染检测（GEO 关键）{RESET}")
    js_rendered_pages = []
    for h in htmls[:50]:  # 抽样前 50 个
        txt = read(h)
        # 启发式：body 文字少（< 800）但 script 多，且有 fetch/innerHTML 操作
        body_match = re.search(r"<body[^>]*>(.+?)</body>", txt, re.S | re.I)
        body_text = re.sub(r"<[^>]+>", "", body_match.group(1)) if body_match else ""
        body_len = len(body_text.strip())
        has_fetch = "fetch(" in txt or "innerHTML" in txt
        has_script_src = txt.count("<script")
        if body_len < 800 and has_fetch and has_script_src >= 2:
            js_rendered_pages.append((h.relative_to(root), body_len))

    if js_rendered_pages:
        line("warn", f"{len(js_rendered_pages)} 个页面可能依赖 JS 渲染")
        for p, blen in js_rendered_pages[:3]:
            line("info", f"   {p}", f"<body> 仅 {blen} 字, 但含 fetch/script")
        line("info", "🔥 这些页面 LLM 爬虫读不到内容！必须预渲染（prerender_js_site.py）")
    else:
        line("ok", "未发现 JS 渲染陷阱（爬虫和 LLM 都能直接读到内容）")

    # ============ 速度（如果给了 base_url） ============
    if base_url:
        print(f"\n{BOLD}┌─ 速度检查{RESET}  {DIM}{base_url}{RESET}")
        try:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w",
                 "%{time_total}|%{size_download}|%{http_code}|%{remote_ip}",
                 "-H", "Accept-Encoding: gzip", base_url],
                capture_output=True, text=True, timeout=10,
            )
            parts = r.stdout.strip().split("|")
            if len(parts) >= 3:
                t, size, code = float(parts[0]), int(parts[1]), parts[2]
                if code != "200":
                    line("miss", f"主页 HTTP {code}")
                elif t < 1.0:
                    line("ok", f"主页 {t:.2f}s · {size // 1024} KB · 极速")
                elif t < 2.0:
                    line("ok", f"主页 {t:.2f}s · {size // 1024} KB")
                else:
                    line("warn", f"主页 {t:.2f}s · {size // 1024} KB · 慢（爬虫可能放弃）")

                # HTTPS check
                if base_url.startswith("https://"):
                    line("ok", "HTTPS")
                else:
                    line("miss", "HTTPS 缺", "AI 抓取意愿低 + 浏览器标'不安全'")

                # gzip check
                r2 = subprocess.run(
                    ["curl", "-sI", "-H", "Accept-Encoding: gzip", base_url],
                    capture_output=True, text=True, timeout=10,
                )
                if "content-encoding: gzip" in r2.stdout.lower() or "content-encoding:gzip" in r2.stdout.lower():
                    line("ok", "gzip 已开启")
                else:
                    line("warn", "gzip 未开启", "→ nginx gzip on")
        except Exception as e:
            line("info", f"速度测试失败：{e}")

    # ============ 总结 ============
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    base = sys.argv[2] if len(sys.argv) > 2 else ""
    audit(sys.argv[1], base)
