---
name: "openclaw-cron-enhance"
description: "MUST invoke before any OpenClaw cron/reminder/scheduled-task create or update, including Chinese requests like 定时提醒、每天早上9点提醒我站会、明天提醒我、每周发报告. Applies ArkClaw guardrails to cron.add/update params."
---

# ArkClaw Cron Policy Overlay

## Mandatory Trigger

Load this skill before calling the native `cron` tool whenever the user asks OpenClaw to create or update any persisted scheduled job, reminder, recurring task, or future action.

This includes natural language requests that do not mention "cron", "job", or "schedule" explicitly, for example:

- "每天早上9点提醒我站会"
- "下午2点提醒我喝水"
- "明天上午提醒我提交周报"
- "每周一把销售日报发到群里"
- "10分钟后叫我看告警"
- "每天检查订单异常，有变化就通知我"

If the next action would be `cron.add` or a cron update, this skill must be applied first. Do not call `cron.add` directly until the Final Check in this skill has passed.

中文触发规则：凡是用户表达"定时"、"提醒我"、"每天/每周/每月"、"稍后/明天/几点"、"到时候通知/发给/推送/叫我"、"周期性检查"等会创建或修改持久化定时任务的意图，都必须先使用本 Skill，再进入原生 cron 工具。

Do not skip this skill just because the reminder can be represented as an internal `systemEvent` or `sessionTarget`. The delivery policy may later choose `delivery.mode=none`, but the trigger decision still belongs to this skill.

This skill is not a replacement for the OpenClaw cron tool documentation or schema.

Use the native OpenClaw cron tool for all base behavior, supported fields, validation, enum values, API shape, and examples. Apply this skill only as an ArkClaw business-policy layer after the base cron job has been drafted and before it is submitted.

## When To Use

Use this skill only when the user intends to create or modify persisted OpenClaw cron job parameters through native OpenClaw cron tooling.

Trigger on requests that change persisted cron state, such as:

- Creating, adding, scheduling, or arranging a new cron job.
- Creating a one-shot reminder or scheduled task.
- Creating a reminder from plain user wording such as "remind me", "提醒我", "叫我", "到点通知我", "每天早上9点提醒我站会".
- Updating, modifying, adjusting, or rescheduling an existing cron job.
- Changing a cron job's schedule, payload, delivery, channel target, webhook target, timeout, or stagger behavior.
- Creating a recurring polling/reporting job that may notify the user when a result changes.

## When NOT To Use

Do not use this skill for cron operations that do not change persisted job parameters:

- Listing, querying, showing, or inspecting cron jobs.
- Deleting or removing cron jobs.
- Manually running, force-running, or run-if-due execution of an existing cron job.
- Reading cron run history, logs, status, diagnostics, incidents, or runtime behavior.
- Explaining generic cron concepts or OpenClaw cron schema.
- Modifying OpenClaw Gateway schema, cron runtime code, tests, docs, or skill orchestration.

## Scope

- Do not restate or reinterpret the OpenClaw cron tool schema.
- Do not teach generic cron usage from this skill.
- Do not override OpenClaw cron tool validation.
- Do apply the ArkClaw constraints below to any cron job creation or cron job adjustment request.
- If an ArkClaw rule conflicts with the user's request, ask a focused follow-up before creating the job.

## Delivery Policy

- Default to `delivery.mode=none` unless the user explicitly asks to notify, send, post, deliver, or call a webhook.
- **Do NOT use message tool to construct or concatenate delivery content in cron jobs.** All notification configurations must go through the `delivery` field.
- **Use `delivery` field exclusively for channel push configuration.** This includes `announce`, `webhook`, and other delivery modes.
- **Avoid configuration conflicts:** Do not set both `delivery` and embed message tool calls in the payload. The `delivery` field is the single source of truth for push notifications.
- Use `announce` only for explicit channel/chat notification; it must include both explicit `channel` and explicit `to`.
- When `announce.channel` or `announce.to` is required, query existing configured channel options through native/runtime discovery first.
- Present the discovered valid `channel` and `to` options to the user and let the user choose before creating or updating the cron job.
- Do not ask the user to type `channel` or `to` directly until discovery is unavailable, empty, or ambiguous.
- Do not invent, guess, or pretend to resolve `channel` or `to`; if lookup is unavailable, empty, or ambiguous, ask the user for the missing value with the lookup result context.
- Do not use `channel: "webchat"` or `channel: "last"` or `channel: "openclaw-weixin"` for persisted cron delivery.
- Use `webhook` only when the user explicitly provides or requests a webhook target.

