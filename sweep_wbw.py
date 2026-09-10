"""Full sweep of all word-by-word audio clips on audio.qurancdn.com.

Enumerates every word of every ayah via the quran.com v4 API
(/verses/by_chapter with words=true), then HEAD-checks each expected clip
URL with a thread pool. Suspected misses are re-checked (GET + second HEAD
round) before being reported, so transient CDN hiccups don't become findings.

Usage:
  python sweep_wbw.py --output wbw-sweep.json --report wbw-sweep.md
  python sweep_wbw.py --chapters 1-20 --output wbw-part.json
  python sweep_wbw.py --resume wbw-sweep.json   # skips verses already checked

Outputs: JSON with per-file status + markdown triage report.
Designed to be re-run daily (cron) and diffed against the previous run.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://api.quran.com/api/v4"
CDN_BASE = "https://audio.qurancdn.com/wbw"
USER_AGENT = "wbw-sweep/0.1 (+https://github.com/quran/quran.com-frontend-next/issues/3317)"
WORKERS = 20
MAX_RETRIES = 3


def api_json(url: str) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            time.sleep(2**attempt)
    raise RuntimeError(f"GET {url} failed: {last_error}")


# Ayah-end markers ("١", "٦", …) carry no pronounceable word and correctly
# have no clip. Skip any token without a single Unicode letter.
_HAS_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)


def is_pronounceable(text_uthmani: str) -> bool:
    """Whether a word token should have an audio clip."""
    return bool(_HAS_LETTER.search(text_uthmani or ""))


def chapter_word_files(chapter: int, per_page: int = 100) -> list[str]:
    """Expected clip filenames (SSS_AAA_NNN) for one surah."""
    files: list[str] = []
    page = 1
    while True:
        params = urllib.parse.urlencode(
            {
                "words": "true",
                "word_fields": "position,text_uthmani",
                "per_page": per_page,
                "page": page,
            }
        )
        payload = api_json(f"{API_BASE}/verses/by_chapter/{chapter}?{params}")
        for verse in payload.get("verses", []):
            for word in verse.get("words", []):
                if not is_pronounceable(word.get("text_uthmani", "")):
                    continue
                files.append(f"{chapter:03d}_{verse['verse_number']:03d}_{word['position']:03d}")
        pagination = payload.get("pagination", {})
        if page >= int(pagination.get("total_pages", 1)):
            return files
        page += 1
        time.sleep(0.3)


def check_one(filename: str) -> tuple[str, str]:
    """HEAD-check one clip. Returns (filename, status)."""
    url = f"{CDN_BASE}/{filename}.mp3"
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return filename, str(response.status)
    except urllib.error.HTTPError as error:
        return filename, str(error.code)
    except Exception as error:  # network-level failure, not a 404 verdict
        return filename, f"ERR {error}"


def confirm_missing(filename: str) -> bool:
    """Second-round confirmation: GET + fresh HEAD must both miss."""
    url = f"{CDN_BASE}/{filename}.mp3"
    for method in ("GET", "HEAD"):
        request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=20):
                return False
        except urllib.error.HTTPError as error:
            if error.code != 404:
                return False
        except Exception:
            return False
    return True


def parse_chapters(spec: str) -> list[int]:
    chapters: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            chapters.update(range(int(start), int(end) + 1))
        elif part:
            chapters.add(int(part))
    return sorted(c for c in chapters if 1 <= c <= 114)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapters", default="1-114")
    parser.add_argument("--output", default="wbw-sweep.json")
    parser.add_argument("--report", default="")
    parser.add_argument("--resume", default="", help="prior sweep JSON; skips checked files")
    parser.add_argument("--workers", type=int, default=WORKERS)
    args = parser.parse_args(argv)

    done: dict[str, str] = {}
    if args.resume:
        with open(args.resume, encoding="utf-8") as handle:
            prior = json.load(handle)
        done = dict(prior.get("checked", {}))

    chapters = parse_chapters(args.chapters)
    todo: list[str] = []
    for chapter in chapters:
        for filename in chapter_word_files(chapter):
            if filename not in done:
                todo.append(filename)
    print(f"chapters={len(chapters)} todo={len(todo)} resumed={len(done)}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for filename, status in pool.map(check_one, todo):
            done[filename] = status
    candidates = sorted(f for f, s in done.items() if s == "404")
    print(f"first pass: {len(candidates)} suspected missing", flush=True)
    missing = [f for f in candidates if confirm_missing(f)]
    print(f"confirmed missing: {len(missing)}", flush=True)

    payload = {
        "meta": {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "chapters": chapters,
            "checked_files": len(done),
            "missing": missing,
        },
        "checked": done,
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
    if args.report:
        lines = [
            "# Word-by-word audio sweep",
            "",
            f"Checked `{len(done)}` clips across surahs {chapters[0]}-{chapters[-1]}; "
            f"**{len(missing)} confirmed missing** (404 on HEAD round, GET and second HEAD).",
            "",
        ]
        for filename in missing:
            surah, ayah, word = (int(x) for x in filename.split("_"))
            lines.append(
                f"- `{filename}.mp3` — {surah}:{ayah} word {word} — "
                f"`curl -sI https://audio.qurancdn.com/wbw/{filename}.mp3`"
            )
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
