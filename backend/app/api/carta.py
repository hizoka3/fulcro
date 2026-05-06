from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/carta/{anon_id}")
def generate_carta(anon_id: str):
    """Letter-of-complaint generation lives in BE-2's services/carta_reclamo.

    The route is registered here so frontend / BE-2 can target a stable URL.
    Returns 501 until BE-2 wires the real generator.
    """
    raise HTTPException(
        501, "Generación de carta pendiente de integración con BE-2"
    )
