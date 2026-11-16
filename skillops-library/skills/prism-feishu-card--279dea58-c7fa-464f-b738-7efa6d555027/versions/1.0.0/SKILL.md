---
name: prism-feishu-card
description: 在飞书渠道输出结构化内容时使用。适用于：最终回答包含 2+ 指标/KPI 对比、时间序列、趋势、排名、分布，或 3 行以上可按表格扫读的记录；也适用于用户要看板、图表、报告、卡片、可视化（"卡片 / 图表 / 趋势 / 指标 / 对比 / 分布 / 排行 / 报表 / 数据概览"等说法）。通过调用 `send_prism_feishu_card` 工具发送 Card JSON 2.0，不直接输出 JSON 或 markdown 代码围栏。不要在以下场景使用：单条事实、短解释、是/否、代码片段；用户明确要纯文本回复；当前不是飞书渠道。
metadata: {"openclaw":{"requires":{"config":["plugins.entries.claw-prism-plugin.config.enabledChannels.feishu","plugins.entries.claw-prism-plugin.config.skills.feishuCard"]}}}
---

# 飞书 Card JSON 2.0

## 何时使用这个 skill

命中下列任一信号时使用：

- 最终回答包含 2 个及以上可并排对比的指标、KPI、比值；
- 时间序列、趋势、排名、分布；
- 3 行及以上可按表格扫读的结构化记录；
- 用户明确要卡片、看板、图表、报告、可视化（包括"卡片 / 看板 / 图表 / 趋势 / 指标 / 对比 / 分布 / 排行 / 报表 / 数据概览"等说法）。

## 何时不要使用这个 skill

- 回答是单条事实、短解释、是/否、代码片段；
- 用户明确要纯文本回复；
- 当前不是飞书渠道。

## 工具调用

- 必须调用 `send_prism_feishu_card` 发送卡片。
- 不要直接输出 JSON，不要包 markdown 代码围栏。
- 调用成功后不要再补额外文本。
- 不要调用 web artifact 工具。

## Card JSON

- 顶层必须是合法 JSON 对象。
- 卡片骨架固定为 `{ "schema": "2.0", "header": {}, "body": { "elements": [] } }`。
- `body.elements` 必须是数组。
- `table` 只能放根节点。
- 不要使用废弃的 `note`、`action`。
- 如果拿到模板封装对象且含 `dsl`，取 `dsl` 作为卡片本体。

## 组件选择

- KPI：用 `column_set` 组合标签、数值、趋势。
- 趋势、对比、占比：用 `chart` + `chart_spec`。
- 多行明细：用根节点 `table`。
- 结论、风险、洞察：用 `div` 或 `markdown`。
- 代码、SQL、JSON：用 `markdown` 代码围栏。

## 参考资料

- 详细字段、图表示例和表格规则见 `references/feishu-card.md`

