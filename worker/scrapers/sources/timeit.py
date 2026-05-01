import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, RawEvent

ROMANIAN_MONTHS = {
    "Ianuarie": 1, "Februarie": 2, "Martie": 3, "Aprilie": 4,
    "Mai": 5, "Iunie": 6, "Iulie": 7, "August": 8,
    "Septembrie": 9, "Octombrie": 10, "Noiembrie": 11, "Decembrie": 12,
}

DATE_PATTERN = re.compile(r"^(\d{1,2})(?:-(\d{1,2}))?\.?\s*")


class TimeItScraper(BaseScraper):
    name = "Time-iT.ro"
    base_url = "https://time-it.ro/evenimente-2026/"

    def scrape(self) -> list[RawEvent]:
        response = httpx.get(self.base_url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        events = []
        year = 2026

        for col in soup.find_all("div", class_="wpb_column"):
            sep = col.find("div", class_="vc_text_separator")
            if not sep:
                continue
            month_name = sep.get_text(strip=True)
            month_num = ROMANIAN_MONTHS.get(month_name)
            if not month_num:
                continue

            content = col.find("div", class_="wpb_text_column")
            if not content:
                continue

            for p in content.find_all("p"):
                text = p.get_text(strip=True)
                date_match = DATE_PATTERN.match(text)
                if not date_match:
                    continue

                day_start = int(date_match.group(1))
                day_end = int(date_match.group(2)) if date_match.group(2) else None

                try:
                    date_start = date(year, month_num, day_start)
                except ValueError:
                    continue

                date_end_val = None
                if day_end is not None:
                    end_month = month_num + 1 if day_end < day_start else month_num
                    end_year = year + 1 if end_month > 12 else year
                    if end_month > 12:
                        end_month = 1
                    try:
                        date_end_val = date(end_year, end_month, day_end)
                    except ValueError:
                        pass

                links = p.find_all("a")
                if not links:
                    continue

                for link in links:
                    name = link.get_text(strip=True)
                    if not name:
                        continue
                    event_url = link.get("href")

                    safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                    external_id = f"timeit-{safe_name}-{date_start.isoformat()}"

                    events.append(
                        RawEvent(
                            name=name,
                            date_start=date_start,
                            date_end=date_end_val,
                            event_url=event_url,
                            external_id=external_id,
                            raw_data={"source": self.name},
                        )
                    )

        return events
