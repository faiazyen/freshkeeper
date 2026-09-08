"""Engine and session management."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DEFAULT_DB_PATH = Path("data/freshkeeper.db")


def make_engine(db_path: str | Path = DEFAULT_DB_PATH, echo: bool = False):
    """Create the SQLite engine with the pragmas this workload wants.

    WAL lets the acquisition thread write while a request reads, which the
    default rollback journal does not. ``foreign_keys`` is off by default in
    SQLite, so the cascades declared in the schema are inert without it -- an
    easy thing to not notice until orphaned rows pile up.
    """
    if str(db_path) == ":memory:":
        url = "sqlite+pysqlite:///:memory:"
    else:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite+pysqlite:///{path}"

    engine = create_engine(url, echo=echo, future=True,
                           connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        if str(db_path) != ":memory:":
            cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    return engine


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def make_session_factory(engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(factory: sessionmaker):
    """Transactional scope: commit on success, roll back on anything else."""
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
