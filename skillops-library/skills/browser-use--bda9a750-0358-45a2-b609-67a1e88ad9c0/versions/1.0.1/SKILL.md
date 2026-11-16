---
name: browser
description: "Browser automation skill. Read this file before any web task and always use `bua` first, including its forwarded `agent-browser` actions; use the legacy browser tool only when `bua` is unavailable."
metadata:
  {
    "openclaw":
      { "emoji": "🌐", "requires": { "config": ["browser.enabled"] } },
  }
---

# Browser Skill Guide

Use this skill for web browsing, page interaction, screenshots, uploads, downloads, and PDF export.

**Profile:** Use `"chromebrowser"` unless the user explicitly asks otherwise.

---

## Priority Rules

### 1) Always use `bua` first

For any browser task:

1. Try `bua` first.
2. Use the legacy direct browser tool only when `bua` is unavailable.
3. On the next new task, try `bua` first again.

Do **not** treat raw browser-tool calls as a peer flow to `bua`.

### 2) Never mention session wiring

- Do **not** include any explicit session argument in examples or commands
- Do **not** mention session env vars in the skill
- If session context is missing, ask for setup help instead of inventing one

### 3) When `bua` counts as unavailable

`bua` is unavailable only when one of these is true:

- the `bua` command is missing
- `bua doctor` or `bua status` consistently fails
- a required forwarded action fails because `agent-browser` is missing or cannot run
- two consecutive `bua` operations fail with the same service-level error

These do **not** count as `bua` being unavailable:

- a page-specific interaction failure
- login / CAPTCHA / payment / verification
- a site-specific redirect or block

---

## `bua` Model

`bua` has two layers:

1. **Native session/tab commands**
   - `open`, `start`, `close`, `focus`, `status`, `list`, `gc`, `tabs`, `doctor`
2. **Forwarded page commands via `agent-browser`**
   - `snapshot`, `screenshot`, `click`, `type`, `fill`, `select`, `hover`, `drag`, `press`
   - `goto`, `back`, `forward`, `reload`, `wait`
   - `get`, `eval`, `cookies`, `storage`, `network`

Use native `bua` commands for session/window/tab control, and forwarded commands for page interaction.

`bua tabs` stays native. It is session-aware and uses stable refs like `T1` and `T2`.

---

## CLI Rules

When `bua` forwards commands to `agent-browser`, use official `agent-browser` CLI style:

- Prefer verb commands: `click`, `fill`, `type`, `press`
- Do **not** default to `act --kind ...`
- Prefer positional arguments over made-up flag shapes like `--ref` and `--text`
- Snapshot output may show `[ref=e37]`, but CLI commands must use `@e37`

Correct pattern:

```bash
bua snapshot --interactive
bua click @e37
bua fill @e37 "hello world"
bua type @e37 " more text"
bua press Enter
```

Wrong pattern:

```bash
bua act --kind type --ref e37 --text "hello world"
```

---

## Core Workflow

Use this default flow:

1. `bua doctor` or `bua status`
2. `bua open` / `bua focus` / `bua tabs ...`
3. `bua snapshot --interactive`
4. interact with `@eN` refs using `click`, `fill`, `type`, `press`
5. re-snapshot after navigation or meaningful DOM change

Rules:

- perform one browser action at a time
- read the result before the next action
- prefer `fill @eN "text"` to replace content
- use `type @eN "text"` to append
- if the page changes, re-snapshot before using refs again

---

## Handoff Rule

Stop and hand off to the user for:

- login
- CAPTCHA
- QR code
- payment
- SMS or email verification
- cookie consent
- confirmation prompts needing human judgment
- explicit user takeover requests
- unstable SSO redirects or loops

When handing off:

1. explain what the user needs to do
2. Do not call `bua screenshot`, do not attach local image media, and do not include any image in Web handoff replies
3. end the reply with `<browser-handoff />`
4. wait for confirmation before continuing

**Conversation-source branch.**

The 4 steps above are the Web branch (kept as-is).

If the system prompt contains `[CONVERSATION SOURCE]` and the value indicates **IM** (feishu / wechat / discord / slack / telegram / etc.), the user is on an IM client with **no browser of their own** — they cannot "go to the page" you describe. Replace step 2 (no screenshot) and step 3 (`<browser-handoff />`) with the IM rule below. Steps 1 and 4 still apply.

**IM handoff rule:**

1. **First line** of your reply MUST be `MEDIA:~/.openclaw/media/outbound/handoff.jpg`. This is an **intent marker** for the skill-switch plugin / openclaw outbound layer — the plugin independently captures a fresh browser screenshot and attaches it to the IM message. The `MEDIA:` line MUST be emitted **unconditionally** as the very first line, even if you have not yet attempted (or have failed) to capture a screenshot yourself. Do NOT use `![](file://...)` markdown — it is blocked by openclaw security policy.
2. After the `MEDIA:` line, write a detailed guidance message in IM-friendly Chinese tailored to the **interrupt category** below. The plugin-attached screenshot tells the user what the page looks like; your text must tell them what they need to do, and what they should reply to you with.
3. **Best-effort screenshot (optional, non-blocking)**: if your environment has `bua` + imagemagick available, you MAY also capture a screenshot as a fallback — but **only after** the `MEDIA:` line is already emitted, and a capture failure (cwd drift, process gone, imagemagick missing, etc.) MUST NOT cause you to omit, retract, or move the `MEDIA:` line:
   ```
   mkdir -p ~/.openclaw/media/outbound
   RAW=$(bua screenshot)
   convert "$RAW" -resize '1280x1280>' -quality 70 ~/.openclaw/media/outbound/handoff.jpg
   ```
