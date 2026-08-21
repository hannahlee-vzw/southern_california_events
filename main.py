import importlib
import json
import pathlib
import sys
import time

import archive as _archive
import config
import exporter
import html_generator
from scrapers.base import Event, VenueResult

RETRY_DELAY_SECONDS = 3


def main() -> int:
    docs_dir = pathlib.Path("docs")
    docs_dir.mkdir(exist_ok=True)
    prev_snapshot = _load_snapshot(docs_dir / "current_snapshot.json")

    results: list[VenueResult] = []

    for venue in config.VENUES:
        print(f"Scraping {venue.name}...", end=" ", flush=True)
        events = _scrape_with_retry(venue)
        if not events:
            fallback = _previous_events(venue.name, prev_snapshot)
            if fallback:
                print(f"0 events after retry — keeping {len(fallback)} from previous run", file=sys.stderr)
                events = fallback
            else:
                print("0 events after retry", file=sys.stderr)
        else:
            print(f"{len(events)} events")
        results.append(VenueResult(venue_name=venue.name, events=events))

    try:
        past_events = _archive.update_archive(results, docs_dir)
        print(f"Archive: {len(past_events)} past events")
    except Exception as exc:
        print(f"WARNING — archive update failed: {exc}", file=sys.stderr)
        past_events = []

    xlsx_path = pathlib.Path("docs/events.xlsx")
    try:
        exporter.write(results, xlsx_path, past_events)
        print(f"\nWrote {xlsx_path}")
    except Exception as exc:
        print(f"ERROR writing Excel: {exc}", file=sys.stderr)
        return 1

    try:
        html_generator.generate(results, past_events)
    except Exception as exc:
        print(f"ERROR generating HTML: {exc}", file=sys.stderr)
        return 1

    total = sum(len(vr.events) for vr in results)
    print(f"\nDone. {total} events total across {len(results)} venues.")
    return 0


def _find_scraper_class(module):
    """Return the first BaseScraper subclass defined in the module."""
    from scrapers.base import BaseScraper
    import inspect
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseScraper) and obj is not BaseScraper:
            return obj
    raise RuntimeError(f"No BaseScraper subclass found in {module.__name__}")


def _scrape_once(venue) -> list[Event]:
    module = importlib.import_module(venue.scraper_module)
    scraper_class = _find_scraper_class(module)
    return scraper_class(venue.url).scrape()


def _scrape_with_retry(venue) -> list[Event]:
    """Scrape a venue, retrying once if the first attempt errors or returns nothing."""
    for attempt in (1, 2):
        try:
            events = _scrape_once(venue)
        except Exception as exc:
            print(f"WARNING (attempt {attempt}) — {exc}", end=" ", file=sys.stderr, flush=True)
            events = []
        if events:
            return events
        if attempt == 1:
            time.sleep(RETRY_DELAY_SECONDS)
    return []


def _load_snapshot(path: pathlib.Path) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _previous_events(venue_name: str, snapshot: list[dict]) -> list[Event]:
    return [
        Event(day=e["day"], date=e["date"], time=e["time"], name=e["name"], link=e["link"])
        for e in snapshot
        if e.get("venue") == venue_name
    ]


if __name__ == "__main__":
    sys.exit(main())
