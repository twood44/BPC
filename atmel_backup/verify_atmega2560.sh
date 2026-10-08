#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "Usage: $0 firmware.hex" >&2
  exit 2
fi
HEX_FILE="$(realpath "$1")"
avrdude -c atmelice_isp -p m2560 -U "flash:v:$HEX_FILE:i"
echo "Verification completed."
