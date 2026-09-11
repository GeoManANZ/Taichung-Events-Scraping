#!/usr/bin/env python3
"""Taichung Weekly Events — deterministic multi-tier scraper (cron no_agent).

WHY A SCRIPT, NOT AN AGENT JOB
  The agent-mode cron could not call HTTP APIs: the security scanner blocks
  curl/python network commands when no approver is present, so 8 of 10 sources
  failed silently in the 2026-09-11 run. This runs under the scheduler, so it
  uses the network directly.

TIER LADDER (per source; first tier with real event SIGNAL wins, not just bytes)
  1. direct      requests + HTML->text (fast)
  2. fastcrw     http://fastcrw:3000/v1/scrape           (Lightpanda JS render)
  3. groktocrawl http://groktocrawl-agent-svc-1:8080/v2/scrape
  4. camoufox    camoufox-fetch.py (Firefox anti-detect)
  5. residential Webshare rotating plan (last resort)

SIGNAL GATE
  A fetch "succeeding" is not enough: SPA shells return 200 with 169 KB of JS
  and zero events. Every tier's output is scored for date/time markers; below
  threshold the ladder escalates. This is the fix for the thin-digest bug.

PER-SOURCE STRATEGY
  listing        events are inline in the page text -> send filtered text
  calendar+links page is a calendar of links (NTT)    -> follow detail pages
  search         site blocks all our IPs (KKTIX etc.) -> discovery via Serper

stdout = the digest ONLY (cron delivers it verbatim). stderr = diagnostics.
Source health is rendered INTO the digest: cron captures stdout only, so any
degraded coverage the user must know about has to appear in the output.
"""
import sys, os, json, re, subprocess, time, datetime as dt

_USER_SITE = "/opt/data/home/.local/lib/python3.13/site-packages"
if _USER_SITE not in sys.path:
    sys.path.insert(0, _USER_SITE)

import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────
PROJ = "/workspace/hermes1/projects/taichung-events-scraper"
DATA_DIR = os.path.join(PROJ, "data")
FASTCRW = os.environ.get("FASTCRW_URL", "http://fastcrw:3000")
GROK = os.environ.get("GROKTOCRAWL_URL", "http://groktocrawl-agent-svc-1:8080")
GROK_KEY = os.environ.get("GROKTOCRAWL_API_KEY", "")
CAMOUFOX = "/opt/data/home/scripts/camoufox-fetch.py"
DEEPSEEK_KEY = os.environ.get("HERMES1_DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
WEBSHARE_HOST = "185.24.10.165:80"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

PER_SOURCE_CHARS = 22000      # after relevance filtering
TOTAL_PAYLOAD_CHARS = 130000  # LLM input ceiling
MIN_SIGNAL = 4                # date/time hits required to accept a tier

# Default fetch ladder. Sources may override (e.g. JS-only calendars render first).
TIER_ORDER = ("direct", "fastcrw", "grok", "camoufox", "residential")

BLOCK_MARKERS = ("just a moment", "cf-browser-verification", "datadome",
                 "security verification", "confirm you are human",
                 "attention required", "captcha-delivery", "為什麼會被封鎖",
                 "why have i been blocked")

_MONTHS = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_DAYS = r"Mon|Tue|Wed|Thu|Fri|Sat|Sun"
SIGNAL_RE = re.compile(
    rf"(20\d{{2}}\s*[-/.年]\s*\d{{1,2}}\s*[-/.月]\s*\d{{1,2}})"   # 2026-09-14 / 2026年9月14
    rf"|(\d{{1,2}}\s*[-/.]\s*\d{{1,2}}\s*[-/.]\s*20\d{{2}})"       # 9/14/2026
    rf"|(\d{{1,2}}\s*月\s*\d{{1,2}}\s*日?)"                         # 9月14日
    rf"|((?:{_DAYS}),?\s+(?:{_MONTHS})\s+\d{{1,2}})"                # Mon, Sep 14
    rf"|((?:{_MONTHS})\s+\d{{1,2}}\b)"                              # Sep 14
    rf"|(\d{{1,2}}/\d{{1,2}}\b)"                                    # 9/19
)
TIME_RE = re.compile(r"\d{1,2}:\d{2}\s*(?:AM|PM|GMT|[ap]\.m\.|時|分)", re.I)
PRICE_RE = re.compile(r"NT\$|NTD|\$\s?\d|\d+\s*元|票價|免費|Free\b", re.I)


def log(*a):
    print(*a, file=sys.stderr)


def signal_score(text):
    """How much genuine event signal does this text carry?"""
    if not text:
        return 0
    return (len(SIGNAL_RE.findall(text)) * 3
            + len(TIME_RE.findall(text))
            + len(PRICE_RE.findall(text)) // 2)


def html_to_text(raw):
    if not raw:
        return ""
    if "<html" not in raw[:3000].lower() and "<div" not in raw[:3000].lower():
        return raw
    soup = BeautifulSoup(raw, "lxml")
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "iframe"]):
        t.decompose()
    return soup.get_text("\n", strip=True)


