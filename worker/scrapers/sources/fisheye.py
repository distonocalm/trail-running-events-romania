import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, RawEvent

ROMANIAN_MONTHS = {
    "IANUARIE": 1,
    "FEBRUARIE": 2,
    "MARTIE": 3,
    "APRILIE": 4,
    "MAI": 5,
    "IUNIE": 6,
    "IULIE": 7,
    "AUGUST": 8,
    "SEPTEMBRIE": 9,
    "OCTOMBRIE": 10,
    "NOIEMBRIE": 11,
    "DECEMBRIE": 12,
}

TRAIL_KEYWORDS = ("alergare", "trail")
SKIP_KEYWORDS = ("neconfirmată", "amânat", "amanat")


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


class FisheyeScraper(BaseScraper):
    name = "Fisheye.ro"
    base_url = "https://fisheye.ro/calendar-competitional-2026/"

    def scrape(self) -> list[RawEvent]:
        response = httpx.get(self.base_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        response.encoding = "utf-8"
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table")
        if not table:
            return []

        tbody = table.find("tbody")
        rows = tbody.find_all("tr") if tbody else table.find_all("tr")

        # First pass: group multi-row events
        # A row with no logo in col 1 is a continuation of the previous event
        grouped_rows: list[list] = []
        for row in rows:
            cells = row.find_all("td")
            if not cells:
                continue
            # Check if col 1 has an image (logo) — primary row
            has_logo = bool(cells[0].find("img")) if cells else False
            if has_logo or not grouped_rows:
                grouped_rows.append([cells])
            else:
                grouped_rows[-1].append(cells)

        events = []
        for cell_groups in grouped_rows:
            primary = cell_groups[0]
            if len(primary) < 4:
                continue

            # --- Sport type filter ---
            # Column 2 contains event name + sport type text
            col2_text = primary[1].get_text(separator=" ", strip=True).lower()
            if not any(kw in col2_text for kw in TRAIL_KEYWORDS):
                continue

            # --- Name & event URL ---
            name_tag = primary[1].find("h3")
            if name_tag:
                name_link = name_tag.find("a")
                name = name_link.get_text(strip=True) if name_link else name_tag.get_text(strip=True)
                event_url = name_link["href"] if name_link and name_link.has_attr("href") else None
            else:
                name = primary[1].get_text(strip=True)
                event_url = None

            if not name:
                continue

            # --- Image URL from logo column (col 1) ---
            img_tag = primary[0].find("img")
            image_url = None
            if img_tag:
                image_url = img_tag.get("src") or img_tag.get("data-src")

            # --- Location & Date from col 4 ---
            col4_text = primary[3].get_text(separator="\n", strip=True)

            # Skip unconfirmed / postponed
            col4_lower = col4_text.lower()
            if any(kw in col4_lower for kw in SKIP_KEYWORDS):
                continue

            # Also check continuation rows for extra dates/locations
            for extra_cells in cell_groups[1:]:
                if len(extra_cells) >= 4:
                    col4_text += "\n" + extra_cells[3].get_text(separator="\n", strip=True)

            parsed_date = self._parse_date(col4_text)
            if not parsed_date:
                continue

            location = self._parse_location(col4_text)

            # --- Distances from col 3 ---
            distances_parts = [primary[2].get_text(separator=" ", strip=True)]
            for extra_cells in cell_groups[1:]:
                if len(extra_cells) >= 3:
                    distances_parts.append(extra_cells[2].get_text(separator=" ", strip=True))
            distances = self._parse_distances(" ".join(distances_parts))

            external_id = f"fisheye-{_slugify(name)}-{parsed_date.isoformat()}"

            events.append(
                RawEvent(
                    name=name,
                    date_start=parsed_date,
                    location=location,
                    distances=distances if distances else None,
                    event_url=event_url,
                    image_url=image_url,
                    external_id=external_id,
                    raw_data={
                        "source": self.name,
                        "raw_col4": col4_text,
                    },
                )
            )

        return events

    def _parse_date(self, text: str) -> date | None:
        """Parse a date from column 4 text. Format: DD MONTHNAME YYYY (uppercase Romanian)."""
        pattern = r"(\d{1,2})\s+([A-ZĂÎȘȚ]+)\s+(\d{4})"
        match = re.search(pattern, text)
        if not match:
            return None
        day = int(match.group(1))
        month_name = match.group(2).upper()
        year = int(match.group(3))
        month = ROMANIAN_MONTHS.get(month_name)
        if not month:
            return None
        try:
            return date(year, month, day)
        except ValueError:
            return None

    def _parse_location(self, text: str) -> str | None:
        """Extract location from column 4 text (everything before the date)."""
        pattern = r"(\d{1,2})\s+[A-ZĂÎȘȚ]+\s+\d{4}"
        match = re.search(pattern, text)
        if match:
            location = text[: match.start()].strip().strip(",").strip()
            return location if location else None
        return text.strip() if text.strip() else None

    def _parse_distances(self, text: str) -> list[dict]:
        """Parse distances from bullet-separated text like '▪️ Cros 7 km ▪️ Semi 21.6 km'."""
        distances = []
        # Split on bullet markers (▪️ or ▪ or •)
        parts = re.split(r"[▪️▪•]", text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            match = re.search(r"([\d.,]+)\s*km", part, re.IGNORECASE)
            if match:
                km_str = match.group(1).replace(",", ".")
                try:
                    distances.append({"label": part.strip(), "km": float(km_str)})
                except ValueError:
                    pass
        return distances
