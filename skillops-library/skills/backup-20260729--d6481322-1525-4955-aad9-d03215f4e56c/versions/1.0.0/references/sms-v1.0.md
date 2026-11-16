# Skill 管理标准体系 v1.0（SMS）

> 构建 AI Agent 时代的能力资产管理系统
> 作者：邱懿武 × Claude | 版本：v1.0 | 2026-04-25
> 适配：多 Agent 团队架构（范德 CEO + 10 个独立 Agent）

---

## 核心适配说明

本标准原始设计为「一个总 Agent 调用多个 Skill」的单 Agent 架构。
在范德团队中，架构为「多个独立 Agent 各自有 Skill，范德做编排调度」。

**适配要点：**
- Skill 归属 Agent（`parent_agent` 字段必须填写）
- Agent 之间的 Skill 调用通过范德编排层中转
- 评估时考虑「跨 Agent 可组合性」作为额外维度

---

## 一、Skill 的第一性定义

**Skill = Goal + Context + Input + Process + Knowledge + Tool + Output + Evaluation + Boundary + Relation + Version**

即：目标 + 场景 + 输入 + 流程 + 知识 + 工具 + 输出 + 评估 + 边界 + 关系 + 版本。

### Skill 与相近概念

| 概念 | 本质 | 与 Skill 的关系 |
|------|------|----------------|
| Knowledge | 静态内容 | Skill 的「原料」 |
| Prompt | 一次性指令 | Skill 的最低级实现形式 |
| Tool | 外部能力接口 | Skill 的「手脚」 |
| Template | 固定格式 | Skill 的「骨架」之一 |
| Workflow | 多步流程 | Skill 的「血液循环」 |
| Agent | 角色化智能体 | Skill 的「宿主」 |

---

## 二、三维分类体系

### 维度一：能力类型（12 类）

| # | 类型 | 核心动作 | 典型 Skill |
|---|------|---------|-----------|
| 1 | 理解类 | 听懂 | 意图识别、需求澄清 |
| 2 | 获取类 | 找到 | 知识库检索、竞品采集 |
| 3 | 结构化类 | 整理 | 信息归类、知识图谱 |
| 4 | 分析类 | 拆解 | 竞争分析、商业模式分析 |
| 5 | 判断类 | 选择 | 优先级排序、Go/No-Go |
| 6 | 设计类 | 构造 | 产品设计、流程设计 |
| 7 | 执行类 | 操作 | 发邮件、调用 API |
| 8 | 生成类 | 产出 | 报告生成、PRD |
| 9 | 交互类 | 沟通 | 追问、教练式引导 |
| 10 | 协同类 | 组织 | 任务拆分、Agent 调度 |
| 11 | 评估类 | 检查 | 质量审查、风险评估 |
| 12 | 进化类 | 学习 | 反馈吸收、经验迁移 |

**压缩版（5 大类）：** 认知型（1-5）、行动型（6-7）、生成型（8）、协同型（9-10）、治理型（11-12）

### 维度二：能力成熟度（5 级）

| 等级 | 名称 | 特征 |
|------|------|------|
| L1 | 提示词级 | 一段固定 Prompt，无标准输入输出 |
| L2 | 模板级 | 有固定格式，无判断逻辑 |
| L3 | 流程级 | 有步骤、判断节点、中间产物 |
| L4 | 系统级 | 可调用工具/知识库，有评估机制 |
| L5 | 资产级 | 经真实场景验证，有案例/版本/商业化 |

### 维度三：系统角色（3 层）

| 层级 | 角色 | 服务对象 |
|------|------|---------|
| 元层 Meta | 操作系统能力（理解/路由/质检） | 总 Agent（范德） |
| 专业层 Domain | 领域分析能力 | 子 Agent |
| 交付层 Delivery | 成果生成能力 | 写作/输出 Agent |

---

## 三、Skill Card 标准模板（15 字段）

