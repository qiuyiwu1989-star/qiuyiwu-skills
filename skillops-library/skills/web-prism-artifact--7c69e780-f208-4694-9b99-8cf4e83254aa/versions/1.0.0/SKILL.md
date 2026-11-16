---
name: web-prism-artifact
description: 在 Web 渠道输出可视化/结构化数据时使用。适用于：最终回答包含 2+ 指标/KPI 对比、时间序列、趋势、排名、分布、占比，或 3 行以上可按表格扫读的记录；命中这些数据形态时默认必须使用，即使用户没有明说可视化/报表/看板；也适用于用户明确要看板、图表、报告、可视化、dashboard、chart、visualization。输出一个原始 `<openui-artifact>` 块（使用 OpenUI Lang）作为可视化主体，并额外输出至少一段文字总结；不用 markdown 正文把同一份数据再讲一遍，不输出 JSON、HTML、ECharts option 或伪 OpenUI DSL。不要在以下场景使用：用户明确要纯 HTML 页面、iframe、原生 ECharts option、SVG 源码、自定义脚本；单条事实、短解释、是/否、代码片段。
metadata: {"openclaw":{"requires":{"config":["plugins.entries.claw-prism-plugin.config.enabledChannels.web"]}}}
---

# OpenUI Artifact

> **金规则：artifact 是数据展示主体，文字总结是阅读入口。** 一旦判定要使用 artifact，回答中输出 `<openui-artifact>` 块承载所有指标、明细、图表、洞察和结论，并在块外输出至少一段文字总结。分步骤分析可以输出多段总结；不要把同一份数据、指标、结论先用 markdown 长篇讲一遍，再在 artifact 里做一遍。违反此规则等于回答错误。

本文件是 `web-prism-artifact` skill 的**唯一运行时手册**：触发条件、组件签名、选型指南、构图模板、收尾自检全部在这里。读完本文件就可以直接输出 artifact，运行时不需要读取 references，**不要再读 references/\* 任何文件**。

维护者索引：生成版官方提示词保存在 `references/openui-system-prompt.generated.md`，组件 schema 保存在 `references/openui-library-schema.generated.json`。

## 何时必须使用 artifact

最终回答命中以下任一信号就使用：

- 包含 2 个及以上可并排对比的指标、KPI、比值；
- 时间序列、趋势、排名、分布、占比；
- 3 行及以上可扫读的结构化记录；
- 用户提到"看板 / 图表 / 报告 / 可视化 / dashboard / chart / report / visualization / 趋势 / 指标 / 对比 / 分布 / 排行 / 报表 / 数据概览"。

触发由回答内容决定，不由用户是否说"看板"决定。数据形态本身就是触发条件；命中后默认必须使用，即使用户没有明说可视化/报表/看板。

## 何时不要使用 artifact

命中以下任一情况时直接用纯文本回答，不输出 `<openui-artifact>`：

- 单条事实、短解释、是/否、代码片段；
- 用户明确要纯 HTML 页面、iframe、原生 ECharts option、SVG 源码、自定义脚本、自由 HTML；
- 用户明确要 markdown 表格或纯文本形态。

## 形态（最高优先级）

⚠️ 以下规则优先于一切默认行为：

1. **artifact 承载数据展示，块外必须有总结**：所有数据分析、洞察结论、趋势解读都作为 artifact 内部组件输出；同时在 `<openui-artifact>` 前或后输出至少一段文字总结。分步骤分析可以输出多段文字总结。
2. **绝对禁止自我宣告**：不输出任何暗示技能名称、工具名称、模板/示例编号的文字，包括但不限于：
   - "我将使用 xxx 技能/ skill / 工具 …"
   - "使用示例 2 / 模板 X 来展示 …"
   - "为您生成可视化 / 报告 / 图表 …"
   - "已为您生成 / 已完成渲染 / 如下所示 …"
   - "接下来我会 / 让我来 / 请看下图 …"
3. 文字总结必须是实质性结论，不要只写"已完成/如下所示/为您生成"这类自我宣告；如果需要在图表内部补充解释，可以再用 Callout/TextContent。
4. **默认使用自检**：如果最终回答已经包含 2+ 指标、趋势、对比、排名、分布、占比或 3 行以上明细，但没有 `<openui-artifact>`，先改写为 artifact 再输出。

## 块结构

语法：`<openui-artifact id="..." title="...">...</openui-artifact>`

