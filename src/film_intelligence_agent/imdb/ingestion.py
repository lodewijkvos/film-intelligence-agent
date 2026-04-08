from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup
from sqlalchemy import select

from film_intelligence_agent.config.settings import get_settings
from film_intelligence_agent.db.models import Collaborator, IngestionRun, Person
from film_intelligence_agent.db.session import db_session
from film_intelligence_agent.domain.types import CollaboratorEdge
from film_intelligence_agent.fetching.http import CachedFetcher
from film_intelligence_agent.utils.normalize import normalize_name


class IMDbIngestionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.fetcher = CachedFetcher()

    def run(self) -> list[CollaboratorEdge]:
        with db_session() as session:
            run = IngestionRun(pipeline_name="imdb_collaborator_graph", status="running")
            session.add(run)
        edges = self._ingest_public_fallback()
        self._persist(edges)
        with db_session() as session:
            run = session.scalar(
                select(IngestionRun).where(IngestionRun.pipeline_name == "imdb_collaborator_graph").order_by(
                    IngestionRun.started_at.desc()
                )
            )
            if run:
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                run.run_metadata = {"edge_count": len(edges), "mode": "hybrid_public_fallback"}
        return edges

    def _ingest_public_fallback(self) -> list[CollaboratorEdge]:
        html, _digest = self.fetcher.fetch_text("IMDb Public Name Page", self.settings.imdb_public_url)
        soup = BeautifulSoup(html, "lxml")
        edges: list[CollaboratorEdge] = []
        for anchor in soup.select("a[href*='/title/tt']"):
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "")
            if len(title) < 2:
                continue
            match = re.search(r"/title/(tt\d+)/", href)
            edges.append(
                CollaboratorEdge(
                    person_name=self.settings.subject_name,
                    person_imdb_id=None,
                    person_imdb_url=self.settings.imdb_public_url,
                    role="composer",
                    project_title=title,
                    project_imdb_id=match.group(1) if match else None,
                    project_imdb_url=f"https://www.imdb.com{href}" if href.startswith("/") else href,
                    release_date=None,
                    match_confidence=0.8,
                    match_method="imdb_public_page",
                )
            )
        return edges

    def _persist(self, edges: list[CollaboratorEdge]) -> None:
        with db_session() as session:
            for edge in edges:
                normalized = normalize_name(edge.person_name)
                person = session.scalar(select(Person).where(Person.normalized_name == normalized))
                if person is None:
                    person = Person(
                        full_name=edge.person_name,
                        normalized_name=normalized,
                        imdb_id=edge.person_imdb_id,
                        imdb_url=edge.person_imdb_url,
                        match_confidence=edge.match_confidence,
                        match_method=edge.match_method,
                        is_known_collaborator=False,
                    )
                    session.add(person)
                    session.flush()
                collaborator = session.scalar(select(Collaborator).where(Collaborator.person_id == person.id))
                if collaborator is None:
                    collaborator = Collaborator(
                        person_id=person.id,
                        shared_project_names=[edge.project_title],
                        shared_project_count=1,
                    )
                    session.add(collaborator)
