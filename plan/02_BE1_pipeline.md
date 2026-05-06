# 02 — MEGAPROMPTS BACKEND-1 (BE-1): Pipeline Determinístico

> **Quién:** persona BE-1 del equipo.
> **Stack:** FastAPI + Python + pdfplumber + SQLite + SQLAlchemy.
> **Pre-requisito:** Megaprompt 00 (setup) ejecutado. Repo clonado. `.venv` activo.
> **Total de megaprompts:** 5, secuenciales.

---

## Reglas para usar estos megaprompts

1. Ejecutar uno a la vez. Esperar a que termine antes del siguiente.
2. Cada megaprompt incluye su contexto — pegar entero a Claude Code o a tu agente de coding.
3. NO introduzcas LLMs en este pipeline. Esta capa es 100% determinística.
4. Después de cada megaprompt: `git add . && git commit -m "feat(be1): [resumen]" && git push`.

---

## CONTEXTO COMÚN (incluir al inicio de cada megaprompt)

```
PROYECTO: Defensor — Concierge financiero con IA.
ROL: Backend-1 (Pipeline). Responsable de parser CMF, classifier, catalog matcher,
endpoints REST, persistencia, deploy.

DECISIÓN ARQUITECTÓNICA CRÍTICA:
Esta capa es DETERMINÍSTICA. NUNCA usa LLMs. NUNCA llama a Claude. NUNCA hace
inferencias estadísticas. Es código tradicional, auditable, predecible.

La capa de IA (concierge) la maneja BE-2 ENCIMA de esta. Tú produces ProfileSnapshot
estructurado, BE-2 lo consume.

API CONTRACT:
- POST /ingest (multipart con file PDF) → IngestResult
- GET /profile/{anon_id} → IngestResult
- POST /carta/{anon_id} → blob PDF (la generación la hace BE-2, tú expones el endpoint
  que invoca su servicio)
- GET /alerts → array de alertas mock

USUARIO PROTAGONISTA: María Silva.

PERSISTENCIA: SQLite local. Una tabla "profiles" con anon_id, segment, features (JSON),
created_at. Sin PII.
```

---

## MEGAPROMPT BE1-1: Parser CMF + Classifier (90 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: parser de PDF informe CMF + classifier determinístico funcional contra fixture
de María. Endpoint /ingest stub que retorna IngestResult.

TAREAS:

1. Implementar backend/app/core/anonymizer.py:

```python
import hmac
import hashlib
import os

def anonymize_rut(rut: str) -> str:
    """Genera anon_id determinístico desde RUT usando HMAC."""
    secret = os.environ["HMAC_SECRET"].encode()
    rut_clean = rut.replace(".", "").replace("-", "").upper().encode()
    return hmac.new(secret, rut_clean, hashlib.sha256).hexdigest()[:12]

def generate_avatar_name(anon_id: str) -> str:
    """Genera nombre tipo 'Cóndor 4521' desde anon_id."""
    animals = ["Cóndor", "Puma", "Huemul", "Pudú", "Vizcacha", "Loica",
               "Chinchilla", "Quetru", "Tagua", "Quirquincho"]
    idx = int(anon_id[:2], 16) % len(animals)
    number = int(anon_id[2:6], 16) % 9000 + 1000
    return f"{animals[idx]} {number}"
```

2. Implementar backend/app/core/parser_cmf.py:

