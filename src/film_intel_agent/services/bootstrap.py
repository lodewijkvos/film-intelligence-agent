from __future__ import annotations

from sqlalchemy import text

from film_intel_agent.db.base import Base
from film_intel_agent.db.session import create_engine_from_settings


def init_db() -> None:
    engine = create_engine_from_settings()
    Base.metadata.create_all(bind=engine)


def healthcheck() -> None:
    engine = create_engine_from_settings()
    with engine.connect() as connection:
        connection.execute(text("select 1"))
