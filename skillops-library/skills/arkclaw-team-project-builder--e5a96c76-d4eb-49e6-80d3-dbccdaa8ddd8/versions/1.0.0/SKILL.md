---
name: arkclaw-team-project-builder
description: 项目经理负责项目规划、团队组建与项目调整。涵盖：意图识别 → 澄清沟通 → 规划方案 → 创建团队，以及项目运行中的成员增删改、项目信息修改。通过 openclaw gateway call 调用 RPC 落地变更。
---

# arkclaw-team-project-builder Skill

> 项目经理收到"创建项目"或"调整项目"指令时，**必须**使用本 Skill。

## RPC 调用方式

所有 RPC 通过 `openclaw gateway call` 调用，**必须加 `--json`**，输出用 `jq` 裁剪减少 token 消耗：

```bash
openclaw gateway call <方法名> --params '<json>' --timeout 120000 --json 2>/dev/null | jq '{字段1,字段2}'
```

**JSON 参数含中文/多行时，必须先写文件再读取**：

```bash
cat > /tmp/req.json << 'EOF'
{"name":"项目名","experts":[...]}
EOF
openclaw gateway call <方法名> --params "$(cat /tmp/req.json)" --timeout 120000 --json 2>/dev/null | jq '{字段1,字段2}'
```

## 前提

- 你在一个 draft 项目中，项目里**只有你（Manager）一个成员**。
- 项目ID 从 INPUT.md 读取（字段 `project_id` 或目录名 `p-xxx`）。

## 场景一：创建项目

### 阶段 1：意图识别

分析用户需求是否清晰：

- ✅ 清晰 → 直接进入阶段 3
- ❌ 不清晰 → 先改状态为 waiting，再进入阶段 2

```bash
openclaw gateway call arkclaw.team.project.status.update --params '{"id":"<projectId>","status":"waiting"}' --timeout 120000 --json 2>/dev/null | jq '{id,status}'
```

### 阶段 2：澄清沟通（仅需求不清晰时）

向用户提出 1~3 个关键问题。收到回复后，如需求清晰，改回 creating：

```bash
openclaw gateway call arkclaw.team.project.status.update --params '{"id":"<projectId>","status":"creating"}' --timeout 120000 --json 2>/dev/null | jq '{id,status}'
```

### 阶段 3：规划方案

**第一步：收集参考信息**（1 次调用获取全部）：

```bash
python3 scripts/prepare_data.py
```

返回 JSON 包含：

- `projectTemplates`：项目模板列表（name、description、memberCount、memberNames）。如果某个项目模板与需求匹配，用 `load-project-template` 加载完整成员配置作为参考。
- `agentTemplates`：agent 模板列表（name、shortDescription）。如果某个模板与规划角色匹配，用 `load-template` 加载其 soul、agent、skills 作为参考。
- `skills`：本地已安装的 skill 目录名列表
- `remoteSkills`：远程可用的 skill 列表（name、description），包含本地未安装的 skill。规划时可从中选取，创建成员时会自动安装。
- `agents`：当前已注册的非项目 agent 列表（排除 id 以 `p-` 开头的 project agent），包含 name、identity（IDENTITY.md）。如果某个 agent 与规划角色匹配，用 `load-agent` 加载其 soul 和 agentsMd 作为参考模板。

**如果 `prepare_data` 返回的 `skills` 和 `remoteSkills` 中没有找到合适的 skill，可使用 `find-skills` 按关键词搜索远程 skill 仓库：**

```bash
python3 scripts/find-skills.py find "<关键词>" [page] [pageSize]
```

返回 JSON 包含 `results`（每项含 name、description、downloadCount）。搜索到的 skill name 同样可以直接用于 `expert.skills`，创建成员时会自动安装。**搜索到的 skill name 也必须原样使用，不得截断或修改。**

**规划团队时可参考 `projectTemplates`、`agentTemplates` 和 `agents` 判断匹配度，匹配时按需加载详情：**

```bash
# 加载项目模板的完整成员配置（每个成员的 soul、skills）
python3 scripts/load_data.py load-project-template <name>

# 加载 agent 模板的完整信息（soul、agent、skills）
python3 scripts/load_data.py load-template <name>

# 加载已有 agent 的完整信息（soul、agentsMd）
python3 scripts/load_data.py load-agent <agentId>
```

`load-project-template` 返回 name、description、image、locale、members（每个成员含 name、role、soul、skills、locale）。

`load-template` 返回 name、role、soul、agent、skills。

`load-agent` 返回 id、name、workspace、model、tools、identity、soul（SOUL.md）、agentsMd（AGENTS.md）。

**第二步：规划团队**

拆分出 3~6 个 expert，每个包含：

- `name`：成员名字（中文，≤24 字）
- `role`：成员角色（中文）
- `soul`：成员灵魂描述（**必须结构化**，见下方格式）
- `skills`：技能数组（从 prepare_data 返回的 skills 列表或 find-skills 搜索结果中选取。skill name 可能含命名空间前缀如 `clawhub/alirezarezvani/product-manager-toolkit`，**必须原样填写完整名称，严禁截断为 `product-manager-toolkit`**）

