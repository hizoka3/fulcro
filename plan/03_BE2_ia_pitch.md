# 03 — MEGAPROMPTS BACKEND-2 (BE-2): IA, MCP, RAG, Pitch

> **Quién:** TÚ. Líder de visión, presentas el pitch.
> **Stack:** FastAPI + Anthropic SDK + ChromaDB + sentence-transformers + MCP Python SDK.
> **Pre-requisito:** Megaprompt 00 (setup) ejecutado. Repo clonado. `.venv` activo en
> backend/ y mcp_server/.
> **Total de megaprompts:** 6, secuenciales.

---

## Reglas para usar estos megaprompts

1. Ejecutar uno a la vez. Esperar a que termine antes del siguiente.
2. Cada megaprompt incluye su contexto — pegar entero a Claude Code o a tu agente de coding.
3. Tu rol es triple: IA + contenido + pitch. Megaprompts 1-4 son código. 5-6 son
   pitch, demo, contenido.
4. Después de cada megaprompt: `git add . && git commit -m "feat(be2): [resumen]" && git push`.

---

## CONTEXTO COMÚN (incluir al inicio de cada megaprompt)

```
PROYECTO: Defensor — Concierge financiero con IA.
ROL: Backend-2 (IA + Pitch). Responsable de:
- Concierge conversacional (Claude Sonnet + tools).
- MCP server con RAG sobre normativa CMF/SERNAC.
- Catálogo de recomendaciones (contenido).
- Generación de carta de reclamo.
- Pitch y demo.

DECISIONES ARQUITECTÓNICAS:
1. Tu capa va ENCIMA del pipeline determinístico de BE-1. Recibes ProfileSnapshot como contexto.
2. NO clasificas. NO inventas recomendaciones (las toma del catálogo de BE-1).
3. Citas legales SOLO desde RAG. Prohibido citar de memoria del modelo.
4. MCP server SEPARADO del backend principal — corre en localhost:8001.
5. El concierge usa Claude Sonnet 4.6 con tools y prompt caching.

STACK:
- Anthropic SDK con Sonnet 4.6.
- MCP Python SDK para el server.
- ChromaDB para vector store local.
- sentence-transformers para embeddings (modelo multilingüe).

USUARIO PROTAGONISTA: María Silva, Cóndor 4521, Nivel 2 - Bancarizado Vulnerable.
```

---

## MEGAPROMPT BE2-1: Catálogo de contenido + corpus normativo (90 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: este es trabajo de CONTENIDO, no de código. Es lo más alto leverage del fin de
semana. Sin un buen catálogo y un buen corpus, el concierge no tiene nada que decir.

TAREAS:

1. Descargar corpus normativo a mcp_server/data/corpus_cmf/:

```bash
mkdir -p mcp_server/data/corpus_cmf
cd mcp_server/data/corpus_cmf

# Descargar leyes desde leychile.cl en formato txt cuando posible
# Si solo hay PDF, convertir con pdftotext
```

Leyes prioritarias (en este orden):
- Ley 19.496 (Protección al Consumidor) — focos: arts. 16, 17 A-L
- Ley 20.555 (SERNAC Financiero)
- Ley 18.010 (Operaciones de Crédito de Dinero) — foco: arts. 6, 6 bis (TMC)
- Ley 21.398 (Pro-Consumidor)
- Ley 21.236 (Portabilidad Financiera)

Si tarda mucho descargar, pídele a Claude (en otra ventana) que te genere un JSON con los
artículos clave ya extraídos:

```
TAREA: Genérame un JSON con los artículos más importantes de la Ley 19.496 sobre cláusulas
abusivas (arts. 16 a 17 L). Para cada artículo: numero, titulo, texto_completo (literal,
exacto). Solo los más relevantes para detección de cláusulas abusivas en contratos
financieros. Output: JSON array.
```

Guardar en mcp_server/data/corpus_cmf/ley_19496_extracto.json.

Repetir para cada ley. Total: 5 archivos JSON con artículos clave.

2. Escribir el catálogo de recomendaciones en fixtures/recommendations.json.

Formato exacto:

