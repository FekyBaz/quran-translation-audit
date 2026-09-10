"""Fetch all verses of a quran.com translation resource.

Usage: python fetch_quran_api_translation.py [resource_id] [output.json]
Default: resource 779 (French Rashid Maash).
Stdlib only. Be polite: ~130 requests with pauses.
"""
import json
import sys
import time
import urllib.request

RES = int(sys.argv[1]) if len(sys.argv) > 1 else 779
OUTF = sys.argv[2] if len(sys.argv) > 2 else "translation.json"

OUT = {}
for ch in range(1, 115):
    page = 1
    while True:
        url = (f"https://api.quran.com/api/v4/verses/by_chapter/{ch}"
               f"?translations={RES}&per_page=50&page={page}&fields=verse_key")
        req = urllib.request.Request(url, headers={"User-Agent": "translation-fetch"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        for v in d["verses"]:
            trs = [t for t in v.get("translations", []) if t["resource_id"] == RES]
            if trs:
                OUT[v["verse_key"]] = trs[0]["text"]
        if page >= d["pagination"]["total_pages"]:
            break
        page += 1
        time.sleep(0.25)
    print(f"chapter {ch} done ({len(OUT)} total)", flush=True)

assert len(OUT) == 6236, f"expected 6236 verses, got {len(OUT)}"
with open(OUTF, "w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False)
print("TOTAL:", len(OUT), "->", OUTF)
