#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lp.py — LivePage MCP 极简客户端（qiuyiwu.com PPT 库检索 / 取材）

用法:
  python3 lp.py collections
  python3 lp.py search "<关键词>" [--collection <id>] [--limit N]
  python3 lp.py read <content_id> [--full]
  python3 lp.py context <content_id>
  python3 lp.py assets <content_id>
  python3 lp.py get <content_id> --kind image --out /path/file.jpg
  python3 lp.py --json <上面任一>        # 输出原始 JSON（便于管道）

凭据来源（按序）：$LP_TOKEN / ~/.config/livepage/conn.txt 里的 TOKEN 行
服务: https://qiuyiwu.com/mcp/livepage  (LivePage v1.30.0, MCP streamable-http)
"""
import sys, os, json, base64, argparse, re, urllib.request

URL = os.environ.get("LP_URL", "https://qiuyiwu.com/mcp/livepage")


def token():
    t = os.environ.get("LP_TOKEN")
    if t:
        return t
    p = os.path.expanduser("~/.config/livepage/conn.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.startswith("TOKEN:"):
                return line.split(":", 1)[1].strip()
    raise SystemExit("未找到 token（$LP_TOKEN 或 ~/.config/livepage/conn.txt）")


_ID = [0]


def rpc(method, params=None):
    _ID[0] += 1
    body = {"jsonrpc": "2.0", "id": _ID[0], "method": method}
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token(),
                 "Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8", "ignore"))
    if "error" in d:
        raise SystemExit("MCP error: " + json.dumps(d["error"], ensure_ascii=False))
    return d.get("result", {})


def call(tool, args=None):
    r = rpc("tools/call", {"name": tool, "arguments": args or {}})
    out = []
    for c in r.get("content", []):
        txt = c.get("text", "")
        try:
            out.append(json.loads(txt))
        except Exception:
            out.append(txt)
    return out


def pj(o):
    return json.dumps(o, ensure_ascii=False, indent=1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        sys.argv.pop(1)
        RAW = True
    else:
        RAW = False
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("collections")
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--collection"); s.add_argument("--limit", type=int, default=8)
    r = sub.add_parser("read"); r.add_argument("content_id"); r.add_argument("--full", action="store_true")
    c = sub.add_parser("context"); c.add_argument("content_id")
    a = sub.add_parser("assets"); a.add_argument("content_id")
    g = sub.add_parser("get"); g.add_argument("content_id"); g.add_argument("--kind", required=True, choices=["image", "html"]); g.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.cmd == "collections":
        res = call("livepage_list_collections")
        if RAW: print(pj(res)); return
        for c in res:
            if isinstance(c, dict):
                print(f"{c.get('collection_id')}\t{c.get('title')}\t{c.get('page_count')}p")
    elif args.cmd == "search":
        a = {"query": args.query, "limit": args.limit}
        if args.collection: a["collection_id"] = args.collection
        res = call("livepage_search_content", a)
        if RAW: print(pj(res)); return
        items = (res[0] or {}).get("items", []) if res else []
        for it in items:
            print(f"{it.get('content_id')}\t#{it.get('page_number')}\t{it.get('title')}\t{(it.get('snippet') or '')[:60]}")
        if not items: print("(无结果)")
    elif args.cmd == "read":
        res = call("livepage_read_content", {"content_id": args.content_id})
        if RAW: print(pj(res)); return
        d = res[0] if res else {}
        if isinstance(d, dict):
            print("TITLE:", d.get("title"))
            src = d.get("source", {})
            print(f"SOURCE: {src.get('collection_id')} p{src.get('page_number')}")
            print("--- slide_text ---"); print((d.get("slide_text") or "")[: (100000 if args.full else 1200)])
            ai = d.get("ai_interpretation") or {}
            if ai:
                print("--- ai ---")
                for k in ("audience_takeaway", "claims", "concept_layer", "layout_pattern",
                          "has_chart", "has_diagram", "has_illustration", "has_photo",
                          "narration", "knowledge_atoms"):
                    v = ai.get(k)
                    if v not in (None, "", [], False): print(f"  {k}: {v}")
        else:
            print(d)
    elif args.cmd == "context":
        res = call("livepage_read_context", {"content_id": args.content_id})
        print(pj(res) if RAW else pj(res[0] if res else {}))
    elif args.cmd == "assets":
        res = call("livepage_list_assets", {"content_id": args.content_id})
        print(pj(res) if RAW else pj(res[0] if res else {}))
    elif args.cmd == "get":
        res = call("livepage_get_asset", {"content_id": args.content_id, "kind": args.kind})
        d = res[0] if res else {}
        if not isinstance(d, dict) or "data_base64" not in d:
            print("未取到素材:", pj(d)[:300]); sys.exit(3)
        raw = base64.b64decode(d["data_base64"])
        open(args.out, "wb").write(raw)
        print(f"OK {args.out}  {d.get('mime_type')}  {len(raw)} bytes  sha256={d.get('sha256','')[:16]}")


if __name__ == "__main__":
    main()
