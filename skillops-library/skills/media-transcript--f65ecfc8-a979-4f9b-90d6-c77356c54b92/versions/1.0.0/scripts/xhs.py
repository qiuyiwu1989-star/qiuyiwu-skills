#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xhs.py — 解析小红书分享链接，拿到无水印视频直链 + 元数据。

原理：小红书分享页 HTML 内嵌 window.__INITIAL_STATE__，从中提取
      noteData.data.noteData.video.media.stream.{h264,h265}[].masterUrl

用法:
  python3 xhs.py "<url>" --json out.json
输出 JSON（与 douyin.py 对齐，便于 transcribe.sh 统一消费）:
  {ok, aweme_id, web_url, title, description, author, duration_ms, tags,
   watermark, mp4:{url,size_bytes,height}, streams:[...]}

⚠️ 脆弱路径：xsec_token 有时效、页面结构变更会断。属于"借分享页缝隙"。
"""
import sys, json, re, argparse, urllib.request


UA_M = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")


def http_get(url, headers=None, timeout=25):
    h = {"User-Agent": UA_M, "Referer": "https://www.xiaohongshu.com/"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def extract_state(html):
    m = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*</script>', html, re.S)
    if not m:
        m = re.search(r'__INITIAL_STATE__\s*=\s*(.*?)</script>', html, re.S)
    if not m:
        return None
    raw = re.sub(r'\bundefined\b', 'null', m.group(1))
    try:
        return json.loads(raw)
    except Exception:
        # 尽力截到平衡的 JSON
        for end in range(len(raw), 0, -1):
            try:
                return json.loads(raw[:end])
            except Exception:
                continue
    return None


def find_note(state):
    """在 __INITIAL_STATE__ 里定位含 video.media.stream 的 note 对象"""
    def walk(o, depth=0):
        if depth > 8:
            return None
        if isinstance(o, dict):
            if "media" in o and isinstance(o["media"], dict) and "stream" in o["media"]:
                return o
            for v in o.values():
                r = walk(v, depth + 1)
                if r:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = walk(v, depth + 1)
                if r:
                    return r
        return None
    return walk(state)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    note_id = re.search(r'/(?:item|explore)/([0-9a-f]+)', a.url)
    tid = note_id.group(1) if note_id else ""
    try:
        html = http_get(a.url)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"抓取页面失败: {e}"}, ensure_ascii=False))
        sys.exit(2)

    state = extract_state(html)
    if not state:
        print(json.dumps({"ok": False, "error": "未找到 __INITIAL_STATE__（可能被风控/需登录/token 过期）"},
                         ensure_ascii=False))
        sys.exit(3)

    note = find_note(state)
    if not note:
        print(json.dumps({"ok": False, "error": "未在 state 中找到 video.media.stream"}, ensure_ascii=False))
        sys.exit(4)

    streams = note["media"]["stream"]
    cands = []
    for codec, lst in streams.items():
        for s in (lst or []):
            if s.get("masterUrl"):
                cands.append({
                    "codec": codec, "format": s.get("format", "mp4"),
                    "height": s.get("height"), "size_bytes": s.get("size"),
                    "duration_ms": s.get("duration"), "url": s["masterUrl"],
                })
    if not cands:
        print(json.dumps({"ok": False, "error": "stream 中无可用 masterUrl"}, ensure_ascii=False))
        sys.exit(5)
    cands.sort(key=lambda x: x.get("size_bytes") or 9e18)
    best = cands[0]

    # 元数据（note 里可能有 title/desc/user/tagList；也可能在 noteData 外层）
    def deep(o, key, depth=0):
        if depth > 8:
            return None
        if isinstance(o, dict):
            if key in o and o[key]:
                return o[key]
            for v in o.values():
                r = deep(v, key, depth + 1)
                if r:
                    return r
        return None

    title = note.get("title") or deep(state, "title") or ""
    desc = note.get("desc") or deep(state, "desc") or ""
    user = note.get("user") or {}
    author = user.get("nickName") or user.get("nickname") or deep(state, "nickName") or ""
    tags = [t.get("name") for t in (note.get("tagList") or []) if isinstance(t, dict)]

    out = {
        "ok": True,
        "platform": "xiaohongshu",
        "aweme_id": note.get("noteId") or note.get("id") or tid,
        "web_url": f"https://www.xiaohongshu.com/explore/{tid}" if tid else a.url,
        "title": title,
        "description": desc,
        "author": author,
        "duration_ms": best.get("duration_ms"),
        "tags": tags,
        "watermark": False,
        "mp4": {"url": best["url"], "size_bytes": best.get("size_bytes"), "height": best.get("height")},
        "streams": cands,
    }
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
