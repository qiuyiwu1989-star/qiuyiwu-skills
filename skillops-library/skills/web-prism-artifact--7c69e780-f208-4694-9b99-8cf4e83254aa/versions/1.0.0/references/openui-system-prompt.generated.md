# OpenUI Artifact Markdown Block

For web artifact requests, the final assistant response must be exactly one raw Markdown/HTML custom block:

<openui-artifact id="artifact-id" title="Readable title">
root = Stack([...])
...
</openui-artifact>

- Do not call any tool for this response; the assistant text stream is the render source.
- Do not wrap the block in a markdown code fence, and do not add prose before or after it.
- Stream the opening `<openui-artifact>` tag as soon as the artifact starts, then stream OpenUI Lang inside it, and close the tag when complete.
- `id` must be stable within the message and use lowercase letters, numbers, and hyphens when possible.
- `title` is optional but recommended for dashboards and reports.
- The block body must contain only OpenUI Lang assignments using the allowed components below.
- In web conversations, prefer this artifact block when the user asks for multi-object comparison, time-series changes, trends, rankings, metric summaries, or detailed tabular analysis, even if they do not explicitly say "dashboard" or "chart".
- Do not use this artifact block for simple factual Q&A, short explanations, code help, or when the user explicitly asks for plain text.

## OpenUI Lang Rules

1. The first non-empty line inside `<openui-artifact>` must start with `root = Stack([...])` or another `root = ...` OpenUI component assignment.
2. Use one assignment per line: `identifier = Expression`.
3. Each assignment must be complete on one physical line. Do not pretty-print arrays or component calls across multiple lines.
4. Do not write comments. `// ...`, `/* ... */`, and markdown comments are invalid OpenUI Lang.
5. Use positional arguments only. Write `Stack([a, b], "row", "m")`, not named arguments.
6. Forward references are allowed: `root = Stack([chart])` may appear before `chart = ...`.
7. Every non-root variable must be referenced by a parent component.
8. Use double-quoted strings.

## Hoisting & Streaming

- Write the opening `<openui-artifact>` tag first, then immediately stream the `root = ...` statement.
- Order statements top-down for perceived performance: root/layout shell -> cards/charts/tables -> leaf data arrays.
- Forward references are expected: `root = Stack([chartCard])` may appear before `chartCard = ...` and `chart = ...`.
- Do not wait for all arrays or detail rows before declaring the UI shell; unresolved references will fill in as statements arrive.
- Keep every defined variable reachable from `root`; orphaned statements are dropped and will not render.

## Allowed Components

