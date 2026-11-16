#!/usr/bin/env bash
# video-to-prompt skill — main entry.
#
# Responsibilities:
#   - Parse positional arg + CUA_VTP_* env vars (and --from-signal stdin payload)
#   - Resolve VTP runtime dir ($VTP_RUNTIME_DIR / $VTP_HOME / repo dev path)
#   - Load layered config (default.json + local.json + env) via lib/load-config.sh
#   - Load model context from openclaw.json via lib/openclaw-ctx.sh
#   - Preflight: ffmpeg/ffprobe present, video accessible + decodable, path
#     whitelisted, model supports video|image
#   - Per-recording lock via $OUTPUT_DIR/.skill.lock (file lock + pid liveness check)
#   - Emit stdout JSON events aligned with skills/computer-use/scripts/cua.sh style
#   - Spawn $VTP_BIN (SEA single-binary)
#
# Usage:
#   video-to-prompt.sh <videoPath>              # dialog-style invocation
#   video-to-prompt.sh --from-signal <<EOF      # signal-style invocation
#   {"skill":"video-to-prompt","payload":{"videoPath":"/tmp/rec.mp4",...}}
#   EOF
#
# Env:
#   CUA_VTP_RECORDING_ID    (optional; generated if absent)
#   CUA_VTP_SESSION_KEY     (optional)
#   CUA_VTP_LANGUAGE        (default: zh-CN)
#   CUA_VTP_MAX_STEPS       (default: 20)
#   CUA_VTP_CLAW_INSTANCE_ID (optional)
#   CUA_VTP_EMIT_SKILL      (default: false)
#   OPENCLAW_CFG            (default: /root/.openclaw/openclaw.json)
#   OPENCLAW_WORKSPACE      (default: $HOME/.openclaw/workspace)

set -euo pipefail

# ── Signal-style entry: parse JSON payload from stdin and lift fields into
#    positional args + environment variables before the normal flow runs.
if [[ "${1:-}" == "--from-signal" ]]; then
  SIGNAL_JSON="$(cat)"
  if [[ -z "$SIGNAL_JSON" ]]; then
    printf '{"type":"preflight_failed","mode":"preflight","reason":"invalid_signal","message":"--from-signal requires JSON payload on stdin"}\n'
    printf '<computer-handoff />\n'
    exit 2
  fi
  if ! SIGNAL_EXPORTS="$(python3 - <<'PY' "$SIGNAL_JSON"
import json, shlex, sys
try:
    raw = json.loads(sys.argv[1])
except Exception as e:
    print(f'__CUA_VTP_SIGNAL_ERROR__={shlex.quote(str(e))}')
    sys.exit(0)
payload = raw.get("payload") if isinstance(raw, dict) and isinstance(raw.get("payload"), dict) else (raw if isinstance(raw, dict) else {})

def q(v: object) -> str:
    return shlex.quote(str(v))

def export(key: str, value: object) -> None:
    if value is None or value == "":
        return
    print(f'{key}={q(value)}')

export("__CUA_VTP_SIGNAL_VIDEO_PATH", payload.get("videoPath", ""))
export("CUA_VTP_RECORDING_ID", payload.get("recordingId", ""))
export("CUA_VTP_SESSION_KEY", payload.get("sessionKey", ""))
export("CUA_VTP_LANGUAGE", payload.get("language", ""))
max_steps = payload.get("maxSteps")
if isinstance(max_steps, (int, float)) and max_steps > 0:
    export("CUA_VTP_MAX_STEPS", int(max_steps))
hints = payload.get("hints") if isinstance(payload.get("hints"), dict) else {}
export("CUA_VTP_CLAW_INSTANCE_ID", hints.get("clawInstanceId", ""))
emit_skill = payload.get("emitSkill")
if isinstance(emit_skill, bool):
    export("CUA_VTP_EMIT_SKILL", "true" if emit_skill else "false")
