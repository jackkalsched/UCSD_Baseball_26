import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, timezone, date

URL = "https://ucsdtritons.com/sports/baseball/schedule/2026"
SCHEDULE_YEAR = 2026

def parse_game_date(date_str):
    """Parse 'Feb 13 (Fri)' -> date object, or None on failure."""
    m = re.match(r'(\w+ \d+)', date_str)
    if m:
        try:
            return datetime.strptime(f"{m.group(1)} {SCHEDULE_YEAR}", "%b %d %Y").date()
        except ValueError:
            pass
    return None

def scrape():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    today = date.today()

    games = []
    for li in soup.select(".sidearm-schedule-games-container > li.sidearm-schedule-game"):
        classes = li.get("class", [])

        date_div = li.select_one(".sidearm-schedule-game-opponent-date")
        spans = date_div.select("span") if date_div else []
        date_str = spans[0].get_text(strip=True) if spans else ""
        time_str = spans[1].get_text(strip=True) if len(spans) > 1 else ""

        opp_div = li.select_one(".sidearm-schedule-game-opponent-name")
        opponent = opp_div.get_text(strip=True) if opp_div else ""

        loc_div = li.select_one(".sidearm-schedule-game-location")
        location = loc_div.get_text(strip=True) if loc_div else ""

        result_div = li.select_one(".sidearm-schedule-game-result")
        result = result_div.get_text(strip=True) if result_div else ""

        # Determine status from result and actual date, not the site's stale CSS class.
        game_date = parse_game_date(date_str)
        if result or (game_date and game_date < today):
            status = "completed"
        else:
            status = "upcoming"

        games.append({
            "date": date_str,
            "time": time_str,
            "opponent": opponent,
            "location": location,
            "home_away": "away" if "sidearm-schedule-away-game" in classes else "home",
            "result": result,
            "status": status,
        })

    return {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "games": games,
    }

if __name__ == "__main__":
    data = scrape()
    os.makedirs("data", exist_ok=True)
    with open("data/schedule.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Scraped {len(data['games'])} games -> data/schedule.json")
