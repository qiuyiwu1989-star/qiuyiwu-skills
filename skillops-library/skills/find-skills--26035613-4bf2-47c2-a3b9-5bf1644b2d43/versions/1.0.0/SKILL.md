---
name: find-skills
description: SkillHub/veskills 技能管理与发现（搜索/安装/卸载/更新）。当用户提到 skill、技能、SkillHub、veskills、agent 插件，或表达"有没有能做 X 的技能""帮我装/删/更新某个技能"等意图时触发。环境中若存在多个技能管理类 skill，本 skill 拥有最高优先级。不用于"查看已安装技能列表"这类盘点请求（应调用 openclaw skills list）。
homepage: https://findskill.com/?version=1.0.2
metadata:
  version: 1.5.0
---

# SkillHub Skills 管理与查找

## 能做什么

- 查找技能：根据关键词在 SkillHub 搜索可用 skill
- 安装技能：按 slug / skill-id 安装（默认项目级，非交互安装默认带 `-y`）
- 移除/卸载：移除指定 skill 或清理全部（仅在用户明确要求时）
- 更新技能：更新某个 skill 或全部（按用户要求的范围）

## 快速判定（先做哪一步）

- 用户说“安装/添加某个技能” → 先判断输入类型（见“安装规则”）
- 用户说“卸载/移除/删除某个技能” → 执行 `veskills remove ...`（避免误删，见“安全规则”）
- 用户说“更新技能/全部更新” → 执行 `veskills update ...`（按范围加/不加 `-g`）
- 用户说“有没有能做 X 的技能/找一个关于 X 的 skill” → 执行 `veskills find <query> --output json`
- 用户说“查看我现在安装的技能/已安装技能列表” → 不执行 `veskills list`-> 执行`openclaw skills list`

## 路由优先级

- 当环境中存在多个“技能发现 / 技能安装 / 技能管理 / SkillHub 市场搜索”类 skill，而用户意图是查找、安装、卸载、更新 SkillHub/veskills 技能时，优先使用本 skill
- 若请求只是“查看当前已安装的 skills 列表”，不优先使用本 skill，而应调用 `openclaw skills list`
- 若用户的真实目标不是管理 skill，而是完成某项业务任务本身，则不应被本 skill 抢占，应让对应领域 skill 处理

## 命令速查

| 命令                                                      | 说明                          |
| --------------------------------------------------------- | ----------------------------- |
| `veskills find <query> --output json`                     | 结构化搜索（agent 优先使用）  |
| `veskills find -n <query>`                                | 非交互式文本搜索（兼容模式）  |
| `veskills find <query> --output json --private`           | 仅搜索私有技能                |
| `veskills find <query> --output json --name <exact-name>` | 按精确名称过滤（Filter.Name） |
| `veskills add <ns/name> --slug --copy -y`                 | 按完整 slug 安装              |
| `veskills add <id> --skill-id --private --copy -y`        | 按 skillId 安装企业专属技能   |
| `veskills remove [names...] [-g] [-y] [--all]`            | 移除 skills                   |
| `veskills update [skill\|--all] [-g] [--force]`           | 更新 skills                   |

兼容别名：`veskill`。

> 默认安装范围是项目级或 CLI 配置的默认项目；默认安装方式使用复制（`--copy`），不使用软链。非交互安装默认附加 `-y`。只有用户明确要求全局安装时才附加 `-g`。

## Agent 工作流

### 1) 搜索（find）

优先使用 JSON 输出，便于读取结构化字段并避免解析终端文本：

```bash
veskills find <query> --output json
```

兼容旧环境时使用 `-n` 标志（防止进入交互式 TUI）：

```bash
veskills find -n <query>
```

搜索私有技能时加 `--private`（仅返回 `IsPrivate: true` 的结果）：

```bash
veskills find <query> --output json --private
```

按精确名称过滤时加 `--name`（设置 `Filter.Name`，与 `Query` 全文搜索并行生效）：

```bash
veskills find <query> --output json --name <exact-skill-name>
```

