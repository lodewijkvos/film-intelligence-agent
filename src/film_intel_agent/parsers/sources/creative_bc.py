from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intel_agent.domain.types import ExtractedFilm
from film_intel_agent.parsers.base import SourceParser


class CreativeBCParser(SourceParser):
    def parse(self, fetch_result, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(fetch_result.html or "", "lxml")
        items: list[ExtractedFilm] = []
        for row in soup.select("tr, li, article"):
            text = row.get_text(" ", strip=True)
            if not text:
                continue
            title = text.split(" - ")[0].split("|")[0].strip()
            if len(title) < 3:
                continue
            items.append(
                ExtractedFilm(
                    title=title,
                    source_name=source_meta["name"],
                    source_url=source_meta["url"],
                    source_tier=source_meta["tier"],
                    source_type=source_meta["source_type"],
                    status="production",
                    confidence_score=90,
                    date_detected=datetime.utcnow(),
                    country="Canada",
                    region="Canada",
                    province_or_state="British Columbia",
                    budget_text="Unknown",
                    notes="Creative BC parser extracted a production candidate from list markup.",
                )
            )
        return items
