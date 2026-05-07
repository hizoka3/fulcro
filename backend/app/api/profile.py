from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.anonymizer import generate_avatar_name
from app.db.sqlite import ProfileRecord, get_db
from app.models.schemas import (
    Avatar,
    Features,
    IngestResult,
    Recommendation,
    Segment,
)

router = APIRouter()


@router.get("/profile/{anon_id}", response_model=IngestResult)
def get_profile(anon_id: str, db: Session = Depends(get_db)):
    record = (
        db.query(ProfileRecord)
        .filter_by(anon_id=anon_id)
        .order_by(ProfileRecord.created_at.desc())
        .first()
    )
    if not record:
        raise HTTPException(404, "Perfil no encontrado")
    return IngestResult(
        anon_id=record.anon_id,
        avatar=Avatar(
            name=generate_avatar_name(record.anon_id),
            image_url=f"/avatars/{record.anon_id}.svg",
        ),
        segment=Segment(record.segment),
        features=Features(**record.features),
        recommendations=[Recommendation(**r) for r in record.recommendations],
    )
