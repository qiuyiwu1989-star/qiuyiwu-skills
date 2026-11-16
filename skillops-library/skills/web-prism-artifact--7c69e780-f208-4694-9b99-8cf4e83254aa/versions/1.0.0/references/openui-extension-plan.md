# OpenUI Artifact 扩展计划

## 目标

- 统一保持 `<openui-artifact>` 文本流协议，兼容实时渲染和历史渲染。
- 模板、关键词召回、定制组件都在 Agent 生成前影响上下文，不在前端偷偷改写语义。
- 前端只负责解析、存储和渲染 OpenUI Lang。

## 预设模板

- 在 `claw-prism-plugin` 增加 intent/template router。
- 命中预置问题或关键词后，只注入对应模板说明或 OpenUI Lang skeleton。
- Agent 仍输出完整 `<openui-artifact>`，不调用工具。
- 模板优先使用现有基础组件；高频复杂模板再沉淀为自定义组件。

## 定制组件

- 前端定义共享的 `prismOpenUiLibrary`，注册 `defineComponent` 和 React renderer。
- 插件的 `gen:openui-prompt` 改为从同一份 library 生成 prompt 和 JSON Schema。
- `OPENUI_COMPONENT_ALLOWLIST` 加入新组件名后，重新生成 prompt。
- 只有前端可渲染、prompt/schema 已同步的组件才允许 Agent 使用。

## 推荐顺序

1. 先做模板召回，验证常见问题覆盖率。
2. 对重复且 OpenUI Lang 很长的模板抽象成定制组件。
3. 建立 shared library 作为前端渲染和插件 prompt 生成的单一契约。
