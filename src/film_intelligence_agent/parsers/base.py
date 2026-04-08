from __future__ import annotations

from abc import ABC, abstractmethod

from film_intelligence_agent.domain.types import ExtractedFilm


class SourceParser(ABC):
    @abstractmethod
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        raise NotImplementedError
