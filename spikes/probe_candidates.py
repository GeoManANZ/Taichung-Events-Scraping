#!/usr/bin/env python3
"""Probe candidate Taichung event sources we do NOT currently cover.

For each candidate: run the tier ladder, score genuine event signal, and report
how many chars of relevant content we could actually use. Assumption-free —
a URL only qualifies if this probe shows real, extractable date-bearing text.
"""
import importlib.util
import sys

sys.path.insert(0, "/opt/data/home/.local/lib/python3.13/site-packages")
spec = importlib.util.spec_from_file_location(
    "te", "/workspace/hermes1/projects/taichung-events-scraper/taichung_events.py")
te = importlib.util.module_from_spec(spec)
sys.argv = ["x"]
spec.loader.exec_module(te)

CANDIDATES = [
    ("Taichung Culture Bureau ACTIVITY DB", "https://activity.culture.taichung.gov.tw/"),
    ("National Taiwan Museum of Fine Arts", "https://www.ntmofa.gov.tw/"),
    ("Cultural Heritage Bureau platform", "https://event.culture.tw/BOCH"),
    ("Cultural Heritage Park calendar", "https://yii.tw/taichung/calendar?place=tccip"),
    ("Tun District Art Center", "https://www.ttdac.taichung.gov.tw/"),
    ("Taichung City event calendar", "https://www.taichung.gov.tw/8868/8872/12026"),
    ("Taichung MaaS festivals", "https://www.taichung-go.tw/ch/festival/index"),
    ("ERA Ticket", "https://www.ticket.com.tw/"),
    ("UDN ticket", "https://tickets.udnfunlife.com/"),
    ("Artists.tw Taichung gigs", "https://www.artists.tw/gigs/city/taichung/"),
    ("iCulture 文化雲", "https://cloud.culture.tw/"),
    ("TixFun", "https://www.tixfun.com/"),
    ("National Museum of Natural Science", "https://www.nmns.edu.tw/"),
    ("Huludun Cultural Center", "https://www.huludun.taichung.gov.tw/"),
]

print(f"{'candidate':38} {'tier':10} {'status':8} {'signal':>6} {'yield':>7}  note")
print("-" * 108)
for name, url in CANDIDATES:
    try:
        ok, text, note, trail = te.fetch_with_signal(url, wait=6000)
    except Exception as e:
        print(f"{name:38} {'-':10} {'EXC':8} {'-':>6} {'-':>7}  {type(e).__name__}: {e}"[:108])
        continue
    sig = te.signal_score(text or "")
    relev = te.extract_relevant(text or "")
    tier = trail[-1] if isinstance(trail, list) and trail else (str(trail)[-30:] if trail else "?")
    print(f"{name:38} {tier:10} {'OK' if ok else 'no':8} {sig:>6} {len(relev):>7}  {str(note)[:38]}")
