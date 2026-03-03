import os
import logging

from collections.abc import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine


def build_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "carms")
    password = os.getenv("POSTGRES_PASSWORD", "carms")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    database = os.getenv("POSTGRES_DB", "carms")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


DATABASE_URL = build_database_url()
engine = create_engine(DATABASE_URL, echo=False)
logger = logging.getLogger(__name__)


def ensure_search_support() -> None:
    try:
        with engine.begin() as connection:
            connection.execute(text("create extension if not exists vector"))
            connection.execute(
                text("alter table document_chunk add column if not exists embedding vector")
            )
    except Exception as exc:  # pragma: no cover
        logger.warning("pgvector support is not available yet: %s", exc)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    ensure_search_support()


def get_session() -> Session:
    return Session(engine)


def get_db_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
