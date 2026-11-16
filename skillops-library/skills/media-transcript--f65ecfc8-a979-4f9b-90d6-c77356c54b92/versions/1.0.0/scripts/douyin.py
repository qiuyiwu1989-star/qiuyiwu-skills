#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
douyin.py — 解析抖音分享链接，拿到无水印视频直链 + 元数据。

用法:
  python3 douyin.py "<url>" --json out.json [--provider https://api.douyin.wtf]
输出 JSON:
  {ok, aweme_id, title, description, author, duration_ms, tags,
   mp4: {url,size_bytes,height}, streams: [...], hls: ...}

依赖：标准库 urllib（无第三方依赖）
"""
import sys, json, re, time, argparse, urllib.request, urllib.error, http.cookiejar

# 共享 opener：带 cookie jar（/auth/login 走 cookie 会话，不是 Bearer）
_CJ = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_CJ))
_OPENER.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36")]


def _req(url, data=None, headers=None, method=None, timeout=30):
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with _OPENER.open(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def resolve_url(url):
    """短链 v.douyin.com/xxx -> 真实页面 URL"""
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.geturl()
    except Exception:
        return url


def aweme_id_from(url):
    m = re.search(r"/video/(\d+)", url) or re.search(r"(\d{15,})", url)
    return m.group(1) if m else None


def get_demo_creds(provider):
    raw = _req(provider + "/api/v1/auth/demo")
    d = json.loads(raw)
    return d["data"]["username"], d["data"]["password"]


def login(provider):
    user, pw = get_demo_creds(provider)
    raw = _req(provider + "/api/v1/auth/login", data={"username": user, "password": pw})
    d = json.loads(raw)
    if not d.get("success"):
        raise RuntimeError("demo 登录失败: " + json.dumps(d, ensure_ascii=False))
    # 认证靠 cookie jar（无 access_token 字段）
    return True


def fetch_video(provider, aweme_id):
    q = provider + f"/api/v1/douyin/video?aweme_id={aweme_id}"
    raw = _req(q)
    d = json.loads(raw)
    return d


def poll_task(provider, task_id, tries=20, interval=4):
    d = {}
    for _ in range(tries):
        raw = _req(provider + f"/api/v1/tasks/{task_id}")
        d = json.loads(raw)
        st = d.get("data", {}).get("state")
        if st in ("done", "succeeded", "failed"):
            return d
        time.sleep(interval)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--json", default="")
    ap.add_argument("--provider", default="https://api.douyin.wtf")
    args = ap.parse_args()

    url = resolve_url(args.url)
    wid = aweme_id_from(url)
    if not wid:
        print(json.dumps({"ok": False, "error": "无法提取 aweme_id", "url": url}, ensure_ascii=False))
        sys.exit(2)

    token = login(args.provider)
    d = fetch_video(args.provider, wid)

    # 202 = 异步任务
    if d.get("data", {}).get("task_id"):
        d = poll_task(args.provider, d["data"]["task_id"])
    payload = d.get("data", {}).get("data") or d.get("data", {})
    if not payload or "media" not in payload:
        print(json.dumps({"ok": False, "error": "解析失败", "raw": d}, ensure_ascii=False))
        sys.exit(3)

    media = payload.get("media", {})
    mp4s = [s for s in media.get("streams", []) if s.get("format") == "mp4"]
    mp4s.sort(key=lambda x: x.get("size_bytes") or 9e18)
    best = mp4s[0] if mp4s else (media.get("video") or {})
    out = {
        "ok": True,
        "aweme_id": wid,
        "web_url": payload.get("web_url") or f"https://www.douyin.com/video/{wid}",
        "title": payload.get("title"),
        "description": payload.get("description"),
        "author": (payload.get("author") or {}).get("nickname") or (payload.get("author") or {}).get("uid"),
        "duration_ms": payload.get("duration_ms"),
        "tags": payload.get("tags"),
        "watermark": best.get("watermark"),
        "mp4": {"url": best.get("url"), "size_bytes": best.get("size_bytes"), "height": best.get("height")},
        "streams": [{"format": s.get("format"), "height": s.get("height"),
                     "size_bytes": s.get("size_bytes"), "url": s.get("url")} for s in media.get("streams", [])],
    }
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    if args.json:
        open(args.json, "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