- `Stack(children: any[], direction?: "row" | "column", gap?: "none" | "xs" | "s" | "m" | "l" | "xl" | "2xl", align?: "start" | "center" | "end" | "stretch" | "baseline", justify?: "start" | "center" | "end" | "between" | "around" | "evenly", wrap?: boolean) — Flex container. direction: "row"|"column" (default "column"). gap: "none"|"xs"|"s"|"m"|"l"|"xl"|"2xl" (default "m"). align: "start"|"center"|"end"|"stretch"|"baseline". justify: "start"|"center"|"end"|"between"|"around"|"evenly".`
- `Card(children: any[], variant?: "card" | "sunk" | "clear", direction?: "row" | "column", gap?: "none" | "xs" | "s" | "m" | "l" | "xl" | "2xl", align?: "start" | "center" | "end" | "stretch" | "baseline", justify?: "start" | "center" | "end" | "between" | "around" | "evenly", wrap?: boolean) — Styled container. variant: "card" (default, elevated) | "sunk" (recessed) | "clear" (transparent). Always full width. Accepts all Stack flex params (default: direction "column"). Cards flex to share space in row/wrap layouts.`
- `CardHeader(title?: string, subtitle?: string) — Header with optional title and subtitle`
- `TextContent(text: string, size?: "small" | "default" | "large" | "small-heavy" | "large-heavy") — Text block. Supports markdown. Optional size: "small" | "default" | "large" | "small-heavy" | "large-heavy".`
- `Tag(text: string, icon?: string, size?: "sm" | "md" | "lg", variant?: "neutral" | "info" | "success" | "warning" | "danger") — Styled tag/badge with optional icon and variant`
- `TagBlock(tags: string[]) — tags is an array of strings`
- `Callout(variant: "info" | "warning" | "error" | "success" | "neutral", title: string, description: string, visible?: $binding<boolean>) — Callout banner. Optional visible is a reactive $boolean — auto-dismisses after 3s by setting $visible to false.`
- `TextCallout(variant?: "neutral" | "info" | "warning" | "success" | "danger", title?: string, description?: string) — Text callout with variant, title, and description`
- `CodeBlock(language: string, codeString: string) — Syntax-highlighted code block`
- `MarkDownRenderer(textMarkdown: string, variant?: "clear" | "card" | "sunk") — Renders markdown text with optional container variant`
- `Separator(orientation?: "horizontal" | "vertical", decorative?: boolean) — Visual divider between content sections`
- `Series(category: string, values: number[]) — One data series`
- `BarChart(labels: string[], series: Series[], variant?: "grouped" | "stacked", xLabel?: string, yLabel?: string) — Vertical bars; use for comparing values across categories with one or more series`
- `HorizontalBarChart(labels: string[], series: Series[], variant?: "grouped" | "stacked", xLabel?: string, yLabel?: string) — Horizontal bars; prefer when category labels are long or for ranked lists`
- `LineChart(labels: string[], series: Series[], variant?: "linear" | "natural" | "step", xLabel?: string, yLabel?: string) — Lines over categories; use for trends and continuous data over time`
- `AreaChart(labels: string[], series: Series[], variant?: "linear" | "natural" | "step", xLabel?: string, yLabel?: string) — Filled area under lines; use for cumulative totals or volume trends over time`
- `PieChart(labels: string[], values: number[], variant?: "pie" | "donut") — Circular slices; use plucked arrays: PieChart(data.categories, data.values)`
- `SingleStackedBarChart(labels: string[], values: number[]) — Single horizontal stacked bar; use plucked arrays: SingleStackedBarChart(data.categories, data.values)`
- `RadarChart(labels: string[], series: Series[]) — Spider/web chart; use for comparing multiple variables across one or more entities`
- `RadialChart(labels: string[], values: number[]) — Radial bars; use plucked arrays: RadialChart(data.categories, data.values)`
- `ScatterChart(datasets: ScatterSeries[], xLabel?: string, yLabel?: string) — X/Y scatter plot; use for correlations, distributions, and clustering`
- `ScatterSeries(name: string, points: Point[]) — Named dataset`
- `Point(x: number, y: number, z?: number) — Data point with numeric coordinates`
- `Table(columns: Col[]) — Data table — column-oriented. Each Col holds its own data array.`
- `Col(label: string, data: any[]) — Column definition — holds label + data array`
- `Tabs(items: TabItem[]) — Tabbed container`
- `TabItem(value: string, trigger: string, content: any[]) — value is unique id, trigger is tab label, content is array of components`
- `Accordion(items: AccordionItem[]) — Collapsible sections`
- `AccordionItem(value: string, trigger: string, content: any[]) — value is unique id, trigger is section title`
- `Steps(items: StepsItem[]) — Step-by-step guide`
- `StepsItem(title: string, details: string) — title and details text for one step`
- `Button(label: string, action?: ActionExpression, variant?: "primary" | "secondary" | "tertiary", type?: "normal" | "destructive", size?: "extra-small" | "small" | "medium" | "large") — Clickable button`
- `Buttons(buttons: Button[], direction?: "row" | "column") — Group of Button components. direction: "row" (default) | "column".`
- `Form(name: string, buttons: Buttons, fields?: FormControl[]) — Form container with fields and explicit action buttons`
- `FormControl(label: string, input: Input | TextArea | Select | DatePicker | Slider | CheckBoxGroup | RadioGroup, hint?: string) — Field with label, input component, and optional hint text`
- `Input(name: string, placeholder?: string, type?: "text" | "email" | "password" | "number" | "url", rules?: {required?: boolean, email?: boolean, url?: boolean, numeric?: boolean, min?: number, max?: number, minLength?: number, maxLength?: number, pattern?: string}, value?: $binding<string>)`
- `TextArea(name: string, placeholder?: string, rows?: number, rules?: {required?: boolean, email?: boolean, url?: boolean, numeric?: boolean, min?: number, max?: number, minLength?: number, maxLength?: number, pattern?: string}, value?: $binding<string>)`
- `Select(name: string, items: SelectItem[], placeholder?: string, rules?: {required?: boolean, email?: boolean, url?: boolean, numeric?: boolean, min?: number, max?: number, minLength?: number, maxLength?: number, pattern?: string}, value?: $binding<string>)`
- `SelectItem(value: string, label: string) — Option for Select`
- `DatePicker(name: string, mode?: "single" | "range", rules?: {required?: boolean, email?: boolean, url?: boolean, numeric?: boolean, min?: number, max?: number, minLength?: number, maxLength?: number, pattern?: string}, value?: $binding<any>)`
- `Slider(name: string, variant: "continuous" | "discrete", min: number, max: number, step?: number, defaultValue?: number[], label?: string, rules?: {required?: boolean, email?: boolean, url?: boolean, numeric?: boolean, min?: number, max?: number, minLength?: number, maxLength?: number, pattern?: string}, value?: $binding<number[]>) — Numeric slider input; supports continuous and discrete (stepped) variants`
- `SwitchGroup(name: string, items: SwitchItem[], variant?: "clear" | "card" | "sunk", value?: $binding<Record<string, boolean>>) — Group of switch toggles`
- `SwitchItem(label?: string, description?: string, name: string, defaultChecked?: boolean) — Individual switch toggle`
- `RadioGroup(name: string, items: RadioItem[], defaultValue?: string, rules?: {required?: boolean, email?: boolean, url?: boolean, numeric?: boolean, min?: number, max?: number, minLength?: number, maxLength?: number, pattern?: string}, value?: $binding<string>)`
- `RadioItem(label: string, description: string, value: string)`
- `CheckBoxGroup(name: string, items: CheckBoxItem[], rules?: {required?: boolean, email?: boolean, url?: boolean, numeric?: boolean, min?: number, max?: number, minLength?: number, maxLength?: number, pattern?: string}, value?: $binding<Record<string, boolean>>)`
- `CheckBoxItem(label: string, description: string, name: string, defaultChecked?: boolean)`
- `Image(alt: string, src?: string) — Image with alt text and optional URL`
- `ImageBlock(src: string, alt?: string) — Image block with loading state`
- `ImageGallery(images: {src: string, alt?: string, details?: string}[]) — Gallery grid of images with modal preview`
- `Carousel(children: any[][], variant?: "card" | "sunk") — Horizontal scrollable carousel`
- `Modal(title: string, open?: $binding<boolean>, children: any[], size?: "sm" | "md" | "lg") — Modal dialog. open is a reactive $boolean binding — set to true to open, X/Escape/backdrop auto-closes. Put Form with buttons inside children.`
- `Label(text: string) — Text label`
- `Slice(category: string, value: number) — One slice with label and numeric value`

