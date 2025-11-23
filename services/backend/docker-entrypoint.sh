#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/app"
OPEN_TEXT_DIR="${APP_DIR}/src/data/open_text"
PRECOMPUTE_SCRIPT="${APP_DIR}/src/scripts/precompute_open_text_analysis.py"
PRECOMPUTE_MODULE="src.scripts.precompute_open_text_analysis"

echo "[entrypoint] Starting container at $(date -Iseconds)"
cd "$APP_DIR"

REQUIRED_QIDS=(
  "per_ia_oporiscuni_altres"
  "per_ia_posicprof_perque"
  "for_ia_neceformat_altres"
  "comments"
)

if [ "${SKIP_OPEN_TEXT_PRECOMPUTE:-0}" = "1" ]; then
  echo "[entrypoint] SKIP_OPEN_TEXT_PRECOMPUTE=1 → skipping open-text precompute."
else
  NEED_PRECOMPUTE=0

  if [ "${FORCE_OPEN_TEXT_PRECOMPUTE:-0}" = "1" ]; then
    echo "[entrypoint] FORCE_OPEN_TEXT_PRECOMPUTE=1 → forcing open-text precompute."
    NEED_PRECOMPUTE=1
  else
    # Comprobar que existen TODOS los parquet requeridos
    MISSING=0
    for qid in "${REQUIRED_QIDS[@]}"; do
      f="${OPEN_TEXT_DIR}/${qid}_analysis.parquet"
      if [ ! -f "$f" ]; then
        echo "[entrypoint] Missing $f → need precompute."
        MISSING=1
      fi
    done

    if [ "$MISSING" -eq 1 ]; then
      NEED_PRECOMPUTE=1
    else
      echo "[entrypoint] All required open-text parquet files present → skipping precompute."
    fi
  fi

  if [ "$NEED_PRECOMPUTE" -eq 1 ]; then
    if [ ! -f "$PRECOMPUTE_SCRIPT" ]; then
      echo "[entrypoint] ERROR: precompute script not found at ${PRECOMPUTE_SCRIPT}" >&2
      exit 1
    fi
    echo "[entrypoint] Running open-text precompute via module ${PRECOMPUTE_MODULE}..."
    python -m "$PRECOMPUTE_MODULE"
    echo "[entrypoint] Open-text precompute finished."
  fi
fi

echo "[entrypoint] Launching application: $*"
exec "$@"