4. **Do NOT** output `<browser-handoff />` — IM channel renderers do not recognise it and will leak the literal string into the chat.

**Interrupt categories — write text appropriate to whichever applies:**

- **Login / SMS / email verification**: name the site and page, list the actually-available sign-in methods you saw on screen (scan-QR / phone-code / account-password / third-party / SSO / magic-link / email-code / etc.), and for each method tell the user exactly what data to send you (phone number, code, account, password, …) so you will fill it in for them. If the page only supports scan-QR, instruct the user to scan with the right App from their own phone, and to reply when done. Do NOT tell the user to "go to the browser" or "complete the login yourself" — they have no browser.
- **CAPTCHA**: describe the CAPTCHA (image / slider / click-the-X / arithmetic), ask the user to read it from the screenshot and reply with the answer (or for slider/drag types, ask the user to confirm so you can attempt it programmatically).
- **QR code scan** (e.g. WeChat pay, login QR, device pairing): tell the user which App to scan with, and to reply once they complete the action.
- **Payment**: tell the user to complete the payment on their own device / banking App. Do NOT ask the user to send card numbers, CVV, or banking credentials through IM. Ask them to reply once paid (or to abort).
- **Cookie consent / GDPR banner / confirmation prompts needing human judgement**: describe the choice and ask the user to reply with their decision ("同意 / 拒绝" or whichever options the page shows).
- **Explicit user takeover** (the user previously asked you to stop and let them drive): a short message acknowledging you've stopped + the screenshot is enough; ask them to tell you when to continue.
- **SSO redirect loops / unstable flows**: explain what's stuck (e.g. "登录后被反复跳回登录页"), ask the user how to proceed (retry / switch method / abort).
- **Other**: describe the page state in one or two sentences, name what you need from the user, and tell them how to reply.

**Hard constraints (any violation = rewrite the whole reply):**

- The `MEDIA:` line is an **intent marker** for the plugin layer. NEVER omit it because `bua screenshot` failed, `convert` failed, the handoff.jpg file is missing, or any other infrastructure error — those are the plugin layer's concern, not yours. The only allowed reason to omit `MEDIA:` is when the user has already acknowledged and you are continuing/resuming, not handing off.
- Do NOT use refusal phrases: 「由于隐私我无法」「请你手动操作」「请到浏览器」「为保护隐私」「考虑到安全」 — user-initiated data sharing here is explicitly allowed; never refuse for these reasons.
- Mask sensitive data when echoing back: phone numbers as `138****1111`, codes/passwords as `******`. Never echo the raw value the user sent you.
- Do NOT output `<browser-handoff />` for IM source.
- Do NOT output `![](file://...)` markdown images — use the `MEDIA:` directive only.

**After the user replies** with the data, fill it in on the page (`bua snapshot --interactive` → `bua fill` → `bua click`) and continue, masking the data on any echo. If the page errors, read the error text and tell the user what went wrong + offer alternatives.

Never automate credentials or bypass verification.

---

## Fallback

Use the legacy direct browser-tool flow only when `bua` is unavailable.

Fallback steps:

1. Check port `9222`

```bash
lsof -i :9222 || netstat -tlnp 2>/dev/null | grep 9222 || ss -tlnp | grep 9222
```

2. If not listening, start browser service

```bash
bash /opt/browser-vnc/start-chromium.sh
```

3. Retry the failed operation once

For legacy browser-tool mode, use the normal loop:

`open` -> `snapshot` -> `act` -> re-snapshot if needed

---

## Downloads

In legacy browser-tool mode only, run this before download-related actions:

```bash
curl -fsSL https://browser-use.tos-cn-beijing.volces.com/fix-cdp-download.py | python3
```

Default download directory:

```text
/home/browser/Downloads
```

---

## Tab Cleanup

At task completion:

- prefer `bua tabs list` on the `bua` path
- use `{ "action": "tabs" }` only in fallback mode
- only close tabs opened during the current task

Prompt policy:

- `<= 5` tabs: silent
- `6 - 10` tabs: ask briefly
- `11 - 19` tabs: recommend closing
- `>= 20` tabs: warn about slowdown or crashes

---

## Minimal Examples

```bash
# health
bua doctor

# open a page
bua open --url "https://example.com"

# inspect tabs
bua tabs list

# switch tabs
bua tabs switch T2

# get refs
bua snapshot --interactive

# click / fill / type
bua click @e37
bua fill @e37 "today's weather in Shanghai"
bua type @e37 " more details"

# keyboard
bua press Enter
bua press Control+a
```

Legacy browser-tool examples:

```text
{ "action": "open", "url": "https://example.com" }
{ "action": "snapshot", "interactive": true }
{ "action": "act", "request": { "kind": "click", "ref": "e5" } }
```

---

## Troubleshooting

- If `Unknown command: act` appears, switch to verb commands like `click`, `fill`, `type`, or `press`
- If `Element not found` appears, verify you used `@eN` rather than `eN`, then re-snapshot before retrying
- Do not classify ordinary page interaction failures as `bua` unavailability
- Stop after two consecutive failures and report clearly

---

## One-line Rule

**For any browser task, always try `bua` first. Use the legacy direct browser-tool flow only when `bua` is explicitly unavailable.**
