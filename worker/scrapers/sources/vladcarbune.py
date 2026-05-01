import re
from datetime import date

import httpx
from bs4 import BeautifulSoup, Tag

from scrapers.base import BaseScraper, RawEvent

ROMANIAN_MONTHS = {
    "ianuarie": 1,
    "februarie": 2,
    "martie": 3,
    "aprilie": 4,
    "mai": 5,
    "iunie": 6,
    "iulie": 7,
    "august": 8,
    "septembrie": 9,
    "octombrie": 10,
    "noiembrie": 11,
    "decembrie": 12,
}

# Sentinel headers that mark the start of recurring weekly events — stop parsing here
STOP_KEYWORDS = {"marțea", "miercurea", "joia", "vinerea", "sâmbăta", "duminica"}

YEAR = 2026


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _parse_date_range(em_text: str) -> tuple[date, date | None] | None:
    """
    Parse the <em> tag text into a (date_start, date_end | None) tuple.

    Accepted formats (after stripping leading '• '):
      - "Ianuarie 24"          → single day
      - "Februarie 06-07"      → multi-day, same month
    Returns None if the text cannot be parsed.
    """
    # Strip bullet character and surrounding whitespace
    text = em_text.strip().lstrip("•").strip().rstrip(":")

    # Match "MonthName day" or "MonthName day1-day2"
    match = re.match(
        r"([A-Za-zÀ-ÿ]+)\s+(\d{1,2})(?:-(\d{1,2}))?",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    month_name = match.group(1).lower()
    month = ROMANIAN_MONTHS.get(month_name)
    if not month:
        return None

    day_start = int(match.group(2))
    try:
        date_start = date(YEAR, month, day_start)
    except ValueError:
        return None

    date_end = None
    if match.group(3):
        day_end = int(match.group(3))
        try:
            date_end = date(YEAR, month, day_end)
        except ValueError:
            pass

    return date_start, date_end


def _parse_distances(text: str) -> list[dict] | None:
    """Extract km distances from a text fragment like '21km, 15km, 7km'."""
    distances = []
    for part in re.split(r"[,;]", text):
        part = part.strip()
        match = re.search(r"([\d.]+)\s*km", part, re.IGNORECASE)
        if match:
            distances.append({"km": float(match.group(1))})
    return distances if distances else None


class VladCarbuneScraper(BaseScraper):
    name = "vladcarbune.ro"
    base_url = "https://vladcarbune.ro/calendar-evenimente-alergare-2026/"

    def scrape(self) -> list[RawEvent]:
        response = httpx.get(self.base_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        response.encoding = "utf-8"
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")

        # Find the WordPress post content wrapper
        content = soup.find("div", class_=re.compile(r"entry-content|post-content"))
        if not content:
            return []

        events: list[RawEvent] = []

        for element in content.find_all(["p", "li", "h3", "h4"]):
            # Stop at the recurring weekly events section
            if element.name in ("h3", "h4"):
                heading_text = element.get_text(strip=True).lower()
                if any(kw in heading_text for kw in STOP_KEYWORDS):
                    break
                continue

            # Each event paragraph contains an <em> with the date
            em_tag = element.find("em")
            if not em_tag:
                continue

            em_text = em_tag.get_text(strip=True)
            parsed = _parse_date_range(em_text)
            if not parsed:
                continue

            date_start, date_end = parsed

            # Event name and URL come from <strong><a> or just <strong>
            strong_tag = element.find("strong")
            if not strong_tag:
                continue

            a_tag = strong_tag.find("a") if strong_tag else None
            if a_tag and a_tag.has_attr("href"):
                event_name = a_tag.get_text(strip=True)
                event_url = a_tag["href"]
            else:
                event_name = strong_tag.get_text(strip=True)
                event_url = None

            if not event_name:
                continue

            # The remaining text after </strong> contains location and distances
            # Strategy: get full paragraph text, strip the em and strong portions
            full_text = element.get_text(separator=" ")
            # Remove the date portion (em text)
            remainder = full_text.replace(em_text, "", 1)
            # Remove the event name
            remainder = remainder.replace(event_name, "", 1)
            remainder = remainder.strip().lstrip(",").strip()

            # Split on ' - ' or ' – ' to separate location from distances
            dist_sep = re.split(r"\s[-–]\s", remainder, maxsplit=1)
            location_raw = dist_sep[0].strip().strip(",").strip() if dist_sep else ""
            distances_raw = dist_sep[1].strip() if len(dist_sep) > 1 else ""

            location = location_raw if location_raw else None
            distances = _parse_distances(distances_raw) if distances_raw else None

            slug = _slugify(event_name)
            external_id = f"vladcarbune-{slug}-{date_start.isoformat()}"

            events.append(
                RawEvent(
                    name=event_name,
                    date_start=date_start,
                    date_end=date_end,
                    location=location,
                    distances=distances,
                    event_url=event_url,
                    external_id=external_id,
                    raw_data={"source": self.name},
                )
            )

        return events
