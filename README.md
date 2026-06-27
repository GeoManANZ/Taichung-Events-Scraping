# 🗓️ Taichung Weekly Events Scraper

Automated kanban process that scrapes multiple Chinese/Taiwanese event platforms, forums, sports schedules, cinema listings, and concert calendars every Friday for events happening in **Central & Northern Taiwan** during the **upcoming week**.

### Geographic Scope
- **Primary**: Taichung + nearby (Changhua, Nantou, Miaoli)
- **Extended reach** (user willing to travel): Taipei, Tainan, Kaohsiung

### Priority Event Types
These are flagged with ⭐ in the digest and trigger extended geographic search (🌏 = outside Taichung):
- 🏅 **Sporting events** — CPBL baseball, basketball leagues, international tournaments, Taipei Dome matches
- 🎬 **Western film releases** — Hollywood premieres, IMAX/4DX at major cinemas
- 🎤 **Western artist concerts** — International artists at Taipei Arena, Legacy Taichung, Kaohsiung Arena, etc.

## How It Works

### Schedule
Runs every **Friday at 08:00 UTC** (16:00 Taiwan time) via Hermes cron.

### Sources

| Source | Type | Description |
|---|---|---|
| [KKTIX](https://kktix.com) | Event Platform | Taiwanese ticketing & event platform |
| [ACCUPASS](https://accupass.com) | Event Platform | Popular Taiwanese event hub |
| [Taichung Culture Bureau](https://activity.culture.taichung.gov.tw) | Government | City cultural events calendar |
| [Dcard Taichung](https://www.dcard.tw/f/taichung) | Forum | Popular Taiwanese social platform |
| [PTT TaichungBun](https://www.ptt.cc/bbs/TaichungBun/index.html) | Forum | Taiwan's largest BBS (Taichung board) |
| [Meetup](https://www.meetup.com/find/tw--taichung/) | Social | Community/group events |
| CPBL / Sports Schedules | Sports | Baseball, basketball, tournaments |
| Cinema Listings | Movies | Vie Show, Ambassador, Mirage — IMAX/4DX |
| Taipei Arena / Legacy Taichung | Concerts | Western artist concert schedules |
| General Web Search | Web | Supplementary search results |

### Kanban Workflow

The process is structured as a kanban board with dependency chaining:

```
K1: KKTIX Scrape ─┐
K2: ACCUPASS Scrape ─┤
K3: Culture Bureau ─┤──→ K6: Compile & Digest
K4: Dcard & PTT ────┤
K5: Meetup & Web ───┘
```

- **K1-K5** run in parallel (independent)
- **K6** waits for all five to complete, then compiles, deduplicates, categorizes by day and type, and delivers the digest

### Output Format

Delivered as a Markdown digest grouped by day and category:

```
## 🗓️ Taichung Events — Jul 7–13 (Next Week)

### Monday, Jul 7
🎵 **Event Name** — Time, Location
  Description. [Source](url)

### Saturday, Jul 12
🎨 Exhibition Name — 10:00-18:00, Museum
  ...
```

Categories used: 🎵 Concerts & Music | 🎨 Arts & Culture | 🍽️ Food & Drink | 🌿 Outdoor & Nature | 🌙 Nightlife | 📚 Workshops & Classes | 🤝 Community | 🎪 Other

## Setup

### Prerequisites
- Hermes Agent with kanban enabled
- `fastcrw` MCP server for web scraping
- SSH key registered on GitHub (for pushing updates)

### Files

| File | Purpose |
|---|---|
| `cron-prompt.md` | The cron job prompt definition |
| `kanban-setup.sh` | Script to recreate the kanban board tasks |
| `setup.sh` | Full one-shot setup script |

### Manual Setup

1. Ensure your Hermes config has kanban enabled:
   ```bash
   hermes config show | grep kanban
   ```

2. The cron job is already registered as `taichung-weekly-events` (job_id: `9c53408b8de0`).

3. To trigger manually:
   ```bash
   hermes cron run taichung-weekly-events
   ```

4. To view the kanban board:
   ```bash
   hermes kanban list
   ```

## Development

To modify the scraping sources or output format, edit:
- `cron-prompt.md` — the full scraping prompt
- Update the kanban task bodies accordingly

## License

MIT
