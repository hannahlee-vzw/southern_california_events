from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Event:
    day: str    # e.g. "Saturday"
    date: str   # e.g. "06/14/2026"
    time: str   # e.g. "7:30 PM" or "TBD"
    name: str
    link: str   # absolute URL


@dataclass
class VenueResult:
    venue_name: str
    events: list[Event]


class BaseScraper(ABC):
    def __init__(self, url: str) -> None:
        self.url = url

    @abstractmethod
    def scrape(self) -> list[Event]:
        """Fetch the events page and return parsed events sorted by date."""
