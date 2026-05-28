import html
import pathlib
from datetime import datetime

from scrapers.base import VenueResult
from config import VENUES

DOCS_DIR = pathlib.Path("docs")


def generate(results: list[VenueResult], past_events: list[dict] | None = None) -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    page = _build_html(results, past_events or [])
    (DOCS_DIR / "index.html").write_text(page, encoding="utf-8")
    print(f"Generated docs/index.html  ({len(results)} venue tabs)")


def _venue_id(name: str) -> str:
    return name.lower().replace(" ", "-").replace(".", "").replace(",", "").replace("'", "")


def _venue_url(venue_name: str) -> str:
    for v in VENUES:
        if v.name == venue_name:
            return v.url
    return "#"


def _event_rows(events: list) -> str:
    if not events:
        return '<tr><td colspan="4" class="text-center text-muted fst-italic">No events found</td></tr>'
    rows = []
    for ev in events:
        name_cell = f'<a href="{html.escape(ev.link)}" target="_blank" rel="noopener">{html.escape(ev.name)}</a>'
        rows.append(
            f"<tr>"
            f"<td>{html.escape(ev.day)}</td>"
            f"<td>{html.escape(ev.date)}</td>"
            f"<td>{html.escape(ev.time)}</td>"
            f"<td>{name_cell}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _tab_nav(results: list[VenueResult]) -> str:
    items = []
    for i, vr in enumerate(results):
        active = ' active' if i == 0 else ''
        selected = 'true' if i == 0 else 'false'
        vid = _venue_id(vr.venue_name)
        count = len(vr.events)
        items.append(
            f'<li class="nav-item" role="presentation">'
            f'<button class="nav-link{active}" id="tab-{vid}" data-bs-toggle="tab" '
            f'data-bs-target="#pane-{vid}" type="button" role="tab" '
            f'aria-controls="pane-{vid}" aria-selected="{selected}">'
            f'{html.escape(vr.venue_name)} <span class="badge bg-secondary">{count}</span>'
            f'</button></li>'
        )
    return "\n".join(items)


def _tab_panes(results: list[VenueResult]) -> str:
    panes = []
    for i, vr in enumerate(results):
        active = ' show active' if i == 0 else ''
        vid = _venue_id(vr.venue_name)
        venue_url = _venue_url(vr.venue_name)
        rows = _event_rows(vr.events)
        panes.append(f"""
        <div class="tab-pane fade{active}" id="pane-{vid}" role="tabpanel" aria-labelledby="tab-{vid}">
          <div class="d-flex justify-content-between align-items-center mt-3 mb-2">
            <span class="text-muted small">{len(vr.events)} event(s)</span>
            <a href="{html.escape(venue_url)}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-secondary">
              View venue site &rarr;
            </a>
          </div>
          <div class="table-responsive">
            <table class="table table-striped table-hover table-sm sortable" id="tbl-{vid}">
              <thead class="table-dark">
                <tr>
                  <th>Day</th><th>Date</th><th>Time</th><th>Event Name</th>
                </tr>
              </thead>
              <tbody>
                {rows}
              </tbody>
            </table>
          </div>
        </div>""")
    return "\n".join(panes)


def _past_event_rows(past_events: list[dict]) -> str:
    if not past_events:
        return '<tr><td colspan="5" class="text-center text-muted fst-italic">No archived events yet</td></tr>'
    rows = []
    for ev in past_events:
        name_cell = f'<a href="{html.escape(ev["link"])}" target="_blank" rel="noopener">{html.escape(ev["name"])}</a>'
        rows.append(
            f'<tr data-venue="{html.escape(ev["venue"])}">'
            f"<td>{html.escape(ev['venue'])}</td>"
            f"<td>{html.escape(ev['day'])}</td>"
            f"<td>{html.escape(ev['date'])}</td>"
            f"<td>{html.escape(ev['time'])}</td>"
            f"<td>{name_cell}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _build_html(results: list[VenueResult], past_events: list[dict] = []) -> str:
    timestamp = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    total = sum(len(vr.events) for vr in results)
    tab_nav = _tab_nav(results)
    tab_panes = _tab_panes(results)

    past_rows = _past_event_rows(past_events)
    past_count = len(past_events)

    unique_venues = sorted({ev["venue"] for ev in past_events}) if past_events else []
    venue_options = "\n".join(
        f'<option value="{html.escape(v)}">{html.escape(v)}</option>'
        for v in unique_venues
    )

    past_nav_item = (
        f'<li class="nav-item" role="presentation">'
        f'<button class="nav-link" id="tab-past-events" data-bs-toggle="tab" '
        f'data-bs-target="#pane-past-events" type="button" role="tab" '
        f'aria-controls="pane-past-events" aria-selected="false">'
        f'Past Events <span class="badge bg-secondary">{past_count}</span>'
        f'</button></li>'
    )
    past_pane = f"""
        <div class="tab-pane fade" id="pane-past-events" role="tabpanel" aria-labelledby="tab-past-events">
          <div class="d-flex justify-content-between align-items-center mt-3 mb-2">
            <span class="text-muted small">{past_count} archived event(s) across all venues, most recent first</span>
            <div class="d-flex align-items-center gap-2">
              <label for="past-venue-filter" class="text-muted small mb-0">Filter by venue:</label>
              <select id="past-venue-filter" class="form-select form-select-sm" style="width:auto">
                <option value="">All Venues</option>
                {venue_options}
              </select>
            </div>
          </div>
          <div class="table-responsive">
            <table class="table table-striped table-hover table-sm sortable" id="tbl-past-events">
              <thead class="table-dark">
                <tr>
                  <th>Venue</th><th>Day</th><th>Date</th><th>Time</th><th>Event Name</th>
                </tr>
              </thead>
              <tbody>
                {past_rows}
              </tbody>
            </table>
          </div>
        </div>"""
    archived_label = f' &middot; {past_count} archived' if past_count else ''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LA Venue Events</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <style>
    body {{ font-family: system-ui, sans-serif; }}
    .nav-tabs {{ flex-wrap: wrap; }}
    th[aria-sort] {{ cursor: pointer; user-select: none; }}
    th[aria-sort="ascending"]::after  {{ content: " ▲"; }}
    th[aria-sort="descending"]::after {{ content: " ▼"; }}
  </style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
  <span class="navbar-brand mb-0 h6">LA Monitors</span>
  <div class="navbar-nav flex-row gap-2">
    <a class="nav-link active fw-semibold" href="index.html">LA Events</a>
    <a class="nav-link text-white-50" href="downdetector.html">DownDetector</a>
  </div>
</nav>
<div class="container-fluid py-4">
  <div class="d-flex justify-content-between align-items-start mb-3">
    <div>
      <h1 class="h3 mb-0">LA Venue Events</h1>
      <p class="text-muted small mb-0">{total} total events across {len(results)} venues{archived_label}</p>
    </div>
    <a href="events.xlsx" download class="btn btn-outline-success btn-sm">
      &#8681; Download Excel
    </a>
  </div>

  <ul class="nav nav-tabs" id="venueTabs" role="tablist">
    {tab_nav}
    {past_nav_item}
  </ul>
  <div class="tab-content" id="venueTabContent">
    {tab_panes}
    {past_pane}
  </div>

  <footer class="mt-4 pt-3 border-top text-muted small">
    Last updated: {timestamp}
  </footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.3.0/tablesort.min.js"></script>
<script>
  document.querySelectorAll('table.sortable').forEach(function(table) {{
    try {{ new Tablesort(table); }} catch(e) {{}}
  }});
  function applyPastVenueFilter() {{
    var selected = document.getElementById('past-venue-filter').value;
    document.querySelectorAll('#tbl-past-events tbody tr').forEach(function(row) {{
      row.hidden = !!selected && row.getAttribute('data-venue') !== selected;
    }});
  }}
  document.getElementById('past-venue-filter').addEventListener('change', applyPastVenueFilter);
  document.getElementById('tbl-past-events').addEventListener('afterSort', applyPastVenueFilter);
</script>
</body>
</html>"""