PY
  )"; then
    printf '{"type":"preflight_failed","mode":"preflight","reason":"invalid_signal","message":"python3 failed to parse signal JSON"}\n'
    printf '<computer-handoff />\n'
    exit 2
  fi
  # R-Round-N H8: replace `eval` with strict KEY=VALUE parser to avoid
  # treating python output as shell code. Each line must match
  # ^[A-Z_][A-Z0-9_]*=... ; values are stripped of surrounding shlex
  # single-quotes if present. Suspicious lines are skipped with a warning.
  while IFS= read -r __vtp_signal_line; do
    [[ -z "$__vtp_signal_line" ]] && continue
    # Strict key whitelist — only CUA_VTP_* / __CUA_VTP_* keys allowed.
    # Prevents a Python-side bug or malicious payload from injecting
    # LD_PRELOAD / PATH / BASH_ENV / PYTHONPATH into the child env.
    if [[ "$__vtp_signal_line" =~ ^(CUA_VTP_[A-Z0-9_]+|__CUA_VTP_[A-Z0-9_]+)=(.*)$ ]]; then
      __vtp_signal_k="${BASH_REMATCH[1]}"
      __vtp_signal_v="${BASH_REMATCH[2]}"
      # strip a single layer of shlex-style single-quotes if present
      if [[ "$__vtp_signal_v" =~ ^\'(.*)\'$ ]]; then
        __vtp_signal_v="${BASH_REMATCH[1]}"
      fi
      export "$__vtp_signal_k=$__vtp_signal_v"
    else
      echo "WARN: ignoring non-whitelisted signal line: $__vtp_signal_line" >&2
    fi
  done <<< "$SIGNAL_EXPORTS"
  unset __vtp_signal_line __vtp_signal_k __vtp_signal_v
  if [[ -n "${__CUA_VTP_SIGNAL_ERROR__:-}" ]]; then
    ERR_MSG_JSON="$(printf '%s' "$__CUA_VTP_SIGNAL_ERROR__" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
    printf '{"type":"preflight_failed","mode":"preflight","reason":"invalid_signal","message":%s}\n' "$ERR_MSG_JSON"
    printf '<computer-handoff />\n'
    exit 2
  fi
  export CUA_VTP_RECORDING_ID CUA_VTP_SESSION_KEY CUA_VTP_LANGUAGE CUA_VTP_MAX_STEPS \
         CUA_VTP_CLAW_INSTANCE_ID CUA_VTP_EMIT_SKILL
  # Re-establish positional args so the rest of the script sees the same shape
  # as the dialog-style invocation.
  set -- "${__CUA_VTP_SIGNAL_VIDEO_PATH:-}"
  unset __CUA_VTP_SIGNAL_VIDEO_PATH
fi

# ── Bootstrap: locate VTP runtime ─────────────────────────────────────────────
# This shell is a thin bootstrap. The actual extractor + config + prompts live
# in the runtime tree. Resolution order:
#   1. $VTP_RUNTIME_DIR   (explicit override)
#   2. $VTP_HOME          (production install, e.g. /root/.vtp)
#   3. repo dev path      (runtime/agents/video-to-prompt/ relative to this skill)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

: "${VTP_HOME:=$HOME/.vtp}"
: "${OPENCLAW_WORKSPACE:=$HOME/.openclaw/workspace}"
: "${OPENCLAW_CFG:=/root/.openclaw/openclaw.json}"

# Locate VTP runtime dir — 用来找 config/default.json + scripts/lib/load-config.sh
# (binary 不内嵌这些；config 仍是文件，bash wrapper 仍要 source helpers)
RUNTIME_DIR=""
if [[ -n "${VTP_RUNTIME_DIR:-}" && -d "$VTP_RUNTIME_DIR/config" ]]; then
    RUNTIME_DIR="$VTP_RUNTIME_DIR"
elif [[ -d "$VTP_HOME/config" ]]; then
    RUNTIME_DIR="$VTP_HOME"
else
    _dev="$SCRIPT_DIR/../../../runtime/agents/video-to-prompt"
    if [[ -d "$_dev/config" ]]; then
        RUNTIME_DIR="$(cd "$_dev" && pwd)"
    fi
fi

if [[ -z "$RUNTIME_DIR" ]]; then
    printf '{"type":"preflight_failed","reason":"runtime_not_found","message":"cannot locate VTP runtime config; set VTP_HOME or install to ~/.vtp"}\n' >&2
    exit 2
fi

SKILL_DIR="$RUNTIME_DIR"            # load-config.sh expects SKILL_DIR pointing at config/
LIB_DIR="$RUNTIME_DIR/scripts/lib"

# SEA binary 是唯一执行路径。
# 检测优先级：
#   1. VTP_BIN env 显式指定（dev / CI override）
#   2. $VTP_HOME/vtp（install.sh 安装路径，生产主路径）
#   3. $RUNTIME_DIR/bin/vtp-<plat>-<arch>（dev build-binary.sh 输出）
if [[ -z "${VTP_BIN:-}" ]]; then
    if [[ -x "$VTP_HOME/vtp" ]]; then
        VTP_BIN="$VTP_HOME/vtp"
    else
        _plat="$(uname -s | tr '[:upper:]' '[:lower:]')"
        _arch="$(uname -m)"
        case "$_arch" in x86_64) _arch=x64 ;; arm64|aarch64) _arch=arm64 ;; esac
        VTP_BIN="$RUNTIME_DIR/bin/vtp-${_plat}-${_arch}"
    fi
