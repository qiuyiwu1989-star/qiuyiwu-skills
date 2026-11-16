#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_CFG="${OPENCLAW_CFG:-/root/.openclaw/openclaw.json}"
CUA_BIN="${CUA_BIN:-/root/.cua/cua}"
CUA_CONFIG_DIR="${CUA_CONFIG_DIR:-/root/.cua/config}"
TASK_STATE_FILE="${TASK_STATE_FILE:-/root/.cua/task_state.json}"
DISPLAY_VAR="${DISPLAY:-:99}"
DEFAULT_RUNS_DIR="${DEFAULT_RUNS_DIR:-/root/.cua/runs}"

CMD_MODE="${1:-preflight}"
PREFLIGHT_EMITTED_SWITCH_TAG="false"
CUA_PID=""
MONITOR_PID=""

now_ts() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

emit_json() {
  python3 - <<'PY' "$@"
import json, sys
from datetime import datetime, timezone

args = sys.argv[1:]
obj = {}
for it in args:
  if "=" in it:
    k, v = it.split("=", 1)
    obj[k] = v
obj["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
print(json.dumps(obj, ensure_ascii=False))
PY
}

progress() {
  emit_json "type=progress" "mode=${CMD_MODE}" "message=$1"
}

on_err() {
  code="${1:-1}"
  msg="${2:-unknown error}"
  emit_json "type=preflight_failed" "mode=${CMD_MODE}" "code=${code}" "message=${msg}"
  printf "preflight_failed: %s\n" "$msg" >&2
  if [[ "$CMD_MODE" == "preflight" && "$PREFLIGHT_EMITTED_SWITCH_TAG" != "true" ]]; then
    emit_json "type=computer_handoff" "mode=${CMD_MODE}" "reason=preflight_failed"
    printf "<computer-handoff />\n"
  fi
  exit "$code"
}

trap 'on_err "$?" "unexpected failure (exit=$?)"' ERR

on_int() {
  progress "signal_received=interrupt"
  if [[ -n "${CUA_PID:-}" ]]; then
    kill "$CUA_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${MONITOR_PID:-}" ]]; then
    kill "$MONITOR_PID" >/dev/null 2>&1 || true
  fi
  printf "<computer-handoff />\n"
  exit 130
}

trap 'on_int' INT TERM

if [[ ! -f "$OPENCLAW_CFG" ]]; then
  on_err 2 "openclaw config not found: $OPENCLAW_CFG"
fi

if [[ ! -x "$CUA_BIN" ]]; then
  on_err 2 "cua binary not found or not executable: $CUA_BIN"
fi

MODEL_ID=""
BASE_URL=""
API_KEY=""
MULTIMODAL_SUPPORTED=""
PROVIDER_NAME=""
MATCHED_MODEL_NAME=""
ARG_PROVIDER=""
ARG_MODEL_ID=""
ARG_BASE_URL=""
ARG_API_KEY=""
RUN_TASK=""

resolve_runs_dir() {
  python3 - <<'PY' "$CUA_CONFIG_DIR" "$DEFAULT_RUNS_DIR"
import json, sys
from pathlib import Path

cfg_dir = Path(sys.argv[1])
fallback = str(sys.argv[2])

def load(p: Path):
  if not p.exists():
    return {}
  try:
    return json.loads(p.read_text(encoding="utf-8"))
  except Exception:
    return {}

local_cfg = load(cfg_dir / "local.json")
default_cfg = load(cfg_dir / "default.json")

def get_runs_dir(obj):
  agent = obj.get("agent", {}) if isinstance(obj, dict) else {}
  v = agent.get("runsDir")
  return v if isinstance(v, str) and v.strip() else ""

runs_dir = get_runs_dir(local_cfg) or get_runs_dir(default_cfg) or fallback
runs_dir = str(runs_dir).strip()
print(runs_dir)
PY
}

