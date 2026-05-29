"""
Dignity Health Sports Park — https://www.dignityhealthsportspark.com/events

Rendering: JS-rendered CMS with paginated "Load More" button.
Strategy: Playwright headless Chromium; click "Load More" until exhausted.

Structure (identical to SoFi — no tagline element):
  div.eventItem.entry                    ← card
    div.thumb > a[href]                  ← detail link
    div.info.clearfix
      div.date
        span.m-date__singleDate
          span.m-date__month             ← "June "
          span.m-date__day               ← "12"
          span.m-date__year              ← ", 2026"
        span.time                        ← "7:30 PM"
      h3.title.long_title
        a[href]                          ← event name + link
"""
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from playwright.sync_api import sync_playwright

from .base import BaseScraper, Event
from ._util import absolute_url, dedup, sort_events

LOAD_MORE_SELECTOR = "#loadMoreEvents"


class DignityHealthScraper(BaseScraper):
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
                month_el = card.select_one("span.m-date__month")
                day_el   = card.select_one("span.m-date__day")
                year_el  = card.select_one("span.m-date__year")
                time_el  = card.select_one("span.time")
                link_el  = card.select_one("h3.title a")

                if not title_el:
                    continue

                name = title_el.get_text(strip=True)

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
        return "TBA", "TBA", raw_time or "TBA"

    time_str = raw_time if raw_time else "TBA"
    try:
        t = dateutil_parser.parse(raw_time, fuzzy=True)
        time_str = t.strftime("%I:%M %p").lstrip("0")
    except Exception:
        pass

    return day_str, date_str, time_str
