from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from film_intelligence_agent.db.models import Film, SourceRecord
from film_intelligence_agent.db.session import db_session
from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.services.scoring import compute_data_confidence, compute_opportunity
from film_intelligence_agent.utils.normalize import normalize_title


class FilmPersistenceService:
    def upsert(self, films: list[ExtractedFilm]) -> list[Film]:
        persisted: list[Film] = []
        with db_session() as session:
            for item in films:
                normalized = normalize_title(item.title)
                existing = session.scalar(select(Film).where(Film.normalized_title == normalized))
                opportunity_score, breakdown = compute_opportunity(item)
                data_confidence = compute_data_confidence(item)
                now = datetime.utcnow()
                if existing is None:
                    existing = Film(
                        title=item.title,
                        normalized_title=normalized,
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
                        budget_min=item.budget_min,
                        budget_max=item.budget_max,
                        budget_currency=item.budget_currency,
                        budget_text=item.budget_text or "Unknown",
                        budget_confidence=item.budget_confidence,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(existing)
                    session.flush()
                else:
                    existing.last_seen_at = now
                    existing.last_changed_at = now
                    existing.updated_at = now
                    existing.confidence_score = max(existing.confidence_score, item.confidence_score)
                    existing.data_confidence_score = max(existing.data_confidence_score, data_confidence)
                    existing.opportunity_score = max(existing.opportunity_score, opportunity_score)
                    existing.opportunity_score_breakdown = breakdown
                session.add(
                    SourceRecord(
                        film_id=existing.id,
                        source_name=item.source_name,
                        source_url=item.source_url,
                        source_type=item.source_type,
                        source_tier=item.source_tier,
                        snippet=item.notes,
                        extraction_payload={"title": item.title, "status": item.status},
                    )
                )
                persisted.append(existing)
        return persisted