- 先流式输出起始标签，再在标签内流式输出 OpenUI Lang，完成后输出结束标签。
- `id` 在当前消息内稳定、小写、连字符。
- `title` 可选但建议填。
- 块体必须是真正的 OpenUI Lang，不是 JSON、JSX、HTML、ECharts option，也不是 `Container(children = ...)`、`Chart(type = ...)`、`Text("标题", size=20)`、`container(...) { ... }` 这类伪 OpenUI DSL。

## OpenUI Lang 规则

- 首行必须是 `root = ...`。
- 每行一条完整赋值，组件调用或数组不跨行。
- 每行形态必须使用真实组件和位置参数，例如 `root = Stack([...], "column", "m")`、`trend = LineChart(labels, [Series("A", values)], "natural")`、`detail = Table([Col("年份", years)])`，或 `labels = [...]`；OpenUI Lang 没有 `{...} block`。
- 不写任何注释（`//`、`/* */`、markdown 注释）。
- 只用位置参数，不写 named args / props：写 `Stack([a], "column", "m")`，不要写 `Container(children = [...])`、`Chart(type = "line")`、`Text("标题", size=20)`、`data = [...]`、`xField = "year"`、`yField = "value"`、`yFields = [...]`、`columns = [...]`、`rows = [...]`。
- 字符串用双引号。
- 允许前向引用；除 `root` 外每个定义都必须可从 `root` 访问到。
- 语句顺序：root/骨架 → 卡片/图表/表格 → 标签、数值数组、明细数据，优先流式体验。
- 不调用任何工具；`<openui-artifact>` 块就是最终回答。
- 禁止输出"已使用工具""已完成渲染""生成了报告""支持悬停/缩放"“使用 x 工具”等状态说明。
- 禁止使用不存在的泛化组件、伪组件或小写组件名：`Container/Chart/Text/container/text/chart/table/badge/icon` 都不是本文组件；标题和正文用 `TextContent(...)`，应使用组件签名总表中的组件。

## 组件签名总表

优先使用展示类组件完成数据分析报告；表单、按钮、弹窗等交互组件只有在用户明确要求输入、筛选或交互操作时才使用。

### 布局与容器

- `Stack(children: any[], direction?: "row"|"column", gap?: "none"|"xs"|"s"|"m"|"l"|"xl"|"2xl", align?: "start"|"center"|"end"|"stretch"|"baseline", justify?: "start"|"center"|"end"|"between"|"around"|"evenly", wrap?: boolean)`
  适用：多个内容块的纵向/横向排列，artifact 顶层骨架一般用 `Stack`。`wrap: true` 可让 row 在窄屏折行。
- `Card(children: any[], variant?: "card"|"sunk"|"clear", direction?: "row"|"column", gap?: "none"|"xs"|"s"|"m"|"l"|"xl"|"2xl", align?: "start"|"center"|"end"|"stretch"|"baseline", justify?: "start"|"center"|"end"|"between"|"around"|"evenly", wrap?: boolean)`
  适用：把 KPI、图表、表格或结论包成区域。`card` 是默认卡片，`sunk` 用于次级块，`clear` 用于透明容器。
- `Separator(orientation?: "horizontal"|"vertical", decorative?: boolean)`
  适用：分隔不属于同一卡片的内容区。数据看板里少用，避免碎片化。
- `Carousel(children: any[][], variant?: "card"|"sunk")`
  适用：同类卡片很多但横向空间有限时做横向滚动；普通报表优先用 `Stack`。
- `Modal(title: string, open?: $binding<boolean>, children: any[], size?: "sm"|"md"|"lg")`
  适用：用户明确要弹窗详情或表单时使用；普通静态报告不要主动用。
- `Tabs(items: TabItem[])`
  适用：同一主题下多个互斥视图，如“趋势/结构/明细”切换。
- `TabItem(value: string, trigger: string, content: any[])`
  适用：`Tabs` 的单个页签，`value` 唯一，`trigger` 是标签文案。
- `Accordion(items: AccordionItem[])`
  适用：折叠长解释、FAQ、风险明细；核心数据不要默认折叠。
- `AccordionItem(value: string, trigger: string, content: any[])`
  适用：`Accordion` 的单个折叠项，`value` 唯一，`trigger` 是标题。
- `Steps(items: StepsItem[])`
  适用：步骤、流程、阶段性建议，如“数据口径 -> 计算 -> 结论”。
- `StepsItem(title: string, details: string)`
  适用：`Steps` 的单个步骤。

