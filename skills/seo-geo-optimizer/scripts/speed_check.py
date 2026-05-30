#!/usr/bin/env python3
"""
速度体检：每个 URL 跑 3 次 curl，报告时间、大小、是否 gzip

用法:
  python3 speed_check.py <url1> [url2] ...
"""
import subprocess
import sys


GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


def color(t: float) -> str:
    if t < 0.5: return GREEN
    if t < 2.0: return GREEN
    if t < 4.0: return YELLOW
    return RED


def check(url: str):
    print(f"\n  {url}")
    times, sizes = [], []
    gzipped = False
    code = None
    for i in range(3):
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w",
             "%{time_total}|%{size_download}|%{http_code}|%{content_type}",
             "-H", "Accept-Encoding: gzip,br", url],
            capture_output=True, text=True, timeout=15,
        )
        t, sz, c, ct = r.stdout.strip().split("|")
        times.append(float(t))
        sizes.append(int(sz))
        code = c
    # gzip check via -I
    r2 = subprocess.run(["curl", "-sI", "-H", "Accept-Encoding: gzip,br", url],
                        capture_output=True, text=True, timeout=10)
    head_lower = r2.stdout.lower()
    if "content-encoding: gzip" in head_lower:
        gzipped = "gzip"
    elif "content-encoding: br" in head_lower:
        gzipped = "br"
    else:
        gzipped = False

    avg = sum(times) / 3
    sz_kb = sizes[0] / 1024

    status = f"{color(avg)}{avg:.2f}s{RESET}"
    gz_status = f"{GREEN}{gzipped}{RESET}" if gzipped else f"{RED}无压缩{RESET}"
    print(f"    avg {status}  {sz_kb:.0f} KB  HTTP {code}  压缩: {gz_status}")
    print(f"    {DIM}runs: {', '.join(f'{t:.2f}s' for t in times)}{RESET}")
    if avg > 2.0:
        print(f"    {RED}⚠️  慢于 2 秒 · AI 爬虫和搜索引擎可能放弃{RESET}")


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    for url in sys.argv[1:]:
        check(url)
    print()


if __name__ == "__main__":
    main()
