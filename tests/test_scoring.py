from datetime import datetime

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.services.scoring import compute_data_confidence, compute_opportunity


def test_canadian_confidence_bonus():
    film = ExtractedFilm(
        title="Example",
        source_name="Telefilm",
        source_url="https://example.com",
        source_tier="tier_0_canada_official",
        source_type="canada_official_funder",
        status="funded",
        confidence_score=90,
        date_detected=datetime.utcnow(),
        country="Canada",
        region="Canada",
    )
    assert compute_data_confidence(film) == 95


def test_opportunity_breakdown_has_budget():
    film = ExtractedFilm(
        title="Example",
        source_name="Playback",
        source_url="https://example.com",
        source_tier="tier_2_canada_trade",
        source_type="canada_trade",
        status="production",
        confidence_score=70,
        date_detected=datetime.utcnow(),
        country="Canada",
        region="Canada",
        budget_text="<$10M",
    )
    score, breakdown = compute_opportunity(film)
    assert score >= 40
    assert breakdown["budget_fit"] == 15
