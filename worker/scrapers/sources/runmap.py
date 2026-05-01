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

        # Event cards link to /events/{slug}-{year}
        event_links = soup.find_all("a", href=re.compile(r"^/events/[^/]+-\d{4}$"))

        for link in event_links:
            card = link

            # Filter for TRAIL events only
            type_badge = card.find(string=re.compile(r"^TRAIL$"))
            if not type_badge:
                # Also check for elements whose text is TRAIL
                badges = card.find_all(string=lambda t: t and t.strip() == "TRAIL")
                if not badges:
                    continue

            # Event URL
            href = link.get("href", "")
            event_url = f"https://runmap.ro{href}" if href else None

            # Name — derive from the slug (strip trailing -YYYY)
            slug_match = re.search(r"/events/(.+)-(\d{4})$", href)
            if not slug_match:
                continue
            slug = slug_match.group(1)
            year_from_slug = int(slug_match.group(2))

            # Prefer a visible heading/title inside the card
            name = self._extract_name(card, slug)

            # Date — text after 📅
            date_start = self._extract_date(card, year_from_slug)
            if not date_start:
                continue

            # Location and county — text after 📍
            location, county = self._extract_location(card)

            # Distances — numbers after "Curse:"
            distances = self._extract_distances(card)

            # Cover image
            img_tag = card.find("img")
            image_url = img_tag.get("src") if img_tag else None

            # external_id
            safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            external_id = f"runmap-{safe_name}-{date_start.isoformat()}"

            events.append(
                RawEvent(
                    name=name,
                    date_start=date_start,
                    location=location,
                    county=county,
                    distances=distances,
                    event_url=event_url,
                    image_url=image_url,
                    external_id=external_id,
                    raw_data={
                        "source": self.name,
                        "slug": slug,
                    },
                )
            )

        return events

    def _extract_name(self, card, slug: str) -> str:
        # Try common heading tags first
        for tag in ("h1", "h2", "h3", "h4", "strong", "b"):
            el = card.find(tag)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        # Fall back to humanising the slug
        return slug.replace("-", " ").title()

    def _extract_date(self, card, fallback_year: int) -> date | None:
        text = card.get_text(" ", strip=True)
        # Look for "📅 <day> <month_name> <year>" pattern
        match = re.search(
            r"📅\s*(\d{1,2})\s+(\w+)\s+(\d{4})",
            text,
        )
        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))
            month = ROMANIAN_MONTHS.get(month_name)
            if month:
                return date(year, month, day)

        # Fallback: day + month without explicit year
        match = re.search(r"📅\s*(\d{1,2})\s+(\w+)", text)
        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            month = ROMANIAN_MONTHS.get(month_name)
            if month:
                return date(fallback_year, month, day)

        return None

    def _extract_location(self, card) -> tuple[str | None, str | None]:
        text = card.get_text(" ", strip=True)
        match = re.search(r"📍\s*(.+?)(?:\s{2,}|$)", text)
        if not match:
            return None, None

        location_text = match.group(1).strip()

        # County is in parentheses: "Târgoviște (DAMBOVITA)"
        county = None
        county_match = re.search(r"\(([^)]+)\)", location_text)
        if county_match:
            county = county_match.group(1).strip()

        return location_text, county

    def _extract_distances(self, card) -> list[dict] | None:
        text = card.get_text(" ", strip=True)
        match = re.search(r"Curse:\s*([\d.\s]+)", text)
        if not match:
            return None

        distances_text = match.group(1).strip()
        distances = []
        for part in distances_text.split():
            try:
                km = float(part)
                distances.append({"km": km})
            except ValueError:
                continue

        return distances if distances else None
