"""SQLite persistence for anon profiles.

Each row is one snapshot. ``anon_id`` is HMAC(secret, name|rut); ``content_hash``
fingerprints the parsed features. ``(anon_id, content_hash)`` is unique, so
re-uploading the same document for the same person is a no-op, while a
different document produces a new historical row.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./defensor.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_features(features: dict) -> str:
    """Stable SHA-256 of features. sort_keys + default=str makes it
    insensitive to dict ordering and tolerant of datetimes/Decimals."""
    blob = json.dumps(features, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


class ProfileRecord(Base):
    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("anon_id", "content_hash"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    anon_id = Column(String, nullable=False, index=True)
    content_hash = Column(String, nullable=False)
    segment = Column(String, nullable=False)
    features = Column(JSON, nullable=False)
    recommendations = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=_utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
