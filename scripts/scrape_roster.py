import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, timezone

URL      = "https://ucsdtritons.com/sports/baseball/roster/2025-26"
BASE_URL = "https://ucsdtritons.com"


def player_id(name: str) -> str:
    """'Roch Cholowsky' → 'RCholowsky'"""
    parts = name.strip().split()
    return (parts[0][0].upper() + parts[-1].capitalize()) if len(parts) >= 2 else name.replace(" ", "")


def absolute_url(src: str) -> str:
    src = (src or "").strip()
    if src.startswith("http"):   return src
    if src.startswith("//"):     return "https:" + src
    if src:                      return BASE_URL + src
    return ""


def clean_position(raw: str) -> str:
    """Remove height (5'11", 6'2") and deduplicate doubled strings."""
    # Strip height pattern, e.g. 5'11" or 6'2"
    p = re.sub(r"\d['’]\d{1,2}\"?", "", raw).strip()
    # Remove dangling punctuation/spaces
    p = p.strip("/ ").strip()
    # Detect and remove duplicated prefix, e.g. "INF/OFINF/OF" → "INF/OF"
    for length in range(1, len(p) // 2 + 1):
        if p[:length] == p[length: length * 2]:
            return p[:length]
    return p


def extract_city(raw: str) -> str:
    """Pull 'City, State' from a messy concatenated string."""
    # Pattern: word(s), two-letter state abbrev or 'Calif.' / 'Wash.' etc.
    m = re.search(r"([A-Z][a-zA-Z'\s]+,\s*(?:[A-Z][a-zA-Z\.]+\.?))", raw)
    return m.group(1).strip() if m else ""


def is_pitcher(position: str) -> bool:
    p = position.upper()
    return (
        "RHP" in p or "LHP" in p
        or re.search(r"(?:^|/)SP(?:/|$)", p)
        or re.search(r"(?:^|/)RP(?:/|$)", p)
        or p == "P"
    )


def scrape():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    players = []

    for li in soup.select("li.sidearm-roster-player"):
        # ── Name ──────────────────────────────────────────────────────────────
        name_el = (li.select_one(".sidearm-roster-player-name a")
                   or li.select_one("h3 a")
                   or li.select_one("[class*='name'] a"))
        name = name_el.get_text(strip=True) if name_el else ""
        if not name:
            continue

        # ── Jersey number ─────────────────────────────────────────────────────
        num_el = (li.select_one(".sidearm-roster-player-jersey-number")
                  or li.select_one("[class*='jersey-number']"))
        number = num_el.get_text(strip=True) if num_el else ""

        # ── Photo ─────────────────────────────────────────────────────────────
        img_el = li.select_one("img")
        photo_url = ""
        if img_el:
            src = img_el.get("data-src") or img_el.get("src") or ""
            photo_url = absolute_url(src)

        # ── Position (FIRST matching span only, to avoid duplicates) ─────────
        pos_el = li.select_one(".sidearm-roster-player-position")
        raw_position = pos_el.get_text(strip=True) if pos_el else ""
        position = clean_position(raw_position)

        # ── Academic year (first span matching class) ─────────────────────────
        yr_el = (li.select_one(".sidearm-roster-player-academic-year")
                 or li.select_one("[class*='academic-year']"))
        year = yr_el.get_text(strip=True) if yr_el else ""

        # ── Height ────────────────────────────────────────────────────────────
        ht_el = li.select_one(".sidearm-roster-player-height")
        height = ht_el.get_text(strip=True) if ht_el else ""

        # ── Hometown (city, state only) ───────────────────────────────────────
        home_el = li.select_one(".sidearm-roster-player-hometown")
        raw_home = home_el.get_text(strip=True) if home_el else ""
        hometown = extract_city(raw_home) or raw_home

        players.append({
            "id":        player_id(name),
            "number":    number,
            "name":      name,
            "position":  position,
            "year":      year,
            "height":    height,
            "hometown":  hometown,
            "photo_url": photo_url,
            "type":      "pitcher" if is_pitcher(position) else "hitter",
        })

    return {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "players": players,
    }


if __name__ == "__main__":
    data = scrape()
    os.makedirs("data", exist_ok=True)
    with open("data/roster.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Scraped {len(data['players'])} players → data/roster.json")
