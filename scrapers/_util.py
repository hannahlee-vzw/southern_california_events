"""Shared helpers used by multiple scrapers."""
import urllib.parse
from datetime import datetime

from dateutil import parser as dateutil_parser


def absolute_url(href: str, base_url: str) -> str:
    return urllib.parse.urljoin(base_url, href)


def parse_date_time(raw_date: str, raw_time: str) -> tuple[str, str, str]:
    """
    Parse raw date and time strings into (day_of_week, date_MM/DD/YYYY, time_H:MM AM/PM).
    Returns ("UNKNOWN", "UNKNOWN", "UNKNOWN") on failure.
    """
    try:
        dt = dateutil_parser.parse(f"{raw_date} {raw_time}", fuzzy=True)
        return (
            dt.strftime("%A"),
            dt.strftime("%m/%d/%Y"),
            dt.strftime("%-I:%M %p") if hasattr(dt, "hour") else "TBA",
        )
    except Exception:
        pass
    # Try date only
    try:
        dt = dateutil_parser.parse(raw_date, fuzzy=True)
        time_str = "TBA"
        if raw_time:
            try:
                t = dateutil_parser.parse(raw_time, fuzzy=True)
                time_str = t.strftime("%I:%M %p").lstrip("0")
            except Exception:
                time_str = raw_time.strip() or "TBA"
        return dt.strftime("%A"), dt.strftime("%m/%d/%Y"), time_str
    except Exception:
        return "UNKNOWN", "UNKNOWN", raw_time.strip() or "TBA"


def dedup(events: list) -> list:
    """Remove duplicate events by (date, name), preserving order."""
    seen: set[tuple[str, str]] = set()
    result = []
    for ev in events:
        key = (ev.date, ev.name.lower().strip())
        if key not in seen:
            seen.add(key)
            result.append(ev)
    return result


def sort_events(events: list) -> list:
    """Sort events by date ascending; unparseable dates go to the end."""
    def sort_key(ev):
        try:
            return datetime.strptime(ev.date, "%m/%d/%Y")
        except ValueError:
            return datetime.max
    return sorted(events, key=sort_key)
