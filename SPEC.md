# Event Scraper — Specification

## Overview

A Python command-line application that scrapes upcoming event listings from eight Los Angeles-area venue websites and writes the results to a single Excel workbook. Each venue gets its own worksheet. Each row represents one event.

---

## Output Format

**File:** `events.xlsx` (written to the working directory)

**Workbook structure:** One sheet per venue, named by short venue name (e.g., `SoFi Stadium`, `Intuit Dome`).

**Columns (in order):**

| Column | Header        | Description                                         | Example                        |
|--------|---------------|-----------------------------------------------------|--------------------------------|
| A      | Day           | Full day of the week                                | `Saturday`                     |
| B      | Date          | Date in `MM/DD/YYYY` format                         | `06/14/2026`                   |
| C      | Time          | Local time in `H:MM AM/PM` format; `TBD` if unknown | `7:30 PM`                      |
| D      | Event Name    | Title of the event as listed on the venue site      | `Taylor Swift – Eras Tour`     |
| E      | Link          | Full URL to the event detail page                   | `https://sofistadium.com/...`  |

Rows are sorted by date ascending within each sheet. The header row is bold and frozen.

---

## Venues

| Sheet Name                    | Events Page URL                                                      |
|-------------------------------|----------------------------------------------------------------------|
| SoFi Stadium                  | https://www.sofistadium.com/events                                   |
| Intuit Dome                   | https://www.intuitdome.com/events                                    |
| Kia Forum                     | https://www.theforum.com/events                                      |
| Dignity Health Sports Park    | https://www.dignityhealthsportsparkla.com/events                    |
| Rose Bowl Stadium             | https://www.rosebowlstadium.com/events                               |
| Crypto.com Arena              | https://www.cryptoarena.com/events                                   |
| L.A. Memorial Coliseum        | https://www.lacoliseum.com/events                                    |
| LA Convention Center          | https://www.lacclink.com/events                                      |

> **Note:** Confirm these URLs before implementation — venue sites occasionally restructure. Update `config.py` (see below) without touching scraper logic.

---

## Architecture

```
events/
├── SPEC.md
├── requirements.txt
├── config.py           # Venue definitions (name, URL, scraper class)
├── main.py             # Entry point: orchestrates scraping and Excel export
├── scrapers/
│   ├── __init__.py
│   ├── base.py         # Abstract base class: scrape() -> list[Event]
│   ├── sofi.py
│   ├── intuit_dome.py
│   ├── kia_forum.py
│   ├── dignity_health.py
│   ├── rose_bowl.py
│   ├── crypto_arena.py
│   ├── coliseum.py
│   └── convention_center.py
└── exporter.py         # Writes list[VenueResult] -> events.xlsx
```

### Data model

```python
@dataclass
class Event:
    day: str        # e.g. "Saturday"
    date: str       # e.g. "06/14/2026"
    time: str       # e.g. "7:30 PM" or "TBD"
    name: str
    link: str       # absolute URL

@dataclass
class VenueResult:
    venue_name: str
    events: list[Event]
```

### Base scraper interface

Each venue scraper inherits from `BaseScraper` and implements a single method:

```python
class BaseScraper(ABC):
    def __init__(self, url: str): ...

    @abstractmethod
    def scrape(self) -> list[Event]:
        """Fetch the events page and return parsed events."""
```

`main.py` instantiates every scraper, calls `scrape()`, wraps results in `VenueResult`, and passes the list to `exporter.write()`.

---

## Scraping Strategy

Venue sites vary in how they render event listings. Use the following approach per site type:

### Static HTML (BeautifulSoup)
If the full event list is present in the initial HTML response, parse with `requests` + `BeautifulSoup`.

### JavaScript-rendered (Selenium or Playwright)
If events are loaded dynamically via JavaScript, use a headless browser. Prefer **Playwright** (`playwright.async_api`) with Chromium in headless mode.

### Paginated listings
If events span multiple pages, the scraper must follow pagination until no next-page link exists or a configurable maximum page count is reached (`MAX_PAGES = 20`).