```python
import pdfplumber
from typing import Dict
from pathlib import Path

def parse_informe_cmf(pdf_path: Path) -> Dict:
    """
    Parsea informe CMF a Features dict.

    Estructura típica de un informe CMF:
    - Header: nombre, RUT, fecha
    - Tabla 1: Deudas vigentes (institución, tipo producto, monto, tasa)
    - Tabla 2: Deudas morosas (institución, monto, días mora)
    - Resumen: totales

    Esta implementación es específica para el formato de informe que tenemos.
    Si falla, usar el fallback de fixtures pre-parseados.
    """
    features = {
        "total_debt": 0,
        "consumo_debt": 0,
        "mortgage_debt": 0,
        "commercial_debt": 0,
        "past_due_amount": 0,
        "consumo_ratio": 0,
        "past_due_ratio": 0,
        "num_institutions": 0,
        "num_refinancings": 0,
        "has_mortgage": False,
        "carga_financiera_pct": 0,
        "dominant_signal": ""
    }

    institutions = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            text = page.extract_text() or ""

            # Detectar refinanciamientos por palabra clave
            if "refinanci" in text.lower():
                features["num_refinancings"] += text.lower().count("refinanci")

            # Procesar tablas de deuda
            for table in tables or []:
                for row in table[1:] if table else []:  # skip header
                    if not row or len(row) < 3:
                        continue
                    try:
                        # asume formato: institución, tipo, monto
                        institucion = (row[0] or "").strip()
                        tipo = (row[1] or "").strip().lower()
                        monto_str = (row[2] or "0").replace(".", "").replace("$", "").strip()
                        monto = float(monto_str) if monto_str.isdigit() else 0

                        institutions.add(institucion)

                        if "consumo" in tipo or "tarjeta" in tipo:
                            features["consumo_debt"] += monto
                        elif "hipotec" in tipo:
                            features["mortgage_debt"] += monto
                            features["has_mortgage"] = True
                        elif "comercial" in tipo:
                            features["commercial_debt"] += monto
                    except (ValueError, IndexError):
                        continue

    features["total_debt"] = (
        features["consumo_debt"]
        + features["mortgage_debt"]
        + features["commercial_debt"]
    )
    features["num_institutions"] = len(institutions)

    if features["total_debt"] > 0:
        features["consumo_ratio"] = features["consumo_debt"] / features["total_debt"]

    # Determinar dominant_signal
    if features["past_due_ratio"] > 0:
        features["dominant_signal"] = "past_due_present"
    elif features["consumo_ratio"] > 0.7:
        features["dominant_signal"] = "high_consumo_ratio"
    elif features["num_refinancings"] >= 2:
        features["dominant_signal"] = "multiple_refinancings"
    elif features["num_institutions"] >= 4:
        features["dominant_signal"] = "many_institutions"
    elif features["has_mortgage"]:
        features["dominant_signal"] = "stable_with_mortgage"
    else:
        features["dominant_signal"] = "low_engagement"

    return features


def parse_informe_with_fallback(pdf_path: Path, fallback_json: Path = None) -> Dict:
    """Si el parser real falla, usa JSON pre-parseado."""
    try:
        return parse_informe_cmf(pdf_path)
    except Exception as e:
        if fallback_json and fallback_json.exists():
            import json
            with open(fallback_json) as f:
                return json.load(f)["features"]
        raise
```

3. Implementar backend/app/core/classifier.py:

```python
from typing import Dict
from app.models.schemas import Segment

def classify(features: Dict, ingreso_mensual: float = 580000) -> Segment:
    """
    Clasificador determinístico. First-match wins.
    ingreso_mensual default: estimación si no hay dato real.
    """
    total_debt = features.get("total_debt", 0)
    past_due_ratio = features.get("past_due_ratio", 0)
    consumo_ratio = features.get("consumo_ratio", 0)
    num_institutions = features.get("num_institutions", 0)
    num_refinancings = features.get("num_refinancings", 0)
    has_mortgage = features.get("has_mortgage", False)

    # Calcular carga financiera (estimación pago mensual = total_debt / 36)
    estimated_monthly_payment = total_debt / 36
    carga = estimated_monthly_payment / ingreso_mensual if ingreso_mensual > 0 else 0
    features["carga_financiera_pct"] = round(carga, 2)

    # Regla 1: Sin deudas = unbanked
    if total_debt == 0 and num_institutions == 0:
        return Segment.UNBANKED

    # Regla 2: Vulnerable
    if (past_due_ratio > 0
        or consumo_ratio > 0.7
        or num_institutions >= 4
        or num_refinancings >= 2
        or carga > 0.4):
        return Segment.VULNERABLE

    # Regla 3: Functional
    if has_mortgage and past_due_ratio == 0 and carga < 0.3:
        return Segment.FUNCTIONAL

    # Regla 4: Recently banked
    if num_institutions <= 2 and total_debt < 500000:
        return Segment.RECENTLY_BANKED

    # Default: functional (estable, sin señales graves)
    return Segment.FUNCTIONAL
```

