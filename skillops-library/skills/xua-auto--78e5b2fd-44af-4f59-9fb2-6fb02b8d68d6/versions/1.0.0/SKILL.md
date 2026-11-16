---
name: "XUA-auto"
description: "A comprehensive skill that uses the optimal strategy to orchestrate opencli, browser-use, and computer-use for browser or desktop automation tasks."
---

# XUA-auto

XUA-auto is a comprehensive skill designed to execute browser and desktop automation tasks using the best possible strategy. It orchestrates the existing `opencli`, `browser-use`, and `computer-use` skills to complete the user's automation requirements as efficiently as possible.

## Skill Dependencies & Discovery

- **opencli**: The skill name is `opencli`.

## Operational Priority & Strategy

When you receive a task requiring browser or desktop automation, you **MUST strictly follow the priorities below** to select and execute the appropriate skill:

### 1. OpenCLI Priority (API-level / CLI-level Data Extraction)

If the target website of the task has already exposed its capabilities via `opencli`, you **MUST directly use the `opencli` skill**.
(Refer to the list in https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/index.md)
**Supported popular sites include but are not limited to**:
twitter, reddit, tieba, hupu, bilibili, zhihu, xiaohongshu, xiaoe, xueqiu, youtube, v2ex, bloomberg, weibo, linkedin, coupang, boss, ctrip, reuters, smzdm, jike, ke, jimeng, yollomi, linux-do, chaoxing, grok, gemini, maimai, yuanbao, notebooklm, doubao, weread, douban, facebook, imdb, instagram, medium, mubu, sinablog, substack, pixiv, tiktok, google, jd, amazon, 1688, gitee, web, weixin, 36kr, producthunt, ones, band, baidu-scholar, zsxq, bluesky, douyin, google-scholar, gov-law, gov-policy, xianyu, quark, uiverse, nowcoder, wanfang, eastmoney, tdx, ths.

### 2. Web Information Extraction (Read-only Scraping)

If the task is to extract web information (e.g., opening a browser and scraping specific information or content from a webpage) and the site is NOT in the opencli supported list, **directly use the `browser-use` skill**.

### 3. Browser Automation Tasks (Interactive Operations)

If the task involves executing browser automation tasks (e.g., logging in, clicking, filling out forms, pagination, etc.):

- **Prioritize the `browser-use` skill**.
- **Fallback Mechanism**: If `browser-use` encounters a failure during execution, you **MUST use the `computer-use` skill** as a fallback to continue and complete the task.

### 4. Desktop Tasks (System-level Operations)

If the task involves executing desktop tasks (e.g., operating local client software, system-level settings, cross-application file processing, etc.), **directly use the `computer-use` skill**.

---

## Interruption & Conversation Source

When a sub-task hits an interruption requiring the user (login, CAPTCHA, verification, etc.), the handoff is owned entirely by the selected sub-skill (`browser-use` or `computer-use`). XUA-auto **MUST**:

- Let the selected sub-skill follow its own conversation-source branch (see the「当前对话来源」marker in the system prompt). Do not override it.
- Never emit or forward `<computer-handoff />` / `<browser-handoff />` tags at the orchestration layer.

---

## Task Execution Summary (Mandatory Standard)

After the entire task is completed, you **MUST** summarize the execution process of the task in stages. The summary format must include the following elements:

- Clearly state how many stages the task was divided into in total.
- Explain step-by-step which skill was used and what specific sub-task was accomplished.

**Summary Report Example:**

> Task Execution Summary:
> This task was divided into 3 stages in total:
>
> 1. Used the `opencli` skill to complete [fetching the top ten trending topics data from Zhihu].
> 2. Used the `browser-use` skill to complete [opening a non-API supported admin dashboard in the browser and taking a screenshot].
> 3. Used the `computer-use` skill to complete [organizing the screenshot and sending it via the local WeChat client].
