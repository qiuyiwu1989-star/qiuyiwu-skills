---
name: ai-assistant-security-openclaw
description: |
  AI Assistant Security (ClawSentry) 安全防护系统，用于查看防护配置、安全记录、设置防护开关、查看可用工具，以及管理 skill 白名单等。
  Activate when user needs to: 查看防护配置、查看安全记录、查看防护记录、设置防护开关、查看可用工具、查看clawSentry防护数据、查看clawSentry可用工具、查看ai-assistant-security-openclaw、查看安全防护、查看安全配置、查看安全日志、使用安全工具、打开安全工具、调用安全工具、安全防护工具、安全工具、使用防护工具、打开防护工具、调用防护工具、防护工具、加白skill、把skill加入白名单、移除skill白名单、查看skill白名单、白名单里有哪些skill。
metadata:
  {
    "openclaw":
      {
        "emoji": "🛡️",
        "skillKey": "ai-assistant-security-openclaw",
        "requires": { "config": ["plugins.entries.ai-assistant-security-openclaw.enabled"] },
      },
  }
---

# ClawSentry

ClawSentry 是一个安全防护系统，提供 LLM 和 Agent 的安全防护功能。

## Agent rules:

- Call tools directly. Never suggest slash commands to the user.
- Always inform the user if they don't have permission to use a tool.
- When a tool returns "no permission", tell the user clearly and remind them they can ask "我可以使用什么功能" or "查看可用工具" to see what tools are available for their version.

## Tool Parameters

### clawSentryListConfig

查看防护配置。**Call when:** "查看防护配置", "看一下防护规则", "有哪些防护规则", "查看安全配置", "查看安全防护配置", "看一下当前配置". No params.

### clawSentryListSecurityLogs

查看防护记录。**Call when:** "查看防护记录", "看一下安全记录", "查看clawSentry防护数据", "有哪些安全记录", "查看安全日志", "看一下安全防护记录", "查看安全记录", "查看防护数据". No params.

### clawSentryFeatSwitch

设置防护开关。**Call when:** "设置防护开关", "开启提示词防护", "关闭提示词防护", "打开提示词防护", "禁用提示词防护", "把 Prompt 防护设为启用", "开启模型滥用防护", "关闭模型滥用防护", "打开模型滥用防护", "禁用模型滥用防护", "把 ModelMisuse 防护设为启用", "开启敏感数据泄露防护", "关闭敏感数据泄露防护", "打开敏感数据泄露防护", "禁用敏感数据泄露防护", "把 PiiLeakage 防护设为启用", "打开安全防护", "关闭安全防护", "启用防护", "禁用防护".

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `switchType` | string | Yes | 要切换的防护类型：`Prompt`（提示词防护）、`ModelMisuse`（模型滥用防护）或 `PiiLeakage`（敏感数据泄露防护） |
| `enable` | boolean | Yes | 是否启用防护：`true` 表示打开，`false` 表示关闭 |

### clawSentryListAvailableTools

查看可用工具。**Call when:** "查看可用工具", "我能用哪些工具", "查看clawSentry可用工具", "查看当前版本可以使用的所有工具列表", "有哪些工具可以用", "查看可用命令", "我可以用什么工具", "有什么功能", "我能做什么", "有哪些功能", "查看功能", "我可以使用哪些功能", "有什么工具", "查看我能使用的工具", "当前版本有什么功能", "有什么可用的功能", "我能使用什么", "我有什么功能可以用". No params.

### clawSentrySkillWhitelist

管理 skill 白名单（查看/加白/移除）。**Call when:** "加白某个 skill", "把某个 skill 加入白名单", "移除白名单", "取消加白", "查看白名单", "白名单里有哪些 skill", "忽略某个 skill 风险".

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | 操作类型：`info`（查看白名单）、`add`（加入白名单）、`remove`（移除白名单） |
| `skillName` | string | No | `action=add/remove` 时必填。填入 skill 的真实名称（来源为该 skill 的 `SKILL.md` frontmatter `name` 字段） |

**Examples:**

- 查看白名单：`{"action":"info"}`
- 加白：`{"action":"add","skillName":"github"}`
- 移除加白：`{"action":"remove","skillName":"github"}`
