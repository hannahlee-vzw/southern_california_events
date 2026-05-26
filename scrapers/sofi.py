"""
SoFi Stadium — https://www.sofistadium.com/events

Rendering: JS-rendered CMS with paginated "Load More" button.
Strategy: Playwright headless Chromium; click "Load More" until exhausted.

Structure:
  div.eventItem.entry                    ← card
    div.thumb > a[href]                  ← detail link
    div.info.clearfix
      div.date
        span.m-date__singleDate
          span.m-date__month             ← "June "
          span.m-date__day               ← "12"
          span.m-date__year              ← ", 2026"
        span.time                        ← "6 PM"
      h3.title.title-withTagline
        span.hoverline > a[href]         ← title text + link
      h4.tagline                         ← subtitle (optional)
"""
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from playwright.sync_api import sync_playwright

from .base import BaseScraper, Event
from ._util import absolute_url, dedup

EXCLUDE_KEYWORDS = [
    "book your flight",
    "stadium tour",
]


def _is_excluded(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in EXCLUDE_KEYWORDS)


LOAD_MORE_SELECTOR = "#loadMoreEvents"


class SofiScraper(BaseScraper):
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

            # Click "Load More" until the button disappears or no new events load
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
                title_el   = card.select_one("h3.title a")
                tagline_el = card.select_one("h4.tagline")
                month_el   = card.select_one("span.m-date__month")
                day_el     = card.select_one("span.m-date__day")
                year_el    = card.select_one("span.m-date__year")
                time_el    = card.select_one("span.time")
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

                # Fallback: if sub-spans are absent, read the parent singleDate text directly
                if not raw_date:
                    single_el = card.select_one("span.m-date__singleDate")
                    if single_el:
                        raw_date = single_el.get_text(separator=" ", strip=True)

                raw_time = time_el.get_text(strip=True) if time_el else ""

                # Fallback: some cards use plain div.date text like "Sun., Feb. 14, 2027 / Time TBA"
                if not raw_date:
                    date_el = card.select_one("div.date")
                    if date_el:
                        parts = date_el.get_text(strip=True).split("/", 1)
                        raw_date = parts[0].strip()
                        if not raw_time and len(parts) > 1:
                            raw_time = parts[1].strip()

                day_str, date_str, time_str = _parse(raw_date, raw_time)

                href = link_el.get("href", "") if link_el else ""
                link = absolute_url(href, self.url)

                events.append(Event(day=day_str, date=date_str, time=time_str, name=name, link=link))
            except Exception:
                continue

        return dedup(events)


def _parse(raw_date: str, raw_time: str) -> tuple[str, str, str]:
    # Treat any "TBA" variant as no time known
    if raw_time and "tba" in raw_time.lower():
        raw_time = ""

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