```json
[
  {
    "id": "vuln_001",
    "segment": "vulnerable",
    "trigger": "high_consumo_ratio",
    "title": "Consolida tus créditos de consumo",
    "explanation_short": "Más del 70% de tu deuda está en tarjetas y créditos de consumo, los más caros del sistema. Consolidar puede reducir tu CAE total entre 15% y 30%.",
    "action": "compare_consolidation_offers",
    "articulos_referencia": ["Ley 18.010 Art. 6", "Ley 19.496 Art. 17B"],
    "priority": 1
  },
  {
    "id": "vuln_002",
    "segment": "vulnerable",
    "trigger": "multiple_refinancings",
    "title": "Cuidado con el ciclo de refinanciamiento",
    "explanation_short": "Ya refinanciaste el mismo crédito varias veces. Cada refinanciamiento agrega comisiones y extiende el plazo. Considera un crédito de consolidación con tasa fija menor.",
    "action": "evaluate_consolidation_loan",
    "articulos_referencia": ["Ley 19.496 Art. 17H"],
    "priority": 1
  },
  ...
]
```

Generar al menos 12 entries para "vulnerable" cubriendo:
- high_consumo_ratio
- multiple_refinancings
- past_due_present
- many_institutions
- carga_financiera_alta
- clausula_abusiva_detectada
- tasa_cerca_tmc
- mora_temprana
- producto_retail_dominante
- avance_efectivo_alto
- comisiones_excesivas
- portabilidad_disponible

Y al menos 3 entries para cada otro segment (recently_banked, functional, unbanked).

Tono de las explicaciones: chileno claro, sin jerga, empático, accionable. Cada
explanation_short ≤25 palabras.

3. Escribir las plantillas de cartas de reclamo en backend/app/services/templates/:

a) carta_sernac.txt — plantilla con placeholders:

```
RECLAMO ANTE EL SERVICIO NACIONAL DEL CONSUMIDOR (SERNAC)

Fecha: {fecha}
Reclamante: {avatar_nombre} (identidad anonimizada vía Defensor)

INSTITUCIÓN RECLAMADA:
{institucion}

MOTIVO DEL RECLAMO:
{motivo}

FUNDAMENTO LEGAL:
{articulos_invocados}

DESCRIPCIÓN DETALLADA:
{descripcion}

PETICIÓN:
{peticion}

DOCUMENTOS DE RESPALDO:
- Informe de deuda CMF (anonimizado)
- Contrato del producto (si aplica)

Firma:
{avatar_nombre}
Reclamo generado vía Defensor (defensorchile.org)
```

b) carta_portabilidad.txt — plantilla para solicitud de portabilidad financiera.

c) carta_clausula_abusiva.txt — plantilla específica para denunciar cláusula abusiva.

ENTREGABLES:
- 5 archivos JSON con artículos extraídos en mcp_server/data/corpus_cmf/.
- fixtures/recommendations.json con ≥20 entries totales.
- 3 plantillas de carta en backend/app/services/templates/.

NO HAGAS:
- No agregues código todavía. Solo contenido.
- No inventes artículos de leyes. Si no estás seguro, déjalo en blanco con TODO.
- No copies textos de leyes copyright (las leyes chilenas son de dominio público).

AL TERMINAR:
git add . && git commit -m "feat(be2): corpus normativo + catalog + templates" && git push
```

---

## MEGAPROMPT BE2-2: MCP Server con RAG (90 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: MCP server funcional que expone una tool `consultar_normativa(query, k)` con
RAG real sobre el corpus indexado.

TAREAS:

1. Implementar mcp_server/rag/indexer.py:

```python
import json
from pathlib import Path
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer

class NormativaIndexer:
    def __init__(self, corpus_dir: Path, db_dir: Path):
        self.corpus_dir = corpus_dir
        self.client = chromadb.PersistentClient(path=str(db_dir))
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.collection = self.client.get_or_create_collection(
            name="normativa_cmf",
            metadata={"hnsw:space": "cosine"}
        )

    def index_corpus(self):
        """Indexa todos los archivos JSON del corpus."""
        documents = []
        metadatas = []
        ids = []

        for json_file in self.corpus_dir.glob("*.json"):
            with open(json_file) as f:
                articulos = json.load(f)
                ley_nombre = json_file.stem  # ej "ley_19496_extracto"

                for art in articulos:
                    doc = f"{art['titulo']}\n\n{art['texto_completo']}"
                    documents.append(doc)
                    metadatas.append({
                        "ley": ley_nombre,
                        "articulo": art["numero"],
                        "titulo": art["titulo"]
                    })
                    ids.append(f"{ley_nombre}_{art['numero']}")

        if not documents:
            print("⚠ No hay documentos para indexar")
            return

        embeddings = self.model.encode(documents, show_progress_bar=True).tolist()

        # Limpiar colección existente
        existing = self.collection.get()
        if existing["ids"]:
            self.collection.delete(ids=existing["ids"])

        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✓ Indexados {len(documents)} artículos")


if __name__ == "__main__":
    indexer = NormativaIndexer(
        corpus_dir=Path("data/corpus_cmf"),
        db_dir=Path("data/chroma")
    )
    indexer.index_corpus()
