# MD 格式规范

## 基本原则

**散文优先**：正文用段落写，不用项目符号作为主要表达结构。
项目符号只用于：行动项清单、例证枚举（超过3条时）、标签列表。

**一份文档，一个核心**：每条入库笔记只聚焦一个核心知识点。发现多个独立价值的洞察时，分拆成多份文档。

**引用块突出核心**：每份文档最重要的一句话用 `>` 引用块突出，让人扫读时能立刻抓住精华。

---

## YAML Frontmatter 规范

```yaml
---
title: [文档标题，见标题命名规则]
date: YYYY-MM-DD
type: [meeting-insight | concept | external-knowledge | project-knowledge | topic-card | teaching-knowledge]
domain: [飞书一级目录名称]
feishu_path: [完整飞书路径，用/分隔]
tags: [用英文逗号分隔，每个标签不含空格]
related: [关联笔记标题列表，用英文逗号分隔]
created_by: brain-agent
---
```

**可选字段**（按内容类型添加）：
- `participants:` 参会人（meeting-insight）
- `source_url:` 来源链接（external-knowledge）
- `author:` 作者（external-knowledge）
- `source_type:` article | book | report | podcast | talk（external-knowledge）
- `project:` 项目名（project-knowledge）
- `knowledge_category:` 策略|产品|运营|技术|教研|踩坑（project-knowledge）
- `priority:` ⭐⭐⭐⭐⭐（topic-card）
- `series:` 系列名（topic-card）
- `status:` 待写|写作中|已发布（topic-card）
- `maturity:` seed|growing|mature（concept）
- `course:` 课程名（teaching-knowledge）
- `audience:` 受众描述（teaching-knowledge）

---

## 标题命名规则

| 类型 | 格式 | 示例 |
|------|------|------|
| meeting-insight | `YYYY-MM-DD [会议主题简称]` | `2024-03-28 AIIP合作模式讨论` |
| concept | 概念名称（精炼，≤15字） | `AI时代信任货币从信息差转向经历差` |
| external-knowledge | `[来源标题] — 精炼` | `智能体经济时代的平台重构 — 精炼` |
| project-knowledge | `[项目名] · [知识点]` | `造物云·AIIP · 探针模型对外开放策略` |
| topic-card | 核心观点句（≤20字） | `中间层没有消失，它在迁移` |
| teaching-knowledge | `[课程简称] · [教学点]` | `浙大MBA · AI认知五层模型讲法` |

---

## 关联节点书写规范

```markdown
## 关联知识节点

→ **[笔记标题]**｜理由：[一句话，说明为什么关联，不超过25字]
→ **[笔记标题]**｜理由：[一句话]
→ **[笔记标题]**｜理由：[一句话]
```

**不合格示例**（不能这样写）：
- `→ **InnoLab方法论**｜理由：相关` ← 「相关」不是理由
- `→ **意图经济**｜理由：同是AI主题` ← 太泛，没有说明具体关联点

**合格示例**：
- `→ **意图经济**｜理由：本文的「判断中介」正是意图经济的核心供给侧`
- `→ **认知五层模型**｜理由：信任转移涉及「价值认知」层，与五层模型第四层对应`

---

## 末尾同步标注格式

每份文档最末尾必须有：
```html
<!-- feishu_sync: [完整feishu_path] -->
```

这一行用于后续飞书同步脚本识别入库路径，不显示在文档正文中。

---

## 格式禁忌

- ❌ 用加粗强调句子中的随机词语（**应该**这样做）
- ❌ 三级以上标题（`### ####`）
- ❌ 正文主体是项目符号列表而非段落
- ❌ 引用块（`>`）嵌套使用
- ❌ 空的字段（不知道填什么的字段，删掉而不是留空）
- ❌ YAML 中出现中文冒号（：）或全角标点
