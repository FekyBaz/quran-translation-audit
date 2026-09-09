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

## Reproduce any finding

```bash
curl -s 'https://api.quran.com/api/v4/verses/by_key/3:189?translations=95' | jq '.verse.translations[0].text'
```
