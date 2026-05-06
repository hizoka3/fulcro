# 00 — MEGAPROMPT PRINCIPAL: Setup del Repo, Guardrails y Git

> **Quién lo ejecuta:** UNA persona del equipo (idealmente BE-1, antes de que los 3 arranquen).
> **Cuándo:** hora 0, antes de que nadie escriba código de feature.
> **Output esperado:** repo inicializado en GitHub, todos los miembros pueden clonar y arrancar.
> **Tiempo estimado:** 20 minutos.

---

## Contexto del proyecto (incluir en cada megaprompt)

```
PROYECTO: Defensor — Concierge financiero con IA, anónimo, conectado a normativa CMF/SERNAC vía MCP.
HACKATHON: Anthropic, 2 días, en Chile.
EQUIPO: 3 personas (1 FE + 2 BE).
STACK: SolidStart + Tailwind (frontend), FastAPI + Python (backend), Claude Sonnet, MCP server, ChromaDB, SQLite.

DECISIONES ARQUITECTÓNICAS NO NEGOCIABLES:
1. Pipeline determinístico (parser → classifier → catalog matcher) decide segment + recommendations. Sin LLM.
2. Concierge conversacional (Claude + tools) ENCIMA del pipeline. Recibe ProfileSnapshot como contexto. NO clasifica. NO inventa recomendaciones.
3. Catálogo curado (JSON) y RAG sobre normativa coexisten: catálogo = qué decir; RAG = con qué cita legal fundamentar.
4. MCP server SEPARADO del backend principal (es la pieza open source).
5. Hash HMAC del RUT, nunca persistir RUT.
6. Citas legales SOLO desde contexto recuperado por RAG. Prohibido citar de memoria.
7. SQLite local. Sesión efímera.
8. Pre-parseo de informes a JSON antes del demo (la falla es para los débiles).

USUARIO PROTAGONISTA: María Silva (avatar Cóndor 4521), Nivel 2 - Bancarizado Vulnerable.
```

---

## El Megaprompt (pegar a Claude Code o similar)

