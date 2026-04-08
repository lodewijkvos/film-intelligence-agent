from __future__ import annotations

from sqlalchemy import text

from film_intelligence_agent.db.base import Base
from film_intelligence_agent.db.session import get_engine


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())


def healthcheck() -> None:
    with get_engine().connect() as connection:
        connection.execute(text("select 1"))
