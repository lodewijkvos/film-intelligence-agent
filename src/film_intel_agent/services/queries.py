from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, desc, or_, select

from film_intel_agent.db.models import CollaboratorMatch, Film, FilmPerson
from film_intel_agent.db.session import db_session


class FilmQueryService:
    def projects_added_last_14_days(self) -> list[Film]:
        since = datetime.utcnow() - timedelta(days=14)
        with db_session() as session:
            stmt = (
                select(Film)
                .where(Film.date_detected >= since)
                .order_by(desc(Film.opportunity_score), desc(Film.data_confidence_score))
            )
            return list(session.scalars(stmt))

    def films_with_role_overlap(self, roles: tuple[str, ...] = ("editor", "producer")) -> list[Film]:
        with db_session() as session:
            stmt = (
                select(Film)
                .join(FilmPerson, FilmPerson.film_id == Film.id)
                .join(CollaboratorMatch, CollaboratorMatch.film_id == Film.id)
                .where(FilmPerson.role.in_(roles))
                .distinct()
                .order_by(desc(Film.opportunity_score), desc(Film.date_detected))
            )
            return list(session.scalars(stmt))

    def high_confidence_canadian_projects(self) -> list[Film]:
        with db_session() as session:
            stmt = (
                select(Film)
                .where(and_(Film.country == "Canada", Film.data_confidence_score >= 70))
                .order_by(desc(Film.data_confidence_score), desc(Film.opportunity_score))
            )
            return list(session.scalars(stmt))

    def us_projects_above_threshold(self, threshold: int = 70) -> list[Film]:
        with db_session() as session:
            stmt = (
                select(Film)
                .where(
                    and_(
                        or_(Film.country == "United States", Film.region == "United States"),
                        Film.data_confidence_score >= threshold,
                    )
                )
                .order_by(desc(Film.data_confidence_score), desc(Film.opportunity_score))
            )
            return list(session.scalars(stmt))
