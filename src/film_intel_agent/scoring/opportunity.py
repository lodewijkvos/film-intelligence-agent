from __future__ import annotations

from film_intel_agent.domain.types import ExtractedFilm


def compute_data_confidence(film: ExtractedFilm) -> int:
    score = film.confidence_score
    if film.country == "Canada":
        score += 5
    if film.imdb_id:
        score += 5
    return max(0, min(100, score))


def compute_opportunity_score(film: ExtractedFilm) -> tuple[int, dict]:
    score = 0
    breakdown: dict[str, int] = {}

    if film.region == "Canada":
        breakdown["region_fit"] = 25
    elif film.region in {"North America", "United States"}:
        breakdown["region_fit"] = 15
    elif film.region == "Europe":
        breakdown["region_fit"] = 8
    else:
        breakdown["region_fit"] = 3

    if film.budget_text == "Unknown":
        breakdown["budget_fit"] = 5
    elif "<$10M" in film.budget_text or "Low-budget" in film.budget_text:
        breakdown["budget_fit"] = 15
    else:
        breakdown["budget_fit"] = 8

    if film.status in {"production", "greenlit", "funded"}:
        breakdown["stage_signal"] = 15

    if film.country == "Canada":
        breakdown["canada_priority"] = 20

    score = sum(breakdown.values())
    return max(0, min(100, score)), breakdown
