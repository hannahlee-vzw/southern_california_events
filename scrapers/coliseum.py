"""
L.A. Memorial Coliseum — https://www.lacoliseum.com/events

Rendering: Static HTML (WordPress).
Strategy: requests + BeautifulSoup.

Structure:
  div.event-box                          ← card
    div.image > a[href]                  ← detail link
    div.text
      a.title[href]                      ← event name + link
      div.bottom
        p.date
          span.month                     ← "Jun"
          span.day                       ← "11-14"  (range — take start day)

Note: no year in date — inferred from current year; bumped to next year if date has passed.
Note: no time element present.
"""
import requests
from bs4 import BeautifulSoup
from datetime import date
from dateutil import parser as dateutil_parser

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}

EXCLUDE_KEYWORDS = [
    "vip tour",
]


def _is_excluded(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in EXCLUDE_KEYWORDS)


class ColiseumScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        resp = requests.get(self.url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("div.event-box"):
            try:
                title_el = card.select_one("div.text a.title")
                month_el = card.select_one("span.month")
                day_el   = card.select_one("span.day")

                if not title_el:
                    continue

                name  = title_el.get_text(strip=True)
                if _is_excluded(name):
                    continue
                href  = title_el.get("href", "")
                link  = absolute_url(href, self.url)

                month = month_el.get_text(strip=True) if month_el else ""
                day   = day_el.get_text(strip=True).split("-")[0].strip() if day_el else ""

                day_str, date_str = _parse_date(month, day)
                events.append(Event(day=day_str, date=date_str, time="TBA", name=name, link=link))
            except Exception:
                continue

        return sort_events(dedup(events))


def _parse_date(month: str, day: str) -> tuple[str, str]:
    """
    Build a date from month ("Jun") and start day ("11"), inferring the year.
    If the resulting date is in the past, use next year.
    """
    if not month or not day:
        return "TBA", "TBA"

    today = date.today()
    for year in (today.year, today.year + 1):
        try:
            dt = dateutil_parser.parse(f"{month} {day} {year}")
            if dt.date() >= today:
                return dt.strftime("%A"), dt.strftime("%m/%d/%Y")
        except Exception:
            continue

    return "TBA", "TBA"
