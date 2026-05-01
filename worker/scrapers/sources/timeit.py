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

CURRENT_YEAR = 2026


class TimeItScraper(BaseScraper):
    name = "Time-iT.ro"
    base_url = "https://time-it.ro/evenimente-2026/"

    def scrape(self) -> list[RawEvent]:
        response = httpx.get(self.base_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        response.encoding = "utf-8"
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        events = []
        current_month: int | None = None

        # Walk all elements in document order looking for month headers and event lines
        for element in soup.find_all(["h2", "h3", "h4", "strong", "p", "li"]):
            text = element.get_text(strip=True)

            # Check if this element is a month header
            month_num = self._detect_month(text)
            if month_num is not None:
                current_month = month_num
                continue

            # Skip if we haven't seen a month yet
            if current_month is None:
                continue

            # Must contain at least one <a> tag (event link)
            links = element.find_all("a", href=True)
            if not links:
                continue

            # Extract the date prefix from the element text before the first link
            day_start, day_end = self._extract_days(text)
            if day_start is None:
                continue

            # Handle multiple events on the same line (separated by "si" / "și")
            for link in links:
                name = link.get_text(strip=True)
                if not name:
                    continue
                event_url = link.get("href") or None

                try:
                    event_date = date(CURRENT_YEAR, current_month, day_start)
                except ValueError:
                    continue

                date_end: date | None = None
                if day_end is not None:
                    # Cross-month date range: end day < start day means it spills to next month
                    end_month = current_month
                    if day_end < day_start:
                        end_month = current_month % 12 + 1
                    try:
                        date_end = date(CURRENT_YEAR, end_month, day_end)
                    except ValueError:
                        date_end = None

                safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                external_id = f"timeit-{safe_name}-{event_date.isoformat()}"

                events.append(
                    RawEvent(
                        name=name,
                        date_start=event_date,
                        date_end=date_end,
                        event_url=event_url,
                        external_id=external_id,
                        raw_data={
                            "source": self.name,
                        },
                    )
                )

        return events

    def _detect_month(self, text: str) -> int | None:
        """Return month number if the text is (or contains) a Romanian month name header."""
        # Normalise: strip whitespace, lowercase
        normalised = text.strip().lower()
        # Exact match or month name as a word within short strings (e.g. "Ianuarie 2026")
        for month_name, num in ROMANIAN_MONTHS.items():
            if re.fullmatch(rf"{month_name}[\s\d]*", normalised):
                return num
        return None

    def _extract_days(self, text: str) -> tuple[int | None, int | None]:
        """Parse day range from patterns like '31-1.', '15-16.', '7.' at the start of a line."""
        # Range: DD-DD. or D-D.
        match = re.match(r"(\d{1,2})-(\d{1,2})\.", text.strip())
        if match:
            return int(match.group(1)), int(match.group(2))

        # Single day: DD. or D.
        match = re.match(r"(\d{1,2})\.", text.strip())
        if match:
            return int(match.group(1)), None

        return None, None