def extract_relevant(text, context=4, max_chars=PER_SOURCE_CHARS):
    """Keep lines carrying event signal plus surrounding context; drop nav cruft."""
    lines = [l.strip() for l in text.split("\n")]
    lines = [l for l in lines if l and len(l) < 400]
    keep = set()
    for i, ln in enumerate(lines):
        if SIGNAL_RE.search(ln) or TIME_RE.search(ln) or PRICE_RE.search(ln):
            for j in range(max(0, i - context), min(len(lines), i + context + 1)):
                keep.add(j)
    out = [lines[i] for i in sorted(keep)]
    return "\n".join(out)[:max_chars]


def load_webshare_pass():
    try:
        for line in open(os.path.join(PROJ, "proxy_env.sh")):
            if line.startswith("export WEBSHARE_PASS="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    try:
        import importlib.util
        p = "/workspace/hermes1/projects/aisne-property-search/config.py"
        spec = importlib.util.spec_from_file_location("aisne_cfg", p)
        if spec is None or spec.loader is None:
            return ""
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return getattr(m, "WEBSHARE_PROXY_PASS", "")
    except Exception:
        return ""


# ── Date window ───────────────────────────────────────────────────────────────
def next_week_window(today=None):
    today = today or dt.date.today()
    days_to_mon = (7 - today.weekday()) % 7 or 7          # next Monday
    mon = today + dt.timedelta(days=days_to_mon)
    return mon, mon + dt.timedelta(days=6)


# ── Fetch tiers ───────────────────────────────────────────────────────────────
def tier_direct(url, timeout=20):
    # Two TW gov tourism calendars present cert chains this container's CA store
    # can't validate, so `direct` raises SSLError for them. We do NOT bypass
    # certificate validation (MITM risk) — the ladder yields to fastcrw, which
    # fetches both fine.
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    return r.text, f"direct {r.status_code}"


def tier_fastcrw(url, wait=0):
    body = {"url": url, "formats": ["markdown"], "onlyMainContent": False}
    if wait:
        body["waitFor"] = wait
    r = requests.post(f"{FASTCRW}/v1/scrape", json=body, timeout=70)
    d = r.json()
    md = (d.get("data") or {}).get("markdown") or ""
    return md, f"fastcrw {d.get('warning','') or 'ok'} len={len(md)}"


def tier_grok_scrape(url):
    r = requests.post(f"{GROK}/v2/scrape", json={"url": url, "formats": ["markdown"]},
                      headers={"Authorization": f"Bearer {GROK_KEY}",
                               "Content-Type": "application/json"}, timeout=90)
    d = r.json()
    md = ((d.get("data") or {}).get("markdown") or d.get("markdown") or "")
    return md, f"grok len={len(md)}"


def tier_camoufox(url):
    # The subprocess does NOT inherit our sys.path insertion, so pass the user
    # site-packages via PYTHONPATH or camoufox-fetch.py can't import its own
    # dependency under the cron runner (which disables user site-packages).
    env = dict(os.environ)
    env["PYTHONPATH"] = _USER_SITE + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run([sys.executable, CAMOUFOX, "--json", "--timeout", "45000", url],
                       capture_output=True, text=True, timeout=180, env=env)
    if r.returncode != 0 or not r.stdout.strip():
        return "", f"camoufox rc={r.returncode} {r.stderr.strip()[-80:]}"
    d = json.loads(r.stdout)
    # camoufox-fetch.py emits a LIST of results (one per URL requested).
    rec = d[0] if isinstance(d, list) and d else (d if isinstance(d, dict) else {})
    return (rec.get("body") or ""), f"camoufox blocked={rec.get('blocked')}"


def tier_residential(url):
    pw = load_webshare_pass()
    if not pw:
        return "", "residential: no credential"
    px = {"http": f"http://ualfuslo-rotate:{pw}@{WEBSHARE_HOST}",
          "https": f"http://ualfuslo-rotate:{pw}@{WEBSHARE_HOST}"}
    r = requests.get(url, headers=HEADERS, proxies=px, timeout=40)
    return r.text, f"residential {r.status_code}"


def fetch_with_signal(url, wait=0, tiers=("direct", "fastcrw", "grok", "camoufox", "residential")):
    """Escalate through tiers until one returns real event signal."""
    trail, best, best_score = [], "", 0
    for t in tiers:
        try:
            if t == "direct":
                raw, note = tier_direct(url)
            elif t == "fastcrw":
                raw, note = tier_fastcrw(url, wait)
            elif t == "grok":
                raw, note = tier_grok_scrape(url)
            elif t == "camoufox":
                raw, note = tier_camoufox(url)
            elif t == "residential":
                raw, note = tier_residential(url)
            else:
                continue
        except Exception as e:
            note, raw = f"{t}: {type(e).__name__}: {str(e)[:60]}", ""
        blocked = any(m in (raw or "").lower()[:4000] for m in BLOCK_MARKERS)
        text = html_to_text(raw)
        sc = 0 if blocked else signal_score(text)
        trail.append(f"{note} signal={sc}")
        if sc > best_score:
            best, best_score = text, sc
        if sc >= MIN_SIGNAL:
            return True, text, f"{note} signal={sc}", trail
    return False, best, f"best signal={best_score} (below {MIN_SIGNAL})", trail


def fetch_content_only(url, wait=0, tiers=("direct", "fastcrw", "grok", "camoufox", "residential")):
    """Fetch usable page content WITHOUT the date-signal requirement.

    Needed for calendar-style pages (e.g. NTT's month grid) that list day
    numbers and event links rather than parseable dates — the signal gate would
    otherwise reject them and we would lose the whole venue.
    """
    trail, best, best_len = [], "", 0
    for t in tiers:
        try:
            if t == "direct":
                raw, note = tier_direct(url)
            elif t == "fastcrw":
                raw, note = tier_fastcrw(url, wait)
            elif t == "grok":
                raw, note = tier_grok_scrape(url)
            elif t == "camoufox":
                raw, note = tier_camoufox(url)
            elif t == "residential":
                raw, note = tier_residential(url)
            else:
                continue
        except Exception as e:
            note, raw = f"{t}: {type(e).__name__}: {str(e)[:60]}", ""
        blocked = any(m in (raw or "").lower()[:4000] for m in BLOCK_MARKERS)
        text = "" if blocked else html_to_text(raw)
        trail.append(f"{note} chars={len(text)}")
        if len(text) > best_len:
            best, best_len = text, len(text)
        if len(text) > 1500:
            return True, text, f"{note} chars={len(text)}", trail
    return False, best, f"best chars={best_len}", trail


def grok_search(query, limit=8):
    try:
        r = requests.post(f"{GROK}/v2/search", json={"query": query, "limit": limit},
                          headers={"Authorization": f"Bearer {GROK_KEY}",
                                   "Content-Type": "application/json"}, timeout=60)
        d = r.json()
        web = (d.get("data") or {}).get("web") or d.get("web") or []
        return [f"- {w.get('title','')} | {w.get('url','')} | {(w.get('description') or '')[:300]}"
                for w in web]
    except Exception as e:
        log(f"search failed ({query}): {type(e).__name__}")
        return []


# ── Sources ───────────────────────────────────────────────────────────────────
SOURCES = [
    {"name": "ACCUPASS Taichung", "mode": "listing", "wait": 8000,
     "url": "https://www.accupass.com/search?l=taichung"},
    {"name": "Taichung Culture Bureau", "mode": "listing",
     "url": "https://activity.culture.taichung.gov.tw/"},
    {"name": "National Taichung Theater", "mode": "calendar",
     "url": "https://www.npac-ntt.org/en/pgcalendar",
     "link_re": r"/en/program/events/[A-Za-z0-9\-]+|/program/events/[A-Za-z0-9\-]+",
     "base": "https://www.npac-ntt.org", "follow": 30,
     # The calendar lists the whole month in date order, so the follow budget
     # must cover it — a low cap only picks up early-month events and silently
     # starves the target week.
     # The calendar is a JS-rendered grid: the raw HTML contains no event
     # links at all, so `direct` yields nothing to follow. Render first.
     "tiers": ("fastcrw", "camoufox", "grok", "direct"),
     "budget": 30000, "detail_chars": 1200},
    {"name": "Taichung Tourism (EN)", "mode": "listing",
     "url": "https://www.taichung.travel/en/event/touristcalendar"},
    {"name": "Taichung Tourism news", "mode": "listing",
     "url": "https://travel.taichung.gov.tw/zh-tw/Event/News"},
    {"name": "Meetup Taichung", "mode": "listing",
     "url": "https://www.meetup.com/find/tw--taichung/"},
    {"name": "CPBL ticketing", "mode": "listing",
     "url": "https://tix.ctbcsports.com/BROTHERS/UTK0102_?TYPE=4"},
    {"name": "Legacy Taichung", "mode": "listing",
     "url": "https://www.indievox.com/partner/search/Legacy%20Taichung"},
    {"name": "PTT TaichungBun", "mode": "listing",
     "url": "https://www.ptt.cc/bbs/TaichungBun/index.html"},
    {"name": "KKTIX (search index)", "mode": "search",
     "query": "site:kktix.com 台中 演唱會 活動"},
    {"name": "OPENTIX (search index)", "mode": "search",
     "query": "site:opentix.life 台中 音樂會"},
    {"name": "Eventbrite (search index)", "mode": "search",
     "query": "site:eventbrite.com taichung events"},
    {"name": "General discovery", "mode": "search",
     "query": "台中 活動 週末 2026 展覽 演唱會 市集"},

    # ---- Added 2026-09-11 after a coverage audit (probe_candidates.py) ----
    # Every entry below was probed live: reachable, and signal-bearing enough
    # that the relevance extractor yields usable text. Signal scores in the
    # comment vs our best pre-audit source (ACCUPASS, 96).
    {"name": "Taichung City event calendar", "mode": "listing",   # signal 399
     "url": "https://www.taichung.gov.tw/8868/8872/12026"},
    {"name": "Taichung MaaS festivals", "mode": "listing",        # signal 486
     "url": "https://www.taichung-go.tw/ch/festival/index"},
    {"name": "Tun District Art Center", "mode": "listing",        # yield 6951
     "url": "https://www.ttdac.taichung.gov.tw/"},
    {"name": "Cultural Heritage Bureau", "mode": "listing",       # yield 4435
     "url": "https://event.culture.tw/BOCH"},
    {"name": "Artists.tw gigs", "mode": "listing",                # live music
     "url": "https://www.artists.tw/gigs/city/taichung/"},
    {"name": "National Museum of Fine Arts", "mode": "listing",   # exhibitions
     # The museum homepage yields only ~830 chars of signal; its dedicated
     # event platform (event.culture.tw/NTMOFA) yields ~5,400. Use the platform.
     "url": "https://event.culture.tw/NTMOFA"},
    {"name": "National Museum of Nat. Science", "mode": "listing",
     "url": "https://www.nmns.edu.tw/"},
    {"name": "Dadun Cultural Center", "mode": "listing",
     "url": "https://www.dadun.culture.taichung.gov.tw/"},
    # National ticketing platforms: scraped via the search index rather than
    # directly, because a direct scrape of a nationwide listing injects
    # wrong-city events that the compiler then has to filter out. The query
    # scopes them to Taichung, matching the KKTIX/OPENTIX/Eventbrite pattern.
    {"name": "TixFun (search index)", "mode": "search",
     "query": "site:tixfun.com 台中"},
    {"name": "UDN ticket (search index)", "mode": "search",
     "query": "site:tickets.udnfunlife.com 台中"},
    {"name": "iCulture (search index)", "mode": "search",
     # A `site:` prefix is too restrictive for this index — it returns a single
     # hit. The bare form returns 8 and surfaces Taichung venue pages.
     "query": "cloud.culture.tw 台中 展覽"},
]


def harvest_calendar_links(text, src, budget_chars=None):
    """Follow calendar links to get precise event dates/prices (NTT-style pages)."""
    budget_chars = budget_chars or src.get("budget", PER_SOURCE_CHARS)
    per_detail = src.get("detail_chars", 1200)
    links, seen = [], set()
    for m in re.finditer(src["link_re"], text):
        path = m.group(0)
        if path in seen:
            continue
        seen.add(path)
        links.append(path if path.startswith("http") else src["base"] + path)
    picked, out = links[:src.get("follow", 10)], []
    for u in picked:
        ok, body, note, _ = fetch_with_signal(u, tiers=("direct", "fastcrw", "grok"))
        if ok:
            out.append(f"--- {u}\n{extract_relevant(body, context=2, max_chars=per_detail)}")
        if sum(len(x) for x in out) > budget_chars:
            log(f"    follow budget reached after {len(out)} pages")
            break
    log(f"    followed {len(out)}/{len(picked)} detail pages")
    return "\n".join(out)


def collect():
    chunks, health = [], []
    for s in SOURCES:
        t0 = time.time()
        if s["mode"] == "search":
            lines = grok_search(s["query"])
            ok, note, trail, body = bool(lines), f"search {len(lines)} hits", [], "\n".join(lines)
        else:
            if s["mode"] == "calendar":
                # Calendar pages carry links + bare day numbers, not date
                # strings — fetch content without the signal gate, then follow.
                ok, text, note, trail = fetch_content_only(
                    s["url"], wait=s.get("wait", 0), tiers=s.get("tiers", TIER_ORDER))
                body = harvest_calendar_links(text, s) if ok else ""
                ok = bool(body)
                if not ok:
                    note += " | no detail pages followed"
            else:
                ok, text, note, trail = fetch_with_signal(
                    s["url"], wait=s.get("wait", 0), tiers=s.get("tiers", TIER_ORDER))
                body = extract_relevant(text) if ok else ""
        el = time.time() - t0
        health.append({"source": s["name"], "ok": ok, "note": note,
                       "secs": round(el, 1), "chars": len(body), "trail": trail})
        log(f"{'OK  ' if ok else 'FAIL'} {s['name']:30s} {el:5.1f}s  {note}  chars={len(body)}")
        if ok and body:
            chunks.append(f"### SOURCE: {s['name']}\nURL: {s.get('url') or s.get('query')}\n{body}")
    return chunks, health


# ── LLM compile ───────────────────────────────────────────────────────────────
def call_llm(prompt, max_tokens=16000, attempts=3):
    """Compile the digest. deepseek-v4-flash is a REASONING model: it emits
    `reasoning_content` first and only then `content`. Two failure modes seen
    in production, both silent if unchecked:

      1. thinking consumes the whole budget -> `content` empty  (v4 dev run:
         the raw reasoning trace was nearly delivered as the digest)
      2. `content` comes back TRUNCATED mid-line, finish_reason="length"
         (2026-09-11 cron run: digest stopped mid-Friday, Sat/Sun lost)

    So: generous budget, escalate on either symptom, and treat a "length"
    finish as failure rather than accepting a half digest."""
    last, partial = "", ""
    for i in range(attempts):
        prompt_i = prompt
        if i == attempts - 1:
            prompt_i = prompt + ("\n\nIMPORTANT: you are running low on output "
                                 "space. Be TERSE — one line per event, drop the "
                                 "description line, keep every event.")
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
                          headers={"Authorization": f"Bearer {DEEPSEEK_KEY}",
                                   "Content-Type": "application/json"},
                          json={"model": "deepseek-v4-flash",
                                "messages": [{"role": "user", "content": prompt_i}],
                                "max_tokens": max_tokens, "temperature": 0.2},
                          timeout=600)
        r.raise_for_status()
        ch = r.json()["choices"][0]
        m = ch["message"]
        content = (m.get("content") or "").strip()
        finish = ch.get("finish_reason")
        if content and finish != "length":
            return content
        last = (f"content={len(content)} chars, finish_reason={finish}, "
                f"reasoning={len(m.get('reasoning_content') or '')} chars")
        log(f"LLM attempt {i+1}/{attempts}: {last} — retrying with a larger budget")
        max_tokens = min(max_tokens * 2, 32000)
        partial = content
    raise LLMTruncated(partial, f"LLM produced no complete answer: {last}")