fi

if [[ ! -x "$VTP_BIN" ]]; then
    printf '{"type":"preflight_failed","reason":"vtp_binary_missing","message":"VTP binary not found at %s. Run scripts/build-binary.sh or install via plugin install.sh."}\n' "$VTP_BIN" >&2
    exit 2
fi
export VTP_HOME VTP_RUNTIME_DIR OPENCLAW_WORKSPACE OPENCLAW_CFG SKILL_DIR
VTP_RUNTIME_DIR="$RUNTIME_DIR"

# Layered skill config (default.json + $VTP_HOME/config/local.json + env).
# Any pre-set CUA_VTP_* env var takes highest precedence and is preserved.
# shellcheck source=../../../runtime/agents/video-to-prompt/scripts/lib/load-config.sh
source "$LIB_DIR/load-config.sh"

VIDEO_PATH="${1:-}"
RECORDING_ID="${CUA_VTP_RECORDING_ID:-rec_$(date -u +%Y%m%dT%H%M%SZ)_$$}"
SESSION_KEY="${CUA_VTP_SESSION_KEY:-}"
LANGUAGE="${CUA_VTP_LANGUAGE:-zh-CN}"
MAX_STEPS="${CUA_VTP_MAX_STEPS:-20}"
CLAW_INSTANCE_ID="${CUA_VTP_CLAW_INSTANCE_ID:-}"
EMIT_SKILL="${CUA_VTP_EMIT_SKILL:-false}"

if [[ ! "$RECORDING_ID" =~ ^[A-Za-z0-9_-]+$ ]]; then
  printf '{"type":"preflight_failed","mode":"preflight","reason":"invalid_recording_id","message":"recordingId contains unsupported characters"}\n'
  printf '<computer-handoff />\n'
  exit 2
fi

# Default output dir follows ~/.vtp/runs/<recordingId>/. Plugin-spawn path
# overrides via explicit CUA_VTP_OUTPUT_DIR (points to recording-scoped promptDir).
OUTPUT_DIR="${CUA_VTP_OUTPUT_DIR:-$VTP_HOME/runs/$RECORDING_ID}"
MODE="run"
VTP_PID=""
PREFLIGHT_EMITTED_SWITCH_TAG="false"