```yaml
# ===== 身份 =====
skill_id: "SK-{领域}-{序号}"
name_zh: ""
name_en: ""
version: "v1.0"
owner: ""
parent_agent: ""  # 归属 Agent（多 Agent 架构必填）

# ===== 能力 =====
type_primary: ""  # 12 类之一
type_secondary: ""
maturity: ""  # L1-L5
system_layer: ""  # meta / domain / delivery
domain_object: ""
one_liner: ""  # ≤30字

# ===== 运行 =====
trigger:
  scenarios: []
  keywords: []
  preconditions: []
input:
  user_input: []
  context_input: []
  knowledge_input: []
  tool_input: []
process:
  steps: []
  decision_points: []
  intermediate_outputs: []
  exception_handling: ""
output:
  type: ""
  format: ""
  fields: []
  downstream_compatible: true

# ===== 治理 =====
quality:
  criteria: []  # 每条含权重
  scoring: ""
boundary:
  not_applicable: []
  common_misuse: []
  risk_level: ""
  human_review_required: false
relations:
  prerequisite: []
  successor: []
  depends_on: []
  composable_with: []
  alternative: []
  evaluated_by: []
  cross_agent_with: []  # 跨 Agent 协作 Skill（多架构新增）
commercial:
  frequency: ""
  monetizable: false
  differentiator: false
  reusability: ""
changelog: []
cases: []
```

---

## 四、评估十维雷达（满分 50）

| 维度 | 评估问题 | 1分 | 3分 | 5分 |
|------|---------|-----|-----|-----|
| 清晰度 | 任务和边界是否明确？ | 描述模糊 | 大致清楚 | 可直接调用 |
| 可调用性 | Agent 能否稳定触发？ | 无触发条件 | 有但不精确 | 触发规则清晰 |
| 可执行性 | 是否有清晰流程？ | 只有概念 | 有步骤无判断 | 步骤+判断+异常处理 |
| 输出稳定性 | 每次输出是否一致？ | 格式随机 | 基本一致 | 标准化可接力 |
| 结果质量 | 实际产出好不好？ | 空泛无洞察 | 有结构有内容 | 有洞察可执行 |
| 复用性 | 能否跨场景使用？ | 仅单一项目 | 跨项目 | 跨行业 |
| 组合性 | 能否与其他 Skill 联动？ | 孤立运行 | 可手动串联 | 有定义好的前后关系 |
| 可评估性 | 输出能否被衡量？ | 无标准 | 有主观标准 | 有量化标准 |
| 安全性 | 有无明显风险？ | 可能输出错误建议 | 有边界不完整 | 有风险清单+审核机制 |
| 商业价值 | 是否值得重点建设？ | 低频低差异 | 有一定需求 | 高频+可变现+强差异化 |

**评估分级：** S(45-50)核心资产 / A(35-44)可用 / B(25-34)实验 / C(15-24)概念 / D(<15)无效

---

## 五、关系类型（7 种 + 跨 Agent）

| 类型 | 含义 | 示例 |
|------|------|------|
| prerequisite | A 必须在 B 之前 | 需求澄清 → 产品九宫格 |
| successor | A 完成后通常接 B | 产品九宫格 → MVP 定义 |
| depends_on | A 运行时必须调用 B | 战略诊断 → 行业研究 |
| composable | A 和 B 经常一起用 | 用户画像 ↔ 消费动机 |
| alternative | A 和 B 可互换 | 九宫格 ↔ MVP 定义 |
| evaluated_by | A 的输出由 B 审查 | 诊断报告 → 逻辑检查 |
| cross_agent | 跨 Agent 协作 | 冷静分析 → 二脑入库 |

---

## 六、生命周期

```
构想 → 定义 → 开发 → 测试 → 发布 → 使用 → 评估 → 迭代 → 沉淀/退役
```

---

## 七、优先级建设矩阵

```
        商业价值高
            │
  ❷ 战略储备  │  ❶ 立即建设
  （打差异化） │  （最优先）
  ────────────┼────────────
  ❹ 观察等待  │  ❸ 效率工具
  （暂不投入） │  （标准化）
            │
        商业价值低
    使用频率低 ──── 使用频率高
```

---

## 八、ID 编码

| 领域代码 | 领域 | ID 范围 |
|---------|------|---------|
| META | 元方法 | SK-META-001~099 |
| STR | 战略 | SK-STR-001~099 |
| ORG | 组织 | SK-ORG-001~099 |
| PRD | 产品 | SK-PRD-001~099 |
| AGT | Agent 构建 | SK-AGT-001~099 |
| IPC | IP/内容 | SK-IPC-001~099 |
| EDU | 教育 | SK-EDU-001~099 |
| RES | 研究 | SK-RES-001~099 |
| DEL | 交付 | SK-DEL-001~099 |
| EVL | 评估 | SK-EVL-001~099 |
| EVO | 进化 | SK-EVO-001~099 |
