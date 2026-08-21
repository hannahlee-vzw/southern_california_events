"""
Hollywood Palladium — https://www.hollywoodpalladium.com/shows

Rendering: Next.js. The server-rendered page (and its schema.org JSON-LD)
           only includes the first page of shows (~2 months out); the rest
           loads client-side via infinite scroll against Live Nation's own
           public content API.
Strategy: call that content API directly with requests — no browser needed,
          and it returns the full show list in one paginated series of calls.

API: https://content.livenationapi.com/v1/venues/{venue_id}/events
     Auth: "x-api-key" header — a public key shipped in the site's own JS
     bundle (not a secret; the same key the page's own frontend uses).
     VENUE_ID is Live Nation/Ticketmaster's internal id for this venue,
     found embedded in the page's React payload.

Fallback: if the content API ever breaks (e.g. the key rotates), fall back
          to parsing the JSON-LD on the static page — fewer events, but
          keeps the scraper from silently returning 0.
"""
import json
import re

import requests
from dateutil import parser as dateutil_parser

from .base import BaseScraper, Event
from ._util import dedup, sort_events

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"}

API_URL = "https://content.livenationapi.com/v1/venues/{venue_id}/events"
API_KEY = "AbDS2tuO3ONIZJVK5p6Q2tiPRYX34Ie9RzQ1zlIb"
VENUE_ID = "KovZpZAEAlaA"
PAGE_SIZE = 100

LD_JSON_RE = re.compile(
    r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S
)

EXCLUDE_KEYWORDS: list[str] = []


def _is_excluded(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in EXCLUDE_KEYWORDS)


class HollywoodPalladiumScraper(BaseScraper):
    def scrape(self) -> list[Event]:
        try:
            events = self._scrape_api()
        except Exception:
            events = self._scrape_ld_json()
        return sort_events(dedup(events))

    def _scrape_api(self) -> list[Event]:
        events: list[Event] = []
        offset = 0
        url = API_URL.format(venue_id=VENUE_ID)

        while True:
            resp = requests.get(
                url,
                headers={**HEADERS, "x-api-key": API_KEY},
                params={"offset": offset, "limit": PAGE_SIZE},
                timeout=20,
            )
            resp.raise_for_status()
            page = resp.json()
            if not page:
                break

            for item in page:
                try:
                    name = item.get("name", "").strip()
                    if not name or _is_excluded(name):
                        continue
                    link = item.get("url", "") or self.url
                    day_str, date_str, time_str = _parse(item.get("datetime_local", ""))
                    events.append(Event(day=day_str, date=date_str, time=time_str, name=name, link=link))
                except Exception:
                    continue

            if len(page) < PAGE_SIZE:
                break
            offset += PAGE_SIZE

        if not events:
            raise RuntimeError("content API returned no events")
        return events

    def _scrape_ld_json(self) -> list[Event]:
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

        return events


def _parse(raw: str) -> tuple[str, str, str]:
    try:
        dt = dateutil_parser.parse(raw)
        return dt.strftime("%A"), dt.strftime("%m/%d/%Y"), dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return "TBA", "TBA", "TBA"
