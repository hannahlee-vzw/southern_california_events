"""
Long Beach Convention Center — https://www.lbentertainmentcenter.com/events/

Rendering: JS-rendered.
Strategy: Playwright headless Chromium; no "Load More" — all events render on page load.

Structure:
  div.card--listing                 ← event card
    div.card__body
      p.date-heading                ← "September 5 - 6" (no year)
      a.card__heading[href]         ← event name + detail link
"""
import re
from datetime import date as date_type

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from playwright.sync_api import sync_playwright

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

CARD_SELECTOR = "div.card--listing"


class LongBeachCCScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="networkidle", timeout=30_000)

            try:
                page.wait_for_selector(CARD_SELECTOR, timeout=15_000)
            except Exception:
                browser.close()
                return events

            soup = BeautifulSoup(page.content(), "html.parser")
            browser.close()

        for card in soup.select(CARD_SELECTOR):
            try:
                title_el = card.select_one("a.card__heading")
                date_el  = card.select_one("p.date-heading")

                if not title_el:
                    continue

                name     = title_el.get_text(strip=True)
                raw_date = date_el.get_text(strip=True) if date_el else ""
                href     = title_el.get("href", "")
                link     = absolute_url(href, self.url)

                day_str, date_str = _parse_date(raw_date)
                events.append(Event(day=day_str, date=date_str, time="TBA", name=name, link=link))
            except Exception:
                continue

        return sort_events(dedup(events))


def _parse_date(raw: str) -> tuple[str, str]:
    """
    Parse strings like "September 5 - 6" or "September 11" (no year).
    Infers the year: uses current year, bumps to next year if the date has passed.
    Returns (day_of_week, MM/DD/YYYY) for the start date.
    """
    raw = raw.strip()
    start = raw.split(" - ")[0].strip()

    today = date_type.today()
    for year in (today.year, today.year + 1):
        try:
            dt = dateutil_parser.parse(f"{start} {year}", fuzzy=True)
            if dt.date() >= today:
                return dt.strftime("%A"), dt.strftime("%m/%d/%Y")
        except Exception:
            continue

    # Fallback: try parsing as-is
    try:
        dt = dateutil_parser.parse(start, fuzzy=True)
        return dt.strftime("%A"), dt.strftime("%m/%d/%Y")
    except Exception:
        return "TBA", "TBA"
