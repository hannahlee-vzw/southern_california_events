from dataclasses import dataclass


@dataclass
class VenueConfig:
    name: str
    url: str
    scraper_module: str  # e.g. "scrapers.sofi"


VENUES: list[VenueConfig] = [
    VenueConfig(
        name="SoFi Stadium",
        url="https://www.sofistadium.com/events",
        scraper_module="scrapers.sofi",
    ),
    VenueConfig(
        name="Intuit Dome",
        url="https://www.intuitdome.com/events/event-schedule",
        scraper_module="scrapers.intuit_dome",
    ),
    VenueConfig(
        name="Kia Forum",
        url="https://www.thekiaforum.com/events",
        scraper_module="scrapers.kia_forum",
    ),
    VenueConfig(
        name="Dignity Health Sports Park",
        url="https://www.dignityhealthsportspark.com/events",
        scraper_module="scrapers.dignity_health",
    ),
    VenueConfig(
        name="Rose Bowl Stadium",
        url="https://www.rosebowlstadium.com/events/calendar/list",
        scraper_module="scrapers.rose_bowl",
    ),
    VenueConfig(
        name="Crypto.com Arena",
        url="https://www.cryptoarena.com/events",
        scraper_module="scrapers.crypto_arena",
    ),
    VenueConfig(
        name="L.A. Memorial Coliseum",
        url="https://www.lacoliseum.com/events",
        scraper_module="scrapers.coliseum",
    ),
    VenueConfig(
        name="LA Convention Center",
        url="https://www.laconventioncenter.com/events",
        scraper_module="scrapers.convention_center",
    ),
    VenueConfig(
        name="Dodger Stadium",
        url="https://www.mlb.com/dodgers/schedule",
        scraper_module="scrapers.dodgers",
    ),
    VenueConfig(
        name="Hollywood Bowl",
        url="https://www.hollywoodbowl.com/events/performances?Venue=Hollywood+Bowl&Season=upcoming",
        scraper_module="scrapers.hollywood_bowl",
    ),
]
