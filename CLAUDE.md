# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the scraper

```bash
# Install dependencies (once)
pip install -r requirements.txt
playwright install chromium

# Run all scrapers and generate outputs
python main.py
```

Outputs: `docs/index.html` and `docs/events.xlsx` — both written directly into `docs/` and committed to git. No Excel file is created in the project root.

## Architecture

**Data flow:** `config.VENUES` → one scraper per venue → `list[VenueResult]` → `exporter.write()` + `html_generator.generate()`

**Key types** (defined in [scrapers/base.py](scrapers/base.py)):
- `Event(day, date, time, name, link)` — one row in the output
- `VenueResult(venue_name, events)` — one sheet / tab in the output
- `BaseScraper` — abstract base; each venue scraper implements `scrape() -> list[Event]`

**Scraper loading** is dynamic: `main.py` reads `venue.scraper_module` from `config.py` and uses `importlib` to find the `BaseScraper` subclass at runtime. Adding a venue = add a row to `config.VENUES` and create a matching file in `scrapers/`.

**Scraping strategies** vary by site:
- JS-rendered (most venues): Playwright headless Chromium — see [scrapers/sofi.py](scrapers/sofi.py) as the reference pattern
- Static HTML: `requests` + BeautifulSoup — see [scrapers/rose_bowl.py](scrapers/rose_bowl.py) as the reference pattern

**Shared helpers** in [scrapers/_util.py](scrapers/_util.py): `parse_date_time()`, `dedup()`, `sort_events()`, `absolute_url()`.

## Implementing a new venue scraper

1. Add a `VenueConfig` entry to `config.VENUES` in [config.py](config.py).
2. Create `scrapers/<name>.py` with a class that extends `BaseScraper`.
3. Inspect the live site HTML to find real CSS selectors (each existing scraper has `# PLACEHOLDER` comments marking where real selectors go).
4. Call `sort_events(dedup(events))` before returning.

All existing scrapers are scaffolded but have **placeholder selectors** — they will return 0 events until the real selectors are filled in.

## Outputs

- **Excel** ([exporter.py](exporter.py)): writes `docs/events.xlsx` directly — one sheet per venue, bold dark-blue header row, frozen first row, auto-fitted columns, hyperlinked links. No local copy is produced.
- **HTML** ([html_generator.py](html_generator.py)): writes `docs/index.html` — Bootstrap 5 + Tablesort, one tab per venue. Venue URL for each tab's "Venue Page" column comes from `config.VENUES`.

## Automation

GitHub Actions ([.github/workflows/scrape.yml](.github/workflows/scrape.yml)) runs the scraper every Monday at 8 AM PT and commits `docs/` back to the repo. GitHub Pages then serves `docs/index.html` automatically. To trigger manually: **Actions → Scrape Events → Run workflow**.

To change the schedule, edit the `cron` expression in the workflow file.
