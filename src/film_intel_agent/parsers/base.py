from __future__ import annotations

from abc import ABC, abstractmethod

from film_intel_agent.domain.types import ExtractedFilm, RawFetchResult


class SourceParser(ABC):
    @abstractmethod
    def parse(self, fetch_result: RawFetchResult, source_meta: dict) -> list[ExtractedFilm]:
        raise NotImplementedError
