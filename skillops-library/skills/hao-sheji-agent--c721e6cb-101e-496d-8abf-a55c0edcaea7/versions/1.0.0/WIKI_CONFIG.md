# 好设计创新智能体 · 知识库配置

> 飞书知识库元信息，用于同步与版本管理。

## 知识库信息

- **Space ID**: 7625550239583243458
- **Space Name**: 好设计创新智能体
- **Created**: 2026-04-06

## 节点结构（V2 — 拆分结构）

### 📌 版本记录
- Node Token: EzZywFyPniqfxBkPfOOczgPLn8n
- Doc Token: XvB5daQp3ooG8Ax7CmScqUOwnA5

### 🧠 技能文档（父节点）
- Node Token: Ovw8whJh7iOWilkLuspcj46vnNc
- Doc Token: Z2V7dE31Eos9TMxQPCUctu6jnTQ
- 子节点：
  - SKILL.md: K8ZRdAzjcok6Z1xsFShchn1DnYd
  - 01-award-system: GAEtdSiV7oafk8xXUTFcvQwjnwU
  - 02-cases-index: NBqbdyMBfoXkH8xWQymcTnNBnId
  - 03-five-constructs: OVLJdp9GTo6GoBxLyCBcLow9nPc
  - 04-philosophy: BV7rdQHrgo62UQxbnFhcnB6Gn2c
  - 05-audience-modes: EWJvdwRhsoD4h5xyAX4cM8y5n4g

### 📦 案例库（父节点）
- Node Token: ZykzwI8B2iPaOAkVGxecjtw8nvb
- Doc Token: SfxFdycnYo8GN3xFstNcYqRMnxe
- 子节点：
  - _template 案例模板: LfIXdIkaLonP4kxA0CZcWIHOnNg
  - 蛟龙号 ✅: XHcVdnuLKoH1g9ximpqcF74Hn7b
  - CRH380A ✅: QSIEdg1IpoitdJxAhrfchhutnze
  - 微信 ✅: YwD5dmJWgoQDVgxfyCAcm9smn3c
  - 复兴号 ⏳: SnnydbQYGoeXl6xBFDKcb3VXnib
  - 天眼FAST ⏳: I00EdBneWozxaqxx38NcRPejn3b
  - 神威·太湖之光 ⏳: X5BMdrI62oo0UAxRD0AcLRCJnWh
  - AG600鲲龙 ⏳: GhxUdCPA3oz1cIxjwuZcf1Fvn4z
  - 白鹤滩机组 ⏳: UqvxdCnNRoN69YxS5sKcQNIunmZ
  - 800MN模锻压机 ⏳: CkTfd7JsIo2wTIxjGaecPdVBn8c
  - 嫦娥五/六号 ⏳: GFTLdyNOTooRK3xfMN3cyNZynHc
  - 祝融号火星车 ✅: AiWzd5QGIoKW88xQ976cc54Qnie (node: THo0wU0bGiyb0Qkpe7ncVa9Qnih)

### 📋 设计方案库（父节点）
- Node Token: XfpvwHOmniZUz9kVJm9cNQDVnAe
- Doc Token: DKMUdmPa2ocmUixshATclKpqnUg
- 子节点：
  - 99A体验馆: VpopdsR6Ko37SxxrwghcmZxxnrd
  - 复兴号课程: VZ2yd733Dos5rFxXAhVcgzunnVd

## 同步规则

1. **技能升级** → 更新「版本记录」+ 对应「技能文档」子节点
2. **案例扩充** → 更新对应「案例库」子节点（基础版→完整版）
3. **新方案产出** → 创建新的「设计方案库」子节点 + 本地 `output/` 备份
4. **新增案例** → 创建新的「案例库」子节点 + 本地 `references/cases/` 备份
