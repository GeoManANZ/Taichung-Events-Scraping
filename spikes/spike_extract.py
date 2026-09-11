#!/usr/bin/env python3
"""Spike: test date-window relevance extraction before wiring into the scraper."""
import sys, re
sys.path.insert(0, "/opt/data/home/.local/lib/python3.13/site-packages")
sys.path.insert(0, "/workspace/hermes1/projects/taichung-events-scraper")
from bs4 import BeautifulSoup
from taichung_events import tier_direct, tier_fastcrw, next_week_window

MON, SUN = next_week_window()
print(f"window: {MON} .. {SUN}\n")

DATE_RE = re.compile(
    r"(20\d{2}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2})"      # 2026-09-14 / 2026.9.14 / 2026年9月14
    r"|(\d{1,2}\s*[-/.]\s*\d{1,2}\s*[-/.]\s*20\d{2})"          # 9/14/2026
    r"|(\d{1,2}\s*月\s*\d{1,2}\s*日)"                            # 9月14日
    r"|(\d{4}\s*-\s*\d{2}\s*-\s*\d{2})"
)


def html_to_text(html):
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        t.decompose()
    return soup.get_text("\n", strip=True)


def extract_relevant(text, context=3, max_chars=45000):
    lines = [l.strip() for l in text.split("\n")]
    lines = [l for l in lines if l]
    keep = set()
    for i, ln in enumerate(lines):
        if DATE_RE.search(ln) and len(ln) > 4:
            for j in range(max(0, i - context), min(len(lines), i + context + 1)):
                keep.add(j)
    out = [lines[i] for i in sorted(keep)]
    joined = "\n".join(out)
    return joined[:max_chars], len(keep), len(lines)


for name, url, wait in [
    ("ACCUPASS", "https://www.accupass.com/search?l=taichung", 8000),
    ("NTT", "https://www.npac-ntt.org/pgcalendar", 0),
    ("Meetup", "https://www.meetup.com/find/tw--taichung/", 0),
    ("Culture Bureau", "https://activity.culture.taichung.gov.tw/", 0),
    ("CPBL", "https://tix.ctbcsports.com/BROTHERS/UTK0102_?TYPE=4", 0),
]:
    ok, raw, note = tier_direct(url)
    txt = html_to_text(raw) if ok else ""
    rel, kept, total = extract_relevant(txt)
    print(f"--- {name}: raw={len(raw)} text={len(txt)} lines={total} kept={kept} -> {len(rel)} chars")
    print("    sample:", " | ".join(rel.split("\n")[:4])[:260].replace("\n", " "))
    print()
