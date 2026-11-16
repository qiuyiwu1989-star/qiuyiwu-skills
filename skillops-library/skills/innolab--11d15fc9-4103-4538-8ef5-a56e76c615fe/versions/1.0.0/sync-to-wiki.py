#!/usr/bin/env python3
"""
InnoLab Wiki Sync: 本地 → 飞书
用法: python3 sync-to-wiki.py [--dry-run] [--method CG01] [--all]

依赖: openclaw feishu_doc / feishu_wiki 工具（通过 gateway 调用）
本脚本生成同步指令，实际同步由 openclaw 执行。
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
MAPPING_FILE = BASE_DIR / "wiki-mapping.json"
METHODS_DIR = BASE_DIR  # file paths in mapping are relative to innolab root
SYNC_LOG = BASE_DIR / "sync-log.json"


def load_mapping():
    with open(MAPPING_FILE, 'r') as f:
        return json.load(f)


def load_sync_log():
    if SYNC_LOG.exists():
        with open(SYNC_LOG, 'r') as f:
            return json.load(f)
    return {"last_sync": None, "synced": {}}


def save_sync_log(log):
    with open(SYNC_LOG, 'w') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def get_local_content(method_file):
    """读取本地方法文件内容"""
    full_path = METHODS_DIR / method_file
    if not full_path.exists():
        return None
    with open(full_path, 'r') as f:
        return f.read()


def get_local_modified_time(method_file):
    """获取本地文件修改时间"""
    full_path = METHODS_DIR / method_file
    if not full_path.exists():
        return None
    return os.path.getmtime(full_path)


def detect_changes(mapping, sync_log):
    """检测哪些方法有本地修改"""
    changes = []
    for method_id, info in mapping.get("method_pages", {}).items():
        local_file = info.get("file", "")
        if not local_file:
            continue

        local_path = METHODS_DIR / local_file
        if not local_path.exists():
            changes.append({
                "method_id": method_id,
                "file": local_file,
                "status": "missing_local",
                "obj_token": info.get("obj_token"),
                "node_token": info.get("node_token"),
            })
            continue

        mtime = os.path.getmtime(local_path)
        last_synced = sync_log.get("synced", {}).get(method_id, {}).get("timestamp", 0)

        if mtime > last_synced:
            changes.append({
                "method_id": method_id,
                "file": local_file,
                "status": "modified",
                "obj_token": info.get("obj_token"),
                "node_token": info.get("node_token"),
                "local_mtime": datetime.fromtimestamp(mtime).isoformat(),
                "last_synced": datetime.fromtimestamp(last_synced).isoformat() if last_synced else "never",
            })

    return changes


def generate_sync_commands(changes, dry_run=True):
    """生成 openclaw 同步命令"""
    commands = []
    for change in changes:
        if change["status"] == "missing_local":
            print(f"  ⚠️  {change['method_id']}: 本地文件缺失 {change['file']}")
            continue

        if change["status"] == "modified":
            content = get_local_content(change["file"])
            if not content:
                continue

            obj_token = change["obj_token"]
            method_id = change["method_id"]

            if dry_run:
                print(f"  📝 {method_id}: 需要同步 ({change['local_mtime']} > {change['last_synced']})")
            else:
                commands.append({
                    "method_id": method_id,
                    "obj_token": obj_token,
                    "content": content,
                    "file": change["file"],
                })

    return commands


def main():
    parser = argparse.ArgumentParser(description="InnoLab Wiki Sync")
    parser.add_argument("--dry-run", action="store_true", help="只检测变更，不执行同步")
    parser.add_argument("--method", type=str, help="只同步指定方法（如 CG01）")
    parser.add_argument("--all", action="store_true", help="强制同步所有方法")
    parser.add_argument("--list", action="store_true", help="列出所有映射状态")
    args = parser.parse_args()

    mapping = load_mapping()
    sync_log = load_sync_log()

    if args.list:
        print(f"\n📋 InnoLab Wiki 映射状态")
        print(f"   总方法数: {len(mapping.get('method_pages', {}))}")
        print(f"   上次同步: {sync_log.get('last_sync', 'never')}")
        print(f"\n   {'ID':<6} {'状态':<10} {'文件':<45} {'obj_token':<15}")
        print(f"   {'─'*6} {'─'*10} {'─'*45} {'─'*15}")
        for method_id, info in sorted(mapping.get("method_pages", {}).items()):
            local_file = info.get("file", "")
            local_path = METHODS_DIR / local_file
            exists = "✅" if local_path.exists() else "❌"
            obj = info.get("obj_token", "")[:12] + "..." if info.get("obj_token") else "none"
            print(f"   {method_id:<6} {exists:<10} {local_file:<45} {obj}")
        return

    print(f"\n🔍 检测本地变更...")
    changes = detect_changes(mapping, sync_log)

    if args.method:
        changes = [c for c in changes if c["method_id"] == args.method.upper()]
        if not changes:
            print(f"   方法 {args.method} 没有变更或不存在")
            return

    if args.all:
        # 强制所有方法都标记为需要同步
        for method_id, info in mapping.get("method_pages", {}).items():
            local_file = info.get("file", "")
            local_path = METHODS_DIR / local_file
            if local_path.exists():
                changes.append({
                    "method_id": method_id,
                    "file": local_file,
                    "status": "modified",
                    "obj_token": info.get("obj_token"),
                    "node_token": info.get("node_token"),
                    "local_mtime": "forced",
                    "last_synced": "forced",
                })

    modified = [c for c in changes if c["status"] == "modified"]
    missing = [c for c in changes if c["status"] == "missing_local"]

    print(f"\n📊 变更摘要:")
    print(f"   需要同步: {len(modified)} 个方法")
    print(f"   本地缺失: {len(missing)} 个方法")
    print(f"   无需变更: {len(mapping.get('method_pages', {})) - len(changes)} 个方法")

    if not modified and not missing:
        print(f"\n✅ 所有方法已同步，无需操作")
        return

    if missing:
        print(f"\n⚠️  本地缺失的方法:")
        for m in missing:
            print(f"   {m['method_id']}: {m['file']}")

    if modified:
        print(f"\n📝 需要同步的方法:")
        commands = generate_sync_commands(modified, dry_run=args.dry_run)

        if not args.dry_run and commands:
            print(f"\n🚀 生成了 {len(commands)} 条同步指令")
            print(f"   请通过 openclaw 执行实际同步")
            # 保存待同步队列
            queue_file = BASE_DIR / "sync-queue.json"
            with open(queue_file, 'w') as f:
                json.dump(commands, f, indent=2, ensure_ascii=False)
            print(f"   已保存到: {queue_file}")


if __name__ == "__main__":
    main()
