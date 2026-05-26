"""
Intuit Dome — https://www.intuitdome.com/events/event-schedule

Rendering: Next.js SSR — content is in the initial HTML.
Strategy: requests + BeautifulSoup.

Structure (events grouped by month):
  div[class*="EventCollection_section"]     ← month group
    h1[class*="monthTitle"]                 ← "June 2026"  (provides the year)
    li[class*="eventCategoryCard"]          ← individual event card
      div[class*="_heading_"]
        div[class*="_title_"]               ← event name
      div[class*="_date_"] > span           ← "SAT, JUN 13 / 7:30 PM"
      div[class*="_buttonWrapper_"]
        a[href*="intuitdome.com/events"]    ← venue detail link (ignore Ticketmaster link)

Note: CSS module hashes in class names (e.g. _11x9n_) may change on redeployment.
      Using [class*=] partial matching to stay resilient.
"""
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}


class IntuitDomeScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        resp = requests.get(self.url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for section in soup.select("div[class*='EventCollection_section']"):
            # Extract the year from the month header (e.g. "June 2026" → "2026")
            month_el = section.select_one("h1[class*='monthTitle']")
            year_str = ""
            if month_el:
                parts = month_el.get_text(strip=True).split()
                year_str = parts[-1] if parts else ""

            for card in section.select("li[class*='eventCategoryCard']"):
                try:
                    title_el    = card.select_one("div[class*='_heading_'] div[class*='_title_']")
                    datetime_el = card.select_one("div[class*='_date_'] span")
                    link_el     = card.select_one("a[href*='intuitdome.com/events']")

                    if not title_el:
                        continue

                    name         = title_el.get_text(strip=True)
                    raw_datetime = datetime_el.get_text(strip=True) if datetime_el else ""
                    href         = link_el.get("href", "") if link_el else ""
                    link         = absolute_url(href, self.url)

                    day_str, date_str, time_str = _parse_datetime(raw_datetime, year_str)
                    events.append(Event(day=day_str, date=date_str, time=time_str, name=name, link=link))
                except Exception:
                    continue

        return sort_events(dedup(events))


def _parse_datetime(raw: str, year: str) -> tuple[str, str, str]:
    """
    Parse "SAT, JUN 13 / 7:30 PM" + year "2026"
    into ("Saturday", "06/13/2026", "7:30 PM").
    """
    raw = raw.strip()
    time_str = "TBA"

    if " / " in raw:
        date_part, time_part = raw.split(" / ", 1)
        time_str = time_part.strip()
    else:
        date_part = raw

    # Append year so dateutil can parse "SAT, JUN 13 2026"
    date_with_year = f"{date_part.strip()} {year}".strip()
    try:
        dt = dateutil_parser.parse(date_with_year, fuzzy=True)
        return dt.strftime("%A"), dt.strftime("%m/%d/%Y"), time_str
    except Exception:
        return "UNKNOWN", "UNKNOWN", time_str
