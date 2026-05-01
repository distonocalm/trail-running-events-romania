import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, RawEvent

ROMANIAN_MONTHS = {
    "ian": 1, "feb": 2, "mar": 3, "apr": 4,
    "mai": 5, "iun": 6, "iul": 7, "aug": 8,
    "sep": 9, "oct": 10, "noi": 11, "dec": 12,
}


class EliteRunningScraper(BaseScraper):
    name = "EliteRunning.ro"
    base_url = "https://eliterunning.ro/calendar-competitii-2026/"

    def scrape(self) -> list[RawEvent]:
        response = httpx.get(self.base_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table")
        if not table:
            return []

        rows = table.find("tbody").find_all("tr") if table.find("tbody") else []
        events = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 7:
                continue

            event_type = cells[3].get_text(strip=True).lower()
            if event_type != "trail":
                continue

            name_cell = cells[0]
            name_link = name_cell.find("a")
            name = name_link.get_text(strip=True) if name_link else name_cell.get_text(strip=True)

            website_cell = cells[6]
            website_link = website_cell.find("a")
            event_url = website_link["href"] if website_link and website_link.has_attr("href") else None

            location = cells[1].get_text(strip=True)
            distances_text = cells[2].get_text(strip=True)
            date_text = cells[4].get_text(strip=True)

            parsed_date = self._parse_date(date_text)
            if not parsed_date:
                continue

            distances = self._parse_distances(distances_text)

            external_id = f"eliterunning-{name.lower().replace(' ', '-')}-{parsed_date.isoformat()}"

            events.append(
                RawEvent(
                    name=name,
                    date_start=parsed_date,
                    location=location,
                    distances=distances,
                    event_url=event_url,
                    external_id=external_id,
                    raw_data={
                        "source": self.name,
                        "organizer": cells[5].get_text(strip=True),
                        "type": event_type,
                    },
                )
            )

        return events

    def _parse_date(self, date_text: str) -> date | None:
        match = re.match(r"(\d{1,2})-(\w{3})-(\d{4})", date_text)
        if not match:
            return None
        day = int(match.group(1))
        month_abbr = match.group(2).lower()
        year = int(match.group(3))
        month = ROMANIAN_MONTHS.get(month_abbr)
        if not month:
            return None
        return date(year, month, day)

    def _parse_distances(self, text: str) -> list[dict]:
        distances = []
        for part in text.split(","):
            part = part.strip()
            match = re.search(r"([\d.]+)\s*km", part, re.IGNORECASE)
            if match:
                distances.append({"km": float(match.group(1))})
        return distances
