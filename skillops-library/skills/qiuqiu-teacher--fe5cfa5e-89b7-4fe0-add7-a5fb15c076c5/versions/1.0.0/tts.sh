#!/bin/bash
# 球球老师 TTS 语音生成脚本
# 用法: bash tts.sh "要说的话"
# 输出: /tmp/qiuqiu_voice.opus（飞书可发送的 OPUS 格式）

TEXT="$1"
if [ -z "$TEXT" ]; then
  echo "用法: bash tts.sh '要说的话'"
  exit 1
fi

# Step 1: 调用本地 TTS 适配器生成 MP3（凭据从环境变量读取，勿硬编码）
MIMO_KEY="${MIMO_TTS_KEY:-$(cat ~/.config/mimo.key 2>/dev/null)}"
curl -s http://127.0.0.1:18800/v1/audio/speech \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MIMO_KEY}" \
  -d "{\"model\":\"mimo-v2.5-tts\",\"input\":\"$TEXT\",\"voice\":\"mimo_default\"}" \
  -o /tmp/qiuqiu_voice.mp3

if [ ! -s /tmp/qiuqiu_voice.mp3 ]; then
  echo "❌ TTS 生成失败"
  exit 1
fi

# Step 2: 转换为 OPUS 格式
ffmpeg -y -i /tmp/qiuqiu_voice.mp3 -c:a libopus -b:a 32k /tmp/qiuqiu_voice.opus 2>/dev/null

if [ ! -s /tmp/qiuqiu_voice.opus ]; then
  echo "❌ OPUS 转换失败"
  exit 1
fi

echo "✅ 语音文件已生成: /tmp/qiuqiu_voice.opus"
ls -la /tmp/qiuqiu_voice.opus
