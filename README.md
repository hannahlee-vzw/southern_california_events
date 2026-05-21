# LA Venue Event Scraper

Scrapes upcoming event listings from 8 Los Angeles-area venues and publishes them to a shared team website updated every week automatically.

**Team website:** `https://<username>.github.io/<repo-name>/`

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
| GitHub Pages website | One tab per venue, sortable columns, updated every Monday |
| `docs/events.xlsx` | Downloadable Excel file linked from the website |

Each event row contains: **Day · Date · Time · Event Name · Link**

---

## Local Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Run the scraper manually:

```bash
python main.py
```

This writes `events.xlsx` locally and regenerates `docs/index.html`. Commit and push `docs/` to update the live website.

---

## Automatic Weekly Updates

A GitHub Actions workflow ([`.github/workflows/scrape.yml`](.github/workflows/scrape.yml)) runs every **Monday at 8:00 AM PT** and automatically commits the updated `docs/` folder. No action needed after initial setup.

To trigger a run manually: **Actions → Scrape Events → Run workflow**

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