```

Correr: `cd mcp_server && python rag/indexer.py`. Verificar que indexa sin error.

2. Implementar mcp_server/rag/retriever.py:

```python
from pathlib import Path
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer

class NormativaRetriever:
    def __init__(self, db_dir: Path):
        self.client = chromadb.PersistentClient(path=str(db_dir))
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.collection = self.client.get_collection("normativa_cmf")

    def query(self, text: str, k: int = 3) -> List[Dict]:
        embedding = self.model.encode([text]).tolist()
        results = self.collection.query(
            query_embeddings=embedding,
            n_results=k
        )
        articulos = []
        for i in range(len(results["ids"][0])):
            articulos.append({
                "ley": results["metadatas"][0][i]["ley"],
                "articulo": results["metadatas"][0][i]["articulo"],
                "titulo": results["metadatas"][0][i]["titulo"],
                "texto": results["documents"][0][i],
                "score": 1 - results["distances"][0][i]
            })
        return articulos
```

3. Implementar mcp_server/server.py con MCP Python SDK:

```python
import asyncio
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from rag.retriever import NormativaRetriever

retriever = NormativaRetriever(Path("data/chroma"))

server = Server("defensor-normativa")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="consultar_normativa",
            description=(
                "Busca artículos de normativa chilena (Ley 19.496, 20.555, 18.010, "
                "21.398, 21.236) relevantes a una situación. Retorna los artículos "
                "más relevantes con su texto completo y referencia exacta."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Pregunta o tema en lenguaje natural"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Cantidad de artículos a retornar (default 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "consultar_normativa":
        results = retriever.query(arguments["query"], k=arguments.get("k", 3))
        text_response = "\n\n---\n\n".join([
            f"**{r['titulo']}** (Ley {r['ley']}, Art. {r['articulo']})\n\n{r['texto']}"
            for r in results
        ])
        return [TextContent(type="text", text=text_response)]
    raise ValueError(f"Tool desconocido: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

4. Test del MCP server:
   - Correr `python mcp_server/server.py`.
   - En otra terminal, usar el SDK de MCP cliente para listar tools y llamar a
     `consultar_normativa("cláusulas abusivas")`.
   - Verificar que retorna artículos relevantes.

5. Documentar en mcp_server/README.md:
   - Cómo correrlo.
   - Cómo consumirlo desde el backend principal.
   - Qué corpus está indexado.

ENTREGABLES:
- mcp_server/rag/indexer.py funcional. Corpus indexado en data/chroma/.
- mcp_server/rag/retriever.py con tests.
- mcp_server/server.py exponiendo `consultar_normativa` vía MCP.
- README del MCP server.

NO HAGAS:
- No agregues otras tools al MCP server todavía. Solo `consultar_normativa`.
- No mezcles el MCP server con el backend principal. Son procesos separados.

AL TERMINAR:
git add . && git commit -m "feat(be2): MCP server with RAG over CMF corpus" && git push
```

---

## MEGAPROMPT BE2-3: Concierge agent (Claude + tools) (90 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: agente concierge funcional que recibe ProfileSnapshot, mantiene conversación,
usa tools, cita normativa via RAG.

TAREAS:

1. Implementar backend/app/agent/prompts.py:

```python
SYSTEM_PROMPT_BASE = """Eres el Concierge Financiero de Defensor, un asistente que ayuda
a personas en Chile a entender su situación financiera y ejercer sus derechos.

PRINCIPIOS INVIOLABLES:

1. Nunca inventes normativa. Si citas una ley o artículo, debe venir del contexto
   recuperado vía la herramienta consultar_normativa. Si no la tienes, dilo claramente.

2. Nunca inventes recomendaciones. Las recomendaciones del usuario vienen del campo
   `recommendations` del ProfileSnapshot. Tú las explicas, contextualizas y respondes
   preguntas sobre ellas.

3. Cada respuesta accionable termina en un siguiente paso concreto.

4. Habla en chileno claro. Cero jerga financiera sin traducir. Si usas un término técnico,
   explícalo en paréntesis la primera vez.

5. No das consejo de inversión específico. No reemplazas asesoría legal formal. Lo dices
   cuando corresponda, sin saturar.

6. Empatía sin paternalismo. El usuario es adulto y capaz; tu rol es nivelar información,
   no tutelar.

CITAS: cuando uses normativa, formato: "según el Art. X de la Ley Y..." con cita textual
breve entre comillas (máx 15 palabras). SIEMPRE indica la ley específica.

CONTEXTO DEL USUARIO:
- Avatar: {avatar_nombre}
- Nivel: {nivel}
- Features: {features_json}
- Recomendaciones del catálogo: {recommendations_json}

{adendum_nivel}
"""

ADENDUM_VULNERABLE = """
NIVEL ESPECÍFICO: Bancarizado Vulnerable

Esta persona tiene múltiples productos crediticios y señales de vulnerabilidad. Probablemente
está estresada por su situación financiera.

Tu foco:
- Diagnóstico claro y sin asustar de su situación.
- Identificar problemas específicos: cláusulas abusivas, tasas excesivas, refinanciamientos
  problemáticos, productos redundantes.
- Proponer plan de acción priorizado: qué pagar primero, qué refinanciar, qué portar, qué
  reclamar.
- Generar documentos accionables (cartas de reclamo, solicitudes de portabilidad) cuando
  corresponda.
- Educar contextualmente sobre los conceptos que aparecen en su caso.

Tono: directo y protector. Esta persona puede estar estresada; sé claro pero firme.
NUNCA minimices la deuda ni la sobredramatices. Datos en la mano, calma profesional.

Primera respuesta esperada al "Hola":
"Hola, [avatar_nombre]. Soy tu Defensor. Acabo de leer tu informe de deudas. Antes de
cualquier cosa: no estás solo en esto y no es tu culpa que el sistema sea opaco. Lo que
tengo para ti son tres cosas concretas que detecté, una por una, con la ley en la mano.
¿Empezamos por la más urgente o prefieres ver el panorama completo primero?"
"""

ADENDUM_FUNCTIONAL = """
NIVEL ESPECÍFICO: Usuario Funcional

Tiene sus finanzas razonablemente ordenadas pero subóptimas.

Tu foco: oportunidades de optimización, negociación de tasas, primeros pasos en inversión,
planificación de metas.

Tono: par técnico, asume conocimiento intermedio, vé al grano.
"""

ADENDUM_RECENTLY_BANKED = """
NIVEL ESPECÍFICO: Recién Bancarizado

Tiene cuenta vista pero historial financiero mínimo.

Tu foco: enseñar uso responsable de débito, cuándo dar el paso a primera tarjeta de crédito,
importancia del historial, ahorro inicial.

Tono: alentador, celebra avances pequeños.
"""

ADENDUM_UNBANKED = """
NIVEL ESPECÍFICO: No Bancarizado Excluido

No tiene productos financieros formales.

Tu foco: alfabetización básica, primer producto seguro (CuentaRUT, cuenta vista gratuita),
advertir sobre prestamistas informales, construcción de historial.

Tono: muy didáctico, ejemplos cotidianos, evita jerga.
"""

ADENDUMS = {
    "vulnerable": ADENDUM_VULNERABLE,
    "functional": ADENDUM_FUNCTIONAL,
    "recently_banked": ADENDUM_RECENTLY_BANKED,
    "unbanked": ADENDUM_UNBANKED
}

def build_system_prompt(snapshot: dict) -> str:
    return SYSTEM_PROMPT_BASE.format(
        avatar_nombre=snapshot["avatar"]["name"],
        nivel=snapshot["segment"],
        features_json=str(snapshot["features"]),
        recommendations_json=str(snapshot["recommendations"]),
        adendum_nivel=ADENDUMS.get(snapshot["segment"], "")
    )
```

2. Implementar backend/app/agent/tools.py:

```python
TOOLS = [
    {
        "name": "consultar_normativa",
        "description": "Busca artículos de normativa chilena relevantes. ÚSALA SIEMPRE antes de citar una ley. Retorna artículos con texto completo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k": {"type": "integer", "default": 3}
            },
            "required": ["query"]
        }
    },
    {
        "name": "calcular_carga_financiera",
        "description": "Calcula carga financiera del usuario dado un ingreso mensual.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ingreso_mensual": {"type": "number"}
            },
            "required": ["ingreso_mensual"]
        }
    },
    {
        "name": "explicar_problema_detectado",
        "description": "Explica en detalle uno de los problemas detectados en el informe del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "problema_id": {"type": "string"}
            },
            "required": ["problema_id"]
        }
    },
    {
        "name": "generar_carta_reclamo",
        "description": "Genera una carta de reclamo dirigida a SERNAC o a una institución.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destinatario": {"type": "string", "enum": ["SERNAC", "INSTITUCION"]},
                "institucion": {"type": "string"},
                "motivo": {"type": "string"},
                "articulos_invocados": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["destinatario", "motivo"]
        }
    },
    {
        "name": "obtener_plan_salida",
        "description": "MOCK. Retorna plan priorizado de pago de deudas.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "comparar_alternativas",
        "description": "MOCK. Retorna alternativas de mercado mejores.",
        "input_schema": {
            "type": "object",
            "properties": {"tipo_producto": {"type": "string"}}
        }
    }
]
```

3. Implementar backend/app/agent/concierge.py:

```python
from anthropic import Anthropic
from app.agent.prompts import build_system_prompt
from app.agent.tools import TOOLS
from typing import AsyncGenerator
import json
import os

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

