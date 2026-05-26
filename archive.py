import json
import pathlib
from datetime import date, datetime

from scrapers.base import Event, VenueResult


def update_archive(current_results: list[VenueResult], docs_dir: pathlib.Path) -> list[dict]:
    """Read previous snapshot, archive aged-out events, write updated archive + new snapshot."""
    today = date.today()
    prev_snapshot = _load_json(docs_dir / "current_snapshot.json")
    archive = _load_json(docs_dir / "past_events.json")

    current_keys = {_make_key(vr.venue_name, ev) for vr in current_results for ev in vr.events}
    archive_keys = {e["key"] for e in archive}

    for ev_dict in prev_snapshot:
        key = ev_dict["key"]
        if key in current_keys or key in archive_keys:
            continue
        ev_date = _parse_date(ev_dict["date"])
        if ev_date and ev_date < today:
            ev_dict["archived_on"] = today.isoformat()
            archive.append(ev_dict)
            archive_keys.add(key)

    _save_json(docs_dir / "past_events.json", archive)

    snapshot = [_event_to_dict(vr.venue_name, ev) for vr in current_results for ev in vr.events]
    _save_json(docs_dir / "current_snapshot.json", snapshot)

    return _sort_descending(archive)


def _load_json(path: pathlib.Path) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_json(path: pathlib.Path, data: list[dict]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _make_key(venue_name: str, event: Event) -> str:
    return "|".join([venue_name.lower().strip(), event.date.strip(), event.name.lower().strip()])


def _event_to_dict(venue_name: str, event: Event) -> dict:
    return {
        "key": _make_key(venue_name, event),
        "venue": venue_name,
        "day": event.day,
        "date": event.date,
        "time": event.time,
        "name": event.name,
        "link": event.link,
    }


def _parse_date(date_str: str) -> date | None:
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y").date()
    except (ValueError, AttributeError):
        return None


def _sort_descending(archive: list[dict]) -> list[dict]:
    def sort_key(ev: dict):
        d = _parse_date(ev.get("date", ""))
        return d if d else date.min

    return sorted(archive, key=sort_key, reverse=True)
