"""SQLite persistence for anon profiles.

Schema is one table, no PII column by design. ``anon_id`` is HMAC(secret, rut)
and is the only identifier; same person re-uploading dedups via primary key.
"""

import os
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./defensor.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProfileRecord(Base):
    __tablename__ = "profiles"

    anon_id = Column(String, primary_key=True)
    segment = Column(String, nullable=False)
    features = Column(JSON, nullable=False)
    recommendations = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
