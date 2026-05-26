from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from .base import BaseScraper, Event
from ._util import dedup, sort_events

_DODGERS_TEAM_ID = 119
_PACIFIC = ZoneInfo("America/Los_Angeles")


class DodgersScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        season = datetime.now().year
        resp = requests.get(
            "https://statsapi.mlb.com/api/v1/schedule",
            params={
                "sportId": 1,
                "teamId": _DODGERS_TEAM_ID,
                "season": season,
                "gameType": "R",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        events = []
        for date_entry in data.get("dates", []):
            for game in date_entry.get("games", []):
                if game["teams"]["home"]["team"]["id"] != _DODGERS_TEAM_ID:
                    continue
                utc_dt = datetime.fromisoformat(
                    game["gameDate"].replace("Z", "+00:00")
                )
                local_dt = utc_dt.astimezone(_PACIFIC)
                day = local_dt.strftime("%A")
                date = local_dt.strftime("%m/%d/%Y")
                h = local_dt.hour % 12 or 12
                time = f"{h}:{local_dt.strftime('%M')} {local_dt.strftime('%p')}"
                opponent = game["teams"]["away"]["team"]["name"]
                link = f"https://www.mlb.com/gameday/{game['gamePk']}"
                events.append(Event(day=day, date=date, time=time,
                                    name=f"vs. {opponent}", link=link))

        return sort_events(dedup(events))
