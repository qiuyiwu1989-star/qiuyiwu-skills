---
name: ppt-ingest
description: 把一批新的 Keynote 导出课件导入 qiuyiwu.com 的 PPT 资产库（data/atom/*.json + data/slide-library.json），跑通「抽取 → 高清 → 空白检测 → 聚类成原子 → 归节 → VLM 标注 → diff 报告」，并在导入后补归节，让备课台能按主题取到页。触发：给一个 Keynote 导出目录，说「导入新课件」「把这套 PPT 进库」「跑一遍 PPT 管线」「pipe.py 跑一下」「新课件入资产库」。⚠ 当前八步里有五步的脚本不存在，本 skill 会先做体检并如实报缺，不会假装能跑。
---

# PPT Ingest · Keynote 课件进资产库

把一批 Keynote 导出的课件，变成资产库里可按主题检索、可被备课台取用的**原子页**。

**这个 skill 的第一职责不是跑管线，是不骗人。** 现在这条线是断的——
`pipeline/pipe.py` 写了八步的骨架，但其中五步的实现从来没有存在过（git 全历史里没有 `pipeline/steps/` 这个目录）。
更糟的是它**断得没有声音**：见 §1 的那段代码。所以每次动这条线，先跑 §3 的体检。

---

## 0. 先读这一段：pipe.py 会静默假装成功

`pipeline/pipe.py:76-83`：

```python
mod = __import__(f"steps.s{code}_{name}", fromlist=[name])
...
except ImportError:
    print(f"  ⚠ steps/s{code}_{name}.py 尚未实现，跳过\n")
```

`pipeline/steps/` 这个包**不存在**。所以八步会一步不落地全部走 `ImportError` 分支，
打印八行「尚未实现，跳过」，然后打印 `━━━ 完成 ━━━`，写一份 `pipeline/reports/run_*.json`，
**退出码 0**。

对调用方（人、CI、另一个 agent）来说，这跟成功一模一样。

**所以：**
- ❌ 不要把 `python3 pipeline/pipe.py <dir>` 当成「导入课件」的动作。它现在等于 `true`。
- ❌ 不要用它的退出码或它写的 report 当验收依据。
- ✅ 判断有没有真的进料，只看 §5 的四个数字变没变。

> 为什么不顺手把 `except ImportError` 改成报错退出？
> 因为那会让「跑一下管线」从静默无效变成显式失败——这确实更好，但它是一次代码变更，
> 需要邱拍板。列在 §7 的前置任务 P0 里。

---

## 1. 八步现状核对表（2026-08-09 静态查证）

| 步 | pipe.py 要 import 的模块 | 存在？ | 实际可用的东西 |
|----|--------------------------|--------|----------------|
| 01 ingest | `steps/s01_ingest.py` | ❌ | `pipeline/ingest.py` 只做**分类 + 归档**；PPT 分支是占位，第 84-86 行明写「⚠ PPT 增量流水尚未实现」 |
| 02 extract | `steps/s02_extract.py` | ❌ | 无任何等价脚本。缩略图 + 页面文字从哪来，仓库里没有记录 |
| 03 gen_hd | `steps/s03_gen_hd.py` | ❌ | 无。`uploads/slides-hd/` 在本机**根本不存在**（`uploads/slides/` 有 2182 张） |
| 04 detect_blank | `steps/s04_detect_blank.py` | ❌ | 无。PIL 已装（10.4.0），重写不难，但现在没有 |
| 05 cluster | `steps/s05_cluster.py` | ❌ | 无。`ingest.py:9` 和 `gen_vlm_mimo.py` 都提到 `cluster_atoms.py`，**全盘搜索不存在**（Documents / Downloads 深度 6 层都找过） |
| 06 section | `steps/s06_section.py` | ❌ 脚本无 | 但**归节这件事有活的通路**：`GET /api/inside/slides?section=none` 取未归节页，`POST /api/inside/slides/section` 写回。见 §6 |
| 07 vlm | `steps/s07_vlm.py` | ❌ 模块无 | ✅ **实现存在**：`scripts/gen_vlm_mimo.py`（串行）/ `gen_vlm_mimo_parallel.py`。可独立运行，见 §4 |
| 08 diff_report | `steps/s08_diff_report.py` | ❌ | 无。`ingest.py:write_report` 只报文字原子的四类计数，跟 PPT 完全无关 |

**结论：八步里能真跑的只有第 07 步，而它依赖第 03 步产出的高清图（本机没有）。**

### 还有一个表里看不见的缺口：两个库对不上

VLM 脚本写回 `data/slide-library.json`。
而下游全部读 `data/atom/*.json`——`build_kernel.py:192`、`build_semantic_index.py:125`、
`assets_snapshot.py:84`、归节 API `api_server.py:1839`，一个不落。

**没有任何脚本把 `slide-library.json` 拆成 `data/atom/*.json`。** 实测差异：

| | slide-library.json | data/atom/*.json |
|---|---|---|
| 原子数 | 1438 | **1443**（多出 atom-1387/1390/1392/1427/1432） |
| 有 VLM | 1284 | **1404** |

也就是说：**`data/atom/*.json` 是真源，`slide-library.json` 已经落后了**，
而唯一能补 VLM 的脚本却只往落后的那份写。跑完 VLM 你得自己把结果搬过去，没有工具。
这条列在 §7 前置任务 P1。

---

## 2. 输入约定

一个 **Keynote 导出目录**，里面每套课件一个子目录，子目录里必须有 `assets/`
（`ingest.py:31` 就是靠 `assets/` 认 PPT 包的）。

```
2026春季新课件/
├── 某某MBA课/
│   ├── assets/          ← 必须有，否则被当成非 PPT 忽略
│   └── index.html
└── 某某K12课/
    └── assets/
```

已在库的 11 套 deck 及其短 id（新课件起 id 时别撞车）：

```
mba 484  k12 466  obj 187  pdf 215  ptc  74  ind 157
mgt 153  art  41  zwy  53  zhd 251  gji 101      合计 2182 页
```

---

## 3. 开工第一件事：体检（30 秒，不花钱）

```bash
cd /Users/qiu/Documents/qiuyiwu.com

echo "── 缺哪些步骤脚本 ──"
ls pipeline/steps 2>&1 | head -1
for s in 01_ingest 02_extract 03_gen_hd 04_detect_blank 05_cluster 06_section 07_vlm 08_diff_report; do
  [ -f "pipeline/steps/s$s.py" ] && echo "  ✓ s$s" || echo "  ✗ s$s 缺"
done

echo "── VLM 那步的三个前提 ──"
python3 -c "import anthropic;print('  ✓ anthropic',anthropic.__version__)" 2>&1|tail -1
grep -q "^MIMO_API_KEY=." pipeline/.env && echo "  ✓ MIMO_API_KEY 已配" || echo "  ✗ MIMO_API_KEY 缺"
ls uploads/slides-hd 2>/dev/null | wc -l | xargs -I{} echo "  高清图 {} 张（0 或报错=VLM 跑不了）"

echo "── 当前基线四个数（导入前后要对比）──"
python3 - <<'PY'
import json,glob,os
fs=glob.glob('data/atom/atom-*.json')
sec=vlm=0
for f in fs:
    a=json.load(open(f))
    sec+= bool(a.get('section')); vlm+= bool(a.get('vlm_summary'))
d=json.load(open('data/slide-library.json'))
print(f"  原子 {len(fs)}  |  归节 {sec} ({sec*100//len(fs)}%)  |  VLM {vlm} ({vlm*100//len(fs)}%)  |  slide-library 页 {d['total_slides']}")
PY
```

**体检结果怎么用：**

- 五步全 `✗`（今天的实际情况）→ **停在这里，把 §7 报给邱**。不要开始搬文件、不要跑 pipe.py。
- 只缺 07 之外的步骤，但你手上就是要补标注 → 走 §4「只跑 VLM」。
- 全 `✓`（前置任务做完之后）→ 走 §5 全量导入。

---

## 4. 现在唯一能真跑的动作：补 VLM 标注

**前提**：`uploads/slides-hd/<representative_id>.jpg` 存在。本机没有，得先从南京机拉：

```bash
# 高清图不在 git 里（.gitignore 第 25 行 uploads/），只能 rsync
rsync -az yongle-nanjing:/var/www/html/uploads/slides-hd/ uploads/slides-hd/
```

跑：

```bash
python3 scripts/gen_vlm_mimo.py --dry-run          # 先看要跑多少个
python3 scripts/gen_vlm_mimo.py --limit 5          # 试跑 5 个，确认输出像话
python3 scripts/gen_vlm_mimo.py --deck <新deck id> # 只跑新课件那批
```

- 模型 `mimo-v2.5`，端点 `https://token-plan-cn.xiaomimimo.com/anthropic`，key 读 `pipeline/.env`。
  （注意：这是**文本/视觉**模型，别跟 TTS 的 `mimo-v2.5-tts` 混）
- 约 10-20 秒/张，每 5 张落盘一次，`Ctrl+C` 中断不丢已完成的。
- **花钱**。全量 1400 张按脚本头部注释是 4-8 小时挂机。没有明确授权就只跑 `--limit`。
- 写回的是 `data/slide-library.json`——**不是**下游读的 `data/atom/*.json`。见 §1 末尾。

---

## 5. 全量导入流程（**前置任务做完之后**才走这一节）

```bash
python3 pipeline/pipe.py --dry-run <keynote导出目录>       # 先演练
python3 pipeline/pipe.py --skip-vlm <keynote导出目录>      # 01-06 + 08，不花钱
# 人工抽查 20 张聚类结果，觉得对了再补 VLM：
python3 scripts/gen_vlm_mimo.py --deck <新deck id>
```

`--only` / `--skip` 用来续跑：

```bash
python3 pipeline/pipe.py --only 05,06 <dir>    # 只重跑聚类和归节
python3 pipeline/pipe.py --skip 01,02 <dir>    # 前两步已完成，跳过
```

**中间断了怎么办：** `pipe.py:87` 会在失败时写 `pipeline/checkpoint_<ts>.json`，
里面是到断点为止每一步的返回值。看它就知道断在哪、前面各步产出了什么，
然后 `--only` 从断的那步接着跑。

**注意这个 checkpoint 机制现在也是空的**——因为八步都走 `ImportError` 分支（那是 `except ImportError`，
不是 `except Exception`），永远不会触发写 checkpoint。等前置任务补完脚本才有意义。

### 五个易断点（补脚本时按这个清单设计错误信息）

| 断点 | 症状 | 怎么确认 |
|---|---|---|
| Keynote 导出结构变了 | 01 说「0 个 PPT deck」 | 子目录里有没有 `assets/` |
| 页面文字是自定义字体 | 02 抽出乱码 / 空 texts | 抽 5 页看 `text_joined` |
| 高清渲染 | 03 报缺工具 | 本机**没有** ImageMagick / pdftoppm，只有 `sips`、`qlmanage`、PyMuPDF（已装） |
| 空白页阈值 | 04 把有内容的页判成空白 | 对比 `blank_slides`，历史值 143/2182 |
| VLM 找不到图 | 07 每张都 `image not found` | `uploads/slides-hd/<rep_id>.jpg` 在不在 |

---

## 6. 跑完之后必须做的事：归节

**这一步不做，前面全白干。** 归节率是 MUI 的命门——
`assets_snapshot.py:111` 的注释写得最直白：「没归节就按主题取不出来」。

现状 **305 / 1443 = 21%**，1138 页取不出来，备课台至今 **0 场**。
再导入一批不归节的页，只会把分母做大、把归节率做低。

**怎么归：**

```bash
# 1. 取未归节的页
curl -s 'https://qiuyiwu.com/api/inside/slides?section=none&limit=200'

# 2. 逐页/批量写回（一次最多 200 页）
curl -X POST 'https://qiuyiwu.com/api/inside/slides/section' \
  -H 'Content-Type: application/json' \
  -d '{"ids":["atom-0123","atom-0124"],"section":"方法论·AIGD 五层"}'
```

- 写入顺序 API 已经处理好：**先写真源 `data/atom/<id>.json`，成功了才同步内核 PG**。
  反过来会让内核领先真源，下次 `build_kernel.py` 全量重建时改动凭空消失。
- 归节是**人在编辑事实**（L1），不是机器反馈。所以可以由 agent 提议、但节名边界要邱裁。
  （见 `docs/PIPELINE-MAP.html` §07 的方向规则）
- **弹药已经在库里**：1404 页有 VLM `topic` 字段，按它聚类出候选分组，人只裁边界，不用从零看图。

**节名沿用现有 65 个，别自造新体系**，前几名：

```
方法论·智能体管理学 35   方法论·AIGD 五层 27   人物·邱懿武 26
方法论·路演双模板 20     案例·利丰 19         提及·zaowuyun 15
```

命名格式是 `<类>·<名>`，类见 `方法论 / 案例 / 人物 / 判断 / 提及`。
现有全量：`curl -s https://qiuyiwu.com/api/inside/slides/sections`

### 还有两件容易忘的

1. **语义索引不会自动重建。** `deploy.sh` 的重建触发条件只看
   `data/extracted-atoms.json` 和 `data/talks-index.json` 比索引新——
   **`data/atom/*.json` 不在触发条件里**（`deploy.sh` 里那个 `-nt` 判断）。
   新导入的 PPT 页不手动重建就进不了检索：
   ```bash
   FASTEMBED_CACHE_PATH="$HOME/.fastembed-cache" python3 pipeline/build_semantic_index.py
   ```
2. **图片不在 git 里。** `uploads/` 被 `.gitignore` 第 25 行整目录排除，Actions 的 rsync 推的是仓库内容，
   所以新页的 `thumb` / `hd_thumb` **不会随部署上线**，得单独 rsync。
   这条目前没有自动通路，是个真缺口（§7 P2）。

---

## 7. 验收标准：怎么知道这次导入成功了

跑完（含归节）重新执行 §3 的基线脚本，逐条对：

| # | 判据 | 通过标准 |
|---|------|----------|
| 1 | 原子数增长 | `data/atom/*.json` 文件数 > 1443，增量 ≈ 新页数 × 0.66（历史 2182→1443 的去重率） |
| 2 | 两库一致 | `slide-library.json` 的 `atoms` 长度 == `data/atom/*.json` 文件数。**今天差 5，不修就一直差** |
| 3 | VLM 覆盖率 | 新原子里有 `vlm_summary` 的 ≥ 95%（现状 1404/1443 = 97%，不能被这批拉低） |
| 4 | **归节率不下降** | 新增页归节完之后，全库归节率 ≥ 导入前的 21%。**这是唯一的硬闸**——导一批不归节的页会让它掉，那等于倒退 |
| 5 | 图能打开 | 随机 5 个新 `atom_id`，`uploads/slides/<rep>.jpg` 和 `uploads/slides-hd/<rep>.jpg` 都在 |
| 6 | 进得了检索 | 重建语义索引后，`data/semantic/index.json` 里 `type=slide_atom` 的条数增加了 |
| 7 | 备课台取得到 | `python3 pipeline/prep_deck.py --to "试" --min 30 --topic "<新课件主题>"` 能命中新页 |

**第 4 条和第 7 条是真验收，1-3 只是「文件写对了」。**
导入的目的不是让数字变大，是让备课台取得出来。

---

## 8. 前置任务（这些不做，本 skill 只能停在 §4）

按堵住多少东西排：

| 优先级 | 缺什么 | 为什么它排在这 |
|--------|--------|----------------|
| **P0** | `pipe.py` 的 `except ImportError` 改成显式失败退出 | 一行的事。现在它把「什么都没做」报成「完成」，比报错危险得多 |
| **P0** | `steps/s05_cluster.py`（原 `cluster_atoms.py`） | 整条线的核心：2182 页 → 1443 原子的去重聚类。没它，新课件进不了原子层 |
| **P1** | `slide-library.json` ⇄ `data/atom/*.json` 的同步脚本 | 两库现在就差着（1438 vs 1443、VLM 1284 vs 1404）。VLM 补了也送不到下游 |
| **P1** | `steps/s02_extract.py` + `s03_gen_hd.py` | 缩略图 + 页面文字 + 1920×1080 高清。PyMuPDF/PIL 都已装，是重写不是攻坚 |
| **P2** | `steps/s04_detect_blank.py` / `s08_diff_report.py` | 质量与可观测，缺了能凑合（历史 143 张空白页可当回归基线） |
| **P2** | `uploads/` 的上线通路 | 图片不进 git 也不随 Actions 走，现在靠手工 rsync，会忘 |
| **P3** | `steps/s06_section.py` | 归节有 API 通路了，脚本化是提效不是解锁 |

**重写这些脚本前，先看 `data/slide-library.json` 里已有的 slide / atom 字段结构**——
那是上一版脚本的完整输出契约，照着它写，新旧数据才能合到一起：

```
slide: id deck deck_name page thumb uuid texts text_joined text_count text_chars
       text_hash is_blank blank_type title keywords section section_asset_id
       related_assets summary ocr_text similar_to hd_thumb atom_id
atom:  atom_id representative_id use_count uses is_blank blank_type thumb hd_thumb
       title section section_asset_id summary vlm_summary texts text_joined
       text_chars keywords related_assets
```

---

## 9. 数字基线（2026-08-09 本机实测，供 diff 用）

```
data/atom/*.json         1443 个   归节 305 (21%)   有 VLM 1404 (97%)
data/slide-library.json  v0.8 · generated_at 2026-06-29
                         total_slides 2182 · unique 1989 · duplicate 193
                         atoms 1438 · vlm_done 1284 · blank 143 · sections_count 65
uploads/slides           2182 张 / 19MB
uploads/slides-hd        本机不存在
已装：anthropic 0.121.0 · PIL 10.4.0 · PyMuPDF · numpy+fastembed · sips · qlmanage
没装：ImageMagick · pdftoppm
```

## 10. 相关文件

```
pipeline/pipe.py                   八步骨架（steps/ 包不存在）
pipeline/ingest.py                 分类归档；PPT 分支是 TODO 占位
scripts/gen_vlm_mimo.py            07 步唯一活着的实现
scripts/gen_vlm_mimo_parallel.py   同上，并发版
pipeline/api_server.py:1819        归节写入点 slides_set_section
pipeline/assets_snapshot.py:82     归节率/VLM 率的官方算法
pipeline/build_semantic_index.py   PPT 原子进检索（读 data/atom/*.json）
pipeline/prep_deck.py              备课台，最终消费方
docs/PIPELINE-MAP.html             全局管线图（§02 输入源、§06 三大瓶颈、§07 分层规则）
docs/WORKSTATION-DEF.md            MUI 里程碑与三条判据
```
