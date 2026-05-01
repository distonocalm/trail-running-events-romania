import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, RawEvent

ROMANIAN_MONTHS = {
    "ianuarie": 1, "februarie": 2, "martie": 3, "aprilie": 4,
    "mai": 5, "iunie": 6, "iulie": 7, "august": 8,
    "septembrie": 9, "octombrie": 10, "noiembrie": 11, "decembrie": 12,
}


class RunMapScraper(BaseScraper):
    name = "RunMap.ro"
    base_url = "https://runmap.ro/events"

    def scrape(self) -> list[RawEvent]:
        response = httpx.get(self.base_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        events = []

        for card in soup.find_all("article", class_="event-card"):
            badge = card.find("span", class_="type-badge")
            if not badge:
                img = card.find("img", class_="thumb-img")
                data_type = img.get("data-type", "") if img else ""
                if data_type.upper() != "TRAIL":
                    continue
            else:
                badge_text = badge.get_text(strip=True).upper()
                if badge_text != "TRAIL":
                    continue

            title_link = card.select_one("h3.event-title a.event-link")
            if not title_link:
                continue

            name = title_link.get_text(strip=True)
            href = title_link.get("href", "")
            event_url = f"https://runmap.ro{href}" if href else None

            time_tag = card.find("time")
            date_start = None
            if time_tag and time_tag.get("datetime"):
                try:
                    date_start = date.fromisoformat(time_tag["datetime"])
                except ValueError:
                    pass
            if not date_start:
                date_start = self._parse_date_text(card)
            if not date_start:
                continue

            location, county = self._extract_location(card)

            chips = card.find_all("span", class_="race-chip")
            distances = []
            for chip in chips:
                try:
                    km = float(chip.get_text(strip=True))
                    distances.append({"km": km})
                except ValueError:
                    continue

            thumb = card.find("img", class_="thumb-img")
            image_url = thumb.get("src") if thumb else None

            safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            external_id = f"runmap-{safe_name}-{date_start.isoformat()}"

            events.append(
                RawEvent(
                    name=name,
                    date_start=date_start,
                    location=location,
                    county=county,
                    distances=distances if distances else None,
                    event_url=event_url,
                    image_url=image_url,
                    external_id=external_id,
                    raw_data={"source": self.name},
                )
            )

        return events

    def _parse_date_text(self, card) -> date | None:
        text = card.get_text(" ", strip=True)
        match = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
        if match:
            day, month_name, year = int(match.group(1)), match.group(2).lower(), int(match.group(3))
            month = ROMANIAN_MONTHS.get(month_name)
            if month:
                return date(year, month, day)
        return None

    def _extract_location(self, card) -> tuple[str | None, str | None]:
        meta_spans = card.find_all("span", class_="meta")
        for span in meta_spans:
            if span.find(string=re.compile("📍")):
                parts = span.find_all("span")
                location_parts = []
                county = None
                for part in parts:
                    if part.get("aria-hidden"):
                        continue
                    if "text-secondary" in (part.get("class") or []):
                        inner = part.find("span")
                        if inner:
                            county = inner.get_text(strip=True)
                    else:
                        location_parts.append(part.get_text(strip=True))
                location = " ".join(location_parts).strip() if location_parts else None
                return location, county
        return None, None
