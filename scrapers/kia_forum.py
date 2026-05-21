"""
Kia Forum — https://www.thekiaforum.com/events

Rendering: Static HTML (The Events Calendar WordPress plugin).
Strategy: requests + BeautifulSoup.

Pagination: The Events Calendar uses ?tribe_paged=N for additional pages.
"""
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}
MAX_PAGES = 20


class KiaForumScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []

        for page_num in range(1, MAX_PAGES + 1):
            url = self.url if page_num == 1 else f"{self.url}/page/{page_num}/"
            resp = requests.get(url, headers=HEADERS, timeout=20)

            if resp.status_code == 404:
                break
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(".single-list-event")

            if not cards:
                break

            for card in cards:
                try:
                    title_el = card.select_one("h2.event-card__title a")
                    sub_el   = card.select_one("p.event-card__sub-heading")
                    time_el  = card.select_one("time.event-card__date")
                    link_el  = card.select_one("h2.event-card__title a")

                    if not title_el:
                        continue

                    name = title_el.get_text(strip=True)
                    if sub_el:
                        sub = sub_el.get_text(strip=True)
                        if sub:
                            name = f"{name} – {sub}"

                    # datetime attr format: "2026-06-12 19:00"
                    datetime_attr = time_el.get("datetime", "") if time_el else ""
                    day, date, time_str = _parse_datetime_attr(datetime_attr)

                    href = link_el.get("href", "") if link_el else ""
                    link = absolute_url(href, self.url)

                    events.append(Event(day=day, date=date, time=time_str, name=name, link=link))
                except Exception:
                    continue

        return sort_events(dedup(events))


def _parse_datetime_attr(value: str) -> tuple[str, str, str]:
    """Parse a 'YYYY-MM-DD HH:MM' datetime attribute into (day, MM/DD/YYYY, H:MM AM/PM)."""
    try:
        dt = dateutil_parser.parse(value)
        time_str = dt.strftime("%I:%M %p").lstrip("0") if dt.hour or dt.minute else "TBD"
        return dt.strftime("%A"), dt.strftime("%m/%d/%Y"), time_str
    except Exception:
        return "UNKNOWN", "UNKNOWN", "TBD"
