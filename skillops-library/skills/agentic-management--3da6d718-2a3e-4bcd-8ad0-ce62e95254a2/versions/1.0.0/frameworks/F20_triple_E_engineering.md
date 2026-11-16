---
name: F20_triple_E_engineering
version: 1.0
framework: 智能体管理学 · 模块四 · 框架20
type: 分析型
description: >
  当用户需要建立或优化Agent开发工程方法时激活。
  触发词：Agent质量不稳定、Triple-E、如何测试Agent、
  Golden Task、Eval、Experiment Registry、脚手架、
  CI/CD门控、传统敏捷在Agent开发中失效、Agent开发流程。
upstream_frameworks: 框架19（MAS架构）
downstream_frameworks: 框架21（Skill治理）、框架24（PRT，模块五）
---

## SKILL 定位
**核心判断**：「谁能把Evals做深做细，谁就能在Agent产品竞争中胜出。」——Andrew Ng。Eval质量是Agent工程能力最重要的单一指标，是Agent时代的「代码覆盖率」。

## 三支柱速查

| 支柱 | 核心要求 | 最常被跳过的步骤 |
|------|---------|----------------|
| Eval-Informed | 先建Golden Task Set再写代码 | 先写代码再补eval（顺序错误） |
| Experiment-Driven | 每次变更都是可追踪实验 | Registry只记录不引用 |
| Scaffolding-First | 脚手架完整才写逻辑 | 「先跑再说，后补质量」 |

## 四步执行
**S1** 建立Golden Task Set（20-100个，先于代码）：覆盖核心场景60%+边界30%+高风险10%
**S2** 搭建完整脚手架（六个组件全部就位）：工具调用/沙箱/记忆/eval套件/追踪/观测
**S3** 建立Experiment Registry（四字段：变更假设/测试配置/eval结果/决策依据）
**S4** 生产失败回灌（持续更新Golden Task Set，这是Triple-E与一次性测试的核心区别）

## 关键规则
- Golden Task Set建立后不是固定的，必须随生产风险持续演化
- 补救性建脚手架比从一开始就建成本高3-5倍
- Experiment Registry必须在决策时被实际引用，否则退化为无效文档

## 典型误区
- Eval-Informed=先穷举eval再开发 → 是评估思维贯穿全程，不是穷举前置
- 脚手架推迟为「上线后再补」 → 补救成本3-5倍，且无法追溯早期失败案例
- Registry流于形式 → 每次实验设计的第一个问题：「我们之前试过这个方向吗」
