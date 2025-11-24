#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/app"
OPEN_TEXT_DIR="${APP_DIR}/src/data/open_text"
PRECOMPUTE_MODULE="src.scripts.precompute_open_text_analysis"

echo "[entrypoint] Start $(date -Iseconds)"
cd "$APP_DIR"

# --- Optional: wait for Redis using pure Python (no nc dependency) ---
if [[ "${WAIT_FOR_REDIS:-0}" == "1" ]]; then
python - <<'PY'
import os, socket, sys, time
host = os.environ.get("REDIS_HOST","redis")
port = int(os.environ.get("REDIS_PORT","6379"))
for i in range(60):
    try:
        with socket.create_connection((host, port), timeout=1):
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("Redis not reachable after 60s", file=sys.stderr)
sys.exit(1)
PY
fi

# --- Optional precompute for open-text parquet files ---
if [[ "${SKIP_OPEN_TEXT_PRECOMPUTE:-0}" != "1" ]]; then
  required_ids=(
    "per_ia_oporiscuni_altres"
    "per_ia_posicprof_perque"
    "for_ia_neceformat_altres"
    "comments"
  )

  need=0
  if [[ "${FORCE_OPEN_TEXT_PRECOMPUTE:-0}" == "1" ]]; then
    echo "[entrypoint] FORCE_OPEN_TEXT_PRECOMPUTE=1 → precomputing"
    need=1
  else
    missing=0
    for q in "${required_ids[@]}"; do
      f="${OPEN_TEXT_DIR}/${q}_analysis.parquet"
      [[ -f "$f" ]] || { echo "[entrypoint] Missing $f"; missing=1; }
    done
    [[ $missing -eq 1 ]] && need=1 || echo "[entrypoint] Parquets present → skip precompute"
  fi

  if [[ $need -eq 1 ]]; then
    echo "[entrypoint] Running: python -m ${PRECOMPUTE_MODULE}"
    python -m "${PRECOMPUTE_MODULE}"
    echo "[entrypoint] Precompute done."
  fi
else
  echo "[entrypoint] SKIP_OPEN_TEXT_PRECOMPUTE=1 → skipping precompute."
fi

# --- DO NOT auto-launch the TUI here in sane workflow ---
# If you ever want it, you can guard it behind ADMIN_TUI_ON_START, but leave it OFF in dev.

echo "[entrypoint] Exec: $*"
exec "$@"
