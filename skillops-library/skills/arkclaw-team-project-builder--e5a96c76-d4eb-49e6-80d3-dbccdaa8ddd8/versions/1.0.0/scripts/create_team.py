#!/usr/bin/env python3
import subprocess
import json
import sys


def read_json_arg(raw):
    if raw.startswith("@"):
        filepath = raw[1:]
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(raw)


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


if len(sys.argv) < 3:
    print("Usage: create_team.py <projectId> @<file-or-json>", file=sys.stderr)
    sys.exit(1)

project_id = sys.argv[1]
team = read_json_arg(" ".join(sys.argv[2:]))

update_params = {"id": project_id}
if "name" in team:
    update_params["name"] = team["name"]
if "description" in team:
    update_params["description"] = team["description"]
if "draftSuggestion" in team:
    update_params["draftSuggestion"] = team["draftSuggestion"]

errors = []

if len(update_params) > 1:
    try:
        call_rpc("arkclaw.team.project.update", update_params)
    except SystemExit:
        errors.append("project.update failed")

experts = team.get("experts", [])
if experts:
    try:
        call_rpc("arkclaw.team.project.member.batch_add", {
            "projectId": project_id,
            "experts": experts,
        })
    except SystemExit:
        errors.append("member.batch_add failed")

try:
    call_rpc("arkclaw.team.project.build.finalize", {"id": project_id})
except SystemExit:
    errors.append("project.build.finalize failed")

result = {
    "projectId": project_id,
    "name": team.get("name", ""),
    "expertCount": len(experts),
    "expertNames": [e.get("name", "") for e in experts],
}

if errors:
    result["errors"] = errors
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

result["status"] = "pending"
print(json.dumps(result, ensure_ascii=False))
