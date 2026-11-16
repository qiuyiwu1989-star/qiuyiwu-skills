---
name: skill-registry-scan
description: "小能核心技能 — 扫描所有workspace的skills/目录，自动生成/更新skill-registry.json。多信号成熟度推断+异常检测+批量模式。触发词：扫描registry/更新技能目录/小能巡检/scan skills"
version: "v2.0"
---

# Skill Registry Scan

> v2.0 | 升级：多信号成熟度推断+异常检测+批量扫描

## 触发词

- "扫描 registry" / "更新技能目录" / "小能巡检" / "scan skills"

## 流程

### Step 1：扫描目录

扫描范围（默认当前workspace，`--all`扫描所有workspace）：
- `/root/.openclaw/workspace/skills/*/SKILL.md`
- `/root/.openclaw/workspace-lengjing/skills/*/SKILL.md`
- `/root/.openclaw/workspace-xiaokai/skills/*/SKILL.md`
- `/root/.openclaw/shared-skills/*/SKILL.md`

对每个SKILL.md提取：
- `name`（frontmatter）
- `description`（frontmatter）
- `version`（如有）
- 是否有 `references/` 目录
- 是否有 `memory/` 目录
- 是否有 `scripts/` 目录
- 是否有 `evals/` 目录
- SKILL.md 行数
- frontmatter完整性（name+description是否齐全）

### Step 2：对比现有 registry

读取 `memory/skill-registry.json`，对比：
- **新增**：目录中有但registry中没有的
- **修改**：SKILL.md最后修改时间比registry的last_scan新的
- **删除**：registry中有但目录中已不存在的

### Step 3：多信号成熟度推断

**不再只看行数，综合5个信号：**

| 信号 | 权重 | 评分规则 |
|------|------|---------|
| SKILL.md行数 | 20% | >500行=5, 300-500=4, 200-300=3, 100-200=2, <100=1 |
| references数量 | 25% | ≥3个=5, 2个=4, 1个=3, 0个=1 |
| memory数量 | 15% | ≥5个=5, 3-4个=4, 1-2个=3, 0个=1 |
| frontmatter完整性 | 20% | name+description+version=5, name+description=4, 只有name=2, 缺失=1 |
| 辅助目录 | 20% | scripts+evals都有=5, 有其一=3, 都没有=1 |

**成熟度映射：**
- 综合分4.5-5.0 → L4（生产级）
- 综合分3.5-4.4 → L3（可用）
- 综合分2.5-3.4 → L2（实验）
- 综合分1.0-2.4 → L1（概念）

### Step 4：异常检测

自动标记以下异常：

| 异常类型 | 检测规则 | 严重度 |
|---------|---------|--------|
| 空SKILL.md | 行数<10或内容为空 | 🔴 严重 |
| frontmatter缺失 | 没有name或description | 🔴 严重 |
| description过短 | description<20字符 | 🟡 警告 |
| 无references的大型Skill | >300行且无references/ | 🟡 警告 |
| 无触发词 | description中无明确触发场景 | 🟡 警告 |
| 孤立Skill | 与其他Skill无任何关系 | 🟢 提示 |

### Step 5：更新 registry.json

增量更新 `memory/skill-registry.json`：

```json
{
  "name": "skill-name",
  "path": "skills/skill-name/",
  "agent": "小能",
  "version": "v2.0",
  "status": "active",
  "maturity": "L3",
  "maturity_signals": {
    "lines": 115,
    "refs_count": 2,
    "mem_count": 1,
    "frontmatter": "complete",
    "aux_dirs": ["scripts"]
  },
  "maturity_score": 4.2,
  "type_primary": "管理类",
  "anomalies": [],
  "last_scan": "2026-05-01T16:00:00+08:00"
}
```

### Step 6：输出变更摘要

```
📊 Skill Registry 扫描完成
━━━━━━━━━━━━━━━━━━━━
扫描范围：{workspace-list}
总计：XX 个 Skill（active XX | deprecated XX）

🆕 新增：X 个
  - skill-name — description [L2]

✏️ 修改：X 个
  - skill-name — 变更说明

🗑️ 删除：X 个
  - skill-name

⚠️ 异常：X 个
  - skill-name — 🔴 空SKILL.md
  - skill-name — 🟡 无触发词

📈 成熟度分布：L4:{N} | L3:{N} | L2:{N} | L1:{N}
```

## 输出文件

- `memory/skill-registry.json` — 更新后的完整registry
- `memory/scan-log.md` — 追加本次扫描记录

## 注意事项

- 只追加/修改，不从头重建registry
- 新Skill自动标记status: "active"，成熟度为推断值
- 异常Skill（空SKILL.md/frontmatter缺失）标为"needs_review"
- 扫描结果喂给skill-audit（深度评估）、skill-graph（关系推断）、agent-capability-map（能力地图）
