# Quran Translation Audit

Regression-tested text-integrity audit for Quran.com v4 API translation
texts — built while investigating
[quran/quran.com-frontend-next#3282](https://github.com/quran/quran.com-frontend-next/issues/3282)
(stray footnote text leaking into verse 3:189 of the Maududi translation).

## What it does

Fetches every verse of a translation resource and flags likely
footnote/commentary leaks:

- **H1** — lowercase letter starting a new sentence (the 3:189 signature:
  `…All-Powerful. indeed been successful.`)
- **H2** — unbalanced parentheses/brackets, or angle-bracket residue
  outside well-formed `<sup foot_note="N">M</sup>` markers

## Usage

```bash
python audit.py --resource-id 95 --output findings.json  # Maududi English
python -m unittest test_audit -v
```

Stdlib only. Be polite to the API (~130 requests per full translation).

## Verified findings (Maududi #95, 2026-09-10)

| Verse | Class | Evidence |
|---|---|---|
| 3:189 | leaked tail fragment (reported) | `…All-Powerful. indeed been successful.` |
| 3:8 | stray period | `…right way, and. bestow upon us…` |
| 6:80 | leading fragment + suspected typo | `His. people remonstrated…`, `Abraharn said` |
| 6:112 | stray period | `…only by way of. delusion.` |
| 2:198 | bracket for apostrophe + unclosed bracket | `al-Mash[ar`, `[Arafat` (never closed) |
| 7:80 | truncation | `[as a Messeng` (missing `er`) |
| 7:96 | trailing stub | `…for their deeds. so.` |
| 12:52 | bracket mismatch | `[i.e. the chief)` |
| 43:61 | bracket mismatch | `[i.e., Jesus)` |
| 43:80 | bracket mismatch | `[i.e., angels)` |
| 48:25 | hyphenation + bracket mismatch + unclosed paren | `chastise-ment`, `[i.e. the Makkans)`, `(then fighting…` never closed |

Deliberately excluded: Maududi's lowercase continuation style
(`…us. and do not…`, `…you. nor can…`) — archaic but intentional;
well-formed `<sup foot_note>` markers, which the API ships by design.

## Round 2 — Russian Kuliev (#45) and Urdu Bayan-ul-Quran (#158)

- **Russian 18:7 confirmed**: `…испытать людей ивыявить, чьи деяния…` —
  missing space (`и выявить`). Full sweep of all 6,236 Russian verses
  found no other bracket/case issues
  ([issue](https://github.com/quran/quran.com-frontend-next/issues/3338)).
  Note: fused-word typos need dictionary checking, which this tool does
  not do — 18:7 was verified by hand.
- **Urdu: structurally sound, with a documented convention.** Bayan-ul-Quran
  commentary parentheses legitimately span verse boundaries (verified
  pairing: the paren opened in 2:101 closes in 2:102; 36:19 balanced).
  Automated per-verse bracket checks do NOT apply to this translation —
  206 raw flags, all attributable to the convention. The
  [quran_android#3789](https://github.com/quran/quran_android/issues/3789)
  complaint concerns that app's own data pipeline, not this API's data.

## Round 3 — word-by-word audio gaps (#3317)

`check_wbw.py` re-verifies a list of `wbw/SSS_AAA_NNN.mp3` clips (HEAD)
plus in-range neighbours as controls. Re-check of the 26 files from
[#3317](https://github.com/quran/quran.com-frontend-next/issues/3317):
**19 now return 200** (fixed upstream since the report); 7 still 404 —
`008_066_002`, `012_008_015`, `018_049_020`, `018_054_007`,
`060_002_007`, `079_001_002`, `098_007_001` — including the most visible
ones (98:7 first word, 79:1 one of two words).

## Round 4 — Hausa Gumi (#32): entity-escaping inconsistency + one paren

- **1,925 of 6,236 verses serve raw `&quot;` entities** (31% of the
  translation) where Maududi serves straight quotes and zero entities.
  Browsers injecting via innerHTML render it fine, but every plaintext
  API consumer (apps, researchers, kids'-education backends across West
  Africa) displays literal `&quot;Ya mutãnena!`. Inconsistent with the
  rest of the API — worth normalizing upstream.
- **2:92 unclosed paren**: `…kuka riƙi maraƙi (daga bãyansa, alhãli
  kuwa kuna mãsu zãlunci.` — no close, no cross-verse pairing.
- Otherwise clean: lowercase continuations are this translation's
  consistent style (not leaks), and no other bracket anomalies found.

## Reproduce any finding

```bash
curl -s 'https://api.quran.com/api/v4/verses/by_key/3:189?translations=95' | jq '.verse.translations[0].text'
```
