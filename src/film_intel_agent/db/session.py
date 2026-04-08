from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from film_intel_agent.config.settings import get_settings


_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker | None = None


def create_engine_from_settings() -> Engine:
    settings = get_settings()
    return create_engine(settings.effective_database_url, pool_pre_ping=True)


def get_session_factory() -> sessionmaker:
    global _ENGINE, _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _ENGINE = create_engine_from_settings()
        _SESSION_FACTORY = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False)
    return _SESSION_FACTORY


@contextmanager
def db_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
