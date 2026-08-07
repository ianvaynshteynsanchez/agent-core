#!/usr/bin/env bash
# Usage: ./run.sh [subject]    (default: hera)
set -euo pipefail
SUBJECT="${1:-hera}"
if [ "$SUBJECT" = "hera" ]; then
  export DB_PATH="agent.db"
  export DASHBOARD_OUT="dashboard.html"
else
  export DB_PATH="agent-${SUBJECT}.db"
  export DASHBOARD_OUT="dashboard-${SUBJECT}.html"
fi
echo "subject: $SUBJECT  db: $DB_PATH  out: $DASHBOARD_OUT"
python -m app.pipeline
