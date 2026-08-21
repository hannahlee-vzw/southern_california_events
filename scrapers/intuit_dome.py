"""
Intuit Dome — https://www.intuitdome.com/events/event-schedule

Rendering: Next.js SSR — content is in the initial HTML.
Strategy: requests + BeautifulSoup.

Structure:
  li[class*="eventCategoryCard"]              ← individual event card, listed in
                                                  chronological order on the page
    div[class*="_heading_"]
      div[class*="_title_"]                    ← event name
    div[class*="_date_"] > span                ← "SAT, JUN 13 / 7:30 PM" or "TBD"
    div[class*="_buttonWrapper_"]
      a[href*="intuitdome.com/events"]         ← venue detail link (ignore Ticketmaster link)

Note: the cards are grouped into wrapper divs (class*="EventCollection_section"),
but that grouping does NOT correspond to a month/year header — there is no year
anywhere in the markup. The cards are simply read in DOM order, which matches the
order shown on the site, and the year is inferred from that order: it starts at
the current year and increments every time the month goes backwards (e.g.
December -> January) relative to the previous card, since the site never lists
events out of chronological order.

Note: CSS module hashes in class names (e.g. _11x9n_) may change on redeployment.
      Using [class*=] partial matching to stay resilient.
"""
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from .base import BaseScraper, Event
from ._util import absolute_url, dedup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}


class IntuitDomeScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        resp = requests.get(self.url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        year = datetime.now().year
        prev_month: int | None = None

        for card in soup.select("li[class*='eventCategoryCard']"):
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

                day_str, date_str, time_str, prev_month, year = _parse_datetime(raw_datetime, prev_month, year)
                events.append(Event(day=day_str, date=date_str, time=time_str, name=name, link=link))
            except Exception:
                continue

        # Not sorted: the site already lists cards in chronological order, and the
        # year inference above depends on preserving that original order.
        return dedup(events)


def _parse_datetime(raw: str, prev_month: int | None, year: int) -> tuple[str, str, str, int | None, int]:
    """
    Parse "SAT, JUN 13 / 7:30 PM" into ("Saturday", "06/13/<year>", "7:30 PM").

    No year appears in the source markup, so it's tracked across calls: it starts
    at the current year and increments whenever the parsed month is earlier than
    the previous card's month, which only happens when the schedule rolls over
    into the next calendar year.
    """
    raw = raw.strip()
    time_str = "TBA"

    if " / " in raw:
        date_part, time_part = raw.split(" / ", 1)
        time_str = time_part.strip()
    else:
        date_part = raw

    try:
        dt = dateutil_parser.parse(date_part.strip(), fuzzy=True, default=datetime(year, 1, 1))
    except Exception:
        return "TBA", "TBA", time_str, prev_month, year

    month, day = dt.month, dt.day
    if prev_month is not None and month < prev_month:
        year += 1
    prev_month = month

    resolved = datetime(year, month, day)
    return resolved.strftime("%A"), resolved.strftime("%m/%d/%Y"), time_str, prev_month, year