Each scraper should handle its site's specific HTML structure. Expected selectors and notes per venue should be documented as inline comments within the scraper file (added during implementation after inspecting the live site).

---

## Dependencies

```
requests>=2.32
beautifulsoup4>=4.12
playwright>=1.44          # only for JS-rendered sites
openpyxl>=3.1
python-dateutil>=2.9      # flexible date/time parsing
```

Install Playwright browsers separately after `pip install`:
```
playwright install chromium
```

---

## Error Handling

| Scenario                          | Behavior                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| Network timeout or HTTP error     | Log a warning, write an empty sheet with a note row, continue other venues |
| Unable to parse a date/time field | Set the field to `"UNKNOWN"`, log a debug message, keep the row          |
| Event link is relative URL        | Resolve to absolute URL using `urllib.parse.urljoin`                     |
| Duplicate events on same page     | Deduplicate by `(date, name)` before writing                             |
| Output file already exists        | Overwrite without prompting                                              |

All errors are printed to stderr. The program exits with code `0` on completion (even partial), `1` on a fatal error (e.g., cannot write output file).

---

## Execution

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run
python main.py

# Output
# events.xlsx written to current directory
# Console shows per-venue event counts and any warnings
```

Expected console output format:
```
[SoFi Stadium]          23 events
[Intuit Dome]           18 events
[Kia Forum]             31 events
[Dignity Health SP]     12 events
[Rose Bowl Stadium]      8 events
[Crypto.com Arena]      40 events
[L.A. Memorial Col.]     5 events
[LA Convention Ctr]     15 events

Wrote events.xlsx  (152 events total)
```

---

## Automation & Publishing

### How it works

The scraper runs automatically every week via **GitHub Actions** — no local machine required. After each run, the updated `docs/` folder is committed back to the repository and GitHub Pages serves the result at a permanent team URL.

```
Every Monday 8 AM PT
       │
       ▼
GitHub Actions (.github/workflows/scrape.yml)
       │  pip install + playwright install chromium
       │  python main.py
       │    → events.xlsx
       │    → docs/index.html
       │    → docs/events.xlsx
       │  git commit docs/ && git push
       ▼
GitHub Pages
  https://<username>.github.io/<repo-name>/
       │
       ▼
Team bookmarks the URL — always shows latest data
```

### Key files

| File | Purpose |
|------|---------|
| `.github/workflows/scrape.yml` | Defines the scheduled GitHub Actions job |
| `html_generator.py` | Generates `docs/index.html` (Bootstrap 5 + Tablesort) |
| `docs/index.html` | Generated website — committed to git, served by GitHub Pages |
| `docs/events.xlsx` | Downloadable Excel — linked from the website footer |

### One-time setup (do this once)

**1. Create a GitHub repository**

```powershell
# Option A: GitHub CLI
gh repo create events-la --public --source=. --remote=origin --push

# Option B: manual — create repo on github.com, then:
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<username>/events-la.git
git push -u origin main
```

> GitHub Pages is **free for public repos**. Private repos require GitHub Pro/Team.

**2. Enable GitHub Pages**

1. Open the repo on github.com → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, folder: `/docs` → **Save**
4. GitHub will show the live URL after ~1 minute:
   `https://<username>.github.io/events-la/`
5. Share that URL with your team.

**3. Verify the workflow runs**

- Go to the repo → **Actions** → **Scrape Events**
- Click **Run workflow** (manual trigger) to test it immediately
- Confirm the run completes with a green checkmark
- Open the GitHub Pages URL and confirm event data appears

### Schedule

The workflow runs every **Monday at 8:00 AM Pacific Time** (`cron: '0 15 * * 1'`).
To change the schedule, edit the `cron` line in `.github/workflows/scrape.yml`.
A **"Run workflow"** button is also available in the Actions tab for on-demand runs.

### Viewing run logs

If a scrape fails for a venue, the warning is visible in the workflow run log:
**Actions** → **Scrape Events** → click the run → expand the **Run scraper** step.

---

## Out of Scope

- Authentication or ticket purchasing
- Images, prices, or seating charts
- Real-time or scheduled execution (run manually on demand)
- Historical events (only future/current events)
