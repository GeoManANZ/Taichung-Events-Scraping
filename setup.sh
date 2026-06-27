#!/bin/bash
# Full setup script — Taichung Weekly Events Scraper
# Run from inside the Hermes container: docker exec hermes1 bash /path/to/setup.sh
#
# This script:
# 1. Creates kanban board tasks (K1-K6)
# 2. Registers the cron job (if not already registered)

set -e

HERMES="${HERMES_CMD:-hermes}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Taichung Weekly Events Scraper Setup ==="

# Step 1: Create kanban board
echo ""
echo "[1/3] Creating kanban board..."
bash "$SCRIPT_DIR/kanban-setup.sh"

# Step 2: Register cron job
echo ""
echo "[2/3] Registering cron job..."
# Check if cron job already exists
EXISTING=$($HERMES cron list 2>/dev/null | grep "taichung-weekly-events" || true)
if [ -n "$EXISTING" ]; then
  echo "  Cron job 'taichung-weekly-events' already exists. Skipping."
else
  $HERMES cron create \
    --name "taichung-weekly-events" \
    --schedule "0 8 * * 5" \
    --prompt "$(cat "$SCRIPT_DIR/cron-prompt.md")" \
    --deliver origin \
    --repeat forever
  echo "  ✅ Cron job registered (Fri 08:00 UTC)"
fi

# Step 3: Verify
echo ""
echo "[3/3] Verification..."
echo "  Kanban tasks:"
$HERMES kanban list
echo ""
echo "  Cron jobs:"
$HERMES cron list | grep "taichung-weekly"

echo ""
echo "=== Setup complete! ==="
echo "Next run: Every Friday at 08:00 UTC"
echo "Manual trigger: $HERMES cron run taichung-weekly-events"
