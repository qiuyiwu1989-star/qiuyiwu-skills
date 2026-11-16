---
name: F24_PRT_probabilistic_regression_testing
version: 1.0
framework: 智能体管理学 · 模块五 · 框架24
type: 分析型
description: >
  当用户需要建立Agent系统的质量门禁时激活。
  触发词：PRT、概率化测试、Agent质量退化、模型升级后变差、
  Golden Task、统计显著性、LLM-as-Judge、eval质量门控、
  False Positive、False Negative、CI/CD质量门禁。
upstream_frameworks: 框架20（Triple-E工程方法论）
downstream_frameworks: 框架25（三层SLI/SLO金字塔）
---

## SKILL 定位
**核心判断**：传统单元测试在Agent系统中产生两种致命错误——False Positive（单次通过=认为质量良好）和False Negative（单次失败=阻断正常变更）。PRT用统计分布代替单点判断，是Agent工程与传统软件工程最深层的哲学差异之一。

## 五步流程速查

| 步骤 | 内容 | 关键要求 |
|------|------|---------|
| Step 1 | 建立Golden Task Set | 20-100个，覆盖核心+边界+高风险，持续更新 |
| Step 2 | 多次采样 | N=10-20次，获得分布而非单次结果 |
| Step 3 | 双类评分 | Code-based（格式/结构）+ LLM-as-Judge（语义/质量）|
| Step 4 | 统计检验 | 双样本比例检验，p<0.05则阻断，95%置信区间 |
| Step 5 | 生产失败回灌 | 持续回灌，这是PRT长期有效性的核心机制 |

## 判断标准
- p < 0.05 且候选通过率下降 → **阻断发布**
- p ≥ 0.05 → 允许合并（附置信区间报告）
- p 在 0.05-0.10 → 橙色告警，需人工判断

## 五条版本线触发优先级
模型升级（极高）→ Prompt变更（高）→ Skill变更（高）→ Tool/MCP变更（中）→ Context/Memory变更（中）

## 四步执行
**S1** 建立统计化Golden Task Set（含治理机制：每月更新、每季度审查分布）
**S2** 配置多次采样 + 双类评分器（Judge需独立于被测模型，建立校准机制）
**S3** 集成统计检验到CI/CD（自动化双样本比例检验作为PR合并门控）
**S4** 季度校准Judge防止Judge Drift（与人工抽检比对，不一致率>10%触发更新）

## 典型误区
- 沿用精确匹配测试逻辑 → 必须用分布而非单次结果
- Golden Task建立后不更新 → 老化测试集只保障历史场景
- LLM-as-Judge不校准 → Judge Drift使PRT结论失真
