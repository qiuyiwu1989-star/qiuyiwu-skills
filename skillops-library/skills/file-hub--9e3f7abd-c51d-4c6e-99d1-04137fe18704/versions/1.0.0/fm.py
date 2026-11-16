#!/usr/bin/env python3
"""文件管理器 - 文件上传到COS + 索引管理"""

import json, subprocess, sys, os, hashlib, mimetypes
from datetime import datetime, timezone
from pathlib import Path

INDEX_PATH = Path(__file__).parent / "index.json"
COS_BUCKET = "opendesign-1359505647"
COS_REGION = "ap-guangzhou"
COS_BASE = f"https://{COS_BUCKET}.cos.{COS_REGION}.myqcloud.com"

def load_index():
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            return json.load(f)
    return {"version": 1, "updated": "", "stats": {"total_files": 0, "total_size_bytes": 0, "by_type": {}}, "files": []}

def save_index(idx):
    idx["updated"] = datetime.now(timezone.utc).isoformat()
    with open(INDEX_PATH, "w") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

def get_file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:12]

def upload_to_cos(local_path, cos_key):
    """上传文件到COS"""
    result = subprocess.run(
        ["coscmd", "upload", str(local_path), cos_key],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ COS上传失败: {result.stderr}")
        return False
    return True

def add_file(local_path, category="inbound", tags=None, desc=""):
    """添加文件到系统"""
    local_path = Path(local_path)
    if not local_path.exists():
        print(f"❌ 文件不存在: {local_path}")
        return None

    idx = load_index()
    
    # 检查重复
    fhash = get_file_hash(local_path)
    for f in idx["files"]:
        if f.get("hash") == fhash:
            print(f"⚠️ 文件已存在: {f['name']} (hash: {fhash})")
            return f

    # 文件信息
    fsize = local_path.stat().st_size
    ftype = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
    fname = local_path.name
    now = datetime.now(timezone.utc).isoformat()

    # COS key
    cos_key = f"{category}/{fname}"

    # 上传到COS
    print(f"📤 上传到COS: {cos_key}")
    if not upload_to_cos(local_path, cos_key):
        return None

    # 构建记录
    entry = {
        "id": fhash,
        "name": fname,
        "size": fsize,
        "type": ftype,
        "category": category,
        "tags": tags or [],
        "desc": desc,
        "hash": fhash,
        "cos_key": cos_key,
        "cos_url": f"{COS_BASE}/{cos_key}",
        "uploaded": now,
        "source": "feishu"
    }

    idx["files"].append(entry)
    idx["stats"]["total_files"] = len(idx["files"])
    idx["stats"]["total_size_bytes"] += fsize
    
    # 按类型统计
    type_key = ftype.split("/")[0] if "/" in ftype else ftype
    idx["stats"]["by_type"][type_key] = idx["stats"]["by_type"].get(type_key, 0) + 1
    
    save_index(idx)
    
    print(f"✅ 已添加: {fname}")
    print(f"   大小: {fsize:,} bytes")
    print(f"   类型: {ftype}")
    print(f"   COS:  {entry['cos_url']}")
    return entry

def list_files(category=None, tag=None, limit=50):
    """列出文件"""
    idx = load_index()
    files = idx["files"]
    
    if category:
        files = [f for f in files if f["category"] == category]
    if tag:
        files = [f for f in files if tag in f.get("tags", [])]
    
    files = sorted(files, key=lambda x: x["uploaded"], reverse=True)[:limit]
    
    print(f"📋 共 {len(files)} 个文件 (总计 {idx['stats']['total_files']})\n")
    for f in files:
        tags_str = f" [{','.join(f['tags'])}]" if f.get("tags") else ""
        size_kb = f["size"] / 1024
        print(f"  {f['uploaded'][:10]}  {f['category']:10}  {size_kb:>8.1f}KB  {f['name']}{tags_str}")
    return files

def search_files(query):
    """搜索文件"""
    idx = load_index()
    query = query.lower()
    results = []
    for f in idx["files"]:
        if (query in f["name"].lower() or 
            query in f.get("desc", "").lower() or 
            any(query in t.lower() for t in f.get("tags", []))):
            results.append(f)
    
    print(f"🔍 搜索 '{query}' 找到 {len(results)} 个结果\n")
    for f in results:
        print(f"  {f['name']}  →  {f['cos_url']}")
    return results

def sync_index_to_cos():
    """同步索引到COS"""
    subprocess.run(["coscmd", "upload", str(INDEX_PATH), ".index/index.json"], capture_output=True)
    print("✅ 索引已同步到COS")

def sync_index_to_server():
    """同步索引到服务器（凭据从 vault / 环境变量读取，不硬编码）"""
    import os
    pw = os.environ.get("ZAO_SERVER_PASS") or _vault_get("zao-server/ubuntu", "PASS")
    host = os.environ.get("ZAO_SERVER_HOST", "146.56.239.22")
    user = os.environ.get("ZAO_SERVER_USER", "ubuntu")
    if not pw:
        print("⚠️ 未取到服务器凭据（设 ZAO_SERVER_PASS 或 vault: zao-server/ubuntu）"); return
    subprocess.run([
        "sshpass", "-p", pw, "scp", "-o", "StrictHostKeyChecking=no",
        str(INDEX_PATH), f"{user}@{host}:/var/www/html/files/.index/index.json"
    ], capture_output=True)
    print("✅ 索引已同步到服务器")


def _vault_get(entry, field):
    """从本地 vault 读取（见 vault/pw）；失败返回 None"""
    import os, subprocess
    pwfile = os.path.expanduser("~/.config/pw/master")
    if not os.path.exists(pwfile):
        return None
    try:
        env = dict(os.environ, PW_MASTER=open(pwfile).read().strip())
        out = subprocess.run(["bash", os.path.expanduser("~/.openclaw/workspace/vault/pw"), "show", entry],
                             capture_output=True, text=True, env=env, timeout=10).stdout
        for line in out.splitlines():
            if line.startswith(field + ":"):
                return line.split(":", 1)[1].strip()
    except Exception:
        return None
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  fm.py add <文件路径> [category] [tags] [desc]  - 上传文件")
        print("  fm.py list [category] [tag]                    - 列出文件")
        print("  fm.py search <关键词>                           - 搜索文件")
        print("  fm.py sync                                      - 同步索引")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 3:
        local_path = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else "inbound"
        tags = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else []
        desc = sys.argv[5] if len(sys.argv) > 5 else ""
        add_file(local_path, category, tags, desc)
    elif cmd == "list":
        cat = sys.argv[2] if len(sys.argv) > 2 else None
        list_files(category=cat)
    elif cmd == "search" and len(sys.argv) >= 3:
        search_files(sys.argv[2])
    elif cmd == "sync":
        sync_index_to_cos()
        sync_index_to_server()
    else:
        print("未知命令")
