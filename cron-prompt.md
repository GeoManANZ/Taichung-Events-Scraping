# Taichung Weekly Events Digest — Friday Scrape

Today is Friday. Your task is to scrape multiple sources for events, activities, and things to do in **Taichung and nearby** (Changhua, Nantou, Miaoli) for the **upcoming week** (Mon through Sun next week).

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
- Deliver the final compiled digest as your response.
