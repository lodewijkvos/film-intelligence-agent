from __future__ import annotations

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.parsers.base import SourceParser


class OntarioCreatesParser(SourceParser):
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        # This program page describes eligibility and deadlines, not funded titles.
        # We intentionally emit nothing unless a future source page exposes named projects.
        return []