class ConciergeAgent:
    def __init__(self, snapshot: dict):
        self.snapshot = snapshot
        self.system_prompt = build_system_prompt(snapshot)
        self.history = []

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Yield chunks de la respuesta del concierge."""
        self.history.append({"role": "user", "content": user_message})

        # Loop de tool use
        while True:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                tools=TOOLS,
                messages=self.history,
            )

            # Procesar bloques de respuesta
            assistant_blocks = []
            for block in response.content:
                if block.type == "text":
                    yield block.text
                    assistant_blocks.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_blocks.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })

            self.history.append({"role": "assistant", "content": assistant_blocks})

            # Si no hay tool_use, terminamos
            if response.stop_reason != "tool_use":
                break

            # Ejecutar tools y agregar resultados
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await self._execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            self.history.append({"role": "user", "content": tool_results})

    async def _execute_tool(self, name: str, args: dict) -> str:
        if name == "consultar_normativa":
            from app.agent.mcp_client import call_mcp_tool
            return await call_mcp_tool("consultar_normativa", args)
        if name == "calcular_carga_financiera":
            ingreso = args["ingreso_mensual"]
            features = self.snapshot["features"]
            estimado = features["total_debt"] / 36
            pct = estimado / ingreso if ingreso > 0 else 0
            return f"Carga financiera estimada: {pct:.1%} del ingreso mensual."
        if name == "explicar_problema_detectado":
            return f"Problema {args['problema_id']}: [explicación contextualizada]"
        if name == "generar_carta_reclamo":
            from app.services.carta_reclamo import generar_carta
            carta_text = generar_carta(self.snapshot, **args)
            return f"Carta generada exitosamente. URL: /carta/{self.snapshot['anon_id']}"
        if name == "obtener_plan_salida":
            return json.dumps({"plan": "mock plan de salida"})
        if name == "comparar_alternativas":
            return json.dumps({"alternativas": "mock alternativas"})
        return f"Tool {name} no implementado"
```

4. Implementar backend/app/agent/mcp_client.py:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_mcp_tool(tool_name: str, args: dict) -> str:
    """Llama una tool del MCP server local."""
    server_params = StdioServerParameters(
        command="python",
        args=["../mcp_server/server.py"],
        env=None
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            return result.content[0].text if result.content else ""
```

5. Implementar backend/app/api/chat.py:

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.agent.concierge import ConciergeAgent
from app.db.sqlite import SessionLocal, ProfileRecord
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

# Memoria en memoria (simple para demo)
_agents: dict[str, ConciergeAgent] = {}

@router.post("/chat/{anon_id}")
async def chat(anon_id: str, req: ChatRequest):
    if anon_id not in _agents:
        db = SessionLocal()
        record = db.query(ProfileRecord).filter_by(anon_id=anon_id).first()
        db.close()
        if not record:
            raise HTTPException(404, "Perfil no encontrado")
        snapshot = {
            "anon_id": record.anon_id,
            "avatar": {"name": "...", "image_url": "..."},
            "segment": record.segment,
            "features": record.features,
            "recommendations": record.recommendations
        }
        _agents[anon_id] = ConciergeAgent(snapshot)

    agent = _agents[anon_id]

    async def event_stream():
        async for chunk in agent.chat(req.message):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

ENTREGABLES:
- prompts.py con system prompts por nivel.
- tools.py con definición de 6 tools.
- concierge.py con loop de tool use.
- mcp_client.py para llamar al MCP server.
- /chat/{anon_id} con SSE funcional.

NO HAGAS:
- No agregues memoria persistente del concierge todavía (en memoria está bien para demo).
- No introduzcas otros modelos. Solo Claude Sonnet.

AL TERMINAR:
git add . && git commit -m "feat(be2): concierge agent with Claude + MCP tools" && git push
```

---

## MEGAPROMPT BE2-4: Generación de carta de reclamo (60 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: servicio que genera carta de reclamo formal con citas a normativa, retorna PDF.

TAREAS:

1. Implementar backend/app/services/carta_reclamo.py:

```python
from pathlib import Path
from datetime import datetime
from typing import Optional
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

TEMPLATES_DIR = Path("backend/app/services/templates")

def generar_carta(
    snapshot: dict,
    destinatario: str = "SERNAC",
    institucion: Optional[str] = None,
    motivo: str = "",
    articulos_invocados: list[str] = None
) -> str:
    """
    Genera el texto de la carta de reclamo.
    Usa Claude con prompt específico para garantizar formalidad legal.
    """
    template_file = {
        "SERNAC": "carta_sernac.txt",
        "INSTITUCION": "carta_clausula_abusiva.txt"
    }.get(destinatario, "carta_sernac.txt")

    template = (TEMPLATES_DIR / template_file).read_text()

    prompt = f"""Genera el cuerpo de una carta de reclamo formal en español chileno.

