#!/usr/bin/env python3
import subprocess
import json
import sys


def call_rpc(method, params):
    cmd = ["openclaw", "gateway", "call", method,
           "--params", json.dumps(params, ensure_ascii=False), "--timeout", "120000", "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(result.stdout)
        if isinstance(data, dict) and "ok" in data:
            if data.get("ok"):
                return data.get("data")
            else:
                print(
                    f"ERROR: {data.get('error', 'unknown')}", file=sys.stderr)
                sys.exit(1)
        else:
            return data
    except json.JSONDecodeError:
        pass
    print("ERROR: no valid JSON response found", file=sys.stderr)
    sys.exit(1)


if len(sys.argv) < 2:
    print("Usage: finalize.py <projectId>", file=sys.stderr)
    sys.exit(1)

project_id = sys.argv[1]
result = call_rpc("arkclaw.team.project.build.finalize", {"id": project_id})

print(json.dumps({
    "projectId": project_id,
    "status": result.get("status", "pending"),
}, ensure_ascii=False))
