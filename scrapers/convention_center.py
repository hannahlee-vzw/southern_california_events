"""
LA Convention Center — https://www.laconventioncenter.com/events

Rendering: JS-rendered CMS with paginated "Load More" button.
Strategy: Playwright headless Chromium; click "Load More" until exhausted.

Structure:
  div.eventItem.entry                    ← card
    div.thumb > a[href]                  ← detail link
    div.info.clearfix
      div.date_wrapper
        div.date                         ← "May 23 - 24, 2026" (plain text range)
        div.presented-by                 ← "Open to Public" (ignored)
      h3.title > a[href]                 ← event name + link

Note: date is a range string — only the start date is extracted.
Note: no time element present for convention events.
"""
import re
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from playwright.sync_api import sync_playwright

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

LOAD_MORE_SELECTOR = "#loadMoreEvents"


class ConventionCenterScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="networkidle", timeout=30_000)

            try:
                page.wait_for_selector("div.eventItem.entry", timeout=15_000)
            except Exception:
                browser.close()
                return events

            while True:
                btn = page.query_selector(LOAD_MORE_SELECTOR)
                if not btn or not btn.is_visible():
                    break
                count_before = len(page.query_selector_all("div.eventItem.entry"))
                btn.scroll_into_view_if_needed()
                btn.click()
                try:
                    page.wait_for_function(
                        f"document.querySelectorAll('div.eventItem.entry').length > {count_before}",
                        timeout=10_000,
                    )
                except Exception:
                    break

            soup = BeautifulSoup(page.content(), "html.parser")
            browser.close()

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

    year_match = re.search(r'\d{4}', raw)
    year = year_match.group() if year_match else ""

    start = raw.split(" - ")[0].strip()

    if year and year not in start:
        start = f"{start} {year}"

    try:
        dt = dateutil_parser.parse(start, fuzzy=True)
        return dt.strftime("%A"), dt.strftime("%m/%d/%Y")
    except Exception:
        return "TBA", "TBA"
