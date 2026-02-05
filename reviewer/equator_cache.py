from __future__ import annotations
import json
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

EQUATOR_URL = "https://www.equator-network.org/reporting-guidelines/"

def _acronym_from_title(title: str) -> str | None:
    m = re.search(r"\(([^)]+)\)", title)
    if not m:
        return None
    cand = m.group(1).strip()
    if 2 <= len(cand) <= 25:
        return cand
    return None

def build_equator_index(out: str | Path) -> None:
    r = requests.get(EQUATOR_URL, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    items = []
    seen = set()
    for a in soup.select("a[href^='/reporting-guidelines/']"):
        href = a.get("href") or ""
        text = " ".join((a.get_text() or "").split())
        if not text or href == "/reporting-guidelines/":
            continue
        url = "https://www.equator-network.org" + href
        key = (text, url)
        if key in seen:
            continue
        seen.add(key)
        items.append({"title": text, "url": url, "acronym": _acronym_from_title(text)})
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps({"source": EQUATOR_URL, "count": len(items), "items": items}, indent=2), encoding="utf-8")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="cache/equator_index.json")
    args = ap.parse_args()
    build_equator_index(args.out)
    print(f"Wrote {args.out}")