load_openclaw_context() {
  python3 - <<'PY' "$OPENCLAW_CFG"
import json, sys
from pathlib import Path

cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
primary = str(cfg["agents"]["defaults"]["model"]["primary"])
parts = primary.split("/", 1)
if len(parts) != 2 or not parts[0] or not parts[1]:
  print(f"invalid primary model spec (expect '<provider>/<model_id>'): {primary!r}", file=sys.stderr)
  sys.exit(2)
provider_name, model_id = parts[0], parts[1]

providers = cfg.get("models", {}).get("providers", {})
if not isinstance(providers, dict) or provider_name not in providers:
  print(f"provider not found in models.providers: {provider_name!r}", file=sys.stderr)
  sys.exit(2)
provider = providers[provider_name]
if not isinstance(provider, dict):
  print(f"provider entry malformed: {provider_name!r}", file=sys.stderr)
  sys.exit(2)

base_url = str(provider.get("baseUrl", "")).strip().strip("`").strip().strip('"').strip("'")
api_key = str(provider.get("apiKey", "")).strip().strip("`").strip().strip('"').strip("'")

provider_models = provider.get("models", []) or []

multimodal_whitelist = {
  "doubao-seed-2.0-pro",
  "kimi-k2.6",
  "kimi-k2.5",
  "doubao-seed-2.0-code",
  "doubao-seed-2.0-lite",
  "doubao-seed-2.0-mini",
  "doubao-seed-1-8",
  "doubao-seed-2.0-code-preview-260215"
}

candidates = []
for m in provider_models:
  if not isinstance(m, dict):
    continue
  raw_name = str(m.get("name", "")).strip()
  if not raw_name:
    continue
  candidates.append((raw_name, raw_name.lower(), m))

target_raw = model_id
target_lower = model_id.lower()

found = None
matched_name = ""
matched_level = ""

if target_lower in multimodal_whitelist:
  for raw, low, m in candidates:
    if low == target_lower:
      found, matched_name = m, raw
      matched_level = "whitelist_with_provider_match"
      break
  if found is None:
    matched_name = target_lower
    matched_level = "whitelist_only"

if found is None and matched_level != "whitelist_only":
  for raw, low, m in candidates:
    if raw == target_raw:
      found, matched_name = m, raw
      matched_level = "L1_raw_exact"
      break
  if found is None:
    for raw, low, m in candidates:
      if low == target_lower:
        found, matched_name = m, raw
        matched_level = "L2_lower_exact"
        break
  if found is None:
    best_len = -1
    for raw, low, m in candidates:
      if target_raw.startswith(raw + "-") and len(raw) > best_len:
        found, matched_name = m, raw
        matched_level = "L3_raw_prefix"
        best_len = len(raw)
  if found is None:
    best_len = -1
    for raw, low, m in candidates:
      if target_lower.startswith(low + "-") and len(low) > best_len:
        found, matched_name = m, raw
        matched_level = "L4_lower_prefix"
        best_len = len(low)

if found is None and matched_level != "whitelist_only":
  print(f"model not found under provider {provider_name!r}: {model_id!r}", file=sys.stderr)
  sys.exit(2)

if matched_level.startswith("whitelist"):
  ok = True
else:
  inputs = found.get("input", []) or []
  ok = "image" in set(map(str, inputs))

print(provider_name)
print(model_id)
print(matched_name)
print(base_url)
print(api_key)
print("true" if ok else "false")
PY
}

