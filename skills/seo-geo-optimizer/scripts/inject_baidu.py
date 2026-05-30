#!/usr/bin/env python3
"""
给一个目录下所有 *.html 注入百度统计 snippet
- 自动检测已有的，不重复注入
- 注入位置：</head> 之前

用法:
  python3 inject_baidu.py <dir> <hm_id>
  python3 inject_baidu.py <dir> <hm_id> --dry-run

例:
  python3 inject_baidu.py /var/www/site e83757828db0e57520651bc1be79715c
"""
import re
import sys
from pathlib import Path


def snippet(hm_id: str) -> str:
    return f"""<script>
var _hmt = _hmt || [];
(function() {{
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?{hm_id}";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
}})();
</script>"""


def inject(html_path: Path, hm_id: str, dry_run: bool = False) -> str:
    text = html_path.read_text(encoding="utf-8")
    if "hm.baidu.com" in text:
        return "skipped (already present)"
    if "</head>" not in text:
        return "skipped (no </head>)"
    new = text.replace("</head>", snippet(hm_id) + "\n</head>", 1)
    if not dry_run:
        html_path.write_text(new, encoding="utf-8")
    return "injected"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    root = Path(sys.argv[1]).expanduser().resolve()
    hm_id = sys.argv[2]
    dry = "--dry-run" in sys.argv

    if not root.is_dir():
        print(f"错误：{root} 不是目录")
        sys.exit(1)

    html_files = [p for p in root.rglob("*.html") if not any(part.startswith(".") for part in p.parts)]
    print(f"扫到 {len(html_files)} 个 HTML")
    print(f"hm_id: {hm_id}")
    if dry:
        print("[DRY RUN]")

    counts = {"injected": 0, "skipped (already present)": 0, "skipped (no </head>)": 0}
    for h in html_files:
        result = inject(h, hm_id, dry)
        counts[result] = counts.get(result, 0) + 1
        print(f"  {result:30s} {h.relative_to(root)}")

    print()
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