4. Implementar tests/test_classifier.py:

```python
import pytest
from app.core.classifier import classify
from app.models.schemas import Segment

def test_maria_vulnerable():
    features = {
        "total_debt": 4500000,
        "consumo_ratio": 0.82,
        "past_due_ratio": 0.15,
        "num_institutions": 5,
        "num_refinancings": 2,
        "has_mortgage": False,
    }
    assert classify(features, ingreso_mensual=580000) == Segment.VULNERABLE

def test_carlos_functional():
    features = {
        "total_debt": 80_000_000,
        "consumo_ratio": 0.05,
        "past_due_ratio": 0.0,
        "num_institutions": 3,
        "num_refinancings": 0,
        "has_mortgage": True,
    }
    assert classify(features, ingreso_mensual=2_500_000) == Segment.FUNCTIONAL

def test_pedro_recently_banked():
    features = {
        "total_debt": 0,
        "consumo_ratio": 0,
        "past_due_ratio": 0,
        "num_institutions": 1,
        "num_refinancings": 0,
        "has_mortgage": False,
    }
    assert classify(features, ingreso_mensual=400000) == Segment.UNBANKED  # sin deuda

def test_unbanked():
    features = {
        "total_debt": 0,
        "consumo_ratio": 0,
        "past_due_ratio": 0,
        "num_institutions": 0,
        "num_refinancings": 0,
        "has_mortgage": False,
    }
    assert classify(features) == Segment.UNBANKED
```

Correr `pytest backend/tests/` y verificar que todos pasen.

5. Implementar endpoint backend/app/api/ingest.py:

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import tempfile
from app.core.parser_cmf import parse_informe_with_fallback
from app.core.classifier import classify
from app.core.anonymizer import anonymize_rut, generate_avatar_name
from app.models.schemas import IngestResult, Avatar, Features

router = APIRouter()

