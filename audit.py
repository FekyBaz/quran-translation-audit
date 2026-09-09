"""Quran.com translation text-integrity audit (re quran/quran.com-frontend-next#3282).

Flags likely footnote/commentary leaks in v4 API translation texts:
  H1: lowercase letter starting a new sentence (the 3:189 signature)
  H2: unbalanced parentheses/brackets
Also records verse lengths for manual anomaly review.

Usage: python audit.py --resource-id 95 --output findings.json
Stdlib only. Be polite: ~130 requests for a full translation.
"""
import argparse
import json
import re
import time
import urllib.request

API = "https://api.quran.com/api/v4"
ABBR = {"e.g", "i.e", "st", "mr", "mrs", "dr", "vs", "no", "fig", "etc",
        "al", "ibn", "bint", "т.е", "т.к", "г", "ст", "др", "пр", "см",
        "напр", "им", "св"}

SENT_END = re.compile(r"(?<=[.!?。۔])\s+(?=[a-zа-яё])")


def fetch(url, retries=4):
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "quran-translation-audit/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if attempt == retries:
                raise
            print(f"  retry ({e})")
            time.sleep(2 * attempt)


def check_h1(text):
    """Lowercase sentence starts, ignoring known abbreviations."""
    hits = []
    for m in SENT_END.finditer(text):
        # Ellipsis suspension ("...", "..", "…") legitimately continues
        # lowercase (French Hamidullah style) — never a leak signature.
        if text[:m.start()].rstrip().endswith(("..", "…")):
            continue
        # word before the boundary: abbreviation?
        before = text[:m.start()].rstrip()
        prev = re.split(r"\s+", before)[-1].rstrip(".").lower() if before else ""
        word = m.group(0).strip()
        if prev in ABBR:
            continue
        # excerpt around hit
        s = max(0, m.start() - 40)
        hits.append(text[s:m.start() + 12].replace("\n", " "))
    return hits


def check_h3_pagenum(text):
    """Stray page/cross-reference residue like `Omniscient 266]`."""
    return re.findall(r"(?<!\[)\b\d{2,4}\]", text)


def check_h4_double_punct(text):
    """Double punctuation like `;.` (excluding ellipsis)."""
    return re.findall(r"(?<!\.)[;:,]\.(?!\.)", text)


def check_h2(text):
    issues = []
    # Strip well-formed footnote markers first; whatever angle
    # brackets remain are tag residue (e.g. `_note="177265">2</sup>`).
    cleaned = re.sub(r'<sup foot_note=("?)\d+\1>\d+</sup>', '', text)
    if '<' in cleaned or '>' in cleaned:
        issues.append("angle-bracket residue outside footnote markers")
    for a, b in (("(", ")"), ("[", "]")):
        if text.count(a) != text.count(b):
            issues.append(f"unbalanced {a}{b}: {text.count(a)} vs {text.count(b)}")
    return issues


def audit_resource(resource_id):
    findings = []
    lengths = []
    for chapter in range(1, 115):
        page = 1
        while True:
            url = (f"{API}/verses/by_chapter/{chapter}"
                   f"?translations={resource_id}&per_page=50&page={page}"
                   f"&fields=verse_key")
            data = fetch(url)
            for v in data["verses"]:
                key = v["verse_key"]
                trs = [t for t in v.get("translations", [])
                       if t["resource_id"] == resource_id]
                if not trs:
                    continue
                text = trs[0]["text"]
                lengths.append((len(text), key))
                h1 = check_h1(text)
                h2 = check_h2(text)
                h3 = check_h3_pagenum(text)
                h4 = check_h4_double_punct(text)
                if h1 or h2 or h3 or h4:
                    findings.append({"verse": key, "h1": h1, "h2": h2,
                                     "h3": h3, "h4": h4, "text": text})
            pages = data["pagination"]["total_pages"]
            if page >= pages:
                break
            page += 1
            time.sleep(0.3)
        print(f"chapter {chapter}: done")
    return findings, lengths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resource-id", type=int, required=True)
    ap.add_argument("--output", default="findings.json")
    args = ap.parse_args()
    findings, lengths = audit_resource(args.resource_id)
    lengths.sort()
    report = {"resource_id": args.resource_id,
              "findings": findings,
              "shortest": [(k, n) for n, k in lengths[:10]],
              "longest": [(k, n) for n, k in lengths[-10:]]}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"findings: {len(findings)} -> {args.output}")


if __name__ == "__main__":
    main()