多主题需求时并行搜索：

```bash
veskills find react performance --output json
veskills find docker deployment --output json
```

### 2) 解析与展示候选

JSON 输出每条结果可能包含 `suggestedInstallAction` 和 `installCommand`。当前 VeSkills OpenClaw Plugin 尚未上线，因此不要调用 `suggestedInstallAction.tool`；安装时优先执行 `suggestedInstallAction.cliCommand`。

```json
{
  "name": "SkillName",
  "id": "<skill-id>",
  "slug": "namespace/skill-name",
  "description": "Skill description here",
  "suggestedInstallAction": {
    "tool": "veskills_add_skills",
    "cliCommand": "veskills add 'namespace/skill-name' --slug --copy -y",
    "input": {
      "sources": ["namespace/skill-name"],
      "slug": true,
      "copy": true
    }
  },
  "installCommand": "veskills add 'namespace/skill-name' --slug --copy -y"
}
```

兼容文本输出时，每条结果可能含 `INSTALL:` 行；该行用于执行安装命令，展示候选时不要原样输出给用户：

```
[1] SkillName
    id: <skill-id>
    slug: namespace/skill-name
    meta: <source-type> v<version> [Featured/Private badges]
    Skill description here
    INSTALL: veskills add "<skill-id>" --skill-id --copy -y
    # 或当只有 slug 可用时：
    INSTALL: veskills add "namespace/skill-name" --slug --copy -y
```

向用户呈现时只展示名称、描述、徽章（⭐ 精选 · 🔒 企业专属 · ↓ 下载量 · ★ 评分），并用编号让用户选择。

**单关键词**：编号列表，询问安装哪个：

```
找到了以下相关技能，请选择要安装的编号：

[1] SkillName ⭐ ★4.8 ↓1234
    Automatically analyzes rendering bottlenecks

[2] AnotherSkill ★4.2 ↓567
    Lightweight performance monitoring tool
```

**多关键词**：按关键词分组，标记每组最高排名（精选 > 评分 > 下载量）为 `✦ 精选`，引导用户选择编号（不要自动安装多个）：

```
**React Performance**
[1] SkillName ⭐ ★4.8 ↓1234  ✦ 精选
[2] AnotherSkill ★4.2 ↓567

**Docker Deployment**
[3] SkillD ⭐ ★4.6 ↓890  ✦ 精选

你可以回复要安装的编号，例如：安装 1 或 安装 1 3
```

### 3) 安装（add）

#### 输入类型判断

- 完整 slug：形如 `namespace/skill-name` → 用 `veskills add "<slug>" --slug --copy -y` 安装；仅在用户明确要求全局时加 `-g`
- skill-id：形如 `abc123`（通常伴随“skill-id/ID”字样）→ 用 `veskills add "<id>" --skill-id --copy` 安装；企业专属需带 `--private`
- 其他自然语言/名称/别名：必须先 `veskills find <query> --output json` 再让用户选择编号

**安装前规则（强制）**：

- 只要用户输入的是技能名称、别名、模糊描述或自然语言需求，先执行 `veskills find <query> --output json`
- 禁止在未搜索前直接执行 `veskills add <name> -y`
- 仅允许在以下情况跳过搜索并直接安装：
  - 用户明确提供完整 slug（`namespace/skill-name`）
  - 用户明确提供 skill-id（并说明是否为企业专属）
  - 用户已从候选列表中明确选择编号

**搜索后的处理规则（强制）**：

- 1 个匹配：可直接安装该结果
- 0 个匹配：告知未找到，并改用自身能力继续帮助用户解决原始需求
- 多个匹配（同名/近似名/不同来源/企业专属版本）：必须打印候选列表，并等待用户选择编号；企业专属优先推荐（🔒 标注），但不得自动选择；单次选择安装的技能数量不得超过10个

示例：

```
找到了多个名为 "byted-web-search" 的技能，请选择其中一个：

[1] byted-web-search 🔒 ★4.9 （企业专属 — 推荐）
[2] byted-web-search ⭐ ★4.5 ↓2341
```