```
Eres un ingeniero senior ayudándome a inicializar el repositorio del proyecto Defensor.

CONTEXTO COMPLETO:
[pegar el bloque de "Contexto del proyecto" de arriba]

OBJETIVO DE ESTA SESIÓN:
Crear la estructura inicial del repo, archivos de configuración, guardrails de seguridad,
y dejar todo listo para que 3 desarrolladores (1 FE, 2 BE) puedan clonar y arrancar
sin bloquearse.

TAREAS A EJECUTAR EN ORDEN:

1. Crear la estructura de carpetas:
defensor/
├── README.md
├── .gitignore
├── .env.example
├── docs/
│   ├── PLAN_DEFINITIVO.md     (lo pego yo después)
│   ├── DIVISION_TAREAS.md     (lo pego yo después)
│   └── API_CONTRACT.md
├── fixtures/
│   ├── personas/
│   │   ├── maria.json
│   │   ├── carlos.json
│   │   └── pedro.json
│   ├── recommendations.json
│   └── informes_pdf/          (carpeta para los 3 PDFs reales — NO commitear PDFs)
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .python-version
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            (FastAPI entrypoint con /health)
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py
│   │   │   ├── chat.py
│   │   │   ├── carta.py
│   │   │   └── alerts.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── parser_cmf.py
│   │   │   ├── classifier.py
│   │   │   ├── anonymizer.py
│   │   │   └── catalog_matcher.py
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── concierge.py
│   │   │   ├── prompts.py
│   │   │   └── tools.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── carta_reclamo.py
│   │   │   ├── plan_salida.py     (mock)
│   │   │   └── comparador.py      (mock)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── sqlite.py
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py         (Pydantic models según API contract)
│   └── tests/
│       └── test_classifier.py
├── mcp_server/
│   ├── pyproject.toml
│   ├── server.py
│   ├── data/
│   │   ├── corpus_cmf/            (textos legales descargados)
│   │   └── chroma/                (vector store)
│   └── rag/
│       ├── __init__.py
│       ├── indexer.py
│       └── retriever.py
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    └── src/
        ├── app.tsx
        ├── routes/
        │   ├── index.tsx          (landing + upload)
        │   ├── diagnostico.tsx
        │   ├── concierge.tsx
        │   ├── carta.tsx
        │   ├── plan.tsx
        │   ├── comparador.tsx
        │   └── alertas.tsx
        ├── components/
        │   ├── Avatar.tsx
        │   ├── DeudaCard.tsx
        │   ├── Semaforo.tsx
        │   └── ChatMessage.tsx
        └── lib/
            ├── api.ts             (cliente API con mocks)
            └── types.ts           (TS types según API contract)

2. Generar archivos clave:

a) **README.md** — descripción del proyecto, stack, cómo correr cada componente
   (frontend, backend, mcp_server), roles del equipo, link a docs/PLAN_DEFINITIVO.md.

b) **.gitignore** — Python (.venv, __pycache__, .env, *.pyc), Node (node_modules, dist),
   IDEs (.vscode/, .idea/), datos sensibles (fixtures/informes_pdf/*.pdf), ChromaDB local
   (mcp_server/data/chroma/), DB local (*.db, *.sqlite), .env files.

c) **.env.example** con variables necesarias:
   - ANTHROPIC_API_KEY
   - HMAC_SECRET (para anonimización; generar uno aleatorio)
   - DATABASE_URL (sqlite:///./defensor.db)
   - MCP_SERVER_URL (http://localhost:8001)
   - VOYAGE_API_KEY (opcional, para embeddings)

d) **backend/requirements.txt**:
   fastapi==0.110.0
   uvicorn[standard]==0.27.0
   pydantic==2.6.0
   pdfplumber==0.10.3
   anthropic==0.34.0
   chromadb==0.4.22
   sentence-transformers==2.3.0
   python-multipart==0.0.9
   python-dotenv==1.0.0
   sqlalchemy==2.0.25
   pytest==8.0.0
   httpx==0.26.0

e) **backend/app/main.py** con FastAPI app inicializada, CORS abierto a localhost:3000,
   endpoint /health retornando {"ok": true}, registro de routers (aún vacíos).

f) **backend/app/models/schemas.py** con Pydantic models EXACTOS según el API contract:

```python
from pydantic import BaseModel
from typing import Literal, Optional
from enum import Enum

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
    explanation_short: Optional[str] = None
    articulos_referencia: Optional[list[str]] = None

class IngestResult(BaseModel):
    anon_id: str
    avatar: Avatar
    segment: Segment
    features: Features
    recommendations: list[Recommendation]
```

g) **frontend/src/lib/types.ts** — espejo TypeScript de schemas.py (Segment como union,
   Features, Recommendation, IngestResult).

h) **frontend/src/lib/api.ts** — cliente con función `ingest(file)` que retorna fixture
   hardcodeado de María (mismo JSON que en docs/API_CONTRACT.md). Funciones stub para
   chat, carta, alerts.

i) **fixtures/personas/maria.json** — IngestResult de María según API contract:

```json
{
  "anon_id": "a3f9d2e1b4c5",
  "avatar": {
    "name": "Cóndor 4521",
    "image_url": "/avatars/condor_4521.svg"
  },
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

j) **fixtures/personas/carlos.json** y **pedro.json** — análogos pero con segments
   functional y recently_banked respectivamente. Inventa features razonables.

k) **fixtures/recommendations.json** — array vacío por ahora (BE-2 lo llena).

l) **docs/API_CONTRACT.md** — copia textual del contract de la sección 10 del
   PLAN_DEFINITIVO con ejemplos de request/response para cada endpoint.

