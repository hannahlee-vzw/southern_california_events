"""
Standalone scraper for Verizon outage data from DownDetector.
Outputs docs/downdetector.html. Run directly: python scrape_downdetector.py
"""

import html
import pathlib
import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

VERIZON_URL = "https://downdetector.com/status/verizon/"
DOCS_DIR = pathlib.Path("docs")

# Keywords used to filter user comments to Southern California only.
# Checked case-insensitively as substrings of the comment body.
SOCAL_KEYWORDS = {
    # Region names
    "socal", "so cal", "southern california", "inland empire", "coachella valley",
    "san fernando valley", "san gabriel valley", "south bay", "the valley",
    "downtown la", "downtown los angeles", "dtla", "west side", "eastside",
    "high desert", "low desert", "antelope valley", "conejo valley",
    "santa ynez valley", "simi hills", "pacific coast",
    # Counties
    "los angeles county", "orange county", "san diego county",
    "riverside county", "san bernardino county", "ventura county",
    # LA County — cities
    "los angeles", "pasadena", "glendale", "burbank", "torrance", "long beach",
    "compton", "inglewood", "hawthorne", "gardena", "carson", "downey", "norwalk",
    "west covina", "covina", "whittier", "cerritos", "lakewood", "bellflower",
    "paramount", "lynwood", "south gate", "pomona", "el monte", "santa monica",
    "beverly hills", "malibu", "santa clarita", "thousand oaks", "simi valley",
    "oxnard", "ventura", "lancaster", "palmdale", "victorville",
    "van nuys", "northridge", "woodland hills", "encino", "sherman oaks",
    "studio city", "north hollywood", "west hollywood", "culver city",
    "redondo beach", "manhattan beach", "hermosa beach", "el segundo", "lawndale",
    "glendora", "azusa", "covina", "san dimas", "la verne", "claremont",
    "arcadia", "monrovia", "duarte", "temple city", "san gabriel", "alhambra",
    "monterey park", "rosemead", "south el monte", "pico rivera", "montebello",
    "bell", "bell gardens", "huntington park", "maywood", "south pasadena",
    "diamond bar", "rowland heights", "hacienda heights", "la puente",
    "la mirada", "santa fe springs", "artesia", "lomita", "san pedro",
    "wilmington", "harbor city", "rancho palos verdes", "palos verdes",
    "rolling hills", "avalon", "catalina",
    # LA County — neighborhoods
    "hollywood", "los feliz", "silver lake", "echo park", "highland park",
    "eagle rock", "atwater village", "boyle heights", "east los angeles",
    "koreatown", "mid-city", "leimert park", "crenshaw", "watts", "willowbrook",
    "westwood", "brentwood", "bel air", "pacific palisades", "mar vista",
    "palms", "venice", "playa del rey", "playa vista", "century city",
    "hancock park", "miracle mile", "fairfax", "los feliz", "griffith",
    "sun valley", "sylmar", "arleta", "panorama city", "mission hills",
    "granada hills", "porter ranch", "chatsworth", "canoga park", "reseda",
    "tarzana", "winnetka", "west hills",
    # Orange County — additional cities/areas
    "anaheim", "santa ana", "irvine", "huntington beach", "fullerton",
    "garden grove", "costa mesa", "mission viejo", "lake forest", "laguna hills",
    "laguna niguel", "laguna beach", "san clemente", "dana point", "tustin",
    "yorba linda", "placentia", "brea", "la habra", "buena park", "cypress",
    "seal beach", "westminster", "fountain valley", "stanton", "los alamitos",
    "aliso viejo", "rancho santa margarita", "las flores", "coto de caza",
    "ladera ranch", "foothill ranch", "portola hills",
    # San Diego County — cities and neighborhoods
    "san diego", "chula vista", "oceanside", "escondido", "el cajon", "vista",
    "carlsbad", "encinitas", "del mar", "la jolla", "national city", "san ysidro",
    "santee", "la mesa", "poway", "fallbrook", "temecula",
    "mission valley", "mission hills", "north park", "hillcrest", "normal heights",
    "kensington", "college area", "city heights", "barrio logan", "golden hill",
    "south park", "north hills", "miramar", "mira mesa", "scripps ranch",
    "rancho bernardo", "rancho penasquitos", "carmel valley", "solana beach",
    "coronado", "imperial beach", "spring valley", "lemon grove", "lakeside",
    "ramona", "valley center", "bonsall", "san marcos", "san marcos",
    "gaslamp", "old town", "balboa park", "point loma",
    # Riverside County — additional
    "riverside", "temecula", "murrieta", "hemet", "palm springs", "palm desert",
    "coachella", "indio", "moreno valley", "corona", "norco", "perris", "menifee",
    "wildomar", "lake elsinore", "canyon lake", "san jacinto", "beaumont",
    "banning", "desert hot springs", "cathedral city", "rancho mirage",
    "la quinta", "bermuda dunes", "thousand palms",
    # San Bernardino County — additional
    "san bernardino", "fontana", "rancho cucamonga", "ontario", "upland",
    "claremont", "montclair", "chino", "chino hills", "yucaipa", "redlands",
    "hesperia", "apple valley", "barstow", "needles", "twentynine palms",
    "yucca valley", "big bear", "lake arrowhead", "running springs",
    "wrightwood", "rialto", "colton",
    # Ventura County — additional
    "camarillo", "moorpark", "newbury park", "agoura hills", "westlake village",
    "oak park", "port hueneme", "fillmore", "santa paula", "ojai",
    # Popular landmarks and destinations
    "disneyland", "universal studios", "six flags", "knott's berry farm",
    "knotts berry farm", "legoland", "seaworld", "san diego zoo",
    "hollywood bowl", "sofi stadium", "dodger stadium", "rose bowl",
    "angel stadium", "petco park", "crypto.com arena", "staples center",
    "griffith observatory", "griffith park", "santa monica pier",
    "venice beach", "rodeo drive", "sunset strip", "sunset boulevard",
    "mulholland", "pacific coast highway", "pch",
    "joshua tree", "death valley", "big bear lake",
    # Airports
    "lax airport", "los angeles international", "john wayne airport",
    "ontario airport", "long beach airport", "hollywood burbank", "burbank airport",
}

