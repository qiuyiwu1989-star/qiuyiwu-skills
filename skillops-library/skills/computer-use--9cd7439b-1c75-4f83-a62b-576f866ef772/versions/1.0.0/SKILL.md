---
name: computer-use
description: "CUA (Computer Use Agent) for visual GUI-based computer control + Office document automation. When you need screenshots/scrolling/clicking/dragging, Office document operations (Word/Excel/PowerPoint), or need to run CUA commands, **you MUST read this SKILL.md first** — it includes mandatory tags, preflight checks, single-process rules, and operating procedures."
---

# Computer Use (CUA) Guide

CUA visually controls a computer to complete GUI tasks (screenshots, scrolling, clicking, dragging, typing, in-page operations) **AND** supports Office document automation via officecli (Word, Excel, PowerPoint).

---

## 📋 执行前检查清单（MUST READ BEFORE START）

在执行任何CUA任务前，**必须**确认以下所有事项：

- [ ] **1. 已读取本SKILL.md全文**
- [ ] **2. 理解了必须实时展示进度**（不能等完成后再汇总）
- [ ] **3. 理解了两阶段执行流程**（Phase 1: 预检 + Phase 2: tail steps.jsonl实时展示）
- [ ] **4. 明确禁止使用 process log/poll 获取进度**
- [ ] **5. 知道每个 ✅ 必须单独一行**
- [ ] **6. 理解必须过滤掉技术细节（坐标、路径、步骤编号等）**

**如果以上任意一项未确认，请重新阅读本文档！**

---

## ✅ 执行前必须展示检查清单确认

**在正式执行CUA任务前，必须先向用户展示以下内容：**

```
📋 执行前检查清单确认：
- [x] 1. 已读取本SKILL.md全文
- [x] 2. 理解了必须实时展示进度
- [x] 3. 理解了两阶段执行流程
- [x] 4. 明确禁止使用 process log/poll 获取进度
- [x] 5. 知道每个 ✅ 必须单独一行
- [x] 6. 理解必须过滤掉技术细节

✅ 检查清单确认完毕，开始执行任务！
```

**这一步必须展示，不能跳过！**

---

## ⚠️ 最重要：必须实时展示进度！

**这是最重要的要求，绝对不能违反：**

- ❌ **禁止**：等任务全部完成后，一次性汇总展示所有步骤
- ✅ **必须**：每完成一个步骤，就**立即**展示该步骤的进度
- ✅ **必须**：使用 tail `steps.jsonl` 的方式，实时读取每一个新步骤并展示

用户需要看到**实时进度反馈**，而不是最后才看到结果！

---

## ⚠️ CRITICAL: 强制标签与停止规则

### `<model-switch-multimodal />`

如果预检显示不支持多模态，**必须**返回 `<model-switch-multimodal />` 并停止。结果**只能**来自脚本输出——**绝不能**从对话上下文推断。

### `<computer-handoff />`

如果任务中断或需要用户手动操作，**必须**：

1. 立即停止CUA进程
2. 记录检查点（已完成步骤、当前窗口/页面、下一步、阻碍）
3. 在最后一行返回 `<computer-handoff />`
   - Web handoff 不要压缩/附加截图,不要输出媒体指令,不要附加本地图片媒体。
   - 对 Web 或来源缺失，上面 3 步就是完整规则，不使用 IM 分支文案。
   - 仅当 system prompt 注入的「当前对话来源」标记明确为 **IM** 时，禁止返回 `<computer-handoff />` 标签（该标签在多数 IM channel 渲染层不被识别，作为字面字符串残留 —— 飞书显示乱码、Slack 丢成文本、Discord 直接吞掉，行为各异但都不是用户期望的），改为按下方「⏸️ 中断与交接」的 IM 分支输出截图与引导文案。
4. 恢复时：从检查点继续，执行下一步

### 预检失败处理 — 🚨 必须先向用户解释再返回标签

> **绝对禁止静默返回标签！用户必须看到失败原因。**

