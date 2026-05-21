"""
Intuit Dome — https://www.intuitdome.com/events

Rendering: JavaScript.
Strategy: Playwright headless Chromium.

TODO (after inspecting live site):
  - Confirm CSS selectors for event cards, title, date, time, link.
  - Check whether pagination or infinite scroll is used and handle accordingly.
"""
from playwright.sync_api import sync_playwright

from .base import BaseScraper, Event
from ._util import absolute_url, parse_date_time, dedup, sort_events


class IntuitDomeScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="networkidle", timeout=30_000)

            cards = page.query_selector_all(".event-card")  # PLACEHOLDER

            for card in cards:
                try:
                    name_el = card.query_selector(".event-title")   # PLACEHOLDER
                    date_el = card.query_selector(".event-date")    # PLACEHOLDER
                    time_el = card.query_selector(".event-time")    # PLACEHOLDER
                    link_el = card.query_selector("a")              # PLACEHOLDER

                    name = name_el.inner_text().strip() if name_el else ""
                    raw_date = date_el.inner_text().strip() if date_el else ""
                    raw_time = time_el.inner_text().strip() if time_el else ""
                    href = link_el.get_attribute("href") if link_el else ""
                    link = absolute_url(href or "", self.url)

                    if not name:
                        continue

                    day, date, time_ = parse_date_time(raw_date, raw_time)
                    events.append(Event(day=day, date=date, time=time_, name=name, link=link))
                except Exception:
                    continue

            browser.close()

        return sort_events(dedup(events))