CONTEXTO DEL USUARIO:
- Avatar: {snapshot['avatar']['name']}
- Nivel: {snapshot['segment']}
- Problemas detectados: {snapshot['features']['dominant_signal']}

DESTINATARIO: {destinatario}
{f'INSTITUCIÓN RECLAMADA: {institucion}' if institucion else ''}

MOTIVO DEL RECLAMO:
{motivo}

ARTÍCULOS INVOCADOS:
{', '.join(articulos_invocados or [])}

INSTRUCCIONES:
1. Tono: formal pero claro. Sin jerga legal innecesaria.
2. Estructura: presentación → hechos → fundamento legal → petición.
3. Cita los artículos exactamente como se te dieron.
4. Petición concreta y medible.
5. Máximo 3 párrafos en el cuerpo.

Genera SOLO el texto del cuerpo (sin encabezados ni firma — eso lo agregamos por plantilla)."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    cuerpo = response.content[0].text

    carta_completa = template.format(
        fecha=datetime.now().strftime("%d de %B de %Y"),
        avatar_nombre=snapshot["avatar"]["name"],
        institucion=institucion or "—",
        motivo=motivo,
        articulos_invocados=", ".join(articulos_invocados or []),
        descripcion=cuerpo,
        peticion="Solicito formalmente la corrección de la situación denunciada y la "
                 "compensación correspondiente según la normativa vigente."
    )

    return carta_completa
