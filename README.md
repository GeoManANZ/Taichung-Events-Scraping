# Taichung Weekly Events Scraper

Automated Friday cron that scrapes Taiwanese event platforms, forums, sports schedules, and venue calendars for the **upcoming week (Mon–Sun)** in **Central Taiwan**, delivered as a Telegram digest.

## Output Language

**English only.** The user cannot read Chinese. All event names, venues, and descriptions in the delivered digest are translated to English; original Chinese is kept in parentheses only where it helps identify the event on a ticketing page (e.g. `Aomori Nebuta Festival (青森ねぶた祭)`). Venues are rendered as English name + district. Search queries themselves stay in Chinese — only the output is translated.

## Geographic Scope (v3)

| Tier | Area | Flag |
|---|---|---|
| Core | 台中市 all districts (incl. 沙鹿/豐原/大甲) | — |
| Nearby | 彰化縣市 · 南投縣 · 苗栗縣 | 🚗 |
| Extended — priority events only | 台北/新北 · 台南 · 高雄 | 🌏 |

Priority categories earn 🌏 extended radius: sporting events (CPBL anywhere), western film releases, international artist concerts, large festivals.

## Source Matrix (all verified live 2026-08-22)

### Tier 0 — direct scrape works
| Source | Route | Note |
|---|---|---|
| ACCUPASS 台中 | fastCRW + `waitFor:8000` | SPA — without wait you get a loading GIF only |
| Culture Bureau 文化局 | fastCRW | plain server-rendered |
| Meetup | fastCRW | |
| CPBL 洲際 games | fastCRW `tix.ctbcsports.com/BROTHERS/UTK0102_?TYPE=4` | cpbl.com.tw itself is bot-blocked; ticketing page carries full schedule w/ dates |
| Legacy Taichung | fastCRW `indievox.com/partner/search/Legacy%20Taichung` | legacy.com.tw has no /taichung path (404) |
| PTT TaichungBun | groktocrawl_scrape | needs over18 handling — groktocrawl does it internally |
| NTT 歌劇院 / OPENTIX | via `groktocrawl_search` site: queries | direct listing pages render empty/blocked |

### Tier 1 — search-index route ONLY (bot-blocked direct)
KKTIX · Eventbrite · Dcard · Vie Show 威秀 — all return 403/CAPTCHA to every renderer and IP we own (datacenter, WARP, rotating residential). Get their event pages through `groktocrawl_search` (`site:` queries), then open individual event URLs which usually scrape fine.

### Tier 2 — tourism calendars
- `taichung.travel/en/event/touristcalendar` ⚠️ old `/en/event/` is a **404**
- `travel.taichung.gov.tw/zh-tw/Event/News`

## Escalation Ladder

```
direct fetch → fail → ONE retry via Webshare rotating residential
            → still blocked → route through groktocrawl_search index
            → interactive CAPTCHA on high-value source only → 2Captcha
              (hard cap 3 solves/run, balance floor $0.50)
```

Credentials for the proxy live in `proxy_env.sh` (**gitignored**). The 2Captcha key lives in `/workspace/hermes1/projects/aisne-property-search/.env`.

## Known-Broken (do not use)

| Tool/URL | Status |
|---|---|
| `mcp__fastcrw__fastcrw_search` | SearXNG backend returns empty results since ≥2026-08-21. Use `groktocrawl_search`. |
| `delegate_task` in cron | broke delivery with broken-pipe errors historically. Scrape inline. |
| `kktix.com` direct | Cloudflare "Just a moment" loop on every renderer + every IP tier. |
| `dcard.tw` direct | IP-reputation block (403) even on residential. |
| `cpbl.com.tw/schedule` | near-empty anti-bot response. |
| `legacy.com.tw/taichung` | 404 — site has no such path. |
| `eventbrite.com` direct | puzzle CAPTCHA wall. |

## Schedule & Delivery

- Cron job `taichung-weekly-events` (job_id `afb010899802`) — **Fridays 08:00 UTC (16:00 TW)**, delivers to origin chat.
- The stored cron prompt is authoritative; this repo's `cron-prompt.md` mirrors it. After editing the file here, ALSO update the job (`cronjob update`) — file edits do NOT propagate automatically (this bit us once).

## Files

| File | Purpose |
|---|---|
| `cron-prompt.md` | Full v3 scraping prompt (mirror of the stored cron prompt) |
| `proxy_env.sh` | Webshare rotating-plan credentials (gitignored) |
| `searxng-engines.yml` | SearXNG engine overrides (legacy, kept for reference) |
| `setup.sh` / `kanban-setup.sh` | Original kanban-era setup (superseded by single-agent inline flow) |

## History

- **v1** — 10-source kanban board (K1–K6), delegate_task subagents → broken pipe failures
- **v2** — reduced to 6 reliable sources, inline scraping
- **v2.5** (Jul 2) — PTT + Culture Bureau re-added after WARP testing
- **v3** (Aug 22) — full source verification pass; groktocrawl_search promoted; Tier 0/1/2 matrix; escalation ladder (rotating residential + capped 2Captcha); radius widened to 彰化/南投/苗栗 core+nearby
