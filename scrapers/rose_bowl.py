"""
Rose Bowl Stadium — https://www.rosebowlstadium.com/events/calendar/list

Rendering: Server-side rendered Nuxt.js (SSR) — content is in the HTML.
Strategy: requests + BeautifulSoup.

Structure:
  article.card                           ← card
    div.event-info
      span.event-date                    ← "May 30, 2026"
      span.event-time                    ← "/ 7:00 PM"  (strip leading "/ ")
    a.card-title-link[href]              ← relative detail link
      h2.card-title                      ← event name
"""
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}
BASE_URL = "https://www.rosebowlstadium.com"


class RoseBowlScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        resp = requests.get(self.url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("article.card"):
            try:
                title_el = card.select_one("h2.card-title")
                date_el  = card.select_one("span.event-date")
                time_el  = card.select_one("span.event-time")
                link_el  = card.select_one("a.card-title-link")

                if not title_el:
                    continue

                name     = title_el.get_text(strip=True)
                raw_date = date_el.get_text(strip=True) if date_el else ""
                raw_time = time_el.get_text(strip=True).lstrip("/ ").strip() if time_el else ""
                href     = link_el.get("href", "") if link_el else ""
                link     = absolute_url(href, BASE_URL)

                day_str, date_str, time_str = _parse(raw_date, raw_time)
                events.append(Event(day=day_str, date=date_str, time=time_str, name=name, link=link))
            except Exception:
                continue

        return sort_events(dedup(events))


def _parse(raw_date: str, raw_time: str) -> tuple[str, str, str]:
    try:
        dt = dateutil_parser.parse(raw_date, fuzzy=True)
        day_str  = dt.strftime("%A")
        date_str = dt.strftime("%m/%d/%Y")
    except Exception:
        return "UNKNOWN", "UNKNOWN", raw_time or "TBD"

    time_str = raw_time if raw_time else "TBD"
    try:
        t = dateutil_parser.parse(raw_time, fuzzy=True)
        time_str = t.strftime("%I:%M %p").lstrip("0")
    except Exception:
        pass

    return day_str, date_str, time_str
