#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGED_BUA_BIN="${SCRIPT_DIR}/bua"
PACKAGED_AGENT_BROWSER_BIN="${SCRIPT_DIR}/agent-browser"
PACKAGED_SKILL_FILE="${SCRIPT_DIR}/SKILL.md"

INSTALL_BIN_DIR="/usr/local/bin"
BUA_BIN="${INSTALL_BIN_DIR}/bua"
AGENT_BROWSER_BIN="${INSTALL_BIN_DIR}/agent-browser"

OPENCLAW_HOME="/root/.openclaw"
SKILL_DIR="/root/.agents/skills/browser-use"
SKILL_FILE="${SKILL_DIR}/SKILL.md"

BUA_ENV_FILE="/etc/default/bua"
BUA_SERVICE_FILE="/etc/systemd/system/bua-gc.service"
BUA_TIMER_FILE="/etc/systemd/system/bua-gc.timer"

CHROME_BIN="/usr/bin/google-chrome"
DISPLAY_VALUE=":99"
BUA_STATE_DIR="/var/run/bua"
BUA_PROFILE="/root/.arkclaw/bua-profile"
BUA_LOG_DIR="/var/log/arkclaw"
BUA_LOG_FILE="${BUA_LOG_DIR}/bua.log"
BUA_CHROME_LOG_FILE="${BUA_LOG_DIR}/chrome.log"
BUA_CDP_PORT="9222"
GC_IDLE="24h"

log() {
  echo "[install-bua] $*"
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Please run as root" >&2
    exit 1
  fi
}

require_cmd() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Missing required command: ${cmd}" >&2
    exit 1
  fi
}

install_from_package() {
  local src="$1"
  local dst="$2"
  local mode="${3:-}"
  local dir tmp

  if [[ ! -f "${src}" ]]; then
    echo "Missing packaged file: ${src}" >&2
    exit 1
  fi

  dir="$(dirname "${dst}")"
  mkdir -p "${dir}"
  tmp="$(mktemp "${dir}/.$(basename "${dst}").tmp.XXXXXX")"
  trap 'rm -f "${tmp:-}"' RETURN

  cp "${src}" "${tmp}"
  if [[ -n "${mode}" ]]; then
    chmod "${mode}" "${tmp}"
  fi
  mv -f "${tmp}" "${dst}"
  trap - RETURN
}

check_prereqs() {
  require_root
  require_cmd cp
  require_cmd chmod
  require_cmd mkdir
  require_cmd mktemp
  require_cmd mv
  require_cmd systemctl

  if [[ ! -x "${CHROME_BIN}" ]]; then
    echo "Chrome not found at ${CHROME_BIN}" >&2
    echo "Adjust CHROME_BIN in this script or install google-chrome first." >&2
    exit 1
  fi
}

install_binaries() {
  log "Installing packaged bua to ${BUA_BIN}"
  install_from_package "${PACKAGED_BUA_BIN}" "${BUA_BIN}" 755

  log "Installing packaged agent-browser to ${AGENT_BROWSER_BIN}"
  install_from_package "${PACKAGED_AGENT_BROWSER_BIN}" "${AGENT_BROWSER_BIN}" 755
}

install_skill() {
  log "Installing packaged SKILL.md to ${SKILL_FILE}"
  install_from_package "${PACKAGED_SKILL_FILE}" "${SKILL_FILE}"
}

prepare_dirs() {
  log "Preparing runtime directories"
  mkdir -p "${BUA_STATE_DIR}"
  mkdir -p "${BUA_PROFILE}"
  mkdir -p "${BUA_LOG_DIR}"
  chmod 755 "${BUA_STATE_DIR}" "${BUA_PROFILE}" "${BUA_LOG_DIR}"
}

write_env() {
  log "Writing ${BUA_ENV_FILE}"
  cat > "${BUA_ENV_FILE}" <<EOF
HOME=/root
DISPLAY=${DISPLAY_VALUE}
BUA_CHROME_BIN=${CHROME_BIN}
AGENT_BROWSER_BIN=${AGENT_BROWSER_BIN}
BUA_STATE_DIR=${BUA_STATE_DIR}
BUA_PROFILE=${BUA_PROFILE}
BUA_LOG=${BUA_LOG_FILE}
BUA_CHROME_LOG=${BUA_CHROME_LOG_FILE}
BUA_CDP_PORT=${BUA_CDP_PORT}
EOF
}

write_service() {
  log "Writing ${BUA_SERVICE_FILE}"
  cat > "${BUA_SERVICE_FILE}" <<EOF
[Unit]
Description=arkclaw-bua garbage collect

[Service]
Type=oneshot
User=root
EnvironmentFile=${BUA_ENV_FILE}
ExecStart=${BUA_BIN} gc --idle ${GC_IDLE}
Nice=10
EOF
}

write_timer() {
  log "Writing ${BUA_TIMER_FILE}"
  cat > "${BUA_TIMER_FILE}" <<'EOF'
[Unit]
Description=Run bua gc hourly

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
EOF
}

enable_timer() {
  log "Reloading systemd"
  systemctl daemon-reload

  log "Enabling bua-gc.timer"
  systemctl enable --now bua-gc.timer
}

smoke_test() {
  log "Running smoke test: bua doctor"
  set +e
  env $(grep -v '^[[:space:]]*$' "${BUA_ENV_FILE}" | xargs) "${BUA_BIN}" doctor
  local rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    log "Warning: bua doctor returned non-zero (${rc})"
    log "Check Chrome, DISPLAY, and journald logs if needed."
  fi
}

show_result() {
  cat <<EOF

Install complete.

Files:
- ${BUA_BIN}
- ${AGENT_BROWSER_BIN}
- ${SKILL_FILE}
- ${BUA_ENV_FILE}
- ${BUA_SERVICE_FILE}
- ${BUA_TIMER_FILE}

Useful commands:
- systemctl status bua-gc.timer
- systemctl start bua-gc.service
- journalctl -u bua-gc.service -n 50 --no-pager
- journalctl -u bua-gc.timer -n 20 --no-pager
- env \$(grep -v '^[[:space:]]*$' ${BUA_ENV_FILE} | xargs) ${BUA_BIN} doctor

Timer schedule:
- first run: 5 minutes after boot
- repeat: every 1 hour after previous run

If you want "hourly on the clock" instead of "every 1 hour since last run",
replace OnUnitActiveSec=1h with OnCalendar=hourly in:
- ${BUA_TIMER_FILE}
EOF
}

main() {
  check_prereqs
  install_binaries
  install_skill
  prepare_dirs
  write_env
  write_service
  write_timer
  enable_timer
  smoke_test
  show_result
}

main "$@"