# ── Event helpers ─────────────────────────────────────────────────────────────
emit_json() {
  python3 - "$@" <<'PY'
import json, sys
from datetime import datetime, timezone

obj = {}
for item in sys.argv[1:]:
    if "=" in item:
        k, v = item.split("=", 1)
        obj[k] = v
obj["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
print(json.dumps(obj, ensure_ascii=False))
PY
}

progress() {
  emit_json "type=progress" "mode=$MODE" "recordingId=$RECORDING_ID" "message=$1"
}

emit_preflight_failed() {
  local reason="$1"
  local message="${2:-$reason}"
  emit_json "type=preflight_failed" "mode=$MODE" "recordingId=$RECORDING_ID" "reason=$reason" "message=$message"
  if [[ "$PREFLIGHT_EMITTED_SWITCH_TAG" != "true" ]]; then
    emit_json "type=computer_handoff" "mode=$MODE" "recordingId=$RECORDING_ID" "reason=$reason"
    printf "<computer-handoff />\n"
  fi
}

# ── Signal handling ───────────────────────────────────────────────────────────
on_int() {
  emit_json "type=progress" "mode=$MODE" "recordingId=$RECORDING_ID" "message=signal_received"
  if [[ -n "${VTP_PID:-}" ]]; then
    kill "$VTP_PID" >/dev/null 2>&1 || true
  fi
  emit_json "type=computer_handoff" "mode=$MODE" "recordingId=$RECORDING_ID" "reason=interrupted"
  printf "<computer-handoff />\n"
  exit 130
}
trap 'on_int' INT TERM

on_err() {
  local code="${1:-1}"
  local msg="${2:-unexpected failure}"
  emit_preflight_failed "internal_error" "$msg (exit=$code)"
  exit "$code"
}
# Disable ERR trap during preflight: the checks below intentionally inspect
# non-zero exit codes via `set +e` / `$?`. Re-enabled after preflight succeeds.

# ── Preflight ─────────────────────────────────────────────────────────────────
MODE="preflight"
progress "phase=preflight.start videoPath=$VIDEO_PATH recordingId=$RECORDING_ID"

# 1) videoPath present
if [[ -z "$VIDEO_PATH" ]]; then
  emit_preflight_failed "video_path_missing" "first positional argument (videoPath) is required"
  exit 2
fi

# 2) Reject URL-style inputs first (the absolute-path check below would otherwise
#    misclassify them as "not absolute").
case "$VIDEO_PATH" in
  http://*|https://*|tos://*|file://*|s3://*|ftp://*)
    emit_preflight_failed "path_is_url" "URL inputs are not supported; mount the file and pass a local path"
    exit 2
    ;;
esac

# 3) videoPath must be an absolute local path.
if [[ "${VIDEO_PATH:0:1}" != "/" ]]; then
  emit_preflight_failed "path_not_absolute" "videoPath must be an absolute path (got: $VIDEO_PATH)"
  exit 2
fi

# 3) videoPath must live under one of the allowed roots — compared on
#    canonical (symlink-resolved) paths to prevent symlink-based bypass.
#    R-review-fix H2: prior impl did literal-prefix `[[ "$path" == "$root"/* ]]`
#    only, so /tmp/symlink-pointing-to-/etc would pass the allowlist while
#    referencing /etc/* under the kernel. Canonicalize both sides via python
#    os.path.realpath (resolves middle-segment symlinks even if leaf doesn't
#    exist; python3 is already a hard preflight dep).
canonicalize_path() {
  python3 -c 'import sys, os; print(os.path.realpath(sys.argv[1]))' "$1" 2>/dev/null || true
}
RESOLVED_VIDEO_PATH="$(canonicalize_path "$VIDEO_PATH")"
if [[ -z "$RESOLVED_VIDEO_PATH" ]]; then
  emit_preflight_failed "path_canonicalize_failed" "could not canonicalize videoPath: $VIDEO_PATH"
  exit 2
fi
ALLOWED_ROOTS="${CUA_VTP_ALLOWED_ROOTS:-/tmp:${OPENCLAW_WORKSPACE}:${VTP_HOME:-/root/.vtp}}"
PATH_ALLOWED="false"
OLD_IFS="$IFS"
IFS=':'
for ROOT in $ALLOWED_ROOTS; do
  IFS="$OLD_IFS"
  [[ -z "$ROOT" ]] && { IFS=':'; continue; }
  RESOLVED_ROOT="$(canonicalize_path "$ROOT")"
  [[ -z "$RESOLVED_ROOT" ]] && { IFS=':'; continue; }
  if [[ "$RESOLVED_VIDEO_PATH" == "$RESOLVED_ROOT" || "$RESOLVED_VIDEO_PATH" == "$RESOLVED_ROOT"/* ]]; then
    PATH_ALLOWED="true"
    break
  fi
  IFS=':'
done
IFS="$OLD_IFS"
if [[ "$PATH_ALLOWED" != "true" ]]; then
  emit_preflight_failed "path_not_in_allowlist" "videoPath must be under one of: $ALLOWED_ROOTS (canonical: $RESOLVED_VIDEO_PATH)"
  exit 2
fi

# 4) videoPath accessible
if [[ ! -r "$VIDEO_PATH" ]]; then
  emit_preflight_failed "video_not_accessible" "videoPath is not readable: $VIDEO_PATH"
  exit 2
fi

# 5) ffmpeg / ffprobe must be installed (needed by bin/tools/*).
if ! command -v ffprobe >/dev/null 2>&1; then
  emit_preflight_failed "ffprobe_missing" "ffprobe is not on PATH; please install ffmpeg"
  exit 2
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  emit_preflight_failed "ffmpeg_missing" "ffmpeg is not on PATH; please install ffmpeg"
  exit 2
fi

# 6) Probe the video to confirm it is decodable. Capture format + duration.
set +e
PROBE_JSON="$(ffprobe -v error -print_format json -show_entries format=format_name,duration "$VIDEO_PATH" 2>/dev/null)"
PROBE_RC=$?
set -e
if [[ $PROBE_RC -ne 0 || -z "$PROBE_JSON" ]]; then
  emit_preflight_failed "video_corrupted" "ffprobe could not parse the file (exit=$PROBE_RC)"
  exit 2
fi
VIDEO_FORMAT="$(printf '%s' "$PROBE_JSON" | python3 -c 'import json,sys
try:
  d=json.load(sys.stdin)
  print((d.get("format") or {}).get("format_name",""))
except Exception:
  print("")' 2>/dev/null)"
VIDEO_DURATION_SEC="$(printf '%s' "$PROBE_JSON" | python3 -c 'import json,sys
try:
  d=json.load(sys.stdin)
  v=(d.get("format") or {}).get("duration","")
  print(f"{float(v):.3f}" if v else "")
except Exception:
  print("")' 2>/dev/null)"

# 7) openclaw.json present
if [[ ! -f "$OPENCLAW_CFG" ]]; then
  emit_preflight_failed "openclaw_config_missing" "openclaw config not found: $OPENCLAW_CFG"
  exit 2
fi

# 8) Load model context (5 lines: modelId / baseUrl / apiKey / inputs / legacyImageFlag).
#    Use sed -n 'Np' to stay portable across bash 3.2 (macOS) and bash 4+ (Linux).
set +e
CTX_OUTPUT="$(/usr/bin/env bash "$LIB_DIR/openclaw-ctx.sh" "$OPENCLAW_CFG")"
CTX_RC=$?
set -e
if [[ $CTX_RC -ne 0 ]]; then
  emit_preflight_failed "openclaw_config_invalid" "openclaw-ctx.sh exit=$CTX_RC (see $OPENCLAW_CFG)"
  exit 2
fi
MODEL_ID="$(printf '%s\n' "$CTX_OUTPUT" | sed -n '1p')"
BASE_URL="$(printf '%s\n' "$CTX_OUTPUT" | sed -n '2p')"
API_KEY="$(printf '%s\n' "$CTX_OUTPUT" | sed -n '3p')"
INPUTS="$(printf '%s\n' "$CTX_OUTPUT" | sed -n '4p')"
SUPPORTS_IMAGE_LEGACY="$(printf '%s\n' "$CTX_OUTPUT" | sed -n '5p')"

if [[ -z "$MODEL_ID" || -z "$BASE_URL" || -z "$API_KEY" ]]; then
  emit_preflight_failed "openclaw_config_invalid" "missing modelId/baseUrl/apiKey after parsing $OPENCLAW_CFG"
  exit 2
fi

# 9) Capability detection (optimistic):
#    - inputs 显式声明 video → confident video
#    - inputs 显式声明 image → confident image
#    - 两者皆无 → 乐观放行（让 Ark 自己报错，避免本地配置漏写造成的误判）
#    实际能力以 Ark API 响应为准；extractor 在 capability error 时降级或上报。
SUPPORTS_VIDEO="false"
SUPPORTS_IMAGE="false"
SUPPORTS_VIDEO_OPTIMISTIC="false"
if [[ " $INPUTS " == *" video "* ]]; then
  SUPPORTS_VIDEO="true"
fi
if [[ " $INPUTS " == *" image "* ]]; then
  SUPPORTS_IMAGE="true"
fi

# 乐观放行：inputs 完全无多模态声明时也尝试视频与图片。
if [[ "$SUPPORTS_VIDEO" != "true" && "$SUPPORTS_IMAGE" != "true" ]]; then
  SUPPORTS_VIDEO="true"
  SUPPORTS_IMAGE="true"
  SUPPORTS_VIDEO_OPTIMISTIC="true"
fi

emit_json "type=preflight_result" "mode=$MODE" "recordingId=$RECORDING_ID" \
  "modelId=$MODEL_ID" "supportsVideo=$SUPPORTS_VIDEO" "supportsImage=$SUPPORTS_IMAGE" \
  "supportsVideoOptimistic=$SUPPORTS_VIDEO_OPTIMISTIC" \
  "supportsImageLegacy=$SUPPORTS_IMAGE_LEGACY" "inputs=$INPUTS" \
  "videoFormat=$VIDEO_FORMAT" "videoDurationSec=$VIDEO_DURATION_SEC"

# 6) Per-recording lock — 防止同 recording 并发分析；不同 recording 可并发
#    旧实现用 pgrep -f "video-to-prompt.sh" 全局匹配，太脆：
#      - 任何命令行含该字符串的进程都误命中（脚本测试、手工调用）
#      - 不同 recording 也被锁住（实际上独立 OUTPUT_DIR 互不干扰）
#    新实现用 $OUTPUT_DIR/.skill.lock 目录（mkdir 原子锁）+ 锁内 pid/nonce +
#    alive check + owner 校验的 trap 清理。
LOCK_DIR="$OUTPUT_DIR/.skill.lock"
mkdir -p "$OUTPUT_DIR"
# H3: mkdir 是原子操作——锁目录已存在则失败，消除旧版 `[[ -f ]] 检查 + echo >
# 写入` 的 check-then-act 竞态（两个并发同-rid 进程曾可同时通过检查、同时写
# 锁）。nonce 标识本进程；trap 退出时只删仍属本进程的锁，不误删被 stale 清理
# 后另一进程重建的锁（旧版裸 `rm -f` 会删他人锁）。
LOCK_NONCE="$$.$(date +%s 2>/dev/null || echo 0).$RANDOM"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  # 锁目录已存在：pid 未写入（另一进程刚 mkdir 尚未写）或进程存活 → busy；
  # pid 已写且进程已死 → 真 stale。
  OLD_PID="$(cat "$LOCK_DIR/pid" 2>/dev/null)"
  if [[ -z "$OLD_PID" ]] || kill -0 "$OLD_PID" 2>/dev/null; then
    emit_preflight_failed "busy" "another skill instance for recording $RECORDING_ID is running (pid=${OLD_PID:-unknown})"
    exit 2
  fi
  # 真 stale（持有者已死）→ 清掉再抢一次；抢不到说明别的进程先抢走 → busy。
  # 已知残留：读 OLD_PID 与 rm -rf 之间有极窄 PID 复用竞态（stale PID 恰被
  # 复用为新 vtp 进程并 mkdir 锁，rm -rf 会误删其锁）。概率极低，且锁内
  # nonce + trap 兜底（误删后真持有者的 trap 因 nonce 不符不会再误删他人
  # 锁）；纯 bash 无法彻底消除，接受此残留竞态。
  rm -rf "$LOCK_DIR" 2>/dev/null || true
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    emit_preflight_failed "busy" "another skill instance for recording $RECORDING_ID is running"
    exit 2
  fi
fi
# #8: mkdir 成功后立即注册无条件清理 trap —— 此刻锁目录必属本进程;若紧接着
# 的 echo pid/nonce 因磁盘满 / inode 耗尽失败,set -e 会在 trap 注册前退出、
# 锁目录泄漏致该 recording 永久 busy。先挂无条件清理,写完 nonce 再升级为
# owner 校验版(只删仍属本进程的锁)。
trap 'rm -rf "$LOCK_DIR" 2>/dev/null || true' EXIT
echo "$$" > "$LOCK_DIR/pid"
echo "$LOCK_NONCE" > "$LOCK_DIR/nonce"
# trap：仅当锁内 nonce 仍是本进程写的才删——否则锁已被别的进程抢占，不删他人锁。
trap 'if [[ "$(cat "$LOCK_DIR/nonce" 2>/dev/null)" == "$LOCK_NONCE" ]]; then rm -rf "$LOCK_DIR"; fi' EXIT

progress "phase=preflight.ok modelId=$MODEL_ID supportsVideo=$SUPPORTS_VIDEO supportsImage=$SUPPORTS_IMAGE"

# Re-enable the ERR trap once preflight succeeds so any failure during the run
# phase surfaces as a structured event rather than a silent non-zero exit.
trap 'on_err "$?" "unexpected failure"' ERR

# ── Run ───────────────────────────────────────────────────────────────────────
MODE="run"
mkdir -p "$OUTPUT_DIR"
emit_json "type=run_detected" "mode=$MODE" "recordingId=$RECORDING_ID" "runId=$RECORDING_ID" \
  "outputPath=$OUTPUT_DIR" "stepsJsonl=$OUTPUT_DIR/steps.jsonl" "promptJson=$OUTPUT_DIR/prompt.json"

# Spawn SEA binary. 大部分参数走 CLI flag（可见、可调试）；API key 走 env
# CUA_VTP_API_KEY，避免 `ps aux` 列在 argv 中暴露密钥。cli.ts 已实现 env 兜底
# (--api-key 已改为可选)；其余 CUA_VTP_* env 是为 extractor.ts:readConfig 现有
# env-driven 路径保留。
CUA_VTP_RECORDING_ID="$RECORDING_ID" \
CUA_VTP_SESSION_KEY="$SESSION_KEY" \
CUA_VTP_LANGUAGE="$LANGUAGE" \
CUA_VTP_MAX_STEPS="$MAX_STEPS" \
CUA_VTP_CLAW_INSTANCE_ID="$CLAW_INSTANCE_ID" \
CUA_VTP_EMIT_SKILL="$EMIT_SKILL" \
CUA_VTP_MODEL_ID="$MODEL_ID" \
CUA_VTP_BASE_URL="$BASE_URL" \
CUA_VTP_API_KEY="$API_KEY" \
CUA_VTP_INPUTS="$INPUTS" \
CUA_VTP_VIDEO_PATH="$VIDEO_PATH" \
CUA_VTP_OUTPUT_DIR="$OUTPUT_DIR" \
CUA_VTP_VIDEO_DURATION_SEC="$VIDEO_DURATION_SEC" \
CUA_VTP_DELETE_VIDEO_ON_SUCCESS="${CUA_VTP_DELETE_VIDEO_ON_SUCCESS:-false}" \
"$VTP_BIN" run \
    --recording-id "$RECORDING_ID" \
    --video-path "$VIDEO_PATH" \
    --output-dir "$OUTPUT_DIR" \
    --model-id "$MODEL_ID" \
    --base-url "$BASE_URL" \
    --max-steps "$MAX_STEPS" \
    --language "$LANGUAGE" \
    --inputs "$INPUTS" \
    --video-duration-sec "$VIDEO_DURATION_SEC" \
    --session-key "$SESSION_KEY" \
    &
VTP_PID=$!

set +e
wait "$VTP_PID"
EX_CODE=$?
set -e

VTP_PID=""
emit_json "type=final_summary" "mode=$MODE" "recordingId=$RECORDING_ID" \
  "outputPath=$OUTPUT_DIR" "binaryExit=$EX_CODE"
emit_json "type=run_exit" "mode=$MODE" "recordingId=$RECORDING_ID" "code=$EX_CODE"
exit "$EX_CODE"