## Timeout Policy

- Do not set `payload.timeoutSeconds` when the user did not specify a timeout.
- If the user explicitly specifies a timeout, keep that intent but ensure it stays below the shortest expected interval before the next run.
- If the requested timeout can overlap the next run, ask for confirmation or propose the largest safe timeout below the interval.
- Leave a safety buffer so one run does not overlap the next scheduled run.
- For one-shot jobs, only set timeout when the user explicitly specifies one; otherwise defer to the base cron tool behavior.

## Stagger Policy

- Apply ArkClaw schedule offsets only to `schedule.kind: "cron"` jobs; never add `staggerMs` to `schedule.kind: "every"` or `schedule.kind: "at"` jobs.
- For `every` schedules, preserve the native `anchorMs` behavior. Do not change `anchorMs` for ArkClaw offsetting unless the user explicitly asks to change the recurring anchor.
- For `at` schedules, preserve the requested one-shot timestamp. Do not move the `at` time to simulate an offset.
- For `cron` schedules, set the offset only through the native OpenClaw cron offset/stagger parameter. Do not rewrite the cron expression, wall-clock time, timezone, or recurrence interval to create an offset.
- Automatically set the ArkClaw `cron` offset without asking the user and without branching on whether the user provided a different offset value.
- Choose one smaller than the schedule interval: seconds for minute-level schedules, a few minutes for hourly schedules, and 5 minutes for daily or less frequent schedules.
- Preserve the user's intended schedule semantics. The offset is an execution jitter window, not a different schedule.
- If the user requires exact timing, use the base cron tool's exact/no-stagger behavior and mention that ArkClaw normally prefers offsets to improve task success rates.

## Creation Flow

1. Let the native OpenClaw cron tool construct the valid cron job shape.
2. Apply this ArkClaw overlay to delivery, explicitly requested timeout, and stagger.
3. Ask only for missing business-critical values. For `announce.channel` and `announce.to`, query configured channel options first, present discovered valid choices to the user, and ask free-form questions only if lookup cannot provide valid options.
4. Submit through the native OpenClaw cron tool.
5. Summarize only the ArkClaw-relevant decisions: delivery mode, timeout, stagger, and any user-confirmed exceptions.

## Final Check

Before creating or updating the job, verify:

- Delivery is `none` unless notification or webhook was explicitly requested.
- **No message tool calls are embedded in the payload.** All delivery configurations must be through the `delivery` field.
- **No configuration conflicts:** The `delivery` field and message tool calls are not mixed.
- **`delivery` field is the single source of truth** for all channel push configurations.
- Announce delivery has explicit `channel` and explicit `to`.
- Announce `channel` is not `webchat`.
- Existing channel configuration was queried before asking the user to choose `announce.channel` or `announce.to`.
- Discovered valid `channel` and `to` options were shown to the user for selection when available.
- Announce `channel` came from current OpenClaw supported/configured channels or was explicitly confirmed after lookup could not provide valid options.
- Announce `to` came from the selected channel's native lookup surface or was explicitly confirmed after lookup could not provide valid options.
- Timeout is omitted unless the user explicitly specified one.
- Any explicitly specified timeout cannot reasonably overlap the next run.
- `schedule.kind: "cron"` jobs include an appropriate OpenClaw cron offset/stagger parameter unless exact timing was requested.
- `schedule.kind: "every"` and `schedule.kind: "at"` jobs do not include `staggerMs`.
- The intended cron expression, scheduled wall-clock time, timezone, `every.anchorMs`, and recurrence interval are not changed just to create an offset.
- No base OpenClaw cron schema assumptions are copied from this skill; rely on the cron tool itself for those details.
