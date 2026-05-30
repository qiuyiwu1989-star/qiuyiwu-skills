---
name: xiaomi-tts
description: 用小米 MIMO TTS 把中文文本转成高质量 m4a 语音（茉莉知性讲师默认音色 + 风格标签注入 + 段间静音处理 + 异常重试）。当用户要为文章/卡片/课程/详情页配音、做导览音频、生成讲解音频、批量做语音文件、做 podcast 草稿，或提到"小米 TTS / MIMO / 文字转语音 / 配音 / 朗读 / 语音生成"时使用。即使只说"帮我把这段话变成音频"也应触发。
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash
---

# /xiaomi-tts — 小米 MIMO TTS 语音生成

把中文文本通过小米 MIMO API 转成 **m4a 高质量音频**。内置：
- 茉莉知性讲师默认音色（B3-mori-lecturer），8 个预置音色可选
- 长文本自动切片（≤400 字/段，避免 API 截断）
- 风格标签每段注入（防止后续段落变机械播音腔）
- 头尾静音 trim + 段间 80ms 真静音（避免段间停顿过长）
- 异常检测 + 3 次重试（防 API 偶发卡死返回 17MB 空白音频）
- wav → m4a faststart 转换（10× 压缩，浏览器边下边播）

脚本路径：`~/.claude/skills/xiaomi-tts/generate.py`

---

## 前提：API Key

必须设环境变量 `MIMO_API_KEY`：

```bash
export MIMO_API_KEY="sk-xxxxxxxx"
```

或者在调用时一次性传：

```bash
MIMO_API_KEY=sk-xxx python3 ~/.claude/skills/xiaomi-tts/generate.py ...
```

> Key 通过小米开发者后台申请。如果用户没有，先提示"去 https://api.xiaomimimo.com 申请 API key，然后 `export MIMO_API_KEY=...`"。

---

## 使用方式

### 方式 1：单段文本 → 一个音频

```bash
python3 ~/.claude/skills/xiaomi-tts/generate.py \
  --text "(知性 干练 醇厚) 今天我们聊一聊 AI 思维与认知。AI 不是一场技术竞赛，而是一次认知重塑。" \
  --out ./output/intro.m4a \
  --voice 茉莉
```

### 方式 2：批量 JSON → 多个音频

输入文件 `narrations.json`：

```json
{
  "L0-001": {
    "narration": "(知性 干练 醇厚) 蒸汽机刚出现的时候...",
    "voice": "茉莉"
  },
  "L0-002": {
    "narration": "(温柔 思考) 人类历史上每一次技术革命...",
    "voice": "苏打"
  }
}
```

跑：

```bash
python3 ~/.claude/skills/xiaomi-tts/generate.py \
  --json ./narrations.json \
  --out-dir ./output/audio
```

输出 `./output/audio/L0-001.m4a`、`./output/audio/L0-002.m4a` …

可选过滤：`--targets L0-001 L0-002`（只跑指定卡）/ `--force`（覆盖已有文件）

---

## 风格标签（重要）

写讲稿时**在文本最前面**放风格标签，脚本会自动提取并注入每个分段：

| 标签类型 | 写法 | 作用 | 推荐 |
|---------|------|------|-----|
| 风格 | `(知性 干练 醇厚)` | 整段语音风格 | 长讲解 / 课程 |
| 风格 | `(温柔 缓慢 治愈)` | | 冥想 / 故事 |
| 风格 | `(激昂 兴奋)` | | 宣传片 |
| 锚点 | `[稍停]` | 单点情绪 / 节奏 | 关键转折前 |
| 锚点 | `[思考]` `[轻笑]` | | 自然停顿 |

**典型讲稿示例**：

```
(知性 干练 醇厚) 今天我们聊一聊 AI 思维与认知。[稍停]

AI 不是一场技术竞赛，[轻笑] 而是一次认知重塑。

让我们从最简单的问题开始：你过去三个月对 AI 的判断，[思考] 是用旧框架做出的，还是新框架？
```

