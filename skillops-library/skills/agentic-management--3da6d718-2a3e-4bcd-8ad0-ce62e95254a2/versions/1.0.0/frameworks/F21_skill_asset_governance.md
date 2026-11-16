---
name: F21_skill_asset_governance
version: 1.0
framework: 智能体管理学 · 模块四 · 框架21
type: 混合型
description: >
  当用户需要管理企业的Agent Skill资产时激活。
  触发词：Skill治理、Skill Hub、Agent Skill管理、
  提示词资产化、知识可执行化、Skill生命周期、
  SKILL.md、Skill注册表、企业AI能力资产。
upstream_frameworks: 框架20（Triple-E工程方法论）
downstream_frameworks: 框架22（上下文工程）、框架23（AEA第四层）
---

## SKILL 定位
**核心判断**：企业知识管理史上最重要的跃迁——从「文档」（人读）到「可执行资产」（模型直接调用）。Skill注册表是企业知识能力的「可执行地图」。

## 标准Skill结构
```
SKILL.md         # 能力描述与调用说明（模型自主发现的入口）
scripts/         # 执行脚本
resources/       # 所需资源文件
```

## 五阶段生命周期
草稿 → 测试（必须，不可跳过）→ 预发布（必须，不可跳过）→ 生产 → 废弃

## 遥测四指标 + 驱动决策规则
- **调用频次**：低频+高失败 → 触发废弃评估
- **失败率**：高失败 → 触发紧急改进
- **价值贡献**：高频+高价值 → 触发深度优化投入
- **延迟**：性能瓶颈识别
- **原则**：遥测有了但不驱动决策，等于没有遥测

## 四步执行
**S1** 建立Skill标准结构规范（SKILL.md + scripts/ + resources/格式统一）
**S2** 建立Private Skill Hub（Git仓库 + 分类索引 + 贡献规则）
**S3** 实施完整生命周期（Testing和Staging阶段不可跳过）
**S4** 部署遥测并驱动月度运营审查（识别僵尸Skill/高价值Skill/问题Skill）

## 典型误区
- Skill散落各处不统一治理 → 无法发现和复用，重复建设
- 跳过Testing/Staging阶段 → 每次跳过都是给后续运营埋雷
- 遥测只记录不行动 → 月度审查必须产生优先级决策
