#!/usr/bin/env python3
import json
import sys
import os
import urllib.request

TEMPLATES_CACHE_DIR = os.path.expanduser(
    "~/.openclaw/.arkclaw-team/templates")

AGENT_TEMPLATES_URL = "https://arkclaw-team.tos-cn-beijing.volces.com/templates/agent-templates.json"
PROJECT_TEMPLATES_URL = "https://arkclaw-team.tos-cn-beijing.volces.com/templates/project-templates.json"
SKILL_TEMPLATES_URL = "https://arkclaw-team.tos-cn-beijing.volces.com/templates/skill-templates.json"


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


def do_prepare():
    result = {}

    agent_templates_data = download_json(
        AGENT_TEMPLATES_URL, "agent-templates.json")
    if agent_templates_data and isinstance(agent_templates_data, list):
        result["agentTemplates"] = [
            {
                "name": t.get("Name", ""),
                "shortDescription": t.get("ShortDescription", ""),
            }
            for t in agent_templates_data
        ]
    else:
        result["agentTemplates"] = []

    project_templates_data = download_json(
        PROJECT_TEMPLATES_URL, "project-templates.json")
    if project_templates_data and isinstance(project_templates_data, list):
        result["projectTemplates"] = [
            {
                "name": t.get("Name", ""),
                "description": t.get("Description", "")[:200],
                "memberCount": len(t.get("ProjectMembers", [])),
                "memberNames": [m.get("Name", "")
                                for m in t.get("ProjectMembers", [])],
            }
            for t in project_templates_data
        ]
    else:
        result["projectTemplates"] = []

    local_skills = set()
    skills_dir = os.path.expanduser("~/.agents/skills/")
    if os.path.isdir(skills_dir):
        local_skills = set(
            d for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d))
        )

    remote_skills_data = download_json(
        SKILL_TEMPLATES_URL, "skill-templates.json")
    remote_skills = []
    if remote_skills_data and isinstance(remote_skills_data, list):
        remote_skills = [
            {
                "name": s.get("name", ""),
                "description": s.get("description", ""),
            }
            for s in remote_skills_data
        ]

    result["skills"] = sorted(local_skills)
    result["remoteSkills"] = remote_skills

    openclaw_config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    agents = []
    try:
        with open(openclaw_config_path, "r", encoding="utf-8") as f:
            openclaw_config = json.load(f)
        agents_list = openclaw_config.get("agents", {}).get("list", [])
        for agent in agents_list:
            agent_id = agent.get("id", "")
            if not agent_id.startswith("p-"):
                workspace = agent.get("workspace", "")
                agents.append({
                    "name": agent.get("name", ""),
                    "identity": read_workspace_file(workspace, "IDENTITY.md"),
                })
    except Exception:
        pass
    result["agents"] = agents

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    do_prepare()
