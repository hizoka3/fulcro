# API Contract

Locked schema for FE / BE-1 / BE-2 integration. **Do not deviate without team agreement.**

---

## Endpoints

### `POST /ingest`

Accept a CMF *Informe de Deudas* PDF + RUT, classify, persist, return `IngestResult`.

**Request** — `multipart/form-data`:

| field | type | required | notes |
|---|---|---|---|
| `file` | PDF | yes | The CMF Informe de Deudas |
| `rut` | string | yes | Chilean RUT, e.g. `"19523183-4"` (any format accepted) |
| `ingreso` | float | no | Monthly income in CLP. Default: `580000` |

**Response** — `200 OK`, body = `IngestResult` (see below).

**Errors**:
- `400` — file is not a PDF
- `422` — PDF could not be parsed
- `500` — classifier failure

---

### `GET /profile/{anon_id}`

Retrieve a previously-stored profile.

**Response** — `200 OK`, body = `IngestResult`.
**Errors**: `404` if no record.

---

### `POST /carta/{anon_id}`

Generate complaint letter as a PDF blob. Lives in BE-1's API surface but the underlying generation is BE-2's `services/carta_reclamo.py`.

**Response** — `200 OK`, `Content-Type: application/pdf`.

---

### `GET /alerts`

Return mock array of regulatory alerts (CMF / SERNAC / leyes).

**Response** — `200 OK`, body = `Alert[]`:

```json
[
  {
    "id": "alert_001",
    "title": "...",
    "description": "...",
    "source": "CMF",
    "date": "2026-05-04T...",
    "url": "https://..."
  }
]
```

---

### `POST /chat/{anon_id}`

SSE stream of concierge messages. **Owned by BE-2.**

---

### `GET /health`

```json
{ "ok": true, "version": "0.1.0" }
```

In BE1-3 this expands to include per-component checks (`db`, `catalog`, `mcp_server`).

---

## Schemas

```python
class Segment(str, Enum):
    UNBANKED = "unbanked"
    RECENTLY_BANKED = "recently_banked"
    VULNERABLE = "vulnerable"
    FUNCTIONAL = "functional"

class Avatar(BaseModel):
    name: str
    image_url: str

class Features(BaseModel):
    total_debt: float
    consumo_ratio: float
    past_due_ratio: float
    num_institutions: int
    num_refinancings: int
    has_mortgage: bool
    carga_financiera_pct: float
    dominant_signal: str

class Recommendation(BaseModel):
    id: str
    title: str
    trigger: str
    action: str
    priority: int
    explanation_short: Optional[str]
    articulos_referencia: Optional[list[str]]

class IngestResult(BaseModel):
    anon_id: str
    avatar: Avatar
    segment: Segment
    features: Features
    recommendations: list[Recommendation]
```

Source of truth: `backend/app/models/schemas.py`.

---

## Example response (María)

```json
{
  "anon_id": "a3f9d2e1b4c5",
  "avatar": {"name": "Cóndor 4521", "image_url": "/avatars/condor_4521.svg"},
  "segment": "vulnerable",
  "features": {
    "total_debt": 4500000,
    "consumo_ratio": 0.82,
    "past_due_ratio": 0.15,
    "num_institutions": 5,
    "num_refinancings": 2,
    "has_mortgage": false,
    "carga_financiera_pct": 0.52,
    "dominant_signal": "high_consumo_ratio"
  },
  "recommendations": [
    {
      "id": "vuln_001",
      "title": "Consolida tus créditos de consumo",
      "trigger": "high_consumo_ratio",
      "action": "compare_consolidation_offers",
      "priority": 1
    }
  ]
}
```
