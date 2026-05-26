"""
Kia Forum — https://www.thekiaforum.com/events

Rendering: Static HTML (The Events Calendar WordPress plugin).
Strategy: requests + BeautifulSoup.

Pagination: The Events Calendar uses ?tribe_paged=N for additional pages.
"""
import requests
from bs4 import BeautifulSoup
from datetime import date
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

                    # Display text ("May 24") is correct; datetime attr year is stale (2023).
                    # Use display text for date, datetime attr only for time.
                    display_date  = time_el.get_text(strip=True) if time_el else ""
                    datetime_attr = time_el.get("datetime", "") if time_el else ""
                    day, date, time_str = _parse_date_time(display_date, datetime_attr)

                    href = link_el.get("href", "") if link_el else ""
                    link = absolute_url(href, self.url)

                    events.append(Event(day=day, date=date, time=time_str, name=name, link=link))
                except Exception:
                    continue

        return sort_events(dedup(events))


def _parse_date_time(display: str, datetime_attr: str) -> tuple[str, str, str]:
    """
    Use the display text (e.g. "May 24") for the date — the datetime attribute
    year is stale. Infer the year: use current year, bump to next if already past.
    Extract time from the datetime attribute (e.g. "2023-06-12 19:00" → "7:00 PM").
    """
    today = date.today()

    # Extract time from the datetime attribute
    time_str = "TBA"
    try:
        dt_attr = dateutil_parser.parse(datetime_attr)
        if dt_attr.hour or dt_attr.minute:
            time_str = dt_attr.strftime("%I:%M %p").lstrip("0")
    except Exception:
        pass

    # Parse display date with inferred year
    for year in (today.year, today.year + 1):
        try:
            dt = dateutil_parser.parse(f"{display} {year}", fuzzy=True)
            if dt.date() >= today:
                return dt.strftime("%A"), dt.strftime("%m/%d/%Y"), time_str
        except Exception:
            continue

    return "UNKNOWN", "UNKNOWN", time_str
