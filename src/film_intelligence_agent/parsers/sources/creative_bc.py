from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.parsers.base import SourceParser
from film_intelligence_agent.parsers.sources.common import clean_candidate_title
from film_intelligence_agent.utils.quality import is_probable_project_title


class CreativeBCParser(SourceParser):
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(html, "lxml")
        items: list[ExtractedFilm] = []
        seen_titles: set[str] = set()
        for row in soup.select("table tr"):
            cells = row.select("td, th")
            if len(cells) < 2:
                continue
            title_cell = cells[0]
            title_link = title_cell.select_one("a")
            title = clean_candidate_title(title_link.get_text(" ", strip=True) if title_link else title_cell.get_text(" ", strip=True))
            title = title.split(" - ")[0].strip()
            if not is_probable_project_title(title):
                continue
            metadata = " ".join(cell.get_text(" ", strip=True) for cell in cells[1:])
            if not metadata.strip():
                continue
            normalized = title.lower()
            if normalized in seen_titles:
                continue
            seen_titles.add(normalized)
            items.append(
                ExtractedFilm(
                    title=title,
                    source_name=source_meta["name"],
                    source_url=source_meta["url"],
                    source_tier=source_meta["tier"],
                    source_type=source_meta["source_type"],
                    status="production",
                    confidence_score=88,
                    date_detected=datetime.utcnow(),
                    country="Canada",
                    region="Canada",
                    province_or_state="British Columbia",
                    budget_text="Unknown",
                    notes="Extracted from Creative BC production table row.",
                )
            )
        return items
