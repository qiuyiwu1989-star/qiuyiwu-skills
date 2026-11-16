# Feishu Card 参考

## 基本规则

- 顶层必须是合法 JSON 对象
- 卡片骨架：

```json
{ "schema": "2.0", "header": {}, "body": { "elements": [] } }
```

- 如果拿到模板封装对象且含 `dsl`，取 `dsl` 作为卡片本体
- `body.elements` 必须是数组
- `table` 只能放在根节点，不能放进 `column_set`
- 不要使用废弃的 `note`、`action`

## 可用组件

- 容器：`column_set`
- 展示：`markdown` `div` `img` `chart` `table` `hr`
- 交互：`button` `select_static`

## Chart

- 必须使用 `tag: "chart"`
- 图表定义放在 `chart_spec`
- 不要发明 `chart_type`、`x_field`、`y_field` 之类字段
- 柱状图、折线图、面积图、散点图：使用 `type + data.values + xField + yField`
- 饼图：使用 `type + data.values + categoryField + valueField`

```json
{
  "tag": "chart",
  "aspect_ratio": "16:9",
  "chart_spec": {
    "type": "bar",
    "data": {
      "values": [
        { "time": "10", "value": 3 },
        { "time": "11", "value": 211 }
      ]
    },
    "xField": "time",
    "yField": "value"
  }
}
```

```json
{
  "tag": "chart",
  "aspect_ratio": "1:1",
  "chart_spec": {
    "type": "pie",
    "data": {
      "values": [
        { "name": "姜雨蒙", "value": 35 },
        { "name": "郑允煜", "value": 25 }
      ]
    },
    "categoryField": "name",
    "valueField": "value"
  }
}
```

## 明细表

- 使用 `table`
- `rows` 必须是对象数组
- 每行键名必须来自 `columns[].name`

```json
{
  "tag": "table",
  "columns": [
    { "name": "city", "display_name": "城市", "data_type": "text" },
    { "name": "temperature", "display_name": "温度", "data_type": "number" }
  ],
  "rows": [
    { "city": "北京", "temperature": 23 },
    { "city": "上海", "temperature": 26 }
  ]
}
```

## 组件映射

- 指标卡：用 `column_set` 组合标签、数值、趋势
- `Callout`：用 `div`，备注文本可用 `text_size: notation` + `text_color: grey`
- `CodeBlock`：用 `markdown` 代码围栏

## 风格

- 头部优先 `template: "blue"`
- 图表优先 `color_theme: "brand"`
- KPI 与洞察块使用浅色背景，不用大面积深色
- 辅助文本用 `notation` 与 `grey`

## 双图摘要模板

用户明确要求双图、两栏图表、左右各放一个图表时，优先：

- 顶部 `header`
- 一段摘要 `markdown`
- 一个 `column_set`，左图趋势、右图结构
- 一个 `column_set` 放 3 个洞察块
- 一个 `hr`
- 尾部要点 `markdown`