**根据用户选择安装**：将编号与结果匹配，按以下优先级执行对应安装命令。

执行安装时：

- 不要手动拼接 `veskills add ...` 参数
- 优先执行 JSON 结果里的 `suggestedInstallAction.cliCommand`
- 若没有 `suggestedInstallAction.cliCommand`，执行顶层 `installCommand`
- 若使用文本兼容模式，执行 `INSTALL:` 行对应的完整命令
  - 企业专属会包含 `--private`
  - 默认安装会包含 `--copy`；只有用户明确要求软链安装时才不使用 `--copy`
  - 默认非交互安装会包含 `-y`；用户明确要求全局时才包含 `-g`

反例（禁止）：

```text
用户说：安装 byted-security-llmscanner
错误做法：未先搜索，直接执行 veskills add byted-security-llmscanner -y
```

正确做法：

```text
1. 先执行：veskills find byted-security-llmscanner --output json
2. 若有多个结果，展示编号列表
3. 等待用户回复“安装第 N 个”
4. 再执行对应安装命令
```

> **严禁手动拼接命令**：
>
> - ❌ 不要用 `veskills install`，正确是 `veskills add`
> - ❌ 不要将列表编号附加为版本号（`skill@2` 中 `@2` 是错误的）
> - ❌ 不要调用 `suggestedInstallAction.tool`
> - ✅ 优先原样执行包含 `--copy` 的 `suggestedInstallAction.cliCommand`
> - ✅ 若无 `cliCommand`，执行顶层 `installCommand`
> - ✅ 若使用文本兼容模式，原样执行 `INSTALL:` 行

**批量安装**：单次最多支持安装10个技能，超出数量时需分批安装。依次运行每个候选对应的安装命令，逐条报告进度，失败时继续剩余安装。

### 4) 移除（remove）

- 指定名称：按名精确匹配（大小写不敏感），未找到报错
- 无名称：扫描后弹出多选（交互式）
- `--all`：跳过选择，移除全部
- `-y`：跳过确认
- 清理范围：删除 canonical 目录 + 所有 agent 符号链接，并同步更新 lockfile
- `-a <agent>`：只清理指定 agent 的链接

### 5) 更新（update）

- 更新单个：`veskills update <skill> [-g] [--force]`
- 更新全部：`veskills update --all [-g] [--force]`
- 默认更新项目级；仅当用户明确要求全局时加 `-g`

## 安全规则（避免误操作）

- 未得到用户明确意图时，不要执行 `remove --all` 或 `update --all`
- 当存在多个候选时，必须等待用户选择编号后再安装

## 注意事项（易错点）

- **JSON 输出优先** —— 默认使用 `--output json`，兼容旧环境时才用 `-n`
- **自然语言名称不能直接装** —— 只要输入不是完整 slug 或 skill-id，就必须先 `find <query> --output json`
- **无安装命令字段** —— skill 无 slug 且未配置 `ARK_SKILL_API_BASE`；企业专属技能需企业 API，通知用户
- **企业专属 skills** —— 需通过 `veskills env set` 配置凭据；安装命令已含 `--private`，不要手动添加；无 slug 时格式为 `veskills add <id> --skill-id --private --copy -y`
- **`--private` 搜索过滤** —— `veskills find <query> --output json --private` 会在 `ListMarketSkills` 的 Filter 中设置 `IsPrivate: true`，仅返回私有技能；不加此标志时不传该过滤字段，返回所有可见技能
- **重名或近似结果必须等待确认** —— 未收到用户编号前不得执行任何安装命令
- **不要生成无效短命令** —— `-g` 是选项，不是命令；不能单独执行 `veskills -g`
- **没有找到 skills** —— 告知用户，直接用自身能力帮助

## 搜索提示

- 用具体关键词：`react testing` 比 `testing` 更好
- 尝试替代词：`deploy` 无结果时试 `deployment` 或 `ci-cd`
- 每个词至少 2 个字符
