from __future__ import annotations

from film_intelligence_agent.domain.types import ExtractedFilm


def compute_data_confidence(film: ExtractedFilm) -> int:
    score = film.confidence_score
    if film.country == "Canada":
        score += 5
    if film.imdb_id:
        score += 5
    return max(0, min(100, score))


def compute_opportunity(film: ExtractedFilm) -> tuple[int, dict]:
    breakdown: dict[str, int] = {}
    breakdown["region"] = 25 if film.region == "Canada" else 15 if film.region else 5
    breakdown["budget_fit"] = 15 if "<$10M" in film.budget_text or "Low-budget" in film.budget_text else 5
    breakdown["stage"] = 15 if film.status in {"production", "greenlit", "funded"} else 0
    score = sum(breakdown.values())
    return max(0, min(100, score)), breakdown
