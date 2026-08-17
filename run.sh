#!/usr/bin/env bash
# Usage: ./run.sh [subject]    (default: hera)
set -euo pipefail
SUBJECT="${1:-hera}"
export CLIENT="$SUBJECT"
if [ "$SUBJECT" = "hera" ]; then
  export DB_PATH="agent.db"
  export DASHBOARD_OUT="dashboard.html"
else
  export DB_PATH="agent-${SUBJECT}.db"
  export DASHBOARD_OUT="dashboard-${SUBJECT}.html"
fi
export PYTHONPATH=.
echo "subject: $SUBJECT  db: $DB_PATH  out: $DASHBOARD_OUT  client: $CLIENT"
python -m app.pipeline
