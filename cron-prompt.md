# Taichung Weekly Events Digest — v3 (verified sources + escalation ladder)

Today is **Friday**. Your task: find events in **Taichung + Central Taiwan** for **next week (Mon–Sun)** and deliver a Telegram digest as your final response.

## Step 0 — Compute the target week FIRST
```bash
date +%Y-%m-%d            # today
date -d "next monday" +%Y-%m-%d
date -d "next sunday" +%Y-%m-%d
```
Next week = the Mon–Sun following this Friday. Every event you report MUST fall inside those 7 days. If an event has no verifiable date, drop it.

## Tool ladder (use exactly these tools, in this order)
1. `mcp__groktocrawl__groktocrawl_search` — **primary discovery** (Serper-backed, reliable)
2. `mcp__fastcrw__fastcrw_scrape` — page content (Lightpanda JS render; add `"waitFor": 8000` for SPA sites like ACCUPASS)
3. `mcp__groktocrawl__groktocrawl_scrape` — fallback renderer when fastCRW fails
4. `web_extract` — plain static pages only
5. **Escalation (see below)** — rotating proxy / 2Captcha, only when justified

⚠️ Do NOT use `mcp__fastcrw__fastcrw_search` — its SearXNG backend returns empty results (broken since at least 2026-08-21).
⚠️ Do NOT use `delegate_task` — subagent spawning broke delivery (broken-pipe failures).

## Escalation rules (proxy / CAPTCHA)
Default is NO proxy — most sources work directly. Escalate only per-source:

1. A fetch fails with 403 / bot-block / empty-render → retry ONCE through the **Webshare rotating residential proxy**:
   ```bash
   # Credentials in ./proxy_env.sh (user-paid plan — do not commit elsewhere)
   source "$(dirname "$0")/proxy_env.sh" 2>/dev/null || true
   # For fastCRW JSON: add "proxy": "http://ualfuslo-rotate:$WEBSHARE_PASS@185.24.10.165:80"
   # For curl: curl -x "http://ualfuslo-rotate:$WEBSHARE_PASS@185.24.10.165:80"
   ```
   Each request exits from a different residential IP. One retry per source, then move on.
2. Only if a HIGH-VALUE source (CPBL schedule, ticketing) presents an interactive CAPTCHA *and* no search-index alternative exists → use 2Captcha (`twocaptcha_client.py` pattern from the aisne project). **Hard cap: 3 solves per run.** Check balance first; abort below $0.50.
3. Never burn more than 2 attempts on any single source. Breadth beats depth.

## Sources — Tier 0 (always scrape directly, verified working 2026-08-22)

| # | Source | How |
|---|---|---|
| 1 | **ACCUPASS Taichung** | `fastcrw_scrape` `https://www.accupass.com/search?l=taichung` **with `"waitFor":8000`** — renders full event cards w/ dates + links |
| 2 | **Taichung Culture Bureau** | `fastcrw_scrape` `https://activity.culture.taichung.gov.tw/` |
| 3 | **NTT 國家歌劇院** | `groktocrawl_search` `"site:npac-ntt.org 2026年9月"` then scrape top program pages |
| 4 | **OPENTIX 兩廳院** | `groktocrawl_search` `"site:opentix.life 台中 9月"` (search-index route — direct search page renders empty) |
| 5 | **Meetup Taichung** | `fastcrw_scrape` `https://www.meetup.com/find/tw--taichung/` |
| 6 | **CPBL baseball** | `fastcrw_scrape` `https://tix.ctbcsports.com/BROTHERS/UTK0102_?TYPE=4` (Brothers home games @洲際 with dates) |
| 7 | **Legacy Taichung concerts** | `fastcrw_scrape` `https://www.indievox.com/partner/search/Legacy%20Taichung` |
| 8 | **PTT TaichungBun** | `groktocrawl_scrape` `https://www.ptt.cc/bbs/TaichungBun/index.html` (look for [活動]/[情報] posts) |

## Sources — Tier 1 (search-index route; direct scraping is bot-blocked)

These sites block all our IPs/renderers. Get their content THROUGH the search engine instead:

| Site | Query pattern |
|---|---|
| **KKTIX** | `groktocrawl_search`: `site:kktix.com 台中` (+ month name, e.g. `9月`) — indexed pages carry title/date/venue in the description |
| **Eventbrite** | `groktocrawl_search`: `site:eventbrite.com taichung` |
| **Dcard 台中版** | `groktocrawl_search`: `site:dcard.tw f/taichung 活動` |
| **Vie Show 威秀電影** | `groktocrawl_search`: `威秀影城 台中 上映 電影 9月` |

For each hit, open the individual event page (usually scrapes fine even when the listing page is blocked).

## Sources — Tier 2 (tourism / city calendars)

| Source | URL | Note |
|---|---|---|
| 臺中觀光旅遊網 (EN) | `https://www.taichung.travel/en/event/touristcalendar` | ⚠️ old `/en/event/` URL is a 404 — use this exact path |
| 臺中觀光旅遊網活動消息 | `https://travel.taichung.gov.tw/zh-tw/Event/News` | Chinese, current festivals/fairs |

## Search radius (increased in v3)

| Tier | Area | Flag |
|---|---|---|
| Core | 台中市 (all districts incl. 沙鹿/豐原/大甲) | — |
| Nearby | 彰化縣市, 南投縣 (日月潭/草屯/埔里), 苗栗縣 | 🚗 |
| Extended — priority events only | 台北/新北, 台南, 高雄 | 🌏 |

Priority categories earn the extended radius (🌏): ⚽ sporting events (CPBL anywhere, basketball, marathons), 🎬 western film releases/premieres, 🎤 western/international artist concerts, 🎪 large festivals. Everything else stays within Tier "core+nearby".

## Compilation rules
- **Language: ENGLISH ONLY.** The user cannot read Chinese. Every event line must be in English:
  - Event name → translate to English (keep the original Chinese in parentheses only where it helps identify the event on a ticketing page, e.g. `Aomori Nebuta Festival (青森ねぶた祭)`).
  - Venue → English name + district (e.g. `Intercontinental Stadium (北屯區)`), NOT raw Chinese.
  - Time/date/price → numbers, no translation needed.
  - Search queries can stay in Chinese (that's how you find the events) — only the DIGEST OUTPUT is English.
- Deduplicate across sources (same title + same date = one entry; prefer the link with the richest detail).
- Group by day (Mon→Sun), then category within each day: 🎵 Concerts · 🎨 Arts/Culture · ⚽ Sports · 🎬 Movies · 🍽️ Food/Festivals · 📚 Workshops · 🤝 Community/Meetups · 🌿 Outdoor.
- Every event line carries: English name, time, English venue (+district), price if known, and a markdown source link.
- **Never fabricate**: if a source gave you a title but no date, either verify the date by opening the linked page or drop the event. Zero invented details.
- Ongoing exhibitions section at the bottom (open ≥ the whole target week).
- End with a one-line provenance footer listing which sources actually returned data and which failed/skipped (transparency over silence).

## Budget & failure handling
- Cap total tool calls at ~35. If you're running out, stop collecting and compile with what you have.
- A source failing = note it in the footer and continue. Never stall on retries.
- If literally everything failed → reply `[SILENT]`.

## Output format
```
## 🗓️ Taichung Events — [Mon date] – [Sun date]

### Monday, [date]
🎵 **[Event]** — time · venue · price
  one-line description [Source](url)

...

### 📌 Ongoing Exhibitions
🖼️ **[Exhibition]** — venue, closed [date], hours

---
*🤖 Sources: [list OK ones] · Skipped: [list failed ones]*
```
