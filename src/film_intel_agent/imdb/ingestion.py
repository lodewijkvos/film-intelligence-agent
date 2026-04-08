from __future__ import annotations

import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup
from sqlalchemy import select

from film_intel_agent.config.settings import get_settings
from film_intel_agent.db.models import Collaborator, IngestionRun, Person
from film_intel_agent.db.session import db_session
from film_intel_agent.domain.types import CollaboratorEdge
from film_intel_agent.fetching.http import CachedFetcher
from film_intel_agent.utils.text import normalize_name

logger = logging.getLogger(__name__)


class IMDbCollaboratorIngestionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.fetcher = CachedFetcher()

    def run(self) -> list[CollaboratorEdge]:
        with db_session() as session:
            run = IngestionRun(pipeline_name="imdb_collaborator_graph", status="running")
            session.add(run)
            session.flush()
            try:
                edges = self._run_public_fallback()
                self._persist_edges(edges)
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                run.run_metadata = {"edge_count": len(edges), "mode": "hybrid_public_first"}
                return edges
            except Exception as exc:
                run.status = "failed"
                run.completed_at = datetime.utcnow()
                run.error_summary = str(exc)
                raise

    def _run_public_fallback(self) -> list[CollaboratorEdge]:
        result = self.fetcher.fetch("IMDb Public Name Page", self.settings.imdb_public_url)
        soup = BeautifulSoup(result.html or "", "lxml")
        credits: list[CollaboratorEdge] = []
        for anchor in soup.select("a[href*='/title/tt']"):
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "")
            imdb_id_match = re.search(r"/title/(tt\d+)/", href)
            credits.append(
                CollaboratorEdge(
                    person_name=self.settings.subject_name,
                    person_imdb_id=None,
                    person_imdb_url=self.settings.imdb_public_url,
                    role="composer",
                    project_title=title,
                    project_imdb_id=imdb_id_match.group(1) if imdb_id_match else None,
                    project_imdb_url=f"https://www.imdb.com{href}" if href.startswith("/") else href,
                    release_date=None,
                    match_confidence=0.8,
                    match_method="imdb_public_page",
                )
            )
        return credits

    def _persist_edges(self, edges: list[CollaboratorEdge]) -> None:
        with db_session() as session:
            for edge in edges:
                person = session.scalar(
                    select(Person).where(Person.normalized_name == normalize_name(edge.person_name))
                )
                if person is None:
                    person = Person(
                        full_name=edge.person_name,
                        normalized_name=normalize_name(edge.person_name),
                        imdb_id=edge.person_imdb_id,
                        imdb_url=edge.person_imdb_url,
                        match_confidence=edge.match_confidence,
                        match_method=edge.match_method,
                        is_known_collaborator=edge.person_name != self.settings.subject_name,
                    )
                    session.add(person)
                    session.flush()
                collaborator = session.scalar(select(Collaborator).where(Collaborator.person_id == person.id))
                if collaborator is None:
                    collaborator = Collaborator(
                        person_id=person.id,
                        shared_project_names=[edge.project_title],
                        shared_project_count=1,
                        role_summary=[edge.role],
                        source="imdb_public_page",
                    )
                    session.add(collaborator)
                else:
                    projects = set(collaborator.shared_project_names or [])
                    projects.add(edge.project_title)
                    collaborator.shared_project_names = sorted(projects)
                    collaborator.shared_project_count = len(projects)
