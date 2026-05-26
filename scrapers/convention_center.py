"""
LA Convention Center — https://www.laconventioncenter.com/events

Rendering: Static HTML (same CMS as SoFi / Dignity Health / Crypto.com Arena).
Strategy: requests + BeautifulSoup.

Structure:
  div.eventItem.entry                    ← card
    div.thumb > a[href]                  ← detail link
    div.info.clearfix
      div.date_wrapper
        div.date                         ← "May 23 - 24, 2026"  (plain text range)
        div.presented-by                 ← "Open to Public" (ignored)
      h3.title > a[href]                 ← event name + link

Note: date is a range string — only the start date is extracted.
Note: no time element present for convention events.
Note: page has a "Load More" AJAX button (data-increment="6").
      Only the initial 6 events are returned; AJAX pagination is not yet implemented.
      To get all events, switch this scraper to Playwright and click #loadMoreEvents
      until it disappears.
"""
import re
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}


class ConventionCenterScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        resp = requests.get(self.url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("div.eventItem.entry"):
            try:
                title_el = card.select_one("h3.title a")
                date_el  = card.select_one("div.date_wrapper div.date")
                link_el  = card.select_one("h3.title a")

                if not title_el:
                    continue

                name     = title_el.get_text(strip=True)
                raw_date = date_el.get_text(strip=True) if date_el else ""
                href     = link_el.get("href", "") if link_el else ""
                link     = absolute_url(href, self.url)

                day_str, date_str = _parse_date(raw_date)
                events.append(Event(day=day_str, date=date_str, time="TBA", name=name, link=link))
            except Exception:
                continue

        return sort_events(dedup(events))


def _parse_date(raw: str) -> tuple[str, str]:
    """
    Extract the start date from strings like "May 23 - 24, 2026" or "May 23, 2026".
    Returns (day_of_week, MM/DD/YYYY).
    """
    raw = raw.strip()

    # Pull year from anywhere in the string
    year_match = re.search(r'\d{4}', raw)
    year = year_match.group() if year_match else ""

    # Take only the portion before " - " for range dates
    start = raw.split(" - ")[0].strip()

    # Append year if not already present in the start portion
    if year and year not in start:
        start = f"{start} {year}"

    try:
        dt = dateutil_parser.parse(start, fuzzy=True)
        return dt.strftime("%A"), dt.strftime("%m/%d/%Y")
    except Exception:
        return "UNKNOWN", "UNKNOWN"
