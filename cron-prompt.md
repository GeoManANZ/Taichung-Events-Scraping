# Taichung Weekly Events Digest — Friday Scrape

Today is Friday. Your task is to scrape multiple sources for events, activities, and things to do in **Central & Northern Taiwan** for the **upcoming week** (Mon through Sun next week).

## Geographic Scope
- **Primary**: Taichung city and nearby (Changhua, Nantou, Miaoli)
- **Extended reach** (user willing to travel): **Taipei** (north) and **Tainan / Kaohsiung** (south)
- Include any notable events in these extended locations, especially for priority categories below

## IMPORTANT: How to scrape

**DO NOT use `web_search` or SearXNG — they return empty results.**
Use these tools instead, in this priority order:

1. **fastCRW MCP tools** (`mcp_fastcrw_fastcrw_scrape` / `mcp_fastcrw_fastcrw_crawl` / `mcp_fastcrw_fastcrw_map`) — preferred for most sites
2. **Browser** (`browser_navigate`, `browser_snapshot`, `browser_click`) — for JS-heavy sites
3. **`web_extract`** — for simple markdown extraction from plain URLs

## Sources to scrape

Use `delegate_task` (parallel subagents, 3 at a time). Each subagent gets ONE of these batches:

### Batch 1 — Event Platforms (fastCRW preferred)
1. **ACCUPASS Taichung** — `mcp_fastcrw_fastcrw_scrape` on `https://www.accupass.com/search?l=taichung` and individual event pages. Extract name, date, time, location, price, description.
2. **KKTIX** — Try `mcp_fastcrw_fastcrw_search` or `mcp_fastcrw_fastcrw_scrape` on `https://kktix.com/search?q=台中`. If Cloudflare-blocked, skip and report.
3. **小藝行事曆 (yii.tw)** — `mcp_fastcrw_fastcrw_crawl` on `https://yii.tw/taichung` — great aggregation of music, exhibitions, drama, lectures. Depth 2.

### Batch 2 — Forums & Social (Browser + fastCRW)
4. **PTT TaichungBun** — Browser on `https://www.ptt.cc/bbs/TaichungBun/index.html`. Scroll and look for posts with [活動], [情報], [分享] about upcoming events. Check multiple index pages.
5. **Meetup.com** — `mcp_fastcrw_fastcrw_scrape` on `https://www.meetup.com/find/tw--taichung/`. Community/group events.
6. **Dcard Taichung** — Browser on `https://www.dcard.tw/f/taichung`. If Cloudflare-blocked, skip.

### Batch 3 — Venues, Sports, Movies, Concerts (fastCRW + Browser)
7. **Legacy Taichung / Taipei / TERA** — `mcp_fastcrw_fastcrw_scrape` on `https://www.legacy.com.tw/` for upcoming concert schedules.
8. **Taipei Arena** — Browser on `https://www.arena.taipei/`. Events calendar.
9. **Taichung Tourism** — `mcp_fastcrw_fastcrw_scrape` on `https://taichung.travel/en/` for event calendar.
10. **Taichung Culture Bureau** — Browser on `https://activity.culture.taichung.gov.tw/`. May be slow — set shorter timeout.

### Priority Event Sources — Always check these separately
11. **CPBL / Sports** — `mcp_fastcrw_fastcrw_search` query "CPBL 賽程 2026" or browser on `https://www.cpbl.com.tw/` for game schedule.
12. **Cinemas** — `mcp_fastcrw_fastcrw_scrape` on Vie Show (威秀) Taichung or Taipei for Hollywood release listings.
13. **Concerts** — `mcp_fastcrw_fastcrw_scrape` on `https://www.arena.taipei/` and `https://www.legacy.com.tw/` for international artist schedules.

## Compilation

After collecting from all sources:
1. **Deduplicate** — remove same events from multiple sources
2. **Date filter** — ONLY include events happening next week (Mon-Sun)
3. **Categorize by day** — group events under each day of the week
4. **Within each day, categorize as**: ⭐ Priority Events | 🎵 Concerts & Music | 🎨 Arts & Culture | 🍽️ Food & Drink | 🌿 Outdoor & Nature | 🌙 Nightlife | 📚 Workshops & Classes | 🤝 Community | 🎪 Other
5. **Format nicely in Markdown** for Telegram delivery

## Output format

```
## 🗓️ Taichung Events — [Date Range] (Next Week)

### ⭐ Priority Events
🌏 Taipei — 🎤 [Event Name] — Date, Time, Location
...

### Monday, [Date]
...

---

*🤖 Scraped from ACCUPASS, 小藝行事曆, PTT, Meetup, Legacy, Taipei Arena, and venue sites*
```

## Important notes
- If a source is unreachable (Cloudflare, timeout), skip it gracefully. Don't waste time retrying.
- Prioritize quality over quantity — real events with confirmed dates > vague mentions.
- Include both Chinese and English event listings.
- Flag events outside Taichung (Taipei, Kaohsiung, Tainan) with 🌏
- Deliver the final compiled digest as your response.

## Priority Event Types — Flag These Prominently with ⭐

### 🏅 Sporting Events
- CPBL baseball games, P. League+ / T1 basketball, international tournaments
- Big matches at Taipei Dome, Taichung Intercontinental Baseball Stadium
- Check: `mcp_fastcrw_fastcrw_search` "CPBL" or browser on CPBL site

### 🎬 Western Film Releases
- Hollywood / major western film premieres at Taichung or Taipei cinemas
- Check: Vie Show Cinemas (威秀), Ambassador (國賓)
- IMAX / 4DX releases — usually on Fridays

### 🎤 Western Artist Concerts
- English-language / international artists in Taipei, Taichung, Kaohsiung
- Check: Taipei Arena (小巨蛋), Legacy Taichung, Legacy Taipei, Zepp New Taipei, Kaohsiung Arena