load_openclaw_context_override() {
  python3 - <<'PY' "$OPENCLAW_CFG" "$ARG_PROVIDER" "$ARG_MODEL_ID" "$ARG_BASE_URL" "$ARG_API_KEY"
import json, sys
from pathlib import Path

cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
override_provider = str(sys.argv[2]).strip()
override_model_id = str(sys.argv[3]).strip()
override_base_url = str(sys.argv[4]).strip().strip("`").strip().strip('"').strip("'")
override_api_key = str(sys.argv[5]).strip().strip("`").strip().strip('"').strip("'")

if not override_model_id or not override_api_key:
  print("override model/api key missing", file=sys.stderr)
  sys.exit(2)

providers = cfg.get("models", {}).get("providers", {})
if not isinstance(providers, dict) or not providers:
  print("models.providers missing", file=sys.stderr)
  sys.exit(2)

multimodal_whitelist = {
  "doubao-seed-2.0-pro",
  "kimi-k2.6",
  "kimi-k2.5",
  "doubao-seed-2.0-code",
  "doubao-seed-2.0-lite",
  "doubao-seed-2.0-mini",
  "doubao-seed-1-8",
  "doubao-seed-2.0-code-preview-260215"
}

def clean(value):
  return str(value or "").strip().strip("`").strip().strip('"').strip("'")

def build_candidates(provider_entry):
  candidates = []
  for item in provider_entry.get("models", []) or []:
    if not isinstance(item, dict):
      continue
    raw_name = str(item.get("name", "")).strip()
    if not raw_name:
      continue
    candidates.append((raw_name, raw_name.lower(), item))
  return candidates

def match_model(provider_entry, model_id):
  candidates = build_candidates(provider_entry)
  target_raw = model_id
  target_lower = model_id.lower()
  found = None
  matched_name = ""
  matched_level = ""

  if target_lower in multimodal_whitelist:
    for raw, low, item in candidates:
      if low == target_lower:
        found, matched_name = item, raw
        matched_level = "whitelist_with_provider_match"
        break
    if found is None:
      matched_name = target_lower
      matched_level = "whitelist_only"

  if found is None and matched_level != "whitelist_only":
    for raw, low, item in candidates:
      if raw == target_raw:
        found, matched_name = item, raw
        matched_level = "L1_raw_exact"
        break
    if found is None:
      for raw, low, item in candidates:
        if low == target_lower:
          found, matched_name = item, raw
          matched_level = "L2_lower_exact"
          break
    if found is None:
      best_len = -1
      for raw, low, item in candidates:
        if target_raw.startswith(raw + "-") and len(raw) > best_len:
          found, matched_name = item, raw
          matched_level = "L3_raw_prefix"
          best_len = len(raw)
    if found is None:
      best_len = -1
      for raw, low, item in candidates:
        if target_lower.startswith(low + "-") and len(low) > best_len:
          found, matched_name = item, raw
          matched_level = "L4_lower_prefix"
          best_len = len(low)
  return found, matched_name, matched_level

def resolve_provider_entry():
  if override_provider:
    provider_entry = providers.get(override_provider)
    if not isinstance(provider_entry, dict):
      print(f"provider not found in models.providers: {override_provider!r}", file=sys.stderr)
      sys.exit(2)
    return override_provider, provider_entry

  for provider_name, provider_entry in providers.items():
    if not isinstance(provider_entry, dict):
      continue
    found, matched_name, matched_level = match_model(provider_entry, override_model_id)
    if found is not None or matched_level == "whitelist_only":
      return provider_name, provider_entry

  print(f"unable to resolve provider for model: {override_model_id!r}", file=sys.stderr)
  sys.exit(2)

provider_name, provider_entry = resolve_provider_entry()
found, matched_name, matched_level = match_model(provider_entry, override_model_id)
if found is None and matched_level != "whitelist_only":
  print(f"model not found under provider {provider_name!r}: {override_model_id!r}", file=sys.stderr)
  sys.exit(2)

if matched_level.startswith("whitelist"):
  ok = True
else:
  inputs = found.get("input", []) or []
  ok = "image" in set(map(str, inputs))

base_url = override_base_url or clean(provider_entry.get("baseUrl"))
if not base_url:
  print(f"baseUrl missing for provider {provider_name!r}", file=sys.stderr)
  sys.exit(2)

print(provider_name)
print(override_model_id)
print(matched_name)
print(base_url)
print(override_api_key)
print("true" if ok else "false")
PY
}

load_openclaw_context_from_args_or_default() {
  if [[ -n "$ARG_MODEL_ID" && -n "$ARG_API_KEY" ]]; then
    if load_openclaw_context_override 2>/dev/null; then
      return 0
    fi
  fi
  load_openclaw_context
}

