# Taichung Weekly Events Digest — Friday Scrape

Today is Friday. Your task is to scrape multiple sources for events, activities, and things to do in **Central & Northern Taiwan** for the **upcoming week** (Mon through Sun next week).

## Geographic Scope
- **Primary**: Taichung city and nearby (Changhua, Nantou, Miaoli)
- **Extended reach** (user willing to travel): **Taipei** (north) and **Tainan / Kaohsiung** (south)
- Include any notable events in these extended locations, especially for categories below

## Sources to scrape

Use delegate_task (parallel subagents, 3 at a time) to scrape these sources:

### Batch 1 — Event Platforms
1. **KKTIX** — Search for Taichung events. Start with web search: `site:kktix.com 台中` and `kktix.com 台中 活動 近期`
2. **ACCUPASS** — Taichung events. Search: `site:accupass.com Taichung` and `accupass.com 台中`
3. **Taichung Culture Bureau** — https://activity.culture.taichung.gov.tw/ — cultural events, exhibitions, performances

### Batch 2 — Forums & Social
4. **Dcard Taichung** — https://www.dcard.tw/f/taichung — look for posts about upcoming events/activities
5. **PTT TaichungBun** — https://www.ptt.cc/bbs/TaichungBun/index.html — look for event-related posts
6. **Meetup.com** — https://www.meetup.com/find/tw--taichung/ — group events

### Batch 3 — General Web
7. Search: "Taichung events this week", "台中週末活動 下週", "things to do in Taichung next week", "Taichung 2026 [current month] events"
8. Check Taichung Tourism website: https://taichung.travel/en/ for event calendar
9. Search for any festival/market/exhibition news in Taichung area

## Compilation

After collecting from all sources:
1. **Deduplicate** — remove same events from multiple sources
2. **Date filter** — ONLY include events happening next week (Mon-Sun)
3. **Categorize by day** — group events under each day of the week
4. **Within each day, categorize as**: 🎵 Concerts & Music | 🎨 Arts & Culture | 🍽️ Food & Drink | 🌿 Outdoor & Nature | 🌙 Nightlife | 📚 Workshops & Classes | 🤝 Community | 🎪 Other
5. **Format nicely in Markdown** for Telegram delivery

## Output format

```
## 🗓️ Taichung Events — Jun [N]–[N] (Next Week)

### Monday, Jun [N]
🎵 **[Event Name]** — Time, Location
  Brief description. [Source](url)

### Tuesday, Jun [N]
...

### Weekend Highlights
...

---

*🤖 Scraped from KKTIX, ACCUPASS, Taichung Culture Bureau, PTT, Dcard, Meetup, and web sources*
```

## Important notes
- Today's date context: It's now June 2026. Calculate next week dates from today's Friday.
- If a source is unreachable, skip it gracefully and report it.
- Prioritize quality over quantity — real events with dates/times > vague mentions.
- Include both Chinese and English event listings.
- "Nearby" includes: Taichung city + 彰化(Changhua), 南投(Nantou), 苗栗(Miaoli)
- "Extended reach" for priority events: Taipei, Tainan, Kaohsiung — flag with 🌏 if outside Taichung
- Deliver the final compiled digest as your response.

## Priority Event Types — Flag These Prominently

When scraping, give extra weight and flag these with ⭐ in the digest:

### 🏅 Sporting Events
- Major league games in Taipei/Taichung (CPBL baseball, P. League+ / T1 basketball)
- International tournaments, marathons, cycling races
- Martial arts events (UFC, boxing, combat sports)
- Big matches at Taipei Dome, Taichung Intercontinental Baseball Stadium
- Search: "Taipei 比賽 2026", "CPBL 賽程", "sports events Taiwan next week"

### 🎬 Western Film Releases
- Hollywood / major western film premieres at Taichung or Taipei cinemas
- Check: Vie Show Cinemas (威秀), Ambassador (國賓), Mirage (夢時代)
- IMAX / 4DX releases
- Search: "新片上映 台中", "movie releases Taichung next week", "IMAX Taipei"

### 🎤 Western Artist Concerts
- Concerts by English-language / international artists in Taipei, Taichung, Kaohsiung
- Check: Taipei Arena (小巨蛋), Kaohsiung Arena, Legacy Taichung, Zepp New Taipei
- Music festivals with international lineups
- Search: "Taipei concert 2026", "western artist Taiwan concert", "演唱會 台北 台中"
