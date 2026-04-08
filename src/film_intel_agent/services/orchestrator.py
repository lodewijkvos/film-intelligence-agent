from __future__ import annotations

from pathlib import Path

from film_intel_agent.imdb.ingestion import IMDbCollaboratorIngestionService
from film_intel_agent.integrations.notion.sync import NotionSyncService
from film_intel_agent.services.discovery import DiscoveryService
from film_intel_agent.services.films import FilmIngestionService
from film_intel_agent.services.reports import WeeklyReportService


class WeeklyOrchestrator:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def run(self, dry_run: bool = True) -> None:
        IMDbCollaboratorIngestionService().run()
        films = DiscoveryService(self.config_path).collect()
        FilmIngestionService().upsert_films(films)
        report = WeeklyReportService().generate_and_optionally_send(dry_run=dry_run)
        notion = NotionSyncService()
        notion.create_report_page(report.id)
        notion.sync_latest_films()
        if dry_run:
            return
