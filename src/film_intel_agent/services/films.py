from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from film_intel_agent.db.models import Film, SourceRecord
from film_intel_agent.db.session import db_session
from film_intel_agent.domain.types import ExtractedFilm
from film_intel_agent.scoring.opportunity import compute_data_confidence, compute_opportunity_score
from film_intel_agent.utils.text import normalize_title


class FilmIngestionService:
    def upsert_films(self, extracted_films: list[ExtractedFilm]) -> list[Film]:
        persisted: list[Film] = []
        with db_session() as session:
            for item in extracted_films:
                normalized_title = normalize_title(item.title)
                film = session.scalar(select(Film).where(Film.normalized_title == normalized_title))
                opportunity_score, breakdown = compute_opportunity_score(item)
                data_confidence = compute_data_confidence(item)
                now = datetime.utcnow()
                if film is None:
                    film = Film(
                        title=item.title,
                        normalized_title=normalized_title,
                        alternate_title=None,
                        imdb_id=item.imdb_id,
                        imdb_url=item.imdb_url,
                        status=item.status,
                        project_type=item.project_type,
                        genre=item.genre,
                        subgenre=item.subgenre,
                        country=item.country,
                        region=item.region,
                        province_or_state=item.province_or_state,
                        production_company=item.production_company,
                        source_name=item.source_name,
                        source_url=item.source_url,
                        first_seen_at=now,
                        last_seen_at=now,
                        last_changed_at=now,
                        notes=item.notes,
                        confidence_score=item.confidence_score,
                        data_confidence_score=data_confidence,
                        opportunity_score=opportunity_score,
                        opportunity_score_breakdown=breakdown,
                        date_detected=item.date_detected,
                        source_tier=item.source_tier,
                        source_type=item.source_type,
                        canada_priority=item.country == "Canada",
                        budget_min=item.budget_min,
                        budget_max=item.budget_max,
                        budget_currency=item.budget_currency,
                        budget_text=item.budget_text or "Unknown",
                        budget_confidence=item.budget_confidence,
                    )
                    session.add(film)
                    session.flush()
                else:
                    film.last_seen_at = now
                    film.last_changed_at = now
                    film.status = item.status or film.status
                    film.country = item.country or film.country
                    film.region = item.region or film.region
                    film.province_or_state = item.province_or_state or film.province_or_state
                    film.production_company = item.production_company or film.production_company
                    film.notes = item.notes or film.notes
                    film.confidence_score = max(film.confidence_score, item.confidence_score)
                    film.data_confidence_score = max(film.data_confidence_score, data_confidence)
                    film.opportunity_score = max(film.opportunity_score, opportunity_score)
                    film.opportunity_score_breakdown = breakdown
                    film.budget_text = item.budget_text or film.budget_text or "Unknown"
                source_record = SourceRecord(
                    film_id=film.id,
                    source_name=item.source_name,
                    source_url=item.source_url,
                    source_type=item.source_type,
                    source_tier=item.source_tier,
                    snippet=item.notes,
                    extraction_payload={
                        "title": item.title,
                        "status": item.status,
                        "people_count": len(item.people),
                    },
                )
                session.add(source_record)
                persisted.append(film)
        return persisted
