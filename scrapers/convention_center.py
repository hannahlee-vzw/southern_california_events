"""
LA Convention Center — https://www.lacclink.com/events

Rendering: Likely static HTML (Momentus / venue management CMS).
Strategy: requests + BeautifulSoup; upgrade to Playwright if needed.

TODO (after inspecting live site):
  - Confirm the correct domain (lacclink.com vs laconventioncenter.com).
  - Inspect raw HTML to confirm events are present without JS.
  - Confirm CSS selectors for event cards, title, date, time, link.
  - Handle pagination if present.
"""
import requests
from bs4 import BeautifulSoup

from .base import BaseScraper, Event
from ._util import absolute_url, parse_date_time, dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}


class ConventionCenterScraper(BaseScraper):
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
