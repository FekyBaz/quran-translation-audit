"""Generate a spqrxi/quranchecksum-compatible manifest from the official app DB.

Usage: python generate_appdb_manifest.py <quran.ar.uthmani.v2.db> <out.json>
Trust chain: hashes the maintainer-published database byte content
(NFC + strip, same canonical form as quranchecksum) — guards against
corrupted downloads and tampered repacks. Verse texts are never redistributed.
"""
import hashlib
import json
import sqlite3
import sys
import unicodedata
from datetime import datetime, timezone


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(db_path, out_path):
    db = sqlite3.connect(db_path)
    rows = db.execute(
        "SELECT sura, ayah, text FROM arabic_text ORDER BY sura, ayah"
    ).fetchall()
    verse_hashes = {}
    surah_groups = {}
    for sura, ayah, text in rows:
        norm = unicodedata.normalize("NFC", text or "").strip()
        h = sha(norm)
        key = f"{sura}:{ayah}"
        verse_hashes[key] = h
        surah_groups.setdefault(str(sura), []).append(h)
    surah_hashes = {s: sha("".join(hs)) for s, hs in surah_groups.items()}
    root = sha("".join(surah_hashes[str(s)] for s in sorted(surah_hashes, key=int)))
    manifest = {
        "meta": {
            "format_version": "1.0",
            "kind": "text",
            "source": "quran_android quran.ar.uthmani.v2.db (maintainer-published)",
            "normalization": "NFC+strip",
            "hash_algorithm": "sha256",
            "verse_count": len(verse_hashes),
            "surah_count": len(surah_hashes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "granularity": "verse",
            "rollup_method": "sha256-of-concatenated-child-hashes",
        },
        "verses": verse_hashes,
        "surahs": surah_hashes,
        "quran": root,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print(f"verses={len(verse_hashes)} root={root[:16]}... -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
