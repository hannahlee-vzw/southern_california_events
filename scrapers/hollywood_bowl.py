"""
Hollywood Bowl — https://www.hollywoodbowl.com/events/performances?Venue=Hollywood+Bowl&Season=upcoming

Rendering: JS-rendered React app.
Strategy: Playwright headless Chromium; all events load in a single request (no pagination).

Structure:
  div.performance-card                           ← card
    div.performance-card__anchor[data-day]       ← ISO date e.g. "2026-05-30"
    div.details > div.info
      p.name-container > a.name                  ← title link (full URL)
        span.supporting-acts                     ← supporting acts (optional)
      div.date > div.date-text                   ← "Sat, May 30"
      p.time                                     ← "8:00PM"
"""
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from playwright.sync_api import sync_playwright

from .base import BaseScraper, Event
from ._util import dedup, sort_events


class HollywoodBowlScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="networkidle", timeout=30_000)

            try:
                page.wait_for_selector("div.performance-card", timeout=15_000)
            except Exception:
                browser.close()
                return events

            soup = BeautifulSoup(page.content(), "html.parser")
            browser.close()

        for card in soup.select("div.performance-card"):
            try:
                anchor = card.select_one("div.performance-card__anchor")
                name_link = card.select_one("a.name")
                support_el = card.select_one("span.supporting-acts")
                time_el = card.select_one("p.time")

                if not name_link:
                    continue

                # Extract name without the nested supporting-acts span
                if support_el:
                    support_text = support_el.get_text(separator=", ", strip=True)
                    support_el.decompose()
                else:
                    support_text = ""
                name = name_link.get_text(strip=True)
                if support_text:
                    name = f"{name} – {support_text}"

                iso_date = anchor.get("data-day", "") if anchor else ""
                raw_time = time_el.get_text(strip=True) if time_el else ""

                day_str, date_str, time_str = _parse(iso_date, raw_time)
                link = name_link.get("href", "")

                events.append(Event(day=day_str, date=date_str, time=time_str, name=name, link=link))
            except Exception:
                continue

        return sort_events(dedup(events))


def _parse(iso_date: str, raw_time: str) -> tuple[str, str, str]:
    if raw_time and "tba" in raw_time.lower():
        raw_time = ""

    try:
        dt = dateutil_parser.parse(iso_date)
        day_str = dt.strftime("%A")
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
