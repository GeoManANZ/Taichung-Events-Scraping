#!/usr/bin/env python3
"""Inspect how dates actually appear in rendered NTT / Meetup markdown."""
import sys, re
sys.path.insert(0, "/opt/data/home/.local/lib/python3.13/site-packages")
sys.path.insert(0, "/workspace/hermes1/projects/taichung-events-scraper")
from taichung_events import tier_fastcrw

for name, url in [("NTT", "https://www.npac-ntt.org/pgcalendar"),
                  ("Meetup", "https://www.meetup.com/find/tw--taichung/")]:
    ok, md, note = tier_fastcrw(url)
    print(f"########## {name} ok={ok} len={len(md)}")
    lines = [l for l in md.split("\n") if l.strip()]
    # print lines mentioning digit-heavy or month-ish content
    hits = [l for l in lines if re.search(r"\d{1,2}[:.]\d{2}|\d{1,2}/\d{1,2}|月|Sep|Oct|Mon|Tue|Wed|Thu|Fri|Sat|Sun", l)]
    for l in hits[:35]:
        print("   ", l[:150])
    print()
