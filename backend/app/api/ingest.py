import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.anonymizer import anonymize_rut, generate_avatar_name
from app.core.classifier import classify
from app.core.parser_cmf import parse_informe_with_fallback
from app.models.schemas import Avatar, Features, IngestResult

router = APIRouter()


@router.post("/ingest", response_model=IngestResult)
async def ingest(
    file: UploadFile = File(...),
    rut: str = Form(...),
    ingreso: float = Form(580_000),
):
    """Accept a CMF Informe de Deudas + RUT, classify, return IngestResult.

    BE1-1 scope: parse + classify + return. Persistence and recommendations
    come in BE1-2.
    """
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

        return IngestResult(
            anon_id=anon_id,
            avatar=Avatar(name=avatar_name, image_url=f"/avatars/{anon_id}.svg"),
            segment=segment,
            features=features_obj,
            recommendations=[],
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def _to_features(d: dict) -> Features:
    """Project the parser's full feature dict to the Features Pydantic model.

    Parser produces extra internal keys (consumo_debt, mortgage_debt, etc.)
    that the public schema deliberately doesn't expose.
    """
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