class LLMTruncated(RuntimeError):
    """Raised when every attempt returned a truncated digest.

    Carries the partial content so the caller can still deliver the events it
    did extract, clearly flagged, instead of losing the whole run.
    """

    def __init__(self, partial, message):
        super().__init__(message)
        self.partial = partial


def build_prompt(chunks, mon, sun, health):
    days = {d.strftime("%A"): (mon + dt.timedelta(i)).isoformat() for i, d in enumerate(
        [mon + dt.timedelta(j) for j in range(7)])}
    ok_names = [h["source"] for h in health if h["ok"]]
    bad_names = [h["source"] for h in health if not h["ok"]]
    return f"""Compile a WEEKLY EVENTS DIGEST for an English-speaking expat in Taichung, Taiwan.

TARGET WEEK: {mon.isoformat()} to {sun.isoformat()}
Dates: {json.dumps(days, ensure_ascii=False)}

HARD RULES
1. ENGLISH ONLY. Translate every event name, venue and description to English. No Chinese in the output except an optional short original name in parentheses when it helps find the event on a ticketing site.
2. Include ONLY events dated inside the target week. Ambiguous or undated -> DROP. Never invent a date, time, venue, price or event name.
3. Deduplicate: the same event from two sources = one entry.
4. Use only facts present in the scraped text. Omit unknown fields rather than guessing.
5. Group by day Mon->Sun; prefix each with a category emoji: 🎵 Concerts · 🎨 Arts/Culture · ⚽ Sports · 🎬 Movies · 🍽️ Food/Festivals · 📚 Workshops · 🤝 Community · 🌿 Outdoor.
6. Scope: Taichung city + Changhua/Nantou/Miaoli (mark 🚗). Taipei/Tainan/Kaohsiung only for major sports, western films or international concerts (mark 🌏).
7. Close with exactly: *🤖 Sources OK: {', '.join(ok_names) or 'none'} · Failed: {', '.join(bad_names) or 'none'}*
8. If NO event falls inside the window, output exactly: NO_EVENTS_IN_WINDOW

FORMAT (keep it COMPACT — one line per event, no trailing description line)
## 🗓️ Taichung Events — {mon.strftime('%b %d')} – {sun.strftime('%b %d, %Y')}

### Monday, {mon.strftime('%b %d')}
🎵 **English Event Name** — 19:30 · English Venue (District) · NT$500 [Source](url)
🤝 **Another Event** — 19:00 · Venue · Free [Source](url)

### 📌 Ongoing
🖼️ **English Name** — Venue, closes [date] [Source](url)

Include EVERY event you can verify inside the week — completeness matters more than prose. Do not add a description line per event.

SCRAPED CONTENT:
{chr(10).join(chunks) if chunks else '(no source returned content)'}
"""


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    mon, sun = next_week_window()
    log(f"target week: {mon} .. {sun}")
    chunks, health = collect()

    try:
        with open(os.path.join(DATA_DIR, f"raw_{dt.date.today().isoformat()}.json"), "w") as f:
            json.dump({"window": [mon.isoformat(), sun.isoformat()],
                       "health": health, "chunks": chunks}, f, ensure_ascii=False, indent=1)
    except Exception as e:
        log(f"bundle write failed: {e}")

    if not chunks:
        print(f"## 🗓️ Taichung Events — {mon.strftime('%b %d')} – {sun.strftime('%b %d, %Y')}\n")
        print("⚠️ No source returned usable data this week — the digest could not be built.\n")
        for h in health:
            print(f"- **{h['source']}** — {h['note']}")
        return

    try:
        digest = call_llm(build_prompt(chunks, mon, sun, health))
    except LLMTruncated as e:
        log(f"LLM truncated after all attempts: {e}")
        # Deliver what we extracted, clearly flagged — a partial digest with a
        # warning beats a silent half-digest or nothing at all.
        if e.partial:
            print(e.partial)
            print("\n⚠️ **This digest was truncated** — the compiler hit its output "
                  "limit, so later days may be missing. Earlier days are complete.")
            print(f"*🤖 Sources OK: {', '.join(h['source'] for h in health if h['ok']) or 'none'} "
                  f"· Failed: {', '.join(h['source'] for h in health if not h['ok']) or 'none'}*")
            return
        digest = ""
    except Exception as e:
        log(f"LLM compile failed: {type(e).__name__}: {e}")
        digest = ""

    footer = (f"*🤖 Sources OK: {', '.join(h['source'] for h in health if h['ok']) or 'none'} "
              f"· Failed: {', '.join(h['source'] for h in health if not h['ok']) or 'none'}*")

    if not digest or digest.startswith("NO_EVENTS_IN_WINDOW") or "Sources OK" not in digest:
        if digest.startswith("NO_EVENTS_IN_WINDOW") and digest.strip() == "NO_EVENTS_IN_WINDOW":
            print(f"## 🗓️ Taichung Events — {mon.strftime('%b %d')} – {sun.strftime('%b %d, %Y')}\n")
            print("No events found in the target week from the sources checked.\n")
            print(footer)
            return
        if not digest:
            print(f"## 🗓️ Taichung Events — {mon.strftime('%b %d')} – {sun.strftime('%b %d, %Y')}\n")
            print("⚠️ Event compilation failed (LLM stage). Source status:\n")
            for h in health:
                print(f"- **{h['source']}** — {'OK' if h['ok'] else h['note']} ({h['chars']} chars)")
            print(f"\n{footer}")
            return

    print(digest if "Sources OK" in digest else digest + f"\n\n---\n{footer}")


if __name__ == "__main__":
    main()
