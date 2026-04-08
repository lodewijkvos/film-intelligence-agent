from __future__ import annotations

from pathlib import Path

import typer

from film_intel_agent.config.settings import get_settings
from film_intel_agent.imdb.ingestion import IMDbCollaboratorIngestionService
from film_intel_agent.integrations.notion.sync import NotionSyncService
from film_intel_agent.integrations.notion.setup import NotionSetupService
from film_intel_agent.services.bootstrap import healthcheck, init_db
from film_intel_agent.services.discovery import DiscoveryService
from film_intel_agent.services.films import FilmIngestionService
from film_intel_agent.services.orchestrator import WeeklyOrchestrator
from film_intel_agent.utils.logging import configure_logging

app = typer.Typer(no_args_is_help=True)


def bootstrap_logging() -> None:
    configure_logging(get_settings().log_level)


@app.command()
def initdb() -> None:
    bootstrap_logging()
    init_db()
    typer.echo("Database initialized.")


@app.command()
def check() -> None:
    bootstrap_logging()
    healthcheck()
    typer.echo("Database connection OK.")


@app.command()
def ingest_sources() -> None:
    bootstrap_logging()
    config_path = Path("config/film_greenlight_scraper_spec.yaml")
    films = DiscoveryService(config_path).collect()
    FilmIngestionService().upsert_films(films)
    typer.echo(f"Ingested {len(films)} extracted film records.")


@app.command()
def ingest_imdb() -> None:
    bootstrap_logging()
    edges = IMDbCollaboratorIngestionService().run()
    typer.echo(f"Ingested {len(edges)} IMDb collaborator edges.")


@app.command()
def setup_notion() -> None:
    bootstrap_logging()
    created = NotionSetupService().ensure_core_databases()
    typer.echo(f"Created or confirmed Notion resources: {created}")


@app.command()
def sync_notion(limit: int = typer.Option(25, help="How many recent films to sync.")) -> None:
    bootstrap_logging()
    NotionSyncService().sync_latest_films(limit=limit)
    typer.echo("Notion sync completed.")


@app.command()
def run_weekly(
    dry_run: bool = typer.Option(True, "--dry-run/--live", help="Generate only or send/sync live.")
) -> None:
    bootstrap_logging()
    config_path = Path("config/film_greenlight_scraper_spec.yaml")
    WeeklyOrchestrator(config_path).run(dry_run=dry_run)
    typer.echo("Weekly workflow completed.")
