"""
Rose Bowl Stadium — https://www.rosebowlstadium.com/events/calendar/list

Rendering: Nuxt.js with client-side event loading — events are fetched via
           JavaScript after page load, so requests returns an empty page.
Strategy: Playwright headless Chromium; wait for article.card to appear.

Structure:
  article.card                           ← card
    div.event-info
      span.event-date                    ← "May 30, 2026"
      span.event-time                    ← "/ 7:00 PM"  (strip leading "/ ")
    a.card-title-link[href]              ← relative detail link
      h2.card-title                      ← event name
"""
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from playwright.sync_api import sync_playwright

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

BASE_URL = "https://www.rosebowlstadium.com"


class RoseBowlScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="networkidle", timeout=30_000)

            # Wait for at least one event card to appear
            try:
                page.wait_for_selector("article.card", timeout=15_000)
            except Exception:
                browser.close()
                return events

            soup = BeautifulSoup(page.content(), "html.parser")
            browser.close()

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
