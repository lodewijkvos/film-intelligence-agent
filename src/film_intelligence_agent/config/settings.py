from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    default_timezone: str = "America/Toronto"
    raw_cache_dir: Path = Path("raw_cache")

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_db_password: str | None = None
    database_url: str | None = None

    notion_token: str | None = None
    notion_parent_page_id: str | None = None
    notion_films_database_id: str | None = None
    notion_people_database_id: str | None = None

    resend_api_key: str | None = None
    email_from: str = "reports@lodewijkvos.com"
    email_to: str = "lo@lodewijkvos.com"

    imdb_pro_username: str | None = None
    imdb_pro_password: str | None = None
    imdb_public_url: str = "https://www.imdb.com/name/nm3928402/?ref_=nv_sr_srsg_4_tt_0_nm_8_in_0_q_lodew"
    imdb_pro_url: str = "https://pro.imdb.com/?ref_=spl_stkyhdr_login_imdb"
    subject_name: str = "Lodewijk Vos"

    @computed_field
    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if not self.supabase_url or not self.supabase_db_password:
            raise ValueError("Configure DATABASE_URL or SUPABASE_URL + SUPABASE_DB_PASSWORD.")
        project_ref = self.supabase_url.removeprefix("https://").split(".")[0]
        return (
            f"postgresql+psycopg://postgres:{self.supabase_db_password}"
            f"@db.{project_ref}.supabase.co:5432/postgres"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
