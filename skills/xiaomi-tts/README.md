# Xiaomi MIMO TTS Skill

把中文文本转成高质量 m4a 语音，使用小米 MIMO API。

## 快速开始

```bash
# 1) 设 API Key
export MIMO_API_KEY="sk-xxxxxxxx"

# 2) 单段文本
python3 ~/.claude/skills/xiaomi-tts/generate.py \
  --text "(知性) 你好，这是测试。" \
  --out ./test.m4a

# 3) 批量 JSON
cat > narrations.json <<'EOF'
{
  "intro": {
    "narration": "(知性 干练 醇厚) 欢迎来到 AI 思维与认知。",
    "voice": "茉莉"
  }
}
EOF

python3 ~/.claude/skills/xiaomi-tts/generate.py \
  --json ./narrations.json \
  --out-dir ./audio
```

## 完整参数

```
--text STR            单段文本
--json FILE           批量 JSON 输入
--out PATH            单段输出 m4a 路径
--out-dir DIR         批量输出目录
--targets ID1 ID2 ... 只跑指定 ID
--force               覆盖已存在文件
--voice NAME          音色（默认 茉莉）
--director STR        Director prompt（默认值见 SKILL.md）
--max-chars N         单段最大字数（默认 400）
--gap-ms N            段间停顿毫秒（默认 80）
--no-silence-gap      等同 --gap-ms 0
--retries N           单段重试次数（默认 3）
--bitrate N           m4a 码率 kbps（默认 96）
```

## 音色

茉莉（默认）/ 苏打 / 白桦 / 冰糖 / Mia / Chloe / Milo / Dean

详见 `SKILL.md` 推荐场景。

## 输出

- `out-dir/{id}.m4a` — 最终音频
- `out-dir/_wav/{id}.wav` — 中间产物（可清掉）

约 100 KB/分钟（96 kbps AAC + faststart，浏览器边下边播）。

## 实战来源

这套配置从 `qiuyiwu.com/ai-cognition` 项目 87 张知识卡 ~6 小时音频内容总结而来。
踩过的坑（API 偶发卡死、后段机械化、段间停顿过长）都内置了对应处理。
