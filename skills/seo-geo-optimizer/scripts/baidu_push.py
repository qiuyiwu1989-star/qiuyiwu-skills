#!/usr/bin/env python3
"""百度站长平台主动推送 — 把 sitemap.xml 里所有 URL 推给百度搜索资源平台。

用法：
  # 1. 从 sitemap.xml 提取 URL 并推送
  BAIDU_PUSH_TOKEN=xxxxxx \\
    python3 baidu_push.py sitemap.xml --site www.qiuyiwu.com

  # 2. 从纯文本 url 列表推送（每行一个 URL）
  BAIDU_PUSH_TOKEN=xxxxxx \\
    python3 baidu_push.py urls.txt --site www.qiuyiwu.com --format txt

  # 3. 从 stdin 推送
  cat urls.txt | BAIDU_PUSH_TOKEN=xxx python3 baidu_push.py - --site www.qiuyiwu.com

  # 4. 只看会推什么，不真发（--dry-run）
  python3 baidu_push.py sitemap.xml --site www.qiuyiwu.com --dry-run

申请 token：
  https://ziyuan.baidu.com/ → 普通收录 → API 推送 → 获取推送用准入密钥

回包字段说明：
  remain          — 当天还可以推送的配额（每日通常 100 万 URL）
  success         — 本次成功推送的条数
  not_same_site   — 不属于该站的 URL（site 参数对不上，会被拒）
  not_valid       — 不合法的 URL（格式错 / 域名错 / 含中文未编码）
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request

ENDPOINT = "http://data.zz.baidu.com/urls"


def extract_urls(source: str, fmt: str) -> list[str]:
    """从 sitemap.xml 或纯文本里提取 URL 列表。source 是文件路径或 '-' (stdin)。"""
    if source == "-":
        text = sys.stdin.read()
    else:
        with open(source, encoding="utf-8") as f:
            text = f.read()

    if fmt == "sitemap" or (fmt == "auto" and "<loc>" in text):
        urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)
    else:
        # 纯文本：每行一个 URL，#  开头当注释
        urls = [
            ln.strip() for ln in text.splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
    # 去重保序
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def push(urls: list[str], site: str, token: str, timeout: int = 30) -> dict:
    """把 urls 推给百度，返回 JSON 响应。"""
    url = f"{ENDPOINT}?site={urllib.parse.quote(site)}&token={urllib.parse.quote(token)}"
    body = "\n".join(urls).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "text/plain"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8") if e.fp else ""
        return {"_http_status": e.code, "_raw": text, "error": str(e)}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": text, "error": "non-json response"}


def main():
    ap = argparse.ArgumentParser(
        description="百度主动推送",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("source", help="sitemap.xml / urls.txt / '-' (stdin)")
    ap.add_argument("--site", required=True,
                    help="站点域名（必须是站长平台已验证的，如 www.qiuyiwu.com）")
    ap.add_argument("--token", default=os.environ.get("BAIDU_PUSH_TOKEN", ""),
                    help="百度推送 token（默认读 BAIDU_PUSH_TOKEN 环境变量）")
    ap.add_argument("--format", choices=["auto", "sitemap", "txt"], default="auto",
                    help="输入格式（默认自动判断）")
    ap.add_argument("--batch", type=int, default=2000,
                    help="单次推送最大 URL 数（百度上限 2000，默认 2000）")
    ap.add_argument("--filter", help="只推匹配该正则的 URL（可选）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将推送的 URL，不真发")
    args = ap.parse_args()

    if not args.token and not args.dry_run:
        print("ERROR: 未设 token。\n  export BAIDU_PUSH_TOKEN=xxxxxx\n  或加 --token xxx", file=sys.stderr)
        sys.exit(1)

    urls = extract_urls(args.source, args.format)
    if args.filter:
        pat = re.compile(args.filter)
        urls = [u for u in urls if pat.search(u)]

    if not urls:
        print("没有可推送的 URL。", file=sys.stderr)
        sys.exit(1)

    print(f"准备推送 {len(urls)} 个 URL 到 site={args.site}", file=sys.stderr)
    print(f"前 3 个样本：", file=sys.stderr)
    for u in urls[:3]:
        print(f"  {u}", file=sys.stderr)
    if len(urls) > 3:
        print(f"  ... 共 {len(urls)} 个", file=sys.stderr)

    if args.dry_run:
        print("\n[dry-run] 实际未推送。", file=sys.stderr)
        return

    total_success = 0
    total_invalid = 0
    total_not_same_site = 0
    last_remain = None
    for i in range(0, len(urls), args.batch):
        chunk = urls[i:i + args.batch]
        print(f"\n推送批次 {i // args.batch + 1}：{len(chunk)} 个 URL", file=sys.stderr)
        resp = push(chunk, args.site, args.token)
        print(json.dumps(resp, ensure_ascii=False, indent=2), file=sys.stderr)
        if "_http_status" in resp:
            print(f"HTTP {resp['_http_status']}，停止后续批次。", file=sys.stderr)
            sys.exit(2)
        total_success += int(resp.get("success", 0))
        total_invalid += len(resp.get("not_valid", []) or [])
        total_not_same_site += len(resp.get("not_same_site", []) or [])
        if "remain" in resp:
            last_remain = resp["remain"]

    print("\n=== 汇总 ===", file=sys.stderr)
    print(f"  成功推送：{total_success} 个", file=sys.stderr)
    print(f"  非本站 URL：{total_not_same_site} 个", file=sys.stderr)
    print(f"  非法 URL：{total_invalid} 个", file=sys.stderr)
    if last_remain is not None:
        print(f"  剩余日配额：{last_remain:,} 条", file=sys.stderr)


if __name__ == "__main__":
    main()
