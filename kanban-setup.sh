#!/bin/bash
# Kanban Board Setup — Taichung Weekly Events Scraper
# Run from inside the Hermes container: docker exec hermes1 bash /path/to/kanban-setup.sh
# Or from a host where `hermes` CLI is available.
#
# Creates K1-K6 kanban tasks with proper dependency chaining.

HERMES="${HERMES_CMD:-hermes}"

echo "Creating kanban board for Taichung Weekly Events Scraper..."

# Create scraper tasks (K1-K5) — all independent, run in parallel
K1=$($HERMES kanban create --json --assignee default \
  --body 'Search KKTIX for events in Taichung happening next week. URL: https://kktix.com/search?q=%E5%8F%B0%E4%B8%AD. Extract event name, date, time, location, price and description. Filter to events in the upcoming week only (Mon-Sun).' \
  "K1: Scrape KKTIX — Taichung Events" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

K2=$($HERMES kanban create --json --assignee default \
  --body 'Search ACCUPASS for events in Taichung happening next week. URL: https://www.accupass.com/search?l=taichung. Extract event name, date, time, location, price and description. Filter to events in the upcoming week only (Mon-Sun).' \
  "K2: Scrape Accupass — Taichung Events" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

K3=$($HERMES kanban create --json --assignee default \
  --body 'Scrape Taichung City Government Culture Bureau events calendar at https://activity.culture.taichung.gov.tw/. Extract exhibition, performance, and cultural event listings happening next week. Include event name, date, time, location. Filter to the upcoming week only (Mon-Sun).' \
  "K3: Scrape Taichung Culture Bureau — Cultural Events" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

K4=$($HERMES kanban create --json --assignee default \
  --body 'Search Dcard Taichung board (https://www.dcard.tw/f/taichung) and PTT TaichungBun (https://www.ptt.cc/bbs/TaichungBun/index.html) for recent posts about upcoming events, activities, and things to do in Taichung next week. Look for posts about: concerts, festivals, exhibitions, food events, markets, meetups. Filter to the upcoming week.' \
  "K4: Scrape Dcard & PTT — Forums Events" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

K5=$($HERMES kanban create --json --assignee default \
  --body 'Search Meetup.com (https://www.meetup.com/find/tw--taichung/) and general web search for Taichung events happening next week. Use web searches: "Taichung events this week", "台中週末活動", "Taichung weekend activities", "things to do in Taichung". Collect event name, date, time, location, description. Filter to the upcoming week only.' \
  "K5: Scrape Meetup & Web — General Events" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Create compile task (K6) — depends on all scrapers
K6=$($HERMES kanban create --json --assignee default \
  --parent "$K1" --parent "$K2" --parent "$K3" --parent "$K4" --parent "$K5" \
  --body 'Take the outputs from K1-K5 scraper tasks. Deduplicate events, categorize by day of week (Mon, Tue, Wed, Thu, Fri, Sat, Sun), and compile into a clean weekly digest. Group events by category: Concerts & Music, Arts & Culture, Food & Drink, Outdoor & Nature, Nightlife, Workshops & Classes, Community, Other. Format in Markdown for Telegram delivery. Each event entry: date/time, event name, location, brief description, source URL.' \
  "K6: Compile — Taichung Weekly Events Digest" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo ""
echo "✅ Kanban board created!"
echo "  K1: $K1 — KKTIX"
echo "  K2: $K2 — ACCUPASS"
echo "  K3: $K3 — Culture Bureau"
echo "  K4: $K4 — Dcard & PTT"
echo "  K5: $K5 — Meetup & Web"
echo "  K6: $K6 — Compile (depends on K1-K5)"
echo ""
echo "Run the cron job: $HERMES cron run taichung-weekly-events"
echo "View the board:   $HERMES kanban list"
