"""SQLAlchemy database engine, session, and Base."""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://portfolioq:portfolioq@postgres:5432/portfolioq",
)
_url = (DATABASE_URL or "").strip()
if _url and not _url.lower().startswith("postgresql"):
    raise ValueError(
        "DATABASE_URL must point to PostgreSQL; application uses PostgreSQL end-to-end. "
        "Current value does not start with 'postgresql'."
    )

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables from models."""
    import src.models.portfolio  # noqa: F401
    import src.models.scenario
    import src.models.market_data
    import src.models.exposure
    import src.models.report
    import src.models.alert
    Base.metadata.create_all(bind=engine)
