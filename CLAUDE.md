# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the scrapers

```bash
# Install dependencies (once)
pip install -r requirements.txt
playwright install chromium

# Run venue events scrapers → docs/index.html + docs/events.xlsx
python main.py

# Run DownDetector scraper → docs/downdetector.html
python scrape_downdetector.py
```

`main.py` outputs `docs/index.html` and `docs/events.xlsx`. `scrape_downdetector.py` outputs `docs/downdetector.html`. Both write directly into `docs/` and are committed to git. No files are created in the project root.

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

## DownDetector scraper

**Script:** [scrape_downdetector.py](scrape_downdetector.py) — standalone, does not use `main.py` or `config.VENUES`.

**Target:** Verizon service page on DownDetector (JS-rendered, use Playwright).

**Data captured per run:**
- Current status label (e.g. `Normal`, `Warning`, `Danger`)
- Current report count (number of user reports in the last hour)
- Problem breakdown (percentages by category: Network, Internet, Phone, etc.)
- Up to 20 most recent user comments with timestamps
- Scrape timestamp (written into the page as "Last updated: …")

**Output:** writes `docs/downdetector.html` — Bootstrap 5, shared nav header linking back to `index.html`, status badge, report count, problem breakdown table, comments table.

**Navigation:** Both `docs/index.html` and `docs/downdetector.html` include a shared nav bar at the top with links to each other so users can switch between pages.

## Outputs

- **Excel** ([exporter.py](exporter.py)): writes `docs/events.xlsx` directly — one sheet per venue, bold dark-blue header row, frozen first row, auto-fitted columns, hyperlinked links. No local copy is produced.
- **LA Events HTML** ([html_generator.py](html_generator.py)): writes `docs/index.html` — Bootstrap 5 + Tablesort, one tab per venue. Venue URL for each tab's "Venue Page" column comes from `config.VENUES`.
- **DownDetector HTML** ([scrape_downdetector.py](scrape_downdetector.py)): writes `docs/downdetector.html` — Bootstrap 5, Verizon outage snapshot with status, counts, and comments.

## Automation

Two separate GitHub Actions workflows run on independent schedules:

| Workflow | File | Schedule | Script |
|----------|------|----------|--------|
| Scrape Events | [.github/workflows/scrape.yml](.github/workflows/scrape.yml) | Every day 8 AM PT | `main.py` |
| Scrape DownDetector | [.github/workflows/scrape_downdetector.yml](.github/workflows/scrape_downdetector.yml) | Every hour | `scrape_downdetector.py` |

Each workflow commits only its own output file(s) to `docs/`. GitHub Pages serves both pages automatically.

To trigger manually: **Actions → [workflow name] → Run workflow**.

To change a schedule, edit the `cron` expression in the relevant workflow file.