---

## 音色清单（mimo-v2.5-tts）

| 音色名 | 类型 | 推荐场景 |
|--------|------|----------|
| **茉莉** | 女声 · 知性干练 | 默认 — 长内容讲解、课程、播客 |
| 苏打 | 女声 · 清亮活泼 | 短文案、社媒、青年内容 |
| 白桦 | 女声 · 温柔治愈 | 冥想、故事、儿童 |
| 冰糖 | 女声 · 甜美 | 客服、轻松内容 |
| Mia | 双语女声 | 中英混读、海外用户 |
| Chloe | 双语女声 | 中英混读 |
| Milo | 男声 | 严肃内容、商务 |
| Dean | 男声 · 沉稳 | 纪录片、严肃讲解 |

---

## 默认 Director Prompt

脚本内置（可通过 `--director` 覆盖）：

> 以资深认知导览员的口吻讲解，温暖知性，像一位认真讲到自己得意论点的老师；语速适中偏慢；核心判断放缓加重；不要播音腔，要有思考的停顿和呼吸。

写好 director prompt 的 3 条经验：
1. **短** — 3-5 句以内，太长 API 会忽略
2. **具体角色 + 场景** — "认知导览员" > "讲解员"
3. **直接说不要什么** — "不要播音腔" 比 "要自然" 更有效

---

## 输出格式

- 中间产物：`output/wav/{id}.wav`（每段拼接后的完整 wav）
- 最终产物：`output/{id}.m4a`（96 kbps AAC + faststart，约 100KB/分钟）

m4a 用 `afconvert`（macOS 内置）；其他系统会自动 fallback 到 `ffmpeg`。

---

## 故障排查

| 症状 | 原因 | 修法 |
|------|------|------|
| `MIMO_API_KEY not set` | 没设环境变量 | `export MIMO_API_KEY=sk-xxx` |
| `'audio'` KeyError × 3 重试都败 | 用错了模型——传了聊天模型而不是 TTS 模型 | 确认 `MIMO_MODEL` 是 **`mimo-v2.5-tts`** 不是 `mimo-v2.5`。前者出音频后者出聊天 |
| `Param Incorrect / messages must contain assistant role for TTS` | TTS 端点格式不对 | 检查端点是 `/v1/chat/completions`（不是裸 `/v1`）；脚本默认正确 |
| 某段 17 MB / 6 分钟空白 | API 偶发卡死循环 | 脚本已自动重试 3 次；仍失败则跑 `--force` 重新生成该段 |
| 后段语气变机械 | 风格标签只在第一段 | 检查文本开头有 `(...)` 标签 — 脚本会自动给后续段补 |
| 段间停顿太长 | 默认已 trim + 80ms 静音 | 想再短可改 `generate.py` 里的 `keep_silence_samples` |
| 段间没有任何停顿 | 把 `--no-silence-gap` 加上 | 仅适用于讲稿本身有标点节奏 |
| afconvert 不存在 | 不在 macOS | 自动用 `ffmpeg`；没有则装一下 `brew install ffmpeg` / `apt install ffmpeg` |

---

## 调用流程（agent 视角）

收到用户的语音生成请求时：

1. **检查 `MIMO_API_KEY`** — `echo $MIMO_API_KEY | head -c 10`，如果空 → 提示用户设
2. **拿到讲稿** — 用户直接给 / 从文件读 / 帮用户起草（如果是后者，先确认风格标签 + 长度 + 音色）
3. **决定输出位置** — 单条用 `--text` + `--out`；批量用 `--json` + `--out-dir`
4. **跑脚本** — `python3 ~/.claude/skills/xiaomi-tts/generate.py ...`
5. **报告结果** — 文件位置、大小、时长（可用 `afinfo` 或 `ffprobe` 看）

如果用户问"小米 TTS 怎么配置"、"音色怎么选"、"我要复用这套配置"，直接给他们这个 skill 的路径：`~/.claude/skills/xiaomi-tts/`，他们 `cat SKILL.md` 就够了。
