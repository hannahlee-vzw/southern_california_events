"""
Crypto.com Arena — https://www.cryptoarena.com/events

Rendering: Static HTML (same CMS as SoFi Stadium and Dignity Health Sports Park).
Strategy: requests + BeautifulSoup.

Structure (near-identical to SoFi):
  div.eventItem.entry                    ← card
    div.thumb > a[href]                  ← detail link
    div.info.clearfix
      div.date
        div.wrapper
          span.m-date__singleDate
            span.m-date__month           ← "May "
            span.m-date__day             ← "21"
            span.m-date__year            ← ", 2026"
        span.time                        ← "/ 8:00PM"  (has "/ " prefix — use h5 instead)
      h3.title.title-withTagline
        a[href]                          ← event name + link
      h4.tagline                         ← subtitle e.g. "Mejor Tarde Que Nunca Tour 2026"
      div.meta
        h5.time > span.start             ← "8:00 PM"  (cleaner, no prefix)
"""
import requests
from bs4 import BeautifulSoup
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


class CryptoArenaScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        resp = requests.get(self.url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("div.eventItem.entry"):
            try:
                title_el   = card.select_one("h3.title a")
                tagline_el = card.select_one("h4.tagline")
                month_el   = card.select_one("span.m-date__month")
                day_el     = card.select_one("span.m-date__day")
                year_el    = card.select_one("span.m-date__year")
                time_el    = card.select_one("h5.time span.start")
                link_el    = card.select_one("h3.title a")

                if not title_el:
                    continue

                name = title_el.get_text(strip=True)
                if _is_excluded(name):
                    continue

                if tagline_el:
                    tagline = tagline_el.get_text(strip=True)
                    if tagline:
                        name = f"{name} – {tagline}"

                month = month_el.get_text(strip=True) if month_el else ""
                day   = day_el.get_text(strip=True)   if day_el   else ""
                year  = year_el.get_text(strip=True).strip(", ") if year_el else ""
                raw_date = f"{month} {day} {year}".strip()

                raw_time = time_el.get_text(strip=True) if time_el else ""

                day_str, date_str, time_str = _parse(raw_date, raw_time)

                href = link_el.get("href", "") if link_el else ""
                link = absolute_url(href, self.url)

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
        return "UNKNOWN", "UNKNOWN", raw_time or "TBA"

    time_str = raw_time if raw_time else "TBA"
    try:
        t = dateutil_parser.parse(raw_time, fuzzy=True)
        time_str = t.strftime("%I:%M %p").lstrip("0")
    except Exception:
        pass

    return day_str, date_str, time_str
