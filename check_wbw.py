"""Re-verify the 26 missing wbw clips from quran#3317 + neighbor controls."""
import urllib.request

FILES = [
    "008_066_002", "008_072_021", "012_008_015", "012_018_009",
    "015_018_007", "018_049_020", "018_050_020", "018_054_007",
    "018_055_004", "028_078_021", "028_086_007", "033_019_003",
    "033_019_010", "037_033_005", "037_083_002", "040_045_004",
    "043_052_009", "047_016_011", "053_023_009", "053_029_003",
    "053_032_030", "058_017_014", "060_002_007", "060_011_014",
    "079_001_002", "098_007_001",
]


def head(url):
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "wbw-check"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except Exception as e:
        s = str(e)
        if "404" in s:
            return 404
        return f"ERR {e}"


def neighbor(f, delta):
    sss, aaa, nnn = f.split("_")
    n2 = int(nnn) + delta
    if n2 < 1:
        return None
    return f"{sss}_{aaa}_{n2:03d}"


missing, fixed, neighbor_ok, neighbor_bad = [], [], 0, []
for f in FILES:
    st = head(f"https://audio.qurancdn.com/wbw/{f}.mp3")
    if st == 404:
        missing.append(f)
    else:
        fixed.append((f, st))
    for d in (-1, 1):
        nb = neighbor(f, d)
        if not nb:
            continue
        ns = head(f"https://audio.qurancdn.com/wbw/{nb}.mp3")
        if ns == 200:
            neighbor_ok += 1
        else:
            neighbor_bad.append((nb, ns))

print(f"STILL MISSING: {len(missing)}/{len(FILES)}")
print(f"FIXED SINCE REPORT: {fixed}")
print(f"neighbors 200: {neighbor_ok}, neighbors non-200: {neighbor_bad}")
open("wbw_verify.txt", "w").write(
    f"missing={len(missing)} fixed={fixed} bad_neighbors={neighbor_bad}")
