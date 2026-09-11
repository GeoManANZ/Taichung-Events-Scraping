#!/usr/bin/env python3
"""Spike: quality-gated tier escalation — which tier actually yields event signal?"""
import sys, re
sys.path.insert(0, "/opt/data/home/.local/lib/python3.13/site-packages")
sys.path.insert(0, "/workspace/hermes1/projects/taichung-events-scraper")
from bs4 import BeautifulSoup
from taichung_events import (tier_direct, tier_fastcrw, tier_grok_scrape,
                             tier_camoufox, next_week_window)

DATE_RE = re.compile(
    r"(20\d{2}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2})"
    r"|(\d{1,2}\s*[-/.]\s*\d{1,2}\s*[-/.]\s*20\d{2})"
    r"|(\d{1,2}\s*月\s*\d{1,2}\s*日?)"
)


def to_text(raw):
    if "<html" in raw[:2000].lower() or "<div" in raw[:2000].lower():
        soup = BeautifulSoup(raw, "lxml")
        for t in soup(["script", "style", "noscript", "svg"]):
            t.decompose()
        return soup.get_text("\n", strip=True)
    return raw


def score(raw):
    t = to_text(raw or "")
    return len(t), len(DATE_RE.findall(t)), t


TARGETS = [
    ("ACCUPASS", "https://www.accupass.com/search?l=taichung", 8000),
    ("NTT", "https://www.npac-ntt.org/pgcalendar", 0),
    ("Meetup", "https://www.meetup.com/find/tw--taichung/", 0),
    ("Culture Bureau", "https://activity.culture.taichung.gov.tw/", 0),
    ("CPBT tix", "https://tix.ctbcsports.com/BROTHERS/UTK0102_?TYPE=4", 0),
    ("PTT", "https://www.ptt.cc/bbs/TaichungBun/index.html", 0),
    ("Legacy", "https://www.indievox.com/partner/search/Legacy%20Taichung", 0),
]

for name, url, wait in TARGETS:
    print(f"=== {name} ===")
    for tier_name, fn in [
        ("direct", lambda u=url: tier_direct(u)),
        ("fastcrw", lambda u=url, w=wait: tier_fastcrw(u, w)),
        ("grok", lambda u=url: tier_grok_scrape(u)),
    ]:
        try:
            ok, raw, note = fn()
            tlen, dates, _ = score(raw if ok else "")
            verdict = "USABLE" if (tlen > 800 and dates >= 3) else "thin"
            print(f"  {tier_name:8s} ok={str(ok):5s} text={tlen:6d} dates={dates:4d}  {verdict}")
        except Exception as e:
            print(f"  {tier_name:8s} ERR {type(e).__name__}: {str(e)[:50]}")
    print()