parse_run_args() {
  ARG_PROVIDER=""
  ARG_MODEL_ID=""
  ARG_BASE_URL=""
  ARG_API_KEY=""
  RUN_TASK=""
  RUN_PASSTHROUGH=()

  if [[ $# -lt 1 ]]; then
    on_err 2 "usage: $0 run [--provider <provider>] [--model-id <model_id>] [--base-url <base_url>] [--api-key <api_key>] [extra cua flags...] <task_content>"
  fi

  # 语义：task_content 永远是最后一个参数，其前面均为参数
  # （脚本级 --provider/--model-id/... 或原样透传给 cua 的 flag）。
  local all=( "$@" )
  local last_idx=$(( ${#all[@]} - 1 ))
  RUN_TASK="${all[$last_idx]}"
  set -- "${all[@]:0:$last_idx}"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --provider)
        [[ $# -ge 2 ]] || on_err 2 "missing value for --provider"
        ARG_PROVIDER="$2"
        shift 2
        ;;
      --model-id)
        [[ $# -ge 2 ]] || on_err 2 "missing value for --model-id"
        ARG_MODEL_ID="$2"
        shift 2
        ;;
      --base-url)
        [[ $# -ge 2 ]] || on_err 2 "missing value for --base-url"
        ARG_BASE_URL="$2"
        shift 2
        ;;
      --api-key)
        [[ $# -ge 2 ]] || on_err 2 "missing value for --api-key"
        ARG_API_KEY="$2"
        shift 2
        ;;
      --)
        shift
        RUN_PASSTHROUGH+=( "$@" )
        break
        ;;
      *)
        # 其余参数（含 --trace-id 等 flag 及其空格分隔的值）原样透传给 cua run。
        RUN_PASSTHROUGH+=( "$1" )
        shift
        ;;
    esac
  done

  if [[ -z "$RUN_TASK" ]]; then
    on_err 2 "usage: $0 run [--provider <provider>] [--model-id <model_id>] [--base-url <base_url>] [--api-key <api_key>] [extra cua flags...] <task_content>"
  fi
}

check_single_process() {
  if command -v pgrep >/dev/null 2>&1; then
    if pgrep -f "$CUA_BIN run" >/dev/null 2>&1; then
      on_err 1 "existing cua run process detected"
    fi
  fi
}

do_preflight() {
  progress "phase=preflight.start"
  mapfile -t ctx < <(load_openclaw_context_from_args_or_default)
  PROVIDER_NAME="${ctx[0]:-}"
  MODEL_ID="${ctx[1]:-}"
  MATCHED_MODEL_NAME="${ctx[2]:-}"
  BASE_URL="${ctx[3]:-}"
  API_KEY="${ctx[4]:-}"
  MULTIMODAL_SUPPORTED="${ctx[5]:-}"

  if [[ -z "$PROVIDER_NAME" || -z "$MODEL_ID" || -z "$MATCHED_MODEL_NAME" || -z "$BASE_URL" || -z "$API_KEY" || -z "$MULTIMODAL_SUPPORTED" ]]; then
    on_err 2 "failed to resolve provider/model/base_url/api_key/multimodal from $OPENCLAW_CFG"
  fi

  emit_json "type=preflight_result" "mode=${CMD_MODE}" "provider=${PROVIDER_NAME}" "model_id=${MODEL_ID}" "matched_model=${MATCHED_MODEL_NAME}" "multimodal_supported=${MULTIMODAL_SUPPORTED}"
  if [[ "$MULTIMODAL_SUPPORTED" == "true" ]]; then
    printf "[cua.sh] provider=%s model=%s matched=%s multimodal(image)=YES\n" "$PROVIDER_NAME" "$MODEL_ID" "$MATCHED_MODEL_NAME" >&2
  else
    printf "[cua.sh] provider=%s model=%s matched=%s multimodal(image)=NO\n" "$PROVIDER_NAME" "$MODEL_ID" "$MATCHED_MODEL_NAME" >&2
  fi
  if [[ "$MULTIMODAL_SUPPORTED" != "true" ]]; then
    PREFLIGHT_EMITTED_SWITCH_TAG="true"
    emit_json "type=model_switch_multimodal" "mode=${CMD_MODE}" "provider=${PROVIDER_NAME}" "model_id=${MODEL_ID}"
    printf "<model-switch-multimodal />\n"
    exit 0
  fi
  check_single_process
  progress "phase=preflight.ok provider=${PROVIDER_NAME} model_id=${MODEL_ID}"
}

do_run() {
  if [[ $# -lt 1 ]]; then
    echo "usage: $0 run [--provider <provider>] [--model-id <model_id>] [--base-url <base_url>] [--api-key <api_key>] <task_content>" >&2
    exit 2
  fi
  task="$1"
  shift || true

  # 其余参数原样透传给 cua run；但 --model / --base-url / --api-key 由本脚本
  # 从 openclaw 配置中解析，必须忽略调用方再次传入，避免覆盖。
  passthrough_args=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --model|--base-url|--api-key)
        echo "[cua.sh] ignore reserved flag: $1" >&2
        shift 2 || true
        ;;
      --model=*|--base-url=*|--api-key=*)
        echo "[cua.sh] ignore reserved flag: ${1%%=*}" >&2
        shift
        ;;
      *)
        passthrough_args+=( "$1" )
        shift
        ;;
    esac
  done

  do_preflight
  runs_dir="$(resolve_runs_dir)"
  if [[ -z "$runs_dir" ]]; then
    runs_dir="$DEFAULT_RUNS_DIR"
  fi
  progress "phase=run.prepare runs_dir=${runs_dir}"

  before_dirs=""
  if [[ -d "$runs_dir" ]]; then
    before_dirs="$(ls -1 "$runs_dir" 2>/dev/null | tr '\n' ' ')"
  fi

  progress "phase=run.start"
  DISPLAY="$DISPLAY_VAR" CUA_CONFIG_DIR="$CUA_CONFIG_DIR" "$CUA_BIN" run \
    --model "$MODEL_ID" \
    --base-url "$BASE_URL" \
    --api-key "$API_KEY" \
    ${passthrough_args[@]+"${passthrough_args[@]}"} \
    "$task" &
  CUA_PID="$!"
  emit_json "type=cua_process" "mode=${CMD_MODE}" "pid=${CUA_PID}"

  run_id=""
  for _ in $(seq 1 200); do
    if ! kill -0 "$CUA_PID" >/dev/null 2>&1; then
      break
    fi
    if [[ -d "$runs_dir" ]]; then
      for d in $(ls -1 "$runs_dir" 2>/dev/null); do
        case "$d" in
          output|images) continue ;;
        esac
        if [[ -n "$before_dirs" ]] && [[ " $before_dirs " == *" $d "* ]]; then
          continue
        fi
        if [[ -d "$runs_dir/$d" ]]; then
          run_id="$d"
          break
        fi
      done
    fi
    if [[ -n "$run_id" ]]; then
      break
    fi
    sleep 0.05
  done

  if [[ -n "$run_id" ]]; then
    run_dir="${runs_dir}/${run_id}"
    emit_json "type=run_detected" "mode=${CMD_MODE}" "run_id=${run_id}" "runs_dir=${runs_dir}" "run_dir=${run_dir}"
    emit_json "type=run_paths" "mode=${CMD_MODE}" "run_id=${run_id}" "steps_jsonl=${run_dir}/steps.jsonl" "run_meta=${run_dir}/run.meta.json" "steps_json=${run_dir}/steps.json"
    cat > "$TASK_STATE_FILE" <<TASKSTATE
{"type":"running","runId":"${run_id}","prompt":$(python3 -c "import json,sys; print(json.dumps(sys.argv[1],ensure_ascii=False))" "$task"),"runsDir":"${runs_dir}","pid":${CUA_PID},"startTime":"$(now_ts)"}
TASKSTATE
  else
    emit_json "type=run_detect_failed" "mode=${CMD_MODE}" "runs_dir=${runs_dir}"
  fi

  wait "$CUA_PID"
  code="$?"
  if [[ -n "${run_id:-}" ]] && [[ -f "${runs_dir}/${run_id}/steps.json" ]]; then
    reason_json="$(python3 - <<'PY' "${runs_dir}/${run_id}/steps.json"
import json, sys
p = sys.argv[1]
try:
  data = json.loads(open(p, "r", encoding="utf-8").read())
  print(json.dumps({"success": data.get("success"), "reason": data.get("reason")}, ensure_ascii=False))
except Exception:
  print("{}")
PY
)"
    emit_json "type=final_summary" "mode=${CMD_MODE}" "run_id=${run_id}" "summary=${reason_json}"
  fi
  emit_json "type=run_exit" "mode=${CMD_MODE}" "code=${code}" "run_id=${run_id}"
  rm -f "$TASK_STATE_FILE"
  return "$code"
}

cmd="${1:-preflight}"
shift || true
case "$cmd" in
  preflight)
    do_preflight
    ;;
  run)
    parse_run_args "$@"
    do_run "$RUN_TASK" ${RUN_PASSTHROUGH[@]+"${RUN_PASSTHROUGH[@]}"}
    ;;
  *)
    on_err 2 "usage: $0 {preflight|run} ..."
    ;;
esac
