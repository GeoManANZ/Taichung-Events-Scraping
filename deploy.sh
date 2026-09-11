#!/bin/bash
# Deploy the scraper into the cron runner's scripts directory.
#
# WHY THIS IS A COPY, NOT A SYMLINK:
#   The runner refuses a script path that RESOLVES OUTSIDE /opt/data/scripts/
#   ("Blocked: script path resolves outside the scripts directory"). A symlink
#   into this project therefore fails at fire time. The file must physically
#   live in /opt/data/scripts/. Run this after every edit to taichung_events.py.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/taichung_events.py"
DEST="/opt/data/scripts/taichung-events-weekly.py"

# If a previous deploy left a symlink here, `install` would write THROUGH it
# back into the project file. Unlink first so DEST becomes a real file.
if [ -L "$DEST" ]; then
  rm -f "$DEST"
  echo "removed stale symlink at $DEST"
fi

install -m 755 "$SRC" "$DEST"
echo "deployed: $SRC -> $DEST"
ls -la "$DEST"