NAV_BAR = """<nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
  <span class="navbar-brand mb-0 h6">LA Monitors</span>
  <div class="navbar-nav flex-row gap-2">
    <a class="nav-link text-white-50" href="index.html">LA Events</a>
    <a class="nav-link active fw-semibold" href="downdetector.html">DownDetector</a>
  </div>
</nav>"""


@dataclass
class DownDetectorSnapshot:
    status: str = "Unknown"
    report_count: str = "—"
    problems: list[tuple[str, str]] = field(default_factory=list)
    comments: list[tuple[str, str]] = field(default_factory=list)
    scraped_at: str = ""
    error: str = ""


def scrape() -> DownDetectorSnapshot:
    snap = DownDetectorSnapshot(
        scraped_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page.goto(VERIZON_URL, wait_until="load", timeout=30_000)
            page.wait_for_timeout(4_000)
            soup = BeautifulSoup(page.content(), "html.parser")
            browser.close()

        snap.status = _parse_status(soup)
        snap.report_count = _parse_report_count(soup)
        snap.problems = _parse_problems(soup)
        snap.comments = [c for c in _parse_comments(soup) if _is_socal_comment(c[1])]
    except Exception:
        snap.error = traceback.format_exc()

    return snap


def _parse_status(soup: BeautifulSoup) -> str:
    # h1 reads "User reports show <span>no current problems</span> with Verizon"
    el = soup.select_one("span.text-inherit.font-medium")
    text = el.get_text(strip=True).lower() if el else ""
    if not text:
        # Fallback: scan aria-label on the chart element
        chart = soup.select_one("[aria-label*='Reports chart']")
        text = (chart.get("aria-label", "") if chart else "").lower()
    if "no" in text and "problem" in text:
        return "Normal"
    if "warning" in text:
        return "Warning"
    if "danger" in text or "outage" in text or "problem" in text:
        return "Danger"
    return "Unknown"


def _parse_report_count(soup: BeautifulSoup) -> str:
    # aria-label: "Reports chart for the last 24 hours with a peak of 143 reports, status: ..."
    el = soup.select_one("[aria-label*='Reports chart']")
    if el:
        m = re.search(r"peak of (\d+) reports", el.get("aria-label", ""))
        if m:
            return m.group(1)
    return "—"


def _parse_problems(soup: BeautifulSoup) -> list[tuple[str, str]]:
    # aria-label: "5G Home Internet: 41 percent of reports, 410 reports"
    results = []
    for item in soup.select("div[role='listitem'][aria-label*='percent of reports']"):
        m = re.match(r"^(.+?):\s*(\d+)\s*percent", item.get("aria-label", ""))
        if m:
            results.append((m.group(1).strip(), f"{m.group(2)}%"))
    return results


def _is_socal_comment(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in SOCAL_KEYWORDS)


def _parse_comments(soup: BeautifulSoup) -> list[tuple[str, str]]:
    results = []
    for item in soup.select("li[data-testid='tweet-item']")[:20]:
        time_el = item.select_one("a[data-testid='tweet-timestamp']")
        msg_el = item.select_one("a[data-testid='tweet-message']")
        time_str = time_el.get_text(strip=True) if time_el else "—"
        body = msg_el.get_text(strip=True) if msg_el else ""
        if body:
            results.append((time_str, body))
    return results


def _status_badge(status: str) -> str:
    classes = {
        "Normal": "bg-success",
        "Warning": "bg-warning text-dark",
        "Danger": "bg-danger",
    }.get(status, "bg-secondary")
    return f'<span class="badge {classes} fs-6 px-3 py-2">{html.escape(status)}</span>'


def _problem_rows(problems: list[tuple[str, str]]) -> str:
    if not problems:
        return '<tr><td colspan="2" class="text-center text-muted fst-italic">No breakdown data available</td></tr>'
    return "\n".join(
        f"<tr><td>{html.escape(label)}</td><td>{html.escape(pct)}</td></tr>"
        for label, pct in problems
    )


def _comment_rows(comments: list[tuple[str, str]]) -> str:
    if not comments:
        return '<tr><td colspan="2" class="text-center text-muted fst-italic">No recent comments</td></tr>'
    return "\n".join(
        f"<tr><td class='text-nowrap text-muted small'>{html.escape(ts)}</td>"
        f"<td>{html.escape(body)}</td></tr>"
        for ts, body in comments
    )


def _build_html(snap: DownDetectorSnapshot) -> str:
    error_banner = ""
    if snap.error:
        error_banner = (
            f'<div class="alert alert-danger mt-3" role="alert">'
            f"<strong>Scrape failed.</strong> Data below may be incomplete or unavailable."
            f"<details class='mt-2'><summary>Error details</summary>"
            f"<pre class='small mt-2'>{html.escape(snap.error)}</pre></details></div>"
        )

    status_badge = _status_badge(snap.status)
    problem_rows = _problem_rows(snap.problems)
    comment_rows = _comment_rows(snap.comments)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DownDetector — Verizon</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <style>
    body {{ font-family: system-ui, sans-serif; }}
  </style>
</head>
<body>
{NAV_BAR}
<div class="container-fluid py-4">
  <div class="d-flex justify-content-between align-items-start mb-3">
    <div>
      <h1 class="h3 mb-0">Verizon — DownDetector</h1>
      <p class="text-muted small mb-0">
        <a href="{html.escape(VERIZON_URL)}" target="_blank" rel="noopener">downdetector.com/status/verizon</a>
      </p>
    </div>
    <div class="text-end">
      {status_badge}
      <p class="text-muted small mt-1 mb-0">Current status</p>
    </div>
  </div>

  {error_banner}

  <div class="row g-4 mb-4">
    <div class="col-md-4">
      <div class="card h-100">
        <div class="card-body text-center">
          <p class="text-muted small mb-1">Reports (last hour)</p>
          <p class="display-4 fw-bold mb-0">{html.escape(snap.report_count)}</p>
        </div>
      </div>
    </div>
    <div class="col-md-8">
      <div class="card h-100">
        <div class="card-header fw-semibold">Problem Breakdown</div>
        <div class="card-body p-0">
          <table class="table table-sm mb-0">
            <thead class="table-dark">
              <tr><th>Category</th><th>Share</th></tr>
            </thead>
            <tbody>
              {problem_rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header fw-semibold">Recent User Reports</div>
    <div class="table-responsive">
      <table class="table table-striped table-hover table-sm mb-0">
        <thead class="table-dark">
          <tr><th style="width:120px">Time</th><th>Comment</th></tr>
        </thead>
        <tbody>
          {comment_rows}
        </tbody>
      </table>
    </div>
  </div>

  <footer class="mt-4 pt-3 border-top text-muted small">
    Last updated: {html.escape(snap.scraped_at)}
    &middot; Source: <a href="{html.escape(VERIZON_URL)}" target="_blank" rel="noopener">DownDetector</a>
  </footer>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""


def write(snap: DownDetectorSnapshot) -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "downdetector.html").write_text(_build_html(snap), encoding="utf-8")


if __name__ == "__main__":
    data = scrape()
    write(data)
    status_note = f"  ERROR: {data.error.splitlines()[0]}" if data.error else ""
    print(
        f"Generated docs/downdetector.html  "
        f"(status: {data.status}, {data.report_count} reports){status_note}"
    )
