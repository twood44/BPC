#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "Usage: $0 firmware.hex" >&2
  exit 2
fi
HEX_FILE="$(realpath "$1")"
echo "WARNING: Flash programming can erase existing firmware/bootloader and may erase EEPROM unless EESAVE is programmed."
read -r -p "Type FLASH to continue: " CONFIRM
if [[ "$CONFIRM" != "FLASH" ]]; then echo "Cancelled."; exit 1; fi
# AVRDUDE normally verifies writes; explicit verify is included for clarity.
avrdude -c atmelice_isp -p m2560 \
  -U "flash:w:$HEX_FILE:i" \
  -U "flash:v:$HEX_FILE:i"
echo "Flash and verification completed."
