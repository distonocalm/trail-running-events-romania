import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, RawEvent

ROMANIAN_MONTHS = {
    "IANUARIE": 1, "FEBRUARIE": 2, "MARTIE": 3, "APRILIE": 4,
    "MAI": 5, "IUNIE": 6, "IULIE": 7, "AUGUST": 8,
    "SEPTEMBRIE": 9, "OCTOMBRIE": 10, "NOIEMBRIE": 11, "DECEMBRIE": 12,
}


class FisheyeScraper(BaseScraper):
    name = "Fisheye.ro"
    base_url = "https://fisheye.ro/calendar-competitional-2026/"

    def scrape(self) -> list[RawEvent]:
        response = httpx.get(self.base_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")
        events = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 7:
                continue

            sport_text = cells[2].get_text(" ", strip=True).lower()
            if "alergare" not in sport_text and "trail" not in sport_text:
                continue

            name_tag = cells[1].find("h3")
            if not name_tag:
                continue
            name_link = name_tag.find("a")
            name = name_link.get_text(strip=True) if name_link else name_tag.get_text(strip=True)
            event_url = name_link["href"] if name_link and name_link.has_attr("href") else None

            date_text = cells[6].get_text(" ", strip=True)
            if "neconfirmat" in date_text.lower() or "amânat" in date_text.lower():
                continue
            parsed_date = self._parse_date(date_text)
            if not parsed_date:
                continue

            location = cells[4].get_text(strip=True) or None

            distances = self._parse_distances(cells[3].get_text(" ", strip=True))

            img_tag = cells[0].find("img")
            image_url = (img_tag.get("src") or img_tag.get("data-src")) if img_tag else None

            safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            external_id = f"fisheye-{safe_name}-{parsed_date.isoformat()}"

            events.append(
                RawEvent(
                    name=name,
                    date_start=parsed_date,
                    location=location,
                    distances=distances if distances else None,
                    event_url=event_url,
                    image_url=image_url,
                    external_id=external_id,
                    raw_data={"source": self.name},
                )
            )

        return events

    def _parse_date(self, text: str) -> date | None:
        match = re.search(r"(\d{1,2})\s+([A-ZĂÎȘȚ]+)\s+(\d{4})", text.upper())
        if not match:
            return None
        day = int(match.group(1))
        month = ROMANIAN_MONTHS.get(match.group(2))
        year = int(match.group(3))
        if not month:
            return None
        try:
            return date(year, month, day)
        except ValueError:
            return None

    def _parse_distances(self, text: str) -> list[dict]:
        distances = []
        parts = re.split(r"[▪️▪•]", text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            match = re.search(r"([\d.,]+)\s*km", part, re.IGNORECASE)
            if match:
                km_str = match.group(1).replace(",", ".")
                try:
                    distances.append({"km": float(km_str)})
                except ValueError:
                    pass
        return distances
