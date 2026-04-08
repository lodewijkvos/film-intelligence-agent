from datetime import datetime

from film_intel_agent.domain.types import ExtractedFilm
from film_intel_agent.scoring.opportunity import compute_data_confidence, compute_opportunity_score


def test_data_confidence_rewards_canadian_record():
    film = ExtractedFilm(
        title="Test Film",
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


def test_opportunity_score_returns_breakdown():
    film = ExtractedFilm(
        title="Horror Film",
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
    score, breakdown = compute_opportunity_score(film)
    assert score >= 60
    assert breakdown["budget_fit"] == 15
