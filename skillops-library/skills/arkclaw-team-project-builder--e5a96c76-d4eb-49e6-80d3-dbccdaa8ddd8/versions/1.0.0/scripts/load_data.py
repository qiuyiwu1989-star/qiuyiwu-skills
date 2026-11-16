#!/usr/bin/env python3
import json
import sys
import os
import urllib.request

TEMPLATES_CACHE_DIR = os.path.expanduser(
    "~/.openclaw/.arkclaw-team/templates")

AGENT_TEMPLATES_URL = "https://arkclaw-team.tos-cn-beijing.volces.com/templates/agent-templates.json"
PROJECT_TEMPLATES_URL = "https://arkclaw-team.tos-cn-beijing.volces.com/templates/project-templates.json"


def read_workspace_file(workspace, filename):
    if not workspace:
        return ""
    filepath = os.path.join(workspace, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def download_json(url, cache_filename):
    os.makedirs(TEMPLATES_CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(TEMPLATES_CACHE_DIR, cache_filename)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")
        parsed = json.loads(data)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        return parsed
    except Exception as e:
        print(f"WARN: failed to download {url}: {e}", file=sys.stderr)
        if os.path.isfile(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None


def load_cached_json(cache_filename):
    cache_path = os.path.join(TEMPLATES_CACHE_DIR, cache_filename)
    if not os.path.isfile(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def do_load_agent():
    if len(sys.argv) < 3:
        print("Usage: load_data.py load-agent <agentId>", file=sys.stderr)
        sys.exit(1)

    agent_id = sys.argv[2]
    openclaw_config_path = os.path.expanduser("~/.openclaw/openclaw.json")

    try:
        with open(openclaw_config_path, "r", encoding="utf-8") as f:
            openclaw_config = json.load(f)
        agents_list = openclaw_config.get("agents", {}).get("list", [])
        for agent in agents_list:
            if agent.get("id", "") == agent_id:
                workspace = agent.get("workspace", "")
                print(json.dumps({
                    "id": agent_id,
                    "name": agent.get("name", ""),
                    "workspace": workspace,
                    "model": agent.get("model", ""),
                    "tools": agent.get("tools", {}),
                    "identity": read_workspace_file(workspace, "IDENTITY.md"),
                    "soul": read_workspace_file(workspace, "SOUL.md"),
                    "agentsMd": read_workspace_file(workspace, "AGENTS.md"),
                }, ensure_ascii=False, indent=2))
                return
        print(f"ERROR: agent '{agent_id}' not found", file=sys.stderr)
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def do_load_template():
    if len(sys.argv) < 3:
        print("Usage: load_data.py load-template <name>", file=sys.stderr)
        sys.exit(1)

    template_name = sys.argv[2]
    data = load_cached_json("agent-templates.json")
    if data is None:
        data = download_json(AGENT_TEMPLATES_URL, "agent-templates.json")
    if not data:
        print("ERROR: agent-templates not available", file=sys.stderr)
        sys.exit(1)

    try:
        for t in data:
            if t.get("Name", "") == template_name:
                print(json.dumps({
                    "name": t.get("Name", ""),
                    "role": t.get("Role", ""),
                    "soul": t.get("Soul", ""),
                    "agent": t.get("Agent", ""),
                    "skills": t.get("Skills", []),
                }, ensure_ascii=False, indent=2))
                return
        print(f"ERROR: template '{template_name}' not found", file=sys.stderr)
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def do_load_project_template():
    if len(sys.argv) < 3:
        print("Usage: load_data.py load-project-template <name>",
              file=sys.stderr)
        sys.exit(1)

    template_name = sys.argv[2]
    data = load_cached_json("project-templates.json")
    if data is None:
        data = download_json(PROJECT_TEMPLATES_URL, "project-templates.json")
    if not data:
        print("ERROR: project-templates not available", file=sys.stderr)
        sys.exit(1)

    try:
        for t in data:
            if t.get("Name", "") == template_name:
                members = t.get("ProjectMembers", [])
                print(json.dumps({
                    "name": t.get("Name", ""),
                    "description": t.get("Description", ""),
                    "image": t.get("Image", ""),
                    "locale": t.get("Locale", ""),
                    "members": [
                        {
                            "name": m.get("Name", ""),
                            "role": m.get("Role", ""),
                            "soul": m.get("Soul", ""),
                            "skills": m.get("Skills", []),
                            "locale": m.get("Locale", ""),
                        }
                        for m in members
                    ],
                }, ensure_ascii=False, indent=2))
                return
        print(f"ERROR: project template '{template_name}' not found",
              file=sys.stderr)
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: load_data.py <command> [args...]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  load-agent <agentId>              Load agent detail (soul, agentsMd) by id",
              file=sys.stderr)
        print("  load-template <name>              Load agent template detail (soul, agent, skills)",
              file=sys.stderr)
        print("  load-project-template <name>      Load project template detail (members with soul & skills)",
              file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "load-agent":
        do_load_agent()
    elif command == "load-template":
        do_load_template()
    elif command == "load-project-template":
        do_load_project_template()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
