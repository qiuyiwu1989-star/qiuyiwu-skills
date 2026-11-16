#!/usr/bin/env bash
# transcribe.sh — 抖音链接一条龙：解析 → 下载无水印 mp4 → 抽音 → 转录
#
# 用法:
#   bash transcribe.sh "<抖音分享链接>" [输出目录]
#
# 产出（在 <输出目录>，默认 /tmp/media-transcript/<aweme_id>）:
#   meta.json        解析元数据（含无水印 mp4 直链）
#   source.mp4       无水印视频
#   audio.wav        16k 单声道音频
#   transcript.txt   逐句逐字稿 [hh:mm:ss.mmm-hh:mm:ss.mmm]
#   transcript.srt   标准 SRT（可导剪映/Arctime）
#
# 依赖：python3(douyin.py/transcribe.py)、ffmpeg、faster-whisper
# 模型：~/.openclaw/models/faster-whisper-medium（或 --model-dir 指定）
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL="${1:?用法: bash transcribe.sh \"<抖音链接>\" [输出目录]}"
OUTBASE="${2:-/tmp/media-transcript}"
MODEL_DIR="${MODEL_DIR:-$HOME/.openclaw/models/faster-whisper-medium}"

command -v ffmpeg >/dev/null || { echo "ERROR: 缺 ffmpeg" >&2; exit 1; }
[ -f "$MODEL_DIR/model.bin" ] || echo "⚠️  模型目录无 model.bin: $MODEL_DIR（transcribe.py 会回退默认路径）" >&2

# 1) 解析（按域名分流；带重试）
#   抖音: api.douyin.wtf（稳定 API）
#   小红书: 读分享页 __INITIAL_STATE__（脆弱路径：xsec_token 有时效、结构变更会断）
TMPMETA="$(mktemp)"
case "$URL" in
  *xhslink.com*|*xiaohongshu.com*)
    PARSER="$HERE/xhs.py"; PLAT="小红书" ;;
  *tiktok.com*)
    PARSER="$HERE/douyin.py"; PLAT="TikTok" ;;
  *)
    PARSER="$HERE/douyin.py"; PLAT="抖音" ;;
esac
for attempt in 1 2 3; do
  if python3 "$PARSER" "$URL" --json "$TMPMETA" 2>/dev/null; then break; fi
  echo "⚠️  $PLAT 解析失败（第 $attempt 次），等 5s 重试…" >&2; sleep 5
done
[ -s "$TMPMETA" ] || { echo "ERROR: 解析失败，可能解析服务不可用或链接已过期" >&2; exit 2; }
AID="$(python3 -c "import json;print(json.load(open('$TMPMETA'))['aweme_id'])")"
OUT="$OUTBASE/$AID"
mkdir -p "$OUT"
cp "$TMPMETA" "$OUT/meta.json"

MP4="$(python3 -c "import json;print(json.load(open('$OUT/meta.json'))['mp4']['url'])")"
TITLE="$(python3 -c "import json;d=json.load(open('$OUT/meta.json'));print(d.get('title') or d.get('description') or '')" | head -c 120)"
echo "🎬 $AID  $TITLE"

# 2) 下载无水印 mp4
if [ ! -s "$OUT/source.mp4" ]; then
  curl -sL --max-time 900 -H "User-Agent: Mozilla/5.0" -e "https://www.douyin.com/" "$MP4" -o "$OUT/source.mp4"
fi
echo "📥 source.mp4 $(du -h "$OUT/source.mp4" | cut -f1)"

# 3) 抽音（16k 单声道，whisper 友好）
if [ ! -s "$OUT/audio.wav" ]; then
  ffmpeg -nostdin -y -i "$OUT/source.mp4" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$OUT/audio.wav" >/dev/null 2>&1
fi
echo "🎧 audio.wav $(du -h "$OUT/audio.wav" | cut -f1)"

# 4) 转录（毫秒时间戳 + SRT）
python3 "$HERE/transcribe.py" "$MODEL_DIR" "$OUT/audio.wav" "$OUT/transcript.txt" --ms

# 5) 清理中间音频（wav 很大，转录完即可删；如需保留加 --keep-audio）
if [ "${3:-}" != "--keep-audio" ]; then rm -f "$OUT/audio.wav"; fi

echo "✅ 完成 → $OUT"
ls -la "$OUT"
