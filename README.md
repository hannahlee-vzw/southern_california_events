# LA Venue Event Scraper

Scrapes upcoming event listings from 8 Los Angeles-area venues and publishes them to a shared website updated every week automatically. Also tracks Verizon service outage reports from DownDetector, updated hourly.

**LA Events:** https://hannahlee-vzw.github.io/southern_california_events/
**DownDetector (Verizon):** https://hannahlee-vzw.github.io/southern_california_events/downdetector.html

---

## Venues

- SoFi Stadium
- Intuit Dome
- Kia Forum
- Dignity Health Sports Park
- Rose Bowl Stadium
- Crypto.com Arena
- L.A. Memorial Coliseum
- LA Convention Center

---

## Output

| Format | Description |
|--------|-------------|
| `docs/index.html` | LA Events — one tab per venue, sortable columns, updated every Monday |
| `docs/downdetector.html` | Verizon DownDetector snapshot — status, report count, problem breakdown, updated hourly |
| `docs/events.xlsx` | Downloadable Excel file linked from the events website |

Each event row contains: **Day · Date · Time · Event Name · Link**

---

## Local Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Run the venue events scraper:

```bash
python main.py
```

Run the DownDetector scraper:

```bash
python scrape_downdetector.py
```

Each script writes its output directly to `docs/`. Commit and push `docs/` to update the live website.

---

## Automatic Updates

| Workflow | Schedule | Script | Output |
|----------|----------|--------|--------|
| [Scrape Events](.github/workflows/scrape.yml) | Every Monday 8:00 AM PT | `main.py` | `docs/index.html`, `docs/events.xlsx` |
| [Scrape DownDetector](.github/workflows/scrape_downdetector.yml) | Every hour | `scrape_downdetector.py` | `docs/downdetector.html` |

To trigger a run manually: **Actions → [workflow name] → Run workflow**

---

## One-Time GitHub Pages Setup

1. Push this repo to GitHub
2. Go to **Settings → Pages**
3. Source: **Deploy from a branch** → Branch: `main`, Folder: `/docs` → **Save**
4. Your team URL will appear at the top of the Pages settings within ~1 minute

---

## Adding or Updating a Venue

1. Add or edit an entry in [`config.py`](config.py)
2. Create or update the corresponding scraper in [`scrapers/`](scrapers/)
3. Each scraper file has `# PLACEHOLDER` comments marking the CSS selectors that need to be filled in by inspecting the live venue website

See [`SPEC.md`](SPEC.md) for full technical documentation.