### 文本、标签与说明

- `CardHeader(title?: string, subtitle?: string)`
  适用：每张卡片的标题和副标题（单位、时间段、口径）。通常放在 `Card` 第一位。
- `TextContent(text: string, size?: "small"|"default"|"large"|"small-heavy"|"large-heavy")`
  适用：段落文字、KPI 数值、次要说明。支持 markdown；KPI 数值用 `large-heavy`，指标名用 `small`。
- `MarkDownRenderer(textMarkdown: string, variant?: "clear"|"card"|"sunk")`
  适用：artifact 内承载一段 markdown 说明。不要用它替代表格或图表。
- `Label(text: string)`
  适用：短标签文字，通常配合表单或控件；数据报告中优先用 `TextContent` 或 `Tag`。
- `Tag(text: string, icon?: string, size?: "sm"|"md"|"lg", variant?: "neutral"|"info"|"success"|"warning"|"danger")`
  适用：KPI 卡片里的同环比徽标、分类标签、状态标。`success` 正向，`danger` 负向，`warning` 异常。
- `TagBlock(tags: string[])`
  适用：一组关键词/状态/风险点标签，例如 `TagBlock(["AQI: Good", "Pollen: Low"])`。
- `Callout(variant: "info"|"warning"|"error"|"success"|"neutral", title: string, description: string, visible?: $binding<boolean>)`
  适用：结论、风险提示、异常告警、数据说明等需要高亮的单条信息。不要用 Callout 承载主要数据。
- `TextCallout(variant?: "neutral"|"info"|"warning"|"success"|"danger", title?: string, description?: string)`
  适用：轻量提示，比 `Callout` 更适合卡片内部的辅助结论。
- `CodeBlock(language: string, codeString: string)`
  适用：展示 SQL、JSON、代码片段；普通 dashboard 场景少用。

### 图表与数据系列

- `Series(category: string, values: number[])`
  适用：柱/线/面/雷达图的数据系列，`values` 必须是数字数组且长度与 labels 一致。
- `BarChart(labels: string[], series: Series[], variant?: "grouped"|"stacked", xLabel?: string, yLabel?: string)`
  适用：少量类别的数值对比。多指标并排用 `grouped`，累加对比用 `stacked`。
- `HorizontalBarChart(labels: string[], series: Series[], variant?: "grouped"|"stacked", xLabel?: string, yLabel?: string)`
  适用：类别标签较长、类别较多或排行榜。
- `LineChart(labels: string[], series: Series[], variant?: "linear"|"natural"|"step", xLabel?: string, yLabel?: string)`
  适用：时间序列趋势、多对象随时间变化对比。
- `AreaChart(labels: string[], series: Series[], variant?: "linear"|"natural"|"step", xLabel?: string, yLabel?: string)`
  适用：体量、累计值、容量随时间变化；多 Series 可展示总量结构。
- `PieChart(labels: string[], values: number[], variant?: "pie"|"donut")`
  适用：2~7 个类别的部分-整体占比。values 直接传数组，不传 `Series`。
- `SingleStackedBarChart(labels: string[], values: number[])`
  适用：横向单条占比图，适合替代 Pie 或展示结构拆分。values 直接传数组。
- `RadarChart(labels: string[], series: Series[])`
  适用：多维能力、风险、画像、指标评分对比，例如 ROE/净利率/成长性/风险。
- `RadialChart(labels: string[], values: number[])`
  适用：少量类别的径向强度或完成度展示；不要用于精确排序。
- `ScatterChart(datasets: ScatterSeries[], xLabel?: string, yLabel?: string)`
  适用：相关性、分布、聚类、离群点分析。
- `ScatterSeries(name: string, points: Point[])`
  适用：`ScatterChart` 的一组散点数据。
- `Point(x: number, y: number, z?: number)`
  适用：散点图坐标点，`z` 可作为第三维度。
- `Slice(category: string, value: number)`
  适用：低层切片数据；常规占比图优先用 `PieChart(labels, values)`。

### 表格

- `Table(columns: Col[])`
  适用：3 行以上结构化记录、明细展示、混合文本 + 数值 + 操作列。按列组织，不是按行。
- `Col(label: string, data: any[])`
  适用：Table 的列定义，`data` 是该列所有行的数组。

### 按钮与表单（仅用户明确要求交互时使用）

