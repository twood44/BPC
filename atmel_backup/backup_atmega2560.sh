#!/usr/bin/env bash
set -euo pipefail

SERIAL="${1:?Usage: $0 SERIAL [BACKUP_DIR]}"
BACKUP_DIR="${2:-$PWD/atmega2560_backup}"

TIMESTAMP="$(date +'%Y-%m-%d_%H-%M-%S')"

mkdir -p "$BACKUP_DIR"

# A per-run directory prevents collisions and groups related reads.
RUN_DIR="$BACKUP_DIR/backup_${SERIAL}_$TIMESTAMP"

if [[ -e "$RUN_DIR" ]]; then
  echo "Backup directory already exists: $RUN_DIR" >&2
  exit 1
fi

mkdir "$RUN_DIR"

echo "Reading ATmega2560 serial $SERIAL into $RUN_DIR"

avrdude -c atmelice_isp -p m2560 -B 1 \
  -U "flash:r:$RUN_DIR/flash_${SERIAL}_$TIMESTAMP.hex:i" \
  -U "eeprom:r:$RUN_DIR/eeprom_${SERIAL}_$TIMESTAMP.hex:i" \
  -U "lfuse:r:$RUN_DIR/lfuse_${SERIAL}_$TIMESTAMP.hex:h" \
  -U "hfuse:r:$RUN_DIR/hfuse_${SERIAL}_$TIMESTAMP.hex:h" \
  -U "efuse:r:$RUN_DIR/efuse_${SERIAL}_$TIMESTAMP.hex:h" \
  -U "lock:r:$RUN_DIR/lock_${SERIAL}_$TIMESTAMP.hex:h" \
  -U "signature:r:$RUN_DIR/signature_${SERIAL}_$TIMESTAMP.hex:h"

(cd "$RUN_DIR" && sha256sum -- *.hex > checksums.sha256)

echo "Backup complete: $RUN_DIR"