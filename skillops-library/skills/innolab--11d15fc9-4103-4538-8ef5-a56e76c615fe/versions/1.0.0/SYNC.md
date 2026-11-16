# InnoLab 飞书知识库同步方案

> 更新日期：2026-04-25

## 架构总览

```
本地 (workspace-innolab/skills/innolab/)
  ├── methods/           ← 74个方法文件（本地权威源）
  ├── cases/             ← 9个案例文件（待映射）
  ├── memory/            ← 记忆库（待映射）
  ├── wiki-mapping.json  ← 本地↔飞书地址簿
  ├── sync-to-wiki.py    ← 同步检测脚本
  ├── sync-log.json      ← 同步记录
  └── SYNC.md            ← 本文件

飞书知识库 (space_id: 7625147992015178715)
  ├── 🧠 认知引擎/      ← 19个方法页面
  ├── 🎯 战略引擎/      ← 18个方法页面
  ├── 💡 生成引擎/      ← 12个方法页面
  ├── ⚖️ 决策引擎/      ← 9个方法页面
  ├── 🧩 产品引擎/      ← 13个方法页面
  ├── 🔁 进化引擎/      ← 3个方法页面
  ├── 📚 案例库/        ← 待建
  ├── 📋 迭代日志/      ← 已映射
  ├── 📊 深度评估/      ← 已映射
  └── 🧠 记忆库/        ← 已映射
```

## 同步方向

| 方向 | 触发条件 | 操作 |
|------|---------|------|
| **本地 → 飞书** | 本地方法卡被修改（编辑、新增方法论） | 用 `feishu_doc write` 推送内容 |
| **飞书 → 本地** | 飞书端被手动编辑（懿武在飞书上改了方法卡） | 用 `feishu_doc read` 拉取内容，覆盖本地文件 |
| **双向冲突** | 两边都改了 | 以飞书端为准（懿武的编辑优先），本地备份后覆盖 |

## 内容分叉现状（2026-04-25 诊断）

| 分叉类型 | 占比 | 说明 |
|---------|------|------|
| 飞书端更详细 | ~60% | ST01/PD01/CG04 等在飞书端迭代了多轮，本地是初版 |
| 基本一致 | ~25% | DC01 等内容同步状态良好 |
| 本地更完整 | ~10% | 少数方法本地按7维模板重写过 |
| 飞书端异常 | ~5% | GN01 返回 400 错误 |

### 飞书端远超本地的高优先级方法

| 方法 | 飞书 revision | 飞书 blocks | 本地 bytes | 建议 |
|------|-------------|------------|-----------|------|
| CG04 创造力十段 | 13 | 397 | — | 🔴 拉飞书端到本地 |
| ST01 四代思维 | 2 | 162 | 7557 | 🔴 拉飞书端到本地 |
| PD01 BMC | 2 | 134 | 4662 | 🔴 拉飞书端到本地 |
| EV01 AARRR | 2 | 81 | 2625 | 🟡 拉飞书端到本地 |
| CG01 五层认知 | 7 | 74 | 8445 | 🟡 内容基本一致，格式不同 |

## 同步操作手册

### 手动同步单个方法（本地→飞书）

```python
# 1. 读取本地文件内容
content = open("methods/cognition/five-layer-cognition.md").read()

# 2. 获取 obj_token（从 wiki-mapping.json）
# CG01 → obj_token: MbJwdhIbAoSmRhxymWlcOgfgndc

# 3. 调用 feishu_doc write
feishu_doc(action="write", doc_token="MbJwdhIbAoSmRhxymWlcOgfgndc", content=content)
```

### 手动同步单个方法（飞书→本地）

```python
# 1. 读取飞书端内容
result = feishu_doc(action="read", doc_token="MbJwdhIbAoSmRhxymWlcOgfgndc")

# 2. 写入本地文件
with open("methods/cognition/five-layer-cognition.md", "w") as f:
    f.write(result["content"])
```

### 批量检测变更

```bash
python3 sync-to-wiki.py --dry-run    # 只检测
python3 sync-to-wiki.py --all        # 标记所有为需要同步
python3 sync-to-wiki.py --method CG01  # 只同步指定方法
python3 sync-to-wiki.py --list       # 列出映射状态
```

## 待完成事项

### P0: 内容对齐（最高优先级）

- [x] 飞书→本地拉取：CG04（创造力十段，revision 13）
- [x] 飞书→本地拉取：ST01（四代思维，完整7步流程）
- [x] 飞书→本地拉取：PD01（BMC，完整6步执行）
- [x] 飞书→本地拉取：EV01（AARRR，完整6步）
- [x] 飞书→本地拉取：GN01（六步飞轮，已恢复）
- [x] 修复 GN01（400 错误已恢复，内容已同步）

### P1: 案例库打通

- [x] 创建飞书端案例库 wiki 节点（9个案例 + 1个索引）
- [x] 案例内容写入飞书页面
- [x] wiki-mapping.json 更新（11个 case_pages）
- [ ] 记忆库文件的 wiki 映射
- [ ] 定时同步 cron 任务（可选）

### P2: 内容质量

- [x] SKILL.md 加 Step 4.5 分析质量自评估
- [x] SKILL.md 加 Agent 层面陷阱板块
- [ ] 所有方法卡按 CG14 7维标准审计
- [ ] 从 B+ 升级到 S 级的 Agent 改进

## wiki-mapping.json 结构说明

```json
{
  "space_id": "7625147992015178715",
  "parent_nodes": {
    "cognition": "节点token",
    "strategy": "...",
    ...
  },
  "method_pages": {
    "CG01": {
      "node_token": "wiki节点token",
      "obj_token": "文档token（用于feishu_doc读写）",
      "title": "CG01 五层认知模型",
      "file": "methods/cognition/five-layer-cognition.md"
    }
  },
  "reference_pages": { ... },
  "memory_pages": { ... },
  "case_pages": { ... }
}
```