- `Button(label: string, action?: ActionExpression, variant?: "primary"|"secondary"|"tertiary", type?: "normal"|"destructive", size?: "extra-small"|"small"|"medium"|"large")`
  适用：可点击操作按钮；静态分析报告不要主动添加。
- `Buttons(buttons: Button[], direction?: "row"|"column")`
  适用：一组按钮。
- `Form(name: string, buttons: Buttons, fields?: FormControl[])`
  适用：用户明确要求输入、提交、筛选参数时使用。
- `FormControl(label: string, input: Input|TextArea|Select|DatePicker|Slider|CheckBoxGroup|RadioGroup, hint?: string)`
  适用：表单字段容器。
- `Input(name: string, placeholder?: string, type?: "text"|"email"|"password"|"number"|"url", rules?: object, value?: $binding<string>)`
  适用：单行输入。
- `TextArea(name: string, placeholder?: string, rows?: number, rules?: object, value?: $binding<string>)`
  适用：多行文本输入。
- `Select(name: string, items: SelectItem[], placeholder?: string, rules?: object, value?: $binding<string>)`
  适用：下拉选择。
- `SelectItem(value: string, label: string)`
  适用：`Select` 的选项。
- `DatePicker(name: string, mode?: "single"|"range", rules?: object, value?: $binding<any>)`
  适用：日期或日期范围选择。
- `Slider(name: string, variant: "continuous"|"discrete", min: number, max: number, step?: number, defaultValue?: number[], label?: string, rules?: object, value?: $binding<number[]>)`
  适用：数值范围/阈值选择。
- `SwitchGroup(name: string, items: SwitchItem[], variant?: "clear"|"card"|"sunk", value?: $binding<Record<string, boolean>>)`
  适用：多开关设置。
- `SwitchItem(label?: string, description?: string, name: string, defaultChecked?: boolean)`
  适用：单个开关。
- `RadioGroup(name: string, items: RadioItem[], defaultValue?: string, rules?: object, value?: $binding<string>)`
  适用：单选项。
- `RadioItem(label: string, description: string, value: string)`
  适用：`RadioGroup` 的选项。
- `CheckBoxGroup(name: string, items: CheckBoxItem[], rules?: object, value?: $binding<Record<string, boolean>>)`
  适用：多选项。
- `CheckBoxItem(label: string, description: string, name: string, defaultChecked?: boolean)`
  适用：`CheckBoxGroup` 的选项。

### 图片与媒体

- `Image(alt: string, src?: string)`
  适用：单张图片，适合已有图片 URL。
- `ImageBlock(src: string, alt?: string)`
  适用：带加载状态的图片块。
- `ImageGallery(images: {src: string, alt?: string, details?: string}[])`
  适用：多图网格和预览。

## 数据规则

- `Series.values` 必须是 number[]，长度和 labels 一致。
- `LineChart` / `BarChart` / `AreaChart` 使用 `labels + Series`，不要传 `[{x: ..., y: ...}]` 对象数组，也不要写 `xField`、`yField`、`color`、`smooth` 等参数。
- `PieChart` / `SingleStackedBarChart` 直接传 labels + 数值数组，不传 Series。
- `Table` 是列式：`Table([Col("城市", cities), Col("游客量", values)])`。`Col` 固定两个参数；不要给 `Col` 增加第三个参数；带 `%`、`x`、`,`、单位或评级的展示值都保留为字符串。
- 用 `Card` 包裹每个 KPI / 图表 / 表格区域。

## 选型指南

按意图选图表，不要所有数据都套 BarChart 或 Table：

- **趋势、随时间变化、连续数据** → `LineChart`（对象少时），`AreaChart`（体量、累计、多对象堆叠时）。
- **少量类别对比（≤6 类）** → `BarChart`（默认）、`HorizontalBarChart`（标签长或排行榜）。
- **多指标并排对比** → `BarChart` + 多条 Series + `grouped`。
- **累加对比、总量拆解** → `BarChart` + `stacked` 或 `AreaChart` stacked。
- **占比、部分-整体关系**：
  - 2~7 类、空间充足 → `PieChart` `donut`。
  - 类别多或空间窄 → `SingleStackedBarChart`。
- **排行、TopN** → `HorizontalBarChart`（标签放左侧更易读）。
- **混合文本 + 数值、多列明细** → `Table`。
- **单个核心数值、状态标徽** → `Card` + `TextContent(large-heavy)` + `Tag`（KPI 卡）。
- **结论、风险、说明** → `Callout`。

