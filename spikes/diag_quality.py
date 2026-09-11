#!/usr/bin/env python3
"""Diagnose: why did 'direct 200' sources yield no events?"""
import sys, re, json
sys.path.insert(0, "/opt/data/home/.local/lib/python3.13/site-packages")
sys.path.insert(0, "/workspace/hermes1/projects/taichung-events-scraper")
import requests
from taichung_events import tier_direct, tier_fastcrw, HEADERS

def stats(label, txt):
    if not txt:
        print(f"{label}: EMPTY"); return
    dates = len(re.findall(r"20\d\d[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}月\d{1,2}日", txt))
    months = len(re.findall(r"\d{1,2}/\d{1,2}|\d{1,2}月", txt))
    print(f"{label}: len={len(txt):7d}  date-ish={dates:4d}  month-ish={months:4d}")

targets = [
    ("ACCUPASS", "https://www.accupass.com/search?l=taichung", 8000),
    ("NTT zh", "https://www.npac-ntt.org/pgcalendar", 0),
    ("NTT en", "https://www.npac-ntt.org/en/pgcalendar", 0),
    ("Culture Bureau", "https://activity.culture.taichung.gov.tw/", 0),
    ("PTT", "https://www.ptt.cc/bbs/TaichungBun/index.html", 0),
    ("Legacy/indievox", "https://www.indievox.com/partner/search/Legacy%20Taichung", 0),
    ("CPBL tix", "https://tix.ctbcsports.com/BROTHERS/UTK0102_?TYPE=4", 0),
    ("Meetup", "https://www.meetup.com/find/tw--taichung/", 0),
]

print("=== DIRECT ===")
for name, url, _ in targets:
    try:
        ok, txt, note = tier_direct(url)
        stats(f"{name:18s} {'OK ' if ok else 'no '}", txt)
    except Exception as e:
        print(f"{name:18s} ERR {type(e).__name__}")

print("\n=== FASTCRW (with wait where given) ===")
for name, url, wait in targets:
    try:
        ok, txt, note = tier_fastcrw(url, wait)
        stats(f"{name:18s} {'OK ' if ok else 'no '}", txt)
    except Exception as e:
        print(f"{name:18s} ERR {type(e).__name__}: {str(e)[:60]}")
