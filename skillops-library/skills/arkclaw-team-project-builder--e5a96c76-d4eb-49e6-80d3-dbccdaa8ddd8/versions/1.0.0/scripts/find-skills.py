#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.parse

SKILLS_API_BASE = "https://skills.volces.com/v1/skills"


def do_find_skills():
    if len(sys.argv) < 3:
        print(
            "Usage: find-skills.py <query> [page] [pageSize]", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[2]
    page = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    page_size = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    params = urllib.parse.urlencode({
        "query": query,
        "pageNumber": page,
        "pageSize": page_size,
    })
    url = f"{SKILLS_API_BASE}?{params}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: failed to search skills: {e}", file=sys.stderr)
        sys.exit(1)

    skills_raw = data.get("Skills", [])
    results = []
    for s in skills_raw:
        slug = s.get("Slug", "")
        metadata = s.get("Metadata", {})
        display_desc = ""
        if isinstance(metadata, dict):
            display_desc = metadata.get("DisplayDescription", "")
        if not display_desc:
            display_desc = s.get("Description", "")
        results.append({
            "name": slug,
            "description": display_desc,
            "downloadCount": s.get("DownloadCount", 0),
        })

    output = {
        "query": query,
        "total": len(results),
        "results": results,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) < 2:
        print("Usage: find-skills.py <command> [args...]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print(
            "  find <query> [page] [pageSize]    Search skills by keyword", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command == "find":
        do_find_skills()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
