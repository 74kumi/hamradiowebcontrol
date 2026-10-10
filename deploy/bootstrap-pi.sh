#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${CHAOSCOMMS_APP_ROOT:-/opt/chaoscomms}"
SERVICE_USER="${CHAOSCOMMS_SERVICE_USER:-chaoscomms}"
MODE="${CHAOSCOMMS_MODE:-}"
CHECK_ONLY=0

usage() {
  printf 'Usage: %s [--check]\n' "$0"
  printf '  --check  validate host and source prerequisites without changing the system\n'
}

for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
  esac
done

fail() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }

[[ -f pyproject.toml ]] || fail 'run from the ChaosComms repository root'
[[ -d chaoscomms ]] || fail 'chaoscomms package directory is missing'

command -v python3 >/dev/null || fail 'python3 is required'
command -v systemctl >/dev/null || fail 'systemd is required'
python3 - <<'PY'
import platform
import sys
if sys.version_info < (3, 11):
    raise SystemExit('Python 3.11 or newer is required')
print(f'Python {platform.python_version()} on {platform.machine()}')
PY

if [[ "$(uname -m)" != "aarch64" && "${CHAOSCOMMS_ALLOW_NON_ARM64:-0}" != "1" ]]; then
  fail 'this installer targets Raspberry Pi ARM64; set CHAOSCOMMS_ALLOW_NON_ARM64=1 only for staging validation'
fi

[[ "$MODE" == simulator || "$MODE" == live ]] || fail 'set CHAOSCOMMS_MODE=simulator or CHAOSCOMMS_MODE=live'

if (( CHECK_ONLY )); then
  printf 'Prerequisite check passed; no system changes made.\n'
  exit 0
fi

[[ "$(id -u)" -eq 0 ]] || fail 'run as root'

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends python3-venv python3-pip ca-certificates

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --home-dir "$APP_ROOT" --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0755 "$APP_ROOT" /var/lib/chaoscomms
install -d -o root -g root -m 0755 /etc/chaoscomms

rm -rf "$APP_ROOT/chaoscomms" "$APP_ROOT/deploy" "$APP_ROOT/pyproject.toml" "$APP_ROOT/tests"
cp -a chaoscomms deploy pyproject.toml "$APP_ROOT/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_ROOT" /var/lib/chaoscomms

python3 -m venv "$APP_ROOT/.venv"
"$APP_ROOT/.venv/bin/pip" install --disable-pip-version-check --no-cache-dir --upgrade pip
"$APP_ROOT/.venv/bin/pip" install --disable-pip-version-check --no-cache-dir "$APP_ROOT"

install -o root -g root -m 0644 deploy/chaoscomms.service /etc/systemd/system/chaoscomms.service
printf 'CHAOSCOMMS_MODE=%s\n' "$MODE" > /etc/chaoscomms.env
chown root:root /etc/chaoscomms.env
chmod 0644 /etc/chaoscomms.env

systemctl daemon-reload
systemctl enable chaoscomms.service
systemctl restart chaoscomms.service
systemctl is-active --quiet chaoscomms.service
printf 'ChaosComms installed and active in %s mode.\n' "$MODE"
