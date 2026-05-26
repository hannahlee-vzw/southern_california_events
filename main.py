import importlib
import pathlib
import sys

import archive as _archive
import config
import exporter
import html_generator
from scrapers.base import VenueResult


def main() -> int:
    results: list[VenueResult] = []

    for venue in config.VENUES:
        print(f"Scraping {venue.name}...", end=" ", flush=True)
        try:
            module = importlib.import_module(venue.scraper_module)
            scraper_class = _find_scraper_class(module)
            events = scraper_class(venue.url).scrape()
            results.append(VenueResult(venue_name=venue.name, events=events))
            print(f"{len(events)} events")
        except Exception as exc:
            print(f"WARNING — {exc}", file=sys.stderr)
            results.append(VenueResult(venue_name=venue.name, events=[]))

    pathlib.Path("docs").mkdir(exist_ok=True)

    try:
        past_events = _archive.update_archive(results, pathlib.Path("docs"))
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


if __name__ == "__main__":
    sys.exit(main())
