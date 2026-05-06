import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.anonymizer import anonymize_rut, generate_avatar_name
from app.core.catalog_matcher import get_matcher
from app.core.classifier import classify
from app.core.parser_cmf import parse_informe_with_fallback
from app.db.sqlite import ProfileRecord, get_db
from app.models.schemas import Avatar, Features, IngestResult

router = APIRouter()


@router.post("/ingest", response_model=IngestResult)
async def ingest(
    file: UploadFile = File(...),
    rut: str = Form(...),
    ingreso: float = Form(580_000),
    db: Session = Depends(get_db),
):
    """Parse CMF PDF + RUT, classify, match recommendations, persist, return."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan archivos PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        anon_id = anonymize_rut(rut)
        avatar_name = generate_avatar_name(anon_id)

        try:
            features_dict = parse_informe_with_fallback(tmp_path)
        except Exception as exc:
            raise HTTPException(422, f"No se pudo parsear el informe: {exc}")

        segment = classify(features_dict, ingreso_mensual=ingreso)
        features_obj = _to_features(features_dict)

        recommendations = get_matcher().match(
            segment=segment,
            dominant_signal=features_dict.get("dominant_signal", ""),
        )

        _upsert_profile(db, anon_id, segment.value, features_obj, recommendations)

        return IngestResult(
            anon_id=anon_id,
            avatar=Avatar(name=avatar_name, image_url=f"/avatars/{anon_id}.svg"),
            segment=segment,
            features=features_obj,
            recommendations=recommendations,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def _to_features(d: dict) -> Features:
    return Features(
        total_debt=d.get("total_debt", 0.0),
        consumo_ratio=d.get("consumo_ratio", 0.0),
        past_due_ratio=d.get("past_due_ratio", 0.0),
        num_institutions=d.get("num_institutions", 0),
        num_refinancings=d.get("num_refinancings", 0),
        has_mortgage=d.get("has_mortgage", False),
        carga_financiera_pct=d.get("carga_financiera_pct", 0.0),
        dominant_signal=d.get("dominant_signal", ""),
    )


def _upsert_profile(
    db: Session,
    anon_id: str,
    segment: str,
    features: Features,
    recommendations: list,
) -> None:
    features_json = features.model_dump()
    recs_json = [r.model_dump() for r in recommendations]

    existing = db.query(ProfileRecord).filter_by(anon_id=anon_id).first()
    if existing:
        existing.segment = segment
        existing.features = features_json
        existing.recommendations = recs_json
    else:
        db.add(
            ProfileRecord(
                anon_id=anon_id,
                segment=segment,
                features=features_json,
                recommendations=recs_json,
            )
        )
    db.commit()
