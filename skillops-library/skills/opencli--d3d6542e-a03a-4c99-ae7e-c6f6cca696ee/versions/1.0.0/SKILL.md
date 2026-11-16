---
name: "opencli"
description: "CLI tool for scraping Chinese and international platforms. Use this FIRST for supported sites before falling back to browser-use."
---

# OpenCLI

CLI tool for scraping Chinese and international platforms with structured output.

When the user's task involves fetching data from supported sites, **try opencli first** before falling back to the browser tool.

## Installation & Setup

If opencli is **not installed**, or if you encounter **any execution errors** (e.g., daemon not running, extension not connected), you **must** use the provided script to install or fix the environment:

```bash
sudo bash $(dirname "$0")/install.sh
```

**Success Criteria after running install.sh:**

1. `opencli doctor` outputs "Everything looks good".
2. Chromium debugging port `9222` is listening.
3. Extension is correctly loaded.

## Usage

Before using OpenCLI, check whether `/opt/browser-vnc/start-opencli-chromium.sh` exists. If it does not, run the install command first to set up and launch the browser.

Every command must inline the CDP env when browser extension is needed:

```bash
OPENCLI_CDP_ENDPOINT=http://127.0.0.1:9222 opencli <site> <command> [flags]
```

Default to `-f json` for structured output.

## Supported sites & Scope

Do not rely on hardcoded lists. **Always verify the scope of supported sites and commands dynamically**:

```bash
# Get all supported sites and platforms
opencli list -f json
```

## Discover & compose

Before executing, discover what the site can do and consider whether commands can be chained:

```bash
OPENCLI_CDP_ENDPOINT=http://127.0.0.1:9222 opencli <site> --help
```

For example, if zhihu has `search` + `question`, you can search a topic then drill into the best answers. If bilibili has `search` + `subtitle`, you can find a video then extract its transcript. Proactively suggest these compositions to the user.

## Fallback

- If the site is **not** in the `opencli list` output, you must fall back to the browser tool (Claude in Chrome).
- If a supported site's opencli command returns empty, errors, or no useful result after one retry, you must fall back to the browser tool to complete the task. Do not give up — use Claude in Chrome as the fallback path to finish what opencli could not.
- Complex UI interaction (forms, CAPTCHA, file uploads) — use the browser tool directly.

## Environment notes

No Electron apps. Do not attempt `opencli cursor/notion/antigravity`.