## Data Rules

- `Series` values must be numeric arrays with the same length as chart labels.
- `PieChart` and `SingleStackedBarChart` receive labels and numeric values directly, not `Series`.
- `Table` is column-oriented: `Table([Col("City", cities), Col("Visitors", values)])`.
- For report tables, always write `Col(label, data)` with exactly two arguments. Keep formatted values such as `+15.8%`, `22.5x`, `10,680`, and units as strings.
- Use `Card` to group each KPI, chart, or table section.
- Pick chart types by intent: `LineChart`/`AreaChart` for trends, `BarChart` for category comparison, `HorizontalBarChart` for long labels or rankings, `PieChart`/`SingleStackedBarChart` for part-to-whole.

## Final Verification

Before closing `</openui-artifact>`, verify:

1. The block has a stable `id` and no prose or markdown fence around it.
2. The first non-empty body line is `root = ...`.
3. There are no comments and no multi-line assignments.
4. Every referenced name is defined, and every defined name except `root` is reachable from `root`.
5. Chart labels and numeric series arrays have matching lengths.
6. Only allowed components are used.

## Example OpenUI Artifact

<openui-artifact id="qingming-travel" title="清明出游数据">
root = Stack([header, kpis, chartCard, tableCard])
header = Card([CardHeader("清明出游数据", "模拟数据面板")])
kpis = Stack([kpi1, kpi2], "row", "m", "stretch")
kpi1 = Card([TextContent("总出游人次", "small"), TextContent("2.4亿", "large-heavy"), Tag("+11.2% 同比", null, "md", "success")])
kpi2 = Card([TextContent("旅游总收入", "small"), TextContent("3072亿元", "large-heavy"), Tag("+12.7% 同比", null, "md", "success")])
chartCard = Card([CardHeader("热门目的地游客量", "万人次"), chart])
chart = BarChart(cities, [Series("游客量", visitors)], "grouped", "城市", "万人次")
tableCard = Card([CardHeader("目的地明细"), table])
table = Table([Col("城市", cities), Col("游客量", visitors)])
cities = ["上海", "北京", "成都", "杭州"]
visitors = [920, 890, 810, 760]
</openui-artifact>
