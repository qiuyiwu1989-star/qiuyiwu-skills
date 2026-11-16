#!/usr/bin/env bash
# ingest.sh — 视频常态化入库（一条龙，到"待写总结"为止）
#
# 用法:
#   bash scripts/ingest.sh "<抖音链接>" [slug]
#   slug 默认 = YYYY-MM-DD-<aweme_id>；建议给语义化 slug，如 bourdieu-university-class
#
# 做的事（机械部分全自动）：
#   1. 下载无水印 mp4 → 抽音 → 转录（调 transcribe.sh）
#   2. 上传 mp4/meta/transcript 到 COS video-archive/<slug>/
#   3. 生成 1 年签名直链
#   4. 在 vault-staging/video/ 搭好归档 md 骨架（元数据已填，留 ## 核心主张 / ## 读后判断 待人工/LLM 补）
#   5. 打印下一步（填总结 → publish-video.sh）
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$(cd "$HERE/.." && pwd)"
URL="${1:?用法: bash scripts/ingest.sh \"<链接>\" [slug]}"
SLUG="${2:-}"
COSCONF="$HOME/.cos.conf"
BUCKET="qiuyiwu-1359505647"

# 1) 下载 + 转录
bash "$HERE/../skills/media-transcript/scripts/transcribe.sh" "$URL"
AID="$(ls -t /tmp/media-transcript/ | head -1)"
OUT="/tmp/media-transcript/$AID"
[ -n "$SLUG" ] || SLUG="$(date +%F)-$AID"

META="$OUT/meta.json"
TITLE="$(python3 -c "import json;d=json.load(open('$META'));print(d.get('title') or d.get('description') or '')")"
AUTHOR="$(python3 -c "import json;d=json.load(open('$META'));print(d.get('author') or '')")"
DURMS="$(python3 -c "import json;d=json.load(open('$META'));print(d.get('duration_ms') or 0)")"
WEBURL="$(python3 -c "import json;d=json.load(open('$META'));print(d.get('web_url') or '')")"
DUR="$(python3 -c "s=int('$DURMS')//1000;print(f'{s//60:02d}:{s%60:02d}')")"

# 2) 上传 COS
coscmd -c "$COSCONF" upload -rs "$OUT/source.mp4" "/video-archive/$SLUG/source.mp4" >/dev/null
coscmd -c "$COSCONF" upload -rs "$META" "/video-archive/$SLUG/meta.json" >/dev/null
coscmd -c "$COSCONF" upload -rs "$OUT/transcript.txt" "/video-archive/$SLUG/transcript.txt" >/dev/null
coscmd -c "$COSCONF" upload -rs "$OUT/transcript.txt.srt" "/video-archive/$SLUG/transcript.srt" >/dev/null 2>&1 || true

# 3) 1 年签名直链
SIGNED="$(coscmd -c "$COSCONF" signurl "/video-archive/$SLUG/source.mp4" -t 31536000 2>/dev/null | grep -oE 'https://[^'\'']+' | head -1)"

# 4) 归档 md 骨架
mkdir -p "$WS/vault-staging/video"
cp "$OUT/transcript.txt" "$WS/vault-staging/video/$SLUG.transcript.txt"
[ -f "$OUT/transcript.txt.srt" ] && cp "$OUT/transcript.txt.srt" "$WS/vault-staging/video/$SLUG.transcript.srt" || true

MD="$WS/vault-staging/video/$SLUG.md"
cat > "$MD" <<EOF
# $TITLE

- **日期**：$(date +%F)
- **来源**：$WEBURL
- **讲者**：$AUTHOR
- **信源层级**：一手（视频原声逐字转写）
- **标签**：待补 / 待补 / 待补
- **一句话**：<待补：≤60字>
- **时长**：$DUR
- **视频**：$SIGNED
- **逐字稿**：$SLUG.transcript.txt

---

## 核心主张

<待补：3-9 条结构化要点>

## 读后判断

<待补：范德的增量判断>
EOF

echo
echo "════════════════════════════════════════"
echo "✅ 机械部分完成"
echo "   slug      : $SLUG"
echo "   aweme_id  : $AID"
echo "   COS       : cos://$BUCKET/video-archive/$SLUG/"
echo "   转写段数  : $(wc -l < "$OUT/transcript.txt")"
echo "   归档骨架  : $MD"
echo
echo "👉 下一步（需 LLM 补总结）："
echo "   1) 填 $MD 的「核心主张 / 读后判断 / 标签 / 一句话」"
echo "   2) 校对逐字稿里的专有名词"
echo "   3) bash scripts/publish-video.sh $SLUG"
echo "════════════════════════════════════════"