| 预检结果                           | 你必须做的                                                                                                               | 用户看到的输出                |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------- |
| 输出 `<model-switch-multimodal />` | ① 先用自然语言告诉用户**当前模型不支持多模态（图像输入）**，CUA 无法执行 ② 然后返回 `<model-switch-multimodal />` 并停止 | 见下方「❌ 多模态不支持」示例 |
| 退出码非零且**无** switch tag      | ① 用自然语言解释**具体失败原因**（如配置缺失、二进制不存在、进程冲突等） ② 返回 `<computer-handoff />` 并停止            | 见下方「❌ 预检其他失败」示例 |

#### ❌ WRONG (静默返回标签，用户一头雾水)

```
配置模型标签。
<model-switch-multimodal />
```

#### ✅ CORRECT — 多模态不支持时

```
🔍 正在进行预检检查...
❌ 预检失败：当前模型（doubao-pro-32k）不支持多模态（图像输入）。
   CUA（计算机视觉操作）需要模型具备截图/视觉理解能力才能执行 GUI 任务。
   请切换到支持 image 输入的多模态模型后重试。

<model-switch-multimodal />
```

#### ✅ CORRECT — 其他预检失败时（如二进制缺失）

```
🔍 正在进行预检检查...
❌ 预检失败：CUA 二进制文件不存在或不可执行（/root/.cua/cua）。
   请确认 CUA 组件已正确安装后再试。

<computer-handoff />
```

---

## 🚀 命令执行

```bash
bash skills/computer-use/scripts/cua.sh run "<task_content>"
```

此命令会自动运行预检 + 使用 openclaw 配置（`/root/.openclaw/openclaw.json`）执行 CUA。你**不需要**单独的预检步骤。

`<task_content>` 应包含：目标页面/应用、预期结果（验收标准）、可接受的回退路径。

---

## 🚨 进度报告 — 强制执行规则（简化版）

### 🚫 绝对禁止的做法

- ❌ **禁止**使用 `process` 工具的 `log` / `poll` 获取进度
- ❌ **禁止**将多个步骤挤在同一行
- ❌ **禁止**显示技术细节（坐标、截图路径、时间、步骤编号、原始工具名、原始JSON等）

### ✅ 必须使用的做法

- ✅ **必须**直接启动CUA任务，等待完成
- ✅ **必须**任务完成后从 `steps.json` 读取所有步骤
- ✅ **必须**将每个步骤渲染为一行 `✅ <action description>`
- ✅ **必须**用 `\n` 严格分隔每个步骤
- ✅ **必须**只显示自然语言的动作描述（从 `llm.rationales[0]` 提取）

### 输出格式（唯一正确格式）

```
🔍 正在进行预检检查...
✅ 预检通过，模型支持多模态，开始执行任务

✅ <动作描述1>
✅ <动作描述2>
✅ <动作描述3>

✅ 任务完成：<最终结果描述>

📁 运行文件保存路径：<run_dir>
```

---

## 📝 执行流程（必读！实时进度优先）

### 重要区分：两个文件的用途

- **`steps.jsonl`**：**执行中**实时写入，每行一个JSON步骤（**必须用于实时进度展示**）
- **`steps.json`**：**完成后**写入，包含所有步骤和最终总结（用于最终结果）

---

### 标准执行流程（必须实时展示进度！）

#### 步骤 1：启动CUA任务

```bash
# 直接启动
bash ~/.agents/skills/computer-use/scripts/cua.sh run "<task_content>"
```

使用 `background=true` 在后台运行。

#### 步骤 2：从stdout提取预检和run信息（立即展示）

启动后，读取stdout并**立即展示**：

- 预检结果
- `run_id` 和 `run_dir`（从 `run_detected` 事件）

#### 步骤 3：实时展示进度（这是核心！）

**⚠️ 强制要求：获取到run_id后，必须立即开始tail，绝对不能等待！**

**具体操作：**

1. 检查 `steps.jsonl` 是否存在
2. **立即开始 tail 该文件**（不要有任何延迟！）
   ```bash
   # 立即执行这个命令
   tail -f /root/.cua/runs/<run_id>/steps.jsonl
   ```