禁止：

- 把时间序列塞进 BarChart（应该用 LineChart/AreaChart）；
- 只有 2 个值还用 PieChart（直接用两个 KPI 卡或 SingleStackedBarChart）；
- 把明细数据塞进 Callout；
- 给多对象横向对比选 PieChart（用 grouped BarChart）。
- 使用 `Text(...)`、`LineChart([{x: ..., y: ...}], xField="x", yField="y")`、`Table([{...}], columns=[...])` 这类 JS/React 风格写法。

## 语法示例

以下示例可直接被 OpenUI parser 解析。不要输出 `[...]`、`...` 或未替换占位符；如果数据未知，先用真实的最小样例数据或改用纯文本回答。

```
<openui-artifact id="weather-dashboard" title="Weather Dashboard">
root = Stack([header, kpiRow, chartRow, detailRow])
header = Card([CardHeader("Weather Dashboard", "7-day forecast & current conditions — San Francisco, CA")], "clear")
kpiRow = Stack([kpi1, kpi2, kpi3, kpi4], "row", "m", "stretch")
kpi1 = Card([TextContent("🌡️ Temperature", "small"), TextContent("64°F", "large-heavy"), TextContent("Feels like 61°F", "small")], "card", "column", "s", "center")
kpi2 = Card([TextContent("💧 Humidity", "small"), TextContent("72%", "large-heavy"), TextContent("Dew point 54°F", "small")], "card", "column", "s", "center")
kpi3 = Card([TextContent("💨 Wind Speed", "small"), TextContent("14 mph", "large-heavy"), TextContent("Direction: W", "small")], "card", "column", "s", "center")
kpi4 = Card([TextContent("☀️ UV Index", "small"), TextContent("3", "large-heavy"), TextContent("Moderate", "small")], "card", "column", "s", "center")
chartRow = Stack([tempChart, precipChart], "row", "m", "stretch")
tempChart = Card([CardHeader("7-Day Temperature", "High / Low °F"), tempLine], "card", "column", "m")
tempLine = LineChart(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], [highSeries, lowSeries], "natural", "Day", "°F")
highSeries = Series("High", [64, 67, 70, 66, 63, 59, 62])
lowSeries = Series("Low", [52, 54, 57, 53, 50, 47, 49])
precipChart = Card([CardHeader("Precipitation", "Daily inches"), precipBar], "card", "column", "m")
precipBar = BarChart(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], [precipSeries], "grouped", "Day", "Inches")
precipSeries = Series("Rainfall (in)", [0.0, 0.1, 0.0, 0.3, 0.5, 0.2, 0.0])
detailRow = Stack([condCard, humidCard, sunCard], "row", "m", "stretch")
condCard = Card([CardHeader("Daily Conditions"), condTable], "card")
condTable = Table([dayCol, condCol, highCol, lowCol])
dayCol = Col("Day", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
condCol = Col("Condition", ["Partly Cloudy", "Sunny", "Clear", "Showers", "Rain", "Drizzle", "Sunny"])
highCol = Col("High °F", [64, 67, 70, 66, 63, 59, 62])
lowCol = Col("Low °F", [52, 54, 57, 53, 50, 47, 49])
humidCard = Card([CardHeader("Humidity & Wind"), humidityArea], "card")
humidityArea = AreaChart(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], [humSeries, windSeries], "natural", "Day", "Value")
humSeries = Series("Humidity %", [72, 65, 60, 78, 85, 80, 68])
windSeries = Series("Wind mph", [14, 10, 8, 16, 20, 17, 11])
sunCard = Card([CardHeader("Cloud & UV Breakdown"), sunPie, uvRadar], "card", "column", "m")
sunPie = PieChart(["Sunny", "Partly Cloudy", "Overcast", "Rainy"], [3, 2, 1, 1], "donut")
uvRadar = RadarChart(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], [uvSeries])
uvSeries = Series("UV Index", [3, 5, 6, 2, 1, 2, 5])
</openui-artifact>
```

## 收尾自检

关闭 `</openui-artifact>` 前确认：

1. 首行是 `root = ...`；
2. 无注释、无跨行赋值；
3. 所有被引用的变量都有定义，除 `root` 外每个定义都可从 `root` 到达；
4. 图表 labels 与数值数组长度一致；
5. 只用本文"组件签名总表"中的组件；
6. 图表选型符合"选型指南"——不要所有数据都塞到 BarChart/Table。
