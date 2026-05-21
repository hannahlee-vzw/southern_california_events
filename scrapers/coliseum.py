"""
L.A. Memorial Coliseum — https://www.lacoliseum.com/events

Rendering: Likely static HTML or WordPress-based.
Strategy: requests + BeautifulSoup; upgrade to Playwright if events are JS-rendered.

TODO (after inspecting live site):
  - Inspect raw HTML from requests.get() to confirm events are present.
  - Confirm CSS selectors for event cards, title, date, time, link.
  - Note: the Coliseum sometimes redirects to usc.edu; verify the canonical events URL.
"""
import requests
from bs4 import BeautifulSoup

from .base import BaseScraper, Event
from ._util import absolute_url, parse_date_time, dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}


class ColiseumScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        resp = requests.get(self.url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # TODO: replace with actual selectors after inspecting the live page HTML
        cards = soup.select(".event-card")  # PLACEHOLDER

        for card in cards:
            try:
                name_el = card.select_one(".event-title")   # PLACEHOLDER
                date_el = card.select_one(".event-date")    # PLACEHOLDER
                time_el = card.select_one(".event-time")    # PLACEHOLDER
                link_el = card.select_one("a")              # PLACEHOLDER

                name = name_el.get_text(strip=True) if name_el else ""
                raw_date = date_el.get_text(strip=True) if date_el else ""
                raw_time = time_el.get_text(strip=True) if time_el else ""
                href = link_el.get("href", "") if link_el else ""
                link = absolute_url(href, self.url)

                if not name:
                    continue

                day, date, time_ = parse_date_time(raw_date, raw_time)
                events.append(Event(day=day, date=date, time=time_, name=name, link=link))
            except Exception:
                continue

        return sort_events(dedup(events))
