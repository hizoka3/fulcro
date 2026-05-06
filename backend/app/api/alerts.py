from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

router = APIRouter()


def _days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


_ALERTS_MOCK = [
    {
        "id": "alert_001",
        "title": "Nueva tasa máxima convencional vigente",
        "description": "La CMF actualizó la TMC para créditos de consumo. Ahora es 38.21% anual.",
        "source": "CMF",
        "date": _days_ago(2),
        "url": "https://cmfchile.cl",
    },
    {
        "id": "alert_002",
        "title": "SERNAC inicia mediación contra retail por cláusulas abusivas",
        "description": "Mediación colectiva afecta a 2 millones de clientes.",
        "source": "SERNAC",
        "date": _days_ago(7),
        "url": "https://sernac.cl",
    },
    {
        "id": "alert_003",
        "title": "Ley 21.398 obliga a portabilidad financiera en 4 días",
        "description": "Si te demoran más, puedes reclamar al SERNAC.",
        "source": "Diario Oficial",
        "date": _days_ago(15),
        "url": "https://leychile.cl",
    },
    {
        "id": "alert_004",
        "title": "Nueva ley de protección de datos personales (Ley 21.719)",
        "description": "Vigente desde 2026. Tus derechos se amplían.",
        "source": "Ministerio de Hacienda",
        "date": _days_ago(30),
        "url": "https://leychile.cl",
    },
]


@router.get("/alerts")
def get_alerts():
    return _ALERTS_MOCK
