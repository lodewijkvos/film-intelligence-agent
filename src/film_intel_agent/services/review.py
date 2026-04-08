from __future__ import annotations

from sqlalchemy import desc, select

from film_intel_agent.db.models import CollaboratorMatch, Film
from film_intel_agent.db.session import db_session


class ReviewQueueService:
    def low_confidence_projects(self) -> list[Film]:
        with db_session() as session:
            stmt = (
                select(Film)
                .where(Film.data_confidence_score < 70)
                .order_by(desc(Film.last_changed_at))
            )
            return list(session.scalars(stmt))

    def uncertain_collaborator_matches(self) -> list[CollaboratorMatch]:
        with db_session() as session:
            stmt = (
                select(CollaboratorMatch)
                .where(CollaboratorMatch.review_required.is_(True))
                .order_by(desc(CollaboratorMatch.created_at))
            )
            return list(session.scalars(stmt))