m) **mcp_server/server.py** — esqueleto MCP server en Python que expone una tool
   `consultar_normativa(query: str, k: int = 3)` que por ahora retorna texto hardcodeado.

n) **frontend/package.json** con dependencias mínimas:
   - solid-js ^1.8
   - @solidjs/router ^0.10
   - @solidjs/start ^0.5
   - tailwindcss ^3.4
   - typescript ^5.3
   - vite ^5.0

3. **Inicializar git y subir a GitHub:**
   - git init
   - git add .
   - git commit -m "chore: initial scaffold for Defensor"
   - Crear repo en GitHub (privado por ahora) llamado "defensor"
   - git remote add origin git@github.com:[USER]/defensor.git
   - Crear ramas: main, develop, feature/be1-pipeline, feature/be2-agent, feature/fe-ui
   - Push a GitHub.

4. **Configurar guardrails básicos:**

a) **GitHub branch protection en main**: requires PR, requires 1 approval, no force push.

b) **.github/CODEOWNERS** para auto-asignar reviews:
   /backend/app/core/      @[BE-1]
   /backend/app/api/       @[BE-1]
   /backend/app/agent/     @[BE-2]
   /backend/app/services/  @[BE-2]
   /mcp_server/            @[BE-2]
   /frontend/              @[FE]

c) **.github/PULL_REQUEST_TEMPLATE.md** corto:
   - Qué cambia
   - Por qué
   - Cómo se prueba
   - Checkbox: "Respeta el API contract" / "No introduce LLM en el pipeline determinístico"
     / "No hace citas legales sin RAG"

d) Pre-commit hooks opcional (si hay tiempo): ruff para Python, prettier para TS.

INSTRUCCIONES DE EJECUCIÓN:

- Crea cada archivo con su contenido completo. No dejes TODOs sin contenido.
- Verifica que `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
  arranca sin error.
- Verifica que `cd frontend && npm install && npm run dev` arranca sin error.
- Verifica que `cd mcp_server && python server.py` arranca sin error.

NO HAGAS:
- No agregues funcionalidad de feature (eso lo hacen los desarrolladores en sus megaprompts).
- No instales dependencias que no estén en la lista.
- No agregues autenticación, login, ni base de datos en la nube.
- No dejes prints debug ni código comentado.

CUANDO TERMINES:
1. Imprime el árbol completo del repo.
2. Imprime la URL del repo en GitHub.
3. Imprime los comandos exactos para que cada miembro del equipo clone y arranque su parte.
4. Confirma que los 3 servicios (backend, mcp_server, frontend) corren simultáneamente
   en localhost sin error.
```

---

## Checklist post-ejecución

Antes de dar por terminado este megaprompt, verificar:

- [ ] Repo en GitHub accesible para los 3 miembros.
- [ ] `main` protegida, ramas feature creadas.
- [ ] Cada miembro puede clonar e instalar sin error.
- [ ] FastAPI levanta en `localhost:8000`.
- [ ] MCP server levanta en `localhost:8001`.
- [ ] SolidStart levanta en `localhost:3000`.
- [ ] El fixture de María se sirve correctamente desde mocks de FE.
- [ ] `.env.example` está claro y `.env` está en gitignore.
- [ ] PR template y CODEOWNERS funcionando.

---

## Comandos para los miembros del equipo después del setup

**Para todos:**
```bash
git clone git@github.com:[USER]/defensor.git
cd defensor
cp .env.example .env
# Editar .env con sus claves
```

**FE:**
```bash
cd frontend
npm install
npm run dev
git checkout feature/fe-ui
```

**BE-1:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
git checkout feature/be1-pipeline
```

**BE-2 (TÚ):**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
git checkout feature/be2-agent

# En otra terminal:
cd mcp_server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # crear este archivo
python server.py
```

---

*Fin del megaprompt 00. Una vez completado, los 3 megaprompts de equipo (FE, BE-1, BE-2) pueden ejecutarse en paralelo.*