3. **每读到一个新行，就立即格式化展示**
4. 从 `llm.rationales[0]` 提取动作描述
5. 每个动作单独一行：`✅ <动作描述>`
6. **不要缓存，不要攒结果，读到就展示！**

---

## 🔴 自检点：获取run_id后立即检查

**在获取到run_id和run_dir后，必须自问：**

- [ ] **我是否已经开始tail `steps.jsonl`了？**
- [ ] **我是不是在等任务完成？（这是错误的！）**

**如果答案是"没有"或"是的"，立即停止，开始tail！**

---

## ❌ 常见错误（绝对避免！）

| 错误做法                                   | 正确做法                            |
| ------------------------------------------ | ----------------------------------- |
| ❌ 等任务完成后才读取steps.json            | ✅ 获取run_id后立即tail steps.jsonl |
| ❌ 攒结果，最后一次性展示                  | ✅ 每读到一行就立即展示             |
| ❌ 说"让我读取steps.jsonl文件"但不真正tail | ✅ 直接执行tail命令，实时展示       |
| ❌ 使用process log/poll获取进度            | ✅ 直接tail steps.jsonl文件         |

**记住：用户需要的是实时进度反馈，不是最后的总结！**

#### 步骤 4：任务完成后展示最终总结

任务结束后：

1. 读取 `steps.json` 文件获取最终总结
2. 展示最终结果和保存路径

---

### 输出格式（唯一正确格式）

```
🔍 正在进行预检检查...
✅ 预检通过，模型支持多模态，开始执行任务

✅ <动作描述1>   ← 每完成一步就立即展示这一行
✅ <动作描述2>   ← 每完成一步就立即展示这一行
✅ <动作描述3>   ← 每完成一步就立即展示这一行

✅ 任务完成：<最终结果描述>

📁 运行文件保存路径：<run_dir>
```

**关键：每一步 ✅ 都要在完成后立即展示，不能等全部完成再汇总！**

---

## 📌 如何提取动作描述

```python
# 伪代码说明
for step in steps:
    # 优先使用 llm.rationales[0]
    if step.get("llm", {}).get("rationales"):
        action = step["llm"]["rationales"][0]
    else:
        # 备用方案
        action = step.get("brain", f"执行了 {step.get('actionName')} 操作")

    print(f"✅ {action}")
```

---

## 🔍 执行中自检清单

在格式化输出前，确认：

- [ ] 每个 ✅ 是否都单独一行？
- [ ] 有没有显示技术细节（坐标、路径、步骤编号、原始JSON等）？
- [ ] 是不是只显示了自然语言的动作描述？
- [ ] 预检和最终总结的格式是否正确？

**如果发现违规，立即纠正！**

---

## ⏸️ 中断与交接

当任务中断或需要用户手动操作时：