**soul 格式要求**（必须包含以下四节）：

```
你是 [角色名称]，负责 [核心职责]。

## 核心职责
- [职责1]
- [职责2]

## 输入来源
- [从哪里获取工作信息/素材]

## 输出要求
- [产出什么，格式，交付给谁]

## 协作边界
- [只负责什么，不负责什么]
```

### 阶段 4：一键创建团队

规划完成后，用 `create-team` 一次性完成项目更新 + 成员创建 + finalize：

```bash
cat > /tmp/team.json << 'EOF'
{
  "name": "项目名称",
  "description": "项目描述",
  "draftSuggestion": {
    "prompt": "用户原始需求",
    "name": "项目名称",
    "description": "项目描述",
    "reasoning": "规划理由和协作流程",
    "experts": [
      {"name":"成员名","role":"角色","soul":"灵魂描述","skills":["skill-name"]}
    ],
    "createdAt": "2025-01-01T00:00:00.000Z"
  },
  "experts": [
    {"name":"成员名","role":"角色","soul":"灵魂描述","skills":["skill-name"]}
  ]
}
EOF
python3 scripts/create_team.py <projectId> @/tmp/team.json
```

> `draftSuggestion.experts` 和 `experts` 内容相同，前者供前端展示，后者用于实际创建。

完成后向用户反馈（**不要自动进入项目规划或调用 teamwork skill**），**必须**在回复末尾包含 `<team-project-start-confirm/>` 标签：

> 项目「XXX」已创建完成（ID: p-xxx），团队成员共 N 位：A、B、C……
>
> 你可以继续调整项目（增删改成员、修改项目信息），或确认无误后点击「启动项目」开始工作。
>
> <team-project-start-confirm/>

## 场景二：调整项目

项目运行中，用户要求调整项目（改名、改描述、增/删/改成员）时：

### 修改项目信息

```bash
cat > /tmp/req.json << 'EOF'
{"id":"<projectId>","name":"新项目名称","description":"新项目描述"}
EOF
openclaw gateway call arkclaw.team.project.update --params "$(cat /tmp/req.json)" --timeout 120000 --json 2>/dev/null | jq '{id,name,status}'
```

### 新增成员

```bash
cat > /tmp/req.json << 'EOF'
{"projectId":"<projectId>","experts":[{"name":"成员名","role":"角色","soul":"灵魂描述","skills":["skill-name"]}]}
EOF
openclaw gateway call arkclaw.team.project.member.batch_add --params "$(cat /tmp/req.json)" --timeout 120000 --json 2>/dev/null | jq '{projectId,status,addedCount:.members|length,members:[.members[]|{name,role,agentId}]}'
```

### 修改成员

```bash
cat > /tmp/req.json << 'EOF'
{"projectId":"<projectId>","agentId":"<agentId>","name":"新名字","role":"新角色","soul":"新灵魂描述","skills":["xxx/xxx/xxx"]}
EOF
openclaw gateway call arkclaw.team.project.member.update --params "$(cat /tmp/req.json)" --timeout 120000 --json 2>/dev/null | jq '{id,status}'
```

### 删除成员

```bash
openclaw gateway call arkclaw.team.project.member.delete --params '{"projectId":"<projectId>","agentId":"<agentId>"}' --timeout 120000 --json 2>/dev/null | jq '{id,status}'
```

### 完成调整后 finalize

调整完成后，**必须**调用 finalize：

```bash
python3 scripts/finalize.py <projectId>
```

完成后向用户反馈调整结果，**必须**在回复末尾包含 `<team-project-start-confirm/>` 标签。

## 严格约束

- [MUST] RPC 调用**必须加 `--json`**，输出**必须用 `jq` 裁剪**，只保留关键字段
- [MUST] JSON 参数含中文/多行时**必须先写文件再 `$(cat 文件)` 读取**，禁止在命令行内嵌复杂 JSON
- [MUST] 需求不清晰时**必须**先 status-update 为 waiting，再提问
- [MUST] 用户澄清后**必须**先 status-update 为 creating，再继续
- [MUST] 规划前**必须**执行 `prepare_data` 获取参考信息和可用 skill 列表
- [MUST] `expert.skills` 中的每个 skill name 必须来自 `prepare_data` 返回的 `skills`/`remoteSkills` 或 `find-skills` 搜索结果，名称必须原样使用（含命名空间前缀如 `clawhub/xxx/yyy`），不得截断、缩写、修改或凭空捏造
- [MUST] `soul` 必须包含：核心职责、输入来源、输出要求、协作边界
- [MUST] name ≤24 字，成员 3~6 个
- [MUST] 创建项目场景用 `create-team` 一次性完成，不要分步调用
- [MUST] `create-team` 成功后**只反馈创建结果，不要自动调用 teamwork skill 或进入项目规划**，等用户确认或调整
- [MUST] 调整项目完成后**必须调用 `finalize`**，并在回复末尾输出 `<team-project-start-confirm/>` 标签
- [MUST] CLI 执行失败时反馈具体错误，不要反复尝试
- [MUST] 不要在回复里输出完整 JSON 让用户确认，直接执行
