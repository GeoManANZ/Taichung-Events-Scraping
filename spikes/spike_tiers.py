#!/usr/bin/env python3
"""Spike: validate every fetch tier from a plain-script (cron no_agent) context."""
import sys, json, time
sys.path.insert(0, "/opt/data/home/.local/lib/python3.13/site-packages")
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"}

def timed(label, fn):
    t0 = time.time()
    try:
        ok, info = fn()
    except Exception as e:
        ok, info = False, f"{type(e).__name__}: {e}"
    print(f"{'PASS' if ok else 'FAIL'}  {label:38s} {time.time()-t0:5.1f}s  {info[:110]}")
    return ok

def fastcrw(url, wait=None):
    body = {"url": url, "formats": ["markdown"]}
    if wait:
        body["waitFor"] = wait
    r = requests.post("http://fastcrw:3000/v1/scrape", json=body, timeout=45)
    d = r.json()
    md = (d.get("data") or {}).get("markdown") or ""
    blocked = "warning" in d or len(md) < 300
    return (not blocked), f"len={len(md)} warn={str(d.get('warning'))[:40]}"

def grok_scrape(url):
    r = requests.post("http://groktocrawl:8080/api/scrape", json={"url": url}, timeout=60)
    d = r.json()
    md = d.get("markdown") or ""
    return len(md) > 300, f"len={len(md)}"

def grok_search(q):
    r = requests.post("http://groktocrawl:8080/api/search", json={"query": q, "limit": 5}, timeout=45)
    d = r.json()
    res = d.get("web") or []
    return len(res) > 0, f"{len(res)} results"

def direct(url):
    r = requests.get(url, headers=H, timeout=20)
    return r.status_code == 200 and len(r.text) > 500, f"HTTP {r.status_code} len={len(r.text)}"

print("=== TIER VALIDATION (plain script context) ===\n")
print("-- direct HTTP --")
timed("opentix.life", lambda: direct("https://www.opentix.life/"))
timed("taichung.travel", lambda: direct("https://www.taichung.travel/en/event/touristcalendar"))
timed("travel.taichung.gov.tw", lambda: direct("https://travel.taichung.gov.tw/zh-tw/Event/News"))

print("\n-- groktocrawl search API --")
timed("search: taichung events", lambda: grok_search("Taichung events 台中活動"))

print("\n-- fastcrw scrape API --")
timed("culture bureau", lambda: fastcrw("https://activity.culture.taichung.gov.tw/"))
timed("accupass taichung (+8s wait)", lambda: fastcrw("https://www.accupass.com/search?l=taichung", 8000))
timed("meetup taichung", lambda: fastcrw("https://www.meetup.com/find/tw--taichung/"))
timed("NTT calendar", lambda: fastcrw("https://www.npac-ntt.org/pgcalendar"))
timed("ctbcsports ticketing", lambda: fastcrw("https://tix.ctbcsports.com/BROTHERS/UTK0102_?TYPE=4"))

print("\n-- groktocrawl scrape --")
timed("PTT TaichungBun", lambda: grok_scrape("https://www.ptt.cc/bbs/TaichungBun/index.html"))
timed("npac-ntt.org", lambda: grok_scrape("https://www.npac-ntt.org/pgcalendar"))

print("\n-- known-blocked (expect FAIL) --")
timed("kktix direct", lambda: direct("https://kktix.com/events"))
timed("dcard direct", lambda: direct("https://www.dcard.tw/f/taichung"))