@router.post("/ingest", response_model=IngestResult)
async def ingest(
    file: UploadFile = File(...),
    rut: str = Form(...),
    ingreso: float = Form(580000)
):
    """Recibe PDF informe CMF + RUT. Retorna IngestResult."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Solo PDFs")

    # Guardar PDF temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        anon_id = anonymize_rut(rut)
        avatar_name = generate_avatar_name(anon_id)

        # Fallback path por si parser falla
        fallback = Path(f"fixtures/personas/{rut[-1]}.json")  # placeholder
        features_dict = parse_informe_with_fallback(tmp_path)
        segment = classify(features_dict, ingreso_mensual=ingreso)

        # Por ahora, recommendations vacío. BE-2 las llena en BE1-2.
        return IngestResult(
            anon_id=anon_id,
            avatar=Avatar(name=avatar_name, image_url=f"/avatars/{anon_id}.svg"),
            segment=segment,
            features=Features(**features_dict),
            recommendations=[]
        )
    finally:
        tmp_path.unlink()
```

Registrar router en backend/app/main.py.

6. Verificar que `curl -X POST http://localhost:8000/ingest -F file=@maria.pdf -F rut=12345678-9`
   retorna IngestResult válido.

ENTREGABLES:
- Parser CMF funcional contra el informe de María.
- Classifier con tests pasando.
- Endpoint /ingest devolviendo IngestResult.

NO HAGAS:
- No llames a Claude ni a ningún LLM en esta capa.
- No agregues autenticación.
- No persistas todavía (BE1-2 lo hace).

AL TERMINAR:
git add . && git commit -m "feat(be1): parser cmf + classifier + /ingest endpoint" && git push
```

---

## MEGAPROMPT BE1-2: Catalog matcher + persistencia (90 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: catálogo de recomendaciones (cargado desde JSON que produjo BE-2) + matcher
+ persistencia SQLite + endpoint /profile.

PRE-REQUISITO: BE-2 entregó fixtures/recommendations.json con al menos 12 entries.

TAREAS:

1. Implementar backend/app/core/catalog_matcher.py:

```python
import json
from pathlib import Path
from typing import List
from app.models.schemas import Recommendation, Segment

class CatalogMatcher:
    def __init__(self, catalog_path: Path):
        with open(catalog_path) as f:
            self._catalog = json.load(f)

    def match(self, segment: Segment, dominant_signal: str, max_results: int = 4) -> List[Recommendation]:
        """
        Retorna recomendaciones priorizadas para un segment + signal.
        Lógica:
        - Filtrar por segment.
        - Priorizar las que matchean trigger == dominant_signal.
        - Después por priority asc.
        - Limitar a max_results.
        """
        candidates = [r for r in self._catalog if r["segment"] == segment.value]

        # Marcar matches con dominant_signal
        for c in candidates:
            c["_score"] = (
                0 if c.get("trigger") == dominant_signal else 100
            ) + c.get("priority", 99)

        candidates.sort(key=lambda x: x["_score"])
        results = candidates[:max_results]

        return [
            Recommendation(
                id=r["id"],
                title=r["title"],
                trigger=r.get("trigger", ""),
                action=r.get("action", ""),
                priority=r.get("priority", 99)
            )
            for r in results
        ]


# Singleton para el endpoint
_matcher = None

def get_matcher() -> CatalogMatcher:
    global _matcher
    if _matcher is None:
        _matcher = CatalogMatcher(Path("fixtures/recommendations.json"))
    return _matcher
```

2. Implementar backend/app/db/sqlite.py:

```python
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./defensor.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ProfileRecord(Base):
    __tablename__ = "profiles"
    anon_id = Column(String, primary_key=True)
    segment = Column(String)
    features = Column(JSON)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

3. Actualizar /ingest para:
   - Llamar a catalog_matcher.match() después de classify.
   - Persistir el ProfileRecord.
   - Retornar IngestResult con recommendations llenas.

4. Implementar backend/app/api/profile.py:

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.sqlite import get_db, ProfileRecord
from app.models.schemas import IngestResult, Avatar, Features, Recommendation
from app.core.anonymizer import generate_avatar_name

router = APIRouter()

@router.get("/profile/{anon_id}", response_model=IngestResult)
def get_profile(anon_id: str, db: Session = Depends(get_db)):
    record = db.query(ProfileRecord).filter_by(anon_id=anon_id).first()
    if not record:
        raise HTTPException(404, "Perfil no encontrado")
    return IngestResult(
        anon_id=record.anon_id,
        avatar=Avatar(name=generate_avatar_name(record.anon_id), image_url=f"/avatars/{record.anon_id}.svg"),
        segment=record.segment,
        features=Features(**record.features),
        recommendations=[Recommendation(**r) for r in record.recommendations]
    )
```

5. Implementar backend/app/api/alerts.py:

```python
from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter()

ALERTS_MOCK = [
    {
        "id": "alert_001",
        "title": "Nueva tasa máxima convencional vigente",
        "description": "La CMF actualizó la TMC para créditos de consumo. Ahora es 38.21% anual.",
        "source": "CMF",
        "date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        "url": "https://cmfchile.cl"
    },
    {
        "id": "alert_002",
        "title": "SERNAC inicia mediación contra retail por cláusulas abusivas",
        "description": "Mediación colectiva afecta a 2 millones de clientes.",
        "source": "SERNAC",
        "date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "url": "https://sernac.cl"
    },
    {
        "id": "alert_003",
        "title": "Ley 21.398 obliga a portabilidad financiera en 4 días",
        "description": "Si te demoran más, puedes reclamar al SERNAC.",
        "source": "Diario Oficial",
        "date": (datetime.utcnow() - timedelta(days=15)).isoformat(),
        "url": "https://leychile.cl"
    },
    {
        "id": "alert_004",
        "title": "Nueva ley de protección de datos personales (Ley 21.719)",
        "description": "Vigente desde 2026. Tus derechos se amplían.",
        "source": "Ministerio de Hacienda",
        "date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        "url": "https://leychile.cl"
    }
]

@router.get("/alerts")
def get_alerts():
    return ALERTS_MOCK
```

6. Stub backend/app/api/carta.py — registra el endpoint /carta/{anon_id} pero la lógica
   real la hace BE-2 en su servicio. Por ahora, llamar a un servicio stub que retorna
   un PDF de ejemplo.

ENTREGABLES:
- Catalog matcher funcional.
- Persistencia SQLite operativa.
- /ingest persiste y retorna IngestResult con recommendations.
- /profile/{anon_id} funciona.
- /alerts retorna lista mock.
- Tests adicionales para catalog_matcher.

NO HAGAS:
- No agregues autenticación.
- No introduzcas LLMs.

AL TERMINAR:
git add . && git commit -m "feat(be1): catalog matcher + sqlite + /profile + /alerts" && git push
```

---

## MEGAPROMPT BE1-3: Integración FE + bug bash (60 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: el frontend está conectándose a tu backend. Asegurar que todo funcione,
arreglar bugs detectados en integración.

TAREAS:

1. Setup CORS si no está:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. Verificar end-to-end con FE corriendo:
   - Subir PDF de María desde /upload del FE.
   - Verificar que llega a /ingest.
   - Verificar que retorna IngestResult bien estructurado.
   - Verificar que /diagnostico del FE renderiza datos reales.

3. Manejo robusto de errores:
   - Si el PDF no se puede parsear: retornar 422 con mensaje claro.
   - Si el classifier falla por features inválidos: retornar 500 con log.
   - Logging estructurado: cada request loggea método, path, status, duration.

4. Endpoints de health más detallados:

```python
@app.get("/health")
def health():
    return {
        "ok": True,
        "version": "0.1.0",
        "checks": {
            "db": _check_db(),
            "catalog": _check_catalog(),
            "mcp_server": _check_mcp()
        }
    }
```

5. Bug bash con FE: 30 minutos en par con la persona FE probando todo el flow.

6. Documentar API en docs/API_CONTRACT.md con ejemplos de curl reales.

ENTREGABLES:
- Backend integrado con FE sin errores.
- /health con checks detallados.
- Logging estructurado.
- Documentación de API actualizada.

AL TERMINAR:
git add . && git commit -m "fix(be1): integration with FE + error handling" && git push
```

---

## MEGAPROMPT BE1-4: Fixtures de Carlos y Pedro + pre-parseo (60 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: tener los 3 fixtures funcionando perfectos. Pre-parseo de los 3 informes a JSON
limpio para garantizar demo sin riesgos.

TAREAS:

1. Crear fixtures/personas/carlos.json:
   - Avatar generado, segment functional.
   - Features de un Nivel 3: hipoteca, créditos pequeños, sin moras, carga <30%.

2. Crear fixtures/personas/pedro.json:
   - Avatar generado, segment recently_banked.
   - Features mínimos: 1 cuenta vista, sin créditos.

3. Crear fixtures/personas/cero.json:
   - segment unbanked.
   - Features todos en cero.
   - recommendations vacías o con mensaje educativo.

4. Implementar fallback path en parse_informe_with_fallback:

```python
def parse_informe_with_fallback(pdf_path: Path, persona_hint: str = None) -> Dict:
    # Si persona_hint está, usar fixture directo (modo demo)
    if persona_hint:
        fixture_path = Path(f"fixtures/personas/{persona_hint}.json")
        if fixture_path.exists():
            with open(fixture_path) as f:
                return json.load(f)["features"]

    # Si no, intentar parser real
    try:
        return parse_informe_cmf(pdf_path)
    except Exception as e:
        # Último fallback: usar maría como default
        with open("fixtures/personas/maria.json") as f:
            return json.load(f)["features"]
```

5. Endpoint /ingest acepta query param `?persona=maria|carlos|pedro|cero` para forzar
   uso del fixture (modo demo). Si no se pasa, usa parser real.

6. Test integración: subir PDF random + ?persona=maria → retorna IngestResult de María.

7. Documentar el modo demo en docs/DEMO_MODE.md:
   - Cómo activar `?persona=...`
   - Por qué existe (garantizar demo)
   - Cuándo desactivarlo (post-hackathon)

ENTREGABLES:
- 4 fixtures completos (María, Carlos, Pedro, Cero).
- Modo demo funcional vía query param.
- /ingest robusto contra fallos del parser.

AL TERMINAR:
git add . && git commit -m "feat(be1): fixtures + demo mode" && git push
```

---

## MEGAPROMPT BE1-5: Deploy a URL pública + polish final (último día)

```
[CONTEXTO COMÚN]

OBJETIVO: deploy a Railway/Render/Fly como upside del demo. Pre-cacheo de respuestas.
Bug bash final.

TAREAS:

1. Deploy a Railway (más simple):
   - Crear cuenta Railway.
   - Crear proyecto desde repo GitHub.
   - Configurar variables de entorno (HMAC_SECRET, ANTHROPIC_API_KEY, DATABASE_URL).
   - Build command: `cd backend && pip install -r requirements.txt`
   - Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Verificar que /health retorna ok.

2. Variable de entorno BACKEND_URL en frontend para apuntar a producción si se quiere.

3. Pre-cachear respuestas del concierge para los 3 fixtures:
   - Backend almacena en /tmp o en SQLite las respuestas pregrabadas.
   - Endpoint /chat consulta cache primero, si hay hit retorna. Si no, llama a Claude.

4. Bug bash final con todo el equipo:
   - Demo end-to-end con María, Carlos, Pedro.
   - Cada cita legal verificada manualmente contra el corpus.
   - Cada carta de reclamo revisada.

5. Logs limpios: sin prints, sin warnings.

ENTREGABLES:
- Backend en URL pública funcional (upside).
- Pre-cache implementado.
- Bug bash completado.

AL TERMINAR:
git add . && git commit -m "chore(be1): deploy + precache + bug bash" && git push
git tag v1.0-demo
git push --tags
```

---

## Resumen de tu trayecto BE-1 en 30 horas

| Hora | Megaprompt | Entregable |
|------|-----------|-----------|
| 0–1.5 | BE1-1 | Parser + classifier + /ingest |
| 1.5–3 | BE1-2 | Catalog matcher + SQLite + /profile + /alerts |
| 4–5 | BE1-3 | Integración con FE + error handling |
| 9–10 | BE1-4 | Fixtures de Carlos y Pedro + modo demo |
| 18–22 día 2 | BE1-5 | Deploy + pre-cache + bug bash |

Entre megaprompts: syncs con FE y BE-2, ajustes según feedback.

---

## Reglas para siempre

1. **NO LLM en este pipeline.** Si necesitas inferencia, hablar con BE-2.
2. **Determinismo.** Mismo input → mismo output. Siempre.
3. **Tests para classifier.** Cada cambio de regla = nuevo test.
4. **Sin PII.** Solo anon_id en la base de datos. Nunca RUT, nombre, email.
5. **Errores claros.** Cada 4xx/5xx debe tener mensaje útil.

---

*Fin de los megaprompts BE-1.*