1. **立即停止** CUA 进程
2. **记录检查点**（已完成步骤、当前窗口/页面、下一步、阻碍）
3. **返回 `<computer-handoff />` 作为最后一行**

   Web handoff: do not compress or attach a screenshot, do not emit any media directive, do not include any image. These 3 steps above are the full Web rule.

   **Conversation-source branch (IM):** if the system prompt contains `[CONVERSATION SOURCE]` and the value indicates **IM** (feishu / wechat / discord / slack / telegram / etc.), the user is on an IM client and has **no desktop access**. Step 3 changes: do NOT return `<computer-handoff />` (IM channel renderers don't recognise it and will leak the literal string into the chat). Instead, send the user a screenshot + detailed guidance using the IM rule below. Steps 1, 2 and 4 still apply.

   **IM handoff rule:**
   1. **First line** of your reply MUST be `MEDIA:~/.openclaw/media/outbound/handoff.jpg`. This is an **intent marker** — the skill-switch plugin captures a fresh desktop screenshot independently and attaches it to the IM message. The `MEDIA:` line MUST be emitted **unconditionally** as the very first line, even if you have not yet attempted (or have failed) to compress a screenshot yourself. Do NOT use `![](file://...)` markdown — it is blocked.
   2. After the `MEDIA:` line, write detailed IM-friendly Chinese guidance tailored to the **interrupt category** below. The plugin-attached screenshot shows the user what the desktop looks like; your text must tell them what they need to do and what to reply.
   3. **Best-effort screenshot (optional, non-blocking)**: if `<run_dir>/steps.json` (or `<run_dir>/.wait_for_user.json`) contains a usable `screenshotPath` and imagemagick is available, you MAY also compress it as a fallback — but **only after** the `MEDIA:` line is already emitted, and any failure (missing `screenshotPath`, unreadable path, `convert` failure, etc.) MUST NOT cause you to omit, retract, or move the `MEDIA:` line:
      ```
      mkdir -p ~/.openclaw/media/outbound
      convert "<screenshotPath>" -resize '1280x1280>' -quality 70 ~/.openclaw/media/outbound/handoff.jpg
      ```
   4. **Do NOT** output `<computer-handoff />` for IM source.

   **Interrupt categories — write text appropriate to whichever applies:**
   - **Login / SMS / email verification**: name the app and screen; list the sign-in methods actually shown (scan-QR / phone-code / account-password / third-party / SSO / email-link / etc.); for each method tell the user exactly what data to send so you can drive the GUI for them (account, password, phone number, verification code, ...). If only scan-QR is offered, instruct the user to scan with their phone App and reply when done.
   - **CAPTCHA**: describe the CAPTCHA from the screenshot, ask the user to read it and reply with the answer.
   - **QR code scan** (login / pairing / payment confirmation): tell the user which App to use, ask them to reply when done.
   - **Payment**: ask the user to complete the payment on their own device / banking App. Do NOT ask for card / CVV / banking credentials through IM. Ask them to reply once paid (or to abort).
   - **System dialog / cookie consent / confirmation needing human judgement**: describe the choice and ask the user to reply with their decision.
   - **Explicit user takeover**: a short acknowledgement + the screenshot is enough; ask them to tell you when to continue.
   - **SSO redirect loops / unstable flows**: explain what's stuck, ask the user how to proceed (retry / switch method / abort).
   - **Other**: describe the desktop state in one or two sentences, name what you need from the user, tell them how to reply.

   **Hard constraints (any violation = rewrite the whole reply):**
   - The `MEDIA:` line is an **intent marker** for the plugin layer. NEVER omit it because cua save failed, `screenshotPath` is missing from steps.json, the path is unreadable, or `convert` failed — those are the plugin layer's concern, not yours. The only allowed reason to omit `MEDIA:` is when the user has already acknowledged and you are continuing/resuming, not handing off.
   - Do NOT use refusal phrases: 「由于隐私我无法」「请你手动操作」「请到屏幕前」「为保护隐私」「考虑到安全」 — user-initiated data sharing is explicitly allowed here.
   - Mask sensitive data when echoing: phone numbers as `138****1111`, codes/passwords as `******`. Never echo the raw user data verbatim.
   - When passing user data into a new cua run, write the masked form into the `cua run` task text; the real value goes through environment variable or stdin only.
   - Do NOT output `<computer-handoff />` for IM source.
   - Do NOT output `![](file://...)` markdown — use the `MEDIA:` directive only.

   **After the user replies** with the data, spawn a new cua run to drive the GUI (e.g. fill the input + click submit), and reply to the user with the masked confirmation + next-step ask. If the cua run fails, explain the failure to the user and offer alternatives.

   **GUI relay caveat**: cua has no direct user-input injection interface; "I'll fill it for you" is implemented by spawning a fresh `cua run` with the action as task text. Accuracy is lower than browser-use's `bua fill` and may fail on layout changes — the guidance text should not promise perfection.

4. **恢复时**：从检查点继续，执行下一步

---

## 📌 记住：简单就是美

用户不需要知道坐标、路径、步骤编号这些技术细节。他们只需要知道：

- 现在在做什么
- 已经完成了什么
- 任务成功了还是失败了

按照这个原则输出，就不会出错。