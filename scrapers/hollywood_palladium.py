"""
Hollywood Palladium — https://www.hollywoodpalladium.com/shows

Rendering: Static HTML (Live Nation venue template).
Strategy: requests; events are embedded as schema.org JSON-LD, no HTML parsing needed.

Structure:
  <script type="application/ld+json">                ← one block per event
    {"@type": "MusicEvent",
     "name": "...",                                   ← event name
     "startDate": "2026-08-21T20:00:00-07:00",         ← ISO 8601 with offset
     "url": "https://www.ticketmaster.com/..."}        ← ticket link
"""
import json
import re

import requests
from dateutil import parser as dateutil_parser

from .base import BaseScraper, Event
from ._util import dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}

LD_JSON_RE = re.compile(
    r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S
)

EXCLUDE_KEYWORDS: list[str] = []


def _is_excluded(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in EXCLUDE_KEYWORDS)


class HollywoodPalladiumScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        events: list[Event] = []
        resp = requests.get(self.url, headers=HEADERS, timeout=20)
        resp.raise_for_status()

        for block in LD_JSON_RE.findall(resp.text):
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue

            if data.get("@type") != "MusicEvent":
                continue

            try:
                name = data.get("name", "").strip()
                if not name or _is_excluded(name):
                    continue

                link = data.get("url", "") or self.url

                day_str, date_str, time_str = _parse(data.get("startDate", ""))
                events.append(Event(day=day_str, date=date_str, time=time_str, name=name, link=link))
            except Exception:
                continue

        return sort_events(dedup(events))


def _parse(raw_start: str) -> tuple[str, str, str]:
    try:
        dt = dateutil_parser.parse(raw_start)
        return dt.strftime("%A"), dt.strftime("%m/%d/%Y"), dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return "TBA", "TBA", "TBA"