```

2. Implementar backend/app/api/carta.py para retornar PDF:

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from app.services.carta_reclamo import generar_carta
from app.db.sqlite import SessionLocal, ProfileRecord
from pydantic import BaseModel

router = APIRouter()

class CartaRequest(BaseModel):
    destinatario: str = "SERNAC"
    institucion: str = None
    motivo: str = ""
    articulos_invocados: list[str] = []

@router.post("/carta/{anon_id}")
def generar_carta_endpoint(anon_id: str, req: CartaRequest):
    db = SessionLocal()
    record = db.query(ProfileRecord).filter_by(anon_id=anon_id).first()
    db.close()
    if not record:
        raise HTTPException(404)

    snapshot = {
        "anon_id": record.anon_id,
        "avatar": {"name": "Cóndor 4521", "image_url": ""},  # mejorar
        "segment": record.segment,
        "features": record.features,
        "recommendations": record.recommendations
    }

    texto_carta = generar_carta(
        snapshot,
        destinatario=req.destinatario,
        institucion=req.institucion,
        motivo=req.motivo,
        articulos_invocados=req.articulos_invocados
    )

    # Generar PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = []
    for paragraph in texto_carta.split("\n\n"):
        flowables.append(Paragraph(paragraph, styles["Normal"]))
        flowables.append(Spacer(1, 12))
    doc.build(flowables)
    pdf_bytes = buffer.getvalue()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=carta_{anon_id}.pdf"}
    )
```

Agregar `reportlab==4.0.9` a requirements.txt.

3. Test:
   - Llamar /carta/{anon_id} con motivo "Cláusula abusiva detectada en contrato Ripley".
   - Verificar que retorna PDF descargable.
   - Verificar que el PDF tiene encabezado, cuerpo coherente y firma.

ENTREGABLES:
- carta_reclamo.py con generación vía Claude.
- /carta/{anon_id} retorna PDF.
- Plantillas en backend/app/services/templates/.

NO HAGAS:
- No prometas validez legal (es educativo / borrador).
- No incluyas RUT en la carta.

AL TERMINAR:
git add . && git commit -m "feat(be2): carta reclamo generation with PDF" && git push
```

---

## MEGAPROMPT BE2-5: Verificación legal + pre-cache + bug bash (90 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: garantizar que cada cita legal del demo es exacta. Pre-cachear respuestas para
demo sin riesgo de latencia. Bug bash con todo el equipo.

TAREAS:

1. Verificación manual de citas legales:

   Para los 3 fixtures (María, Carlos, Pedro), correr el flow completo del concierge y
   anotar CADA cita legal que aparece. Por cada cita:

   - Abrir el archivo JSON del corpus correspondiente.
   - Verificar que el artículo citado existe y dice exactamente lo que el concierge cita.
   - Si hay discrepancia: corregir el JSON del corpus o ajustar el system prompt.

   Crear un archivo docs/CITAS_VERIFICADAS.md con:

   ```
   ## María (Cóndor 4521)

   Conversación demo:
   - Cita 1: "Art. 17 B Ley 19.496" — "..." → ✓ verificada
   - Cita 2: "Art. 6 Ley 18.010" — "..." → ✓ verificada

   ## Carlos
   ...
   ```

2. Pre-cache de respuestas para demo:

```python
# backend/app/agent/cache.py
import json
from pathlib import Path

CACHE_DIR = Path("fixtures/concierge_cache")

PRECACHED = {
    "maria_intro": "Hola, Cóndor 4521. Soy tu Defensor...",  # respuesta exacta
    "maria_cita_clausula_abusiva": "Según el Art. 17 B de la Ley 19.496...",
    # ... más entries
}

def get_cached(key: str) -> str | None:
    return PRECACHED.get(key)
```

   Modificar concierge.py para chequear cache antes de llamar a Claude para queries
   conocidas del demo. Esto NO es trampa: es ingeniería de demo (latencia 0).

3. Mock de plan de salida y comparador con datos convincentes:

```python
# backend/app/services/plan_salida.py
def get_plan_salida(snapshot: dict) -> dict:
    """Mock con datos convincentes. Real en post-hackathon."""
    return {
        "estrategia": "avalancha",
        "deudas_priorizadas": [
            {"institucion": "Ripley", "monto": 380000, "tasa": "37%", "prioridad": 1, "accion": "Pagar primero — tasa más alta"},
            {"institucion": "CMR Falabella", "monto": 320000, "tasa": "35%", "prioridad": 2, "accion": "Pagar segundo"},
            {"institucion": "Banco Estado", "monto": 1800000, "tasa": "22%", "prioridad": 3, "accion": "Refinanciar a 12% con consolidación"},
        ],
        "ahorro_estimado_mensual": 75000,
        "tiempo_libertad": "18 meses"
    }
```

4. Bug bash: 30 minutos con todo el equipo testeando:
   - Flow completo con María.
   - Flow completo con Carlos.
   - Flow completo con Pedro.
   - Casos límite: PDF inválido, sin internet, click rápido en botones.

5. Documentar en docs/DEMO_PLAYBOOK.md:
   - Pasos exactos del demo.
   - Qué decir en cada momento.
   - Plan B si algo falla.

ENTREGABLES:
- docs/CITAS_VERIFICADAS.md con cada cita verificada.
- Pre-cache implementado.
- Mocks de plan_salida y comparador.
- Bug bash completado.
- DEMO_PLAYBOOK escrito.

AL TERMINAR:
git add . && git commit -m "chore(be2): verify citations + precache + demo playbook" && git push
```

---

## MEGAPROMPT BE2-6: Pitch y deck (último día — 4 horas)

```
[CONTEXTO COMÚN]

OBJETIVO: el pitch es tu producto final como líder. Este megaprompt es de contenido y
ensayo, no de código.

TAREAS:

1. Escribir el guion del pitch palabra por palabra.

Base: sección 11 del PLAN_DEFINITIVO.md y guion de demo de la sección 16.

Estructura final (3 minutos):

- 00:00–00:15 — Hook
- 00:15–00:35 — Solución en una frase + "sin venta"
- 00:35–02:25 — Demo en vivo
- 02:25–02:40 — Por qué ahora (Claude + MCP + corpus público)
- 02:40–02:50 — Bien público (open source motor MCP)
- 02:50–03:00 — Cierre ("infraestructura del derecho a entender")

Imprimirlo en hoja física y tenerla a mano durante presentación.

2. Armar deck de 10 slides en Google Slides:

Slide 1 — Hook visual: foto de calle chilena + "1 de cada 3 chilenos sobreendeudados firmó
sin entender lo que firmaba"

Slide 2 — Problema: 3 estadísticas duras (carga financiera promedio, costo asesoría,
brecha de información)

Slide 3 — Solución: tagline "Defensor — Concierge financiero anónimo" + frase "Sin venta.
Devolvemos derechos."

Slide 4 — Demo: solo el avatar Cóndor 4521 + un PDF flotando. Minimalista. El demo es el
contenido.

Slide 5 — Cómo funciona: diagrama simple PDF → Pipeline → Concierge + MCP → Corpus CMF

Slide 6 — Roadmap de 4 niveles: visualización con avatares (idea fuerza C: mobility plan)

Slide 7 — Por qué IA y por qué ahora: Claude entiende contratos + MCP conecta normativa +
CMF publica todo abierto

Slide 8 — Bien público: open source Apache 2.0 del motor + privacidad por arquitectura +
modelo institucional fundación / convenio público-privado

Slide 9 — Lo que sigue: cartas formales a CMF y SEGPRES + opinión legal sobre alcance no
asesoría + cumplimiento Ley 21.719 + piloto con SERNAC

Slide 10 — Cierre: "infraestructura del derecho a entender" + foto del equipo

3. Ensayo:

Día 2, 21:00–23:00. Mínimo 8 pasadas cronometradas. Después de cada pasada:
- ¿Tiempo? Debe estar en 3:00 ± 10 segundos.
- ¿Claridad? ¿Se entiende sin contexto previo?
- ¿Energía? ¿Suena convencido?

4. Preguntas previsibles del jurado y respuestas ensayadas:

a) "¿Cómo evitan consejo legal incorrecto?" → respuesta de la sección 15 del PLAN.

b) "¿Cuál es la ventaja contra que un banco lance lo mismo?" → "Por incentivos. Los bancos
no quieren que ejerzas tus derechos contra ellos. Por eso modelo institucional es
fundación o convenio público-privado, no SaaS comercial."

c) "¿Cómo monetizan?" → "No monetizamos al usuario. Modelo: licencias de tecnología a
organismos como SERNAC + cooperación internacional BID/CAF + filantropía. Sostenible sin
explotar al vulnerable."

d) "¿Cuántos usuarios proyectan?" → "Cluster vulnerable en Chile: ~7 millones de personas.
Foco MVP: 1.000-5.000 en cohorte cerrada el primer año. Escalamiento por canales
gratuitos (TikTok, Instagram orgánico) y partnerships con ONGs."

e) "¿Por qué Chile primero?" → "Porque la CMF chilena publica todo abierto. Es una
ventaja regulatoria única en la región. Después: replicación a otros países LATAM con
adaptación al corpus normativo local."

f) "¿Qué pasa si CMF cambia el formato de informe?" → "Parser modular, fácil de actualizar.
Convenio formal con CMF en Fase 0 elimina dependencia de PDF parsing."

g) "¿Cómo escalan el corpus a más leyes?" → "El motor RAG/MCP es agnóstico al corpus. Se
agregan más leyes indexando archivos. SUSESO para Isapres, BCN para todo Diario Oficial,
SII para tributario."

5. Última verificación:

- Cargar batería del laptop al 100%.
- Backup video grabado.
- Hotspot de celular probado por si falla wifi.
- Demo data pre-cacheada confirmada.
- Slides exportadas en PDF (backup si falla Google Slides).

ENTREGABLES:
- docs/PITCH_GUION.md con guion palabra por palabra.
- Deck en Google Slides (link a docs/).
- docs/PREGUNTAS_JURADO.md con respuestas ensayadas.
- Backup de todo (video + PDF de slides + guion impreso).

AL TERMINAR:
git add . && git commit -m "chore(be2): pitch script + deck + Q&A" && git push
git tag v1.0-pitch
git push --tags
```

---

## Resumen de tu trayecto BE-2 en 30 horas

| Hora | Megaprompt | Entregable |
|------|-----------|-----------|
| 0–1.5 | BE2-1 | Corpus + catálogo + plantillas (CONTENIDO) |
| 1.5–3 | BE2-2 | MCP server con RAG funcional |
| 4–6 | BE2-3 | Concierge agent + /chat |
| 9–10 | BE2-4 | Carta de reclamo + PDF |
| 12–14 | BE2-5 | Verificación citas + pre-cache + bug bash |
| 18–22 día 2 | BE2-6 | Pitch + deck + ensayo |

Tu rol carga: 4 megaprompts de código + 2 de contenido/pitch.

---

## Reglas para siempre

1. **Tu capa va ENCIMA del pipeline determinístico.** Recibes input, no clasificas.
2. **Citas SOLO desde RAG.** Prohibido citar de memoria.
3. **El catálogo manda.** Las recomendaciones vienen de ahí, no las inventa Claude.
4. **Honesto cuando no sabe.** Mejor "no tengo eso" que alucinar.
5. **Eres el cara visible.** Tu pitch es el producto. Lo demás es soporte.

---

*Fin de los megaprompts BE-2.*
