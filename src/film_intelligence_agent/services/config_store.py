from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from film_intelligence_agent.db.models import AppConfig
from film_intelligence_agent.db.session import db_session


class ConfigStore:
    def get(self, key: str) -> str | None:
        with db_session() as session:
            record = session.scalar(select(AppConfig).where(AppConfig.key == key))
            return record.value if record else None

    def set(self, key: str, value: str) -> None:
        with db_session() as session:
            record = session.scalar(select(AppConfig).where(AppConfig.key == key))
            if record is None:
                record = AppConfig(key=key, value=value, updated_at=datetime.utcnow())
                session.add(record)
            else:
                record.value = value
                record.updated_at = datetime.utcnow()
