#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)

usage() {
  cat <<'EOF'
Usage: tools/aoe3_automation/setup_linux_host.sh [--install] [--print-only]

This helper inspects the host system outside the Flatpak sandbox and prints the
recommended packages and next steps for the AoE3 Linux automation harness.

Options:
  --install       Run the host package install command through flatpak-spawn.
  --print-only    Only print what would be installed. This is the default.
  --help          Show this help text.
EOF
}

INSTALL_MODE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install)
      INSTALL_MODE=1
      shift
      ;;
    --print-only)
      INSTALL_MODE=0
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v flatpak-spawn >/dev/null 2>&1; then
  echo "error: flatpak-spawn is required to inspect or configure the host system." >&2
  exit 1
fi

HOST_SHELL=(flatpak-spawn --host bash --noprofile --norc -lc)

HOST_OS_RELEASE=$(flatpak-spawn --host cat /etc/os-release)
echo "== Host OS =="
echo "$HOST_OS_RELEASE"
echo

HOST_ID=$("${HOST_SHELL[@]}" '. /etc/os-release && printf %s "$ID"')
HOST_ID_LIKE=$("${HOST_SHELL[@]}" '. /etc/os-release && printf %s "${ID_LIKE:-}"')
HOST_OSTREE=$("${HOST_SHELL[@]}" 'if [[ -e /run/ostree-booted ]]; then printf yes; else printf no; fi')

PACKAGES=(grim slurp wtype ydotool tesseract)
INSTALL_CMD=()
NEXT_STEPS=()

if [[ "$HOST_OSTREE" == "yes" ]] && "${HOST_SHELL[@]}" 'command -v rpm-ostree >/dev/null 2>&1'; then
  INSTALL_CMD=(sudo rpm-ostree install "${PACKAGES[@]}")
  NEXT_STEPS+=("Reboot after rpm-ostree finishes layering packages.")
elif [[ "$HOST_ID" == "fedora" || "$HOST_ID" == "bazzite" || "$HOST_ID_LIKE" == *fedora* ]]; then
  INSTALL_CMD=(sudo dnf install -y "${PACKAGES[@]}")
elif [[ "$HOST_ID" == "ubuntu" || "$HOST_ID" == "debian" || "$HOST_ID_LIKE" == *debian* ]]; then
  INSTALL_CMD=(sudo apt install -y "${PACKAGES[@]}")
elif [[ "$HOST_ID" == "arch" || "$HOST_ID_LIKE" == *arch* ]]; then
  INSTALL_CMD=(sudo pacman -S --needed "${PACKAGES[@]}")
else
  echo "warning: unsupported host distro for automatic package command generation." >&2
fi

echo "== Recommended host packages =="
printf '  %s\n' "${PACKAGES[@]}"
echo

echo "== Current host tool state =="
for tool in ydotool ydotoold wtype grim slurp tesseract; do
  if "${HOST_SHELL[@]}" "command -v $tool >/dev/null 2>&1"; then
    echo "$tool: installed"
  else
    echo "$tool: missing"
  fi
done
echo

if "${HOST_SHELL[@]}" 'pgrep -x ydotoold >/dev/null 2>&1'; then
  echo "ydotoold: running"
else
  echo "ydotoold: not running"
fi
echo

if [[ ${#INSTALL_CMD[@]} -gt 0 ]]; then
  echo "== Host install command =="
  printf '  %q' "${INSTALL_CMD[@]}"
  printf '\n\n'

  if [[ "$INSTALL_MODE" -eq 1 ]]; then
    echo "Running install command on host..."
    flatpak-spawn --host "${INSTALL_CMD[@]}"
    echo
  fi
fi

cat <<'EOF'
== Next steps ==
1. Ensure ydotoold is running on the host before using run-flow on Wayland.
2. Run `python3 tools/aoe3_automation/aoe3_ui_automation.py probe-environment`.
3. Use `tools/aoe3_automation/launch_retest_mod.sh` or `run_runtime_validation.py` for actual test runs.
EOF

if [[ ${#NEXT_STEPS[@]} -gt 0 ]]; then
  printf '4. %s\n' "${NEXT_STEPS[@]}"
fi

echo
echo "Repo: $REPO_ROOT"