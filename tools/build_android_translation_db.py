"""Build a quran_android-compatible SQLite translation database.

Schema per the app's reader (DatabaseHandler: table verses(sura, ayah, text)).
Faithful 1:1 conversion — no text normalization (sup footnote markers and
source quirks like [161] are preserved verbatim for the app to handle).

Usage: python build_android_translation_db.py input.json output.db
Validates: 6,236 rows, standard per-surah counts, no nulls, spot checks.

Example (validated): French Rashid Maash, api resource 779.
"""
import json
import os
import sqlite3
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "translation.json"
DB = sys.argv[2] if len(sys.argv) > 2 else "translation.db"

STD = [7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52,
       99, 128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88,
       69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59,
       37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
       14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31,
       50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21,
       11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6]

d = json.load(open(SRC, encoding="utf-8"))
assert len(d) == 6236, f"expected 6236 verses, got {len(d)}"

if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("CREATE TABLE verses (sura INTEGER, ayah INTEGER, text TEXT)")
rows = []
for key in sorted(d, key=lambda k: tuple(map(int, k.split(":")))):
    s, a = map(int, key.split(":"))
    rows.append((s, a, d[key]))
cur.executemany("INSERT INTO verses (sura, ayah, text) VALUES (?, ?, ?)", rows)
con.commit()

n = cur.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
assert n == 6236, n
nulls = cur.execute("SELECT COUNT(*) FROM verses WHERE text IS NULL OR text=''").fetchone()[0]
assert nulls == 0, nulls
for i, exp in enumerate(STD, start=1):
    got = cur.execute("SELECT COUNT(*) FROM verses WHERE sura=?", (i,)).fetchone()[0]
    assert got == exp, (i, got, exp)
con.close()
print(f"DB OK: {DB} ({os.path.getsize(DB)} bytes, 6236 rows)")
