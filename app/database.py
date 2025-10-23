from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

DB_PATH = Path("/workspace/app/data")
DB_PATH.mkdir(parents=True, exist_ok=True)
DB_URL = f"sqlite:///{DB_PATH / 'travel_journal.db'}"

# check_same_thread False for FastAPI threading model
engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    from .models import Trip, Photo  # noqa: F401 - ensure models are imported
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
