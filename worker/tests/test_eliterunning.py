from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock

import httpx

from scrapers.sources.eliterunning import EliteRunningScraper


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_events_from_html():
    html = (FIXTURES_DIR / "eliterunning.html").read_text()
    scraper = EliteRunningScraper()
    events = scraper.parse_html(html)

    assert len(events) == 2

    assert events[0].name == "Carpathia Trails"
    assert events[0].date_start == date(2026, 7, 4)
    assert events[0].location == "Brașov"
    assert events[0].event_url == "https://carpathiatrails.com"
    assert len(events[0].distances) == 5
    assert events[0].distances[0] == {"km": 6.0}
    assert events[0].distances[4] == {"km": 102.0}


def test_filters_out_road_events():
    html = (FIXTURES_DIR / "eliterunning.html").read_text()
    scraper = EliteRunningScraper()
    events = scraper.parse_html(html)

    names = [e.name for e in events]
    assert "Bucharest Marathon" not in names


def test_parse_distances():
    scraper = EliteRunningScraper()
    distances = scraper._parse_distances("6km, 23km, 36km, 57km, 102km")
    assert distances == [
        {"km": 6.0},
        {"km": 23.0},
        {"km": 36.0},
        {"km": 57.0},
        {"km": 102.0},
    ]


def test_parse_date():
    scraper = EliteRunningScraper()
    assert scraper._parse_date("04-Iul-2026") == date(2026, 7, 4)
    assert scraper._parse_date("15-Oct-2026") == date(2026, 10, 15)


def test_scrape_makes_http_request():
    html = (FIXTURES_DIR / "eliterunning.html").read_text()
    scraper = EliteRunningScraper()

    mock_response = MagicMock()
    mock_response.text = html
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx, "get", return_value=mock_response) as mock_get:
        events = scraper.scrape()
        mock_get.assert_called_once()
        assert len(events) == 2
