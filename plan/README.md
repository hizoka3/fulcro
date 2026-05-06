# Defensor — Megaprompts del Equipo

> **Qué es esto:** colección de megaprompts secuenciales para que cada miembro del equipo
> ejecute con un agente de coding (Claude Code, Cursor, etc.) y avance sin bloquear a los
> demás.
>
> **Filosofía:** un megaprompt = una sesión de ~60-90 minutos de trabajo focalizado.
> Pegarlo entero al agente, dejar que lo ejecute, revisar, commit, siguiente.

---

## Estructura

```
megaprompts/
├── 00_PRINCIPAL_setup_repo.md     ← UNA persona ejecuta primero (hora 0)
├── 01_FE_frontend.md              ← FE ejecuta secuencialmente sus 5 megaprompts
├── 02_BE1_pipeline.md             ← BE-1 ejecuta secuencialmente sus 5 megaprompts
└── 03_BE2_ia_pitch.md             ← BE-2 (TÚ) ejecuta secuencialmente sus 6 megaprompts
```

---

## Orden de ejecución

### Hora 0 (todos juntos)

1. UNA persona (idealmente BE-1) ejecuta el **megaprompt 00**. Tiempo: ~20 min.
2. Cuando termine: los 3 clonan el repo, configuran `.env`, verifican que su parte arranca.
3. Sync de 10 minutos: confirmación de que todos pueden correr local.

### A partir de hora 0.5 (en paralelo)

Cada uno arranca su megaprompt #1 en paralelo. **No hay bloqueos** porque cada uno
trabaja contra fixtures hardcodeados hasta hora 6.

| Persona | Hora | Megaprompt |
|---------|------|------------|
| FE | 0.5–2 | 01_FE_frontend.md → FE-1 |
| BE-1 | 0.5–2 | 02_BE1_pipeline.md → BE1-1 |
| BE-2 (TÚ) | 0.5–2 | 03_BE2_ia_pitch.md → BE2-1 |
| Todos | 2 | **SYNC OBLIGATORIO** (15 min) |
| FE | 2–3.5 | FE-2 |
| BE-1 | 2–3.5 | BE1-2 |
| BE-2 | 2–3.5 | BE2-2 |
| Todos | 4 | **Sync** |
| FE | 4–5 | FE-3 (integración con backend real) |
| BE-1 | 4–5 | BE1-3 (integración con FE) |
| BE-2 | 4–6 | BE2-3 (concierge agent) |
| Todos | 6 | **HITO CRÍTICO: demo end-to-end con María** |
| FE | 9–11 | FE-4 (animaciones) |
| BE-1 | 9–10 | BE1-4 (fixtures Carlos y Pedro) |
| BE-2 | 9–10 | BE2-4 (carta de reclamo) |
| BE-2 | 12–14 | BE2-5 (verificación citas + bug bash) |
| Todos | 14 | **CODE FREEZE NOCTURNO** |
| Todos | 15–18 día 2 | Polish + grabar video |
| FE | 18–22 | FE-5 (demo data + deck visual) |
| BE-1 | 18–22 | BE1-5 (deploy + bug bash) |
| BE-2 | 18–22 | BE2-6 (pitch + deck + ensayo) |
| Todos | 21–23 | **Ensayo del pitch** |
| BE-2 | 24 | **PITCH** |

---

## Reglas de uso de los megaprompts

1. **Pegar el megaprompt entero** al agente de coding. No editar a mitad de camino.
2. **Esperar a que termine** antes del siguiente. No paralelizar megaprompts del mismo
   rol.
3. **Revisar el output** antes de hacer commit. Si algo está mal, corregir manualmente
   y luego commit.
4. **Commit con el mensaje sugerido** al final de cada megaprompt.
5. **No saltar megaprompts.** Cada uno asume que el anterior terminó.

---

## Si un megaprompt falla

1. Leer el error con calma.
2. Si es un error técnico (módulo faltante, sintaxis): corregir y reintentar.
3. Si es un error de scope (algo no estaba en el contexto): ajustar el megaprompt
   manualmente y reintentar.
4. Si después de 30 minutos no avanzas: pedir ayuda en el canal del equipo.
5. **No edites el código del agente para cumplir el megaprompt.** Si el agente no puede,
   tú lo escribes a mano.

---

## Guardrails que TODOS deben respetar

Estos están repetidos en cada megaprompt, pero los listo aquí para alineamiento:

### Backend
- ✅ Pipeline determinístico (BE-1) NO usa LLM nunca.
- ✅ Concierge (BE-2) NUNCA cita ley desde memoria del modelo. Solo desde RAG.
- ✅ Concierge NO inventa recomendaciones. Solo del catálogo.
- ✅ Hash HMAC del RUT, nunca persistir RUT.
- ✅ Sin PII en la base de datos.

### Frontend
- ✅ Sin librerías de UI externas (solo Tailwind).
- ✅ Sin animaciones de framer-motion u otras (solo CSS/Tailwind).
- ✅ Mobile-first.
- ✅ Sin login/auth.

### Producto
- ✅ Sin venta. Sin monetización del usuario.
- ✅ Sin promesas de validez legal de las cartas (educativo / borrador).
- ✅ Sin partners ficticios en el pitch.
- ✅ Sin métricas inventadas.

---

## Glosario rápido

- **ProfileSnapshot** = el JSON estructurado que produce el pipeline determinístico de
  BE-1 y consume el concierge de BE-2.
- **IngestResult** = lo que retorna /ingest. Misma estructura que ProfileSnapshot.
- **Catálogo** = recommendations.json con qué decirle a cada segment.
- **Corpus** = textos de leyes indexados en ChromaDB para RAG.
- **MCP** = protocolo de Anthropic para exponer tools a Claude. Server separado del
  backend.
- **RAG** = Retrieval-Augmented Generation. Recuperar texto relevante para fundamentar
  respuestas.
- **anon_id** = identificador anónimo derivado del RUT vía HMAC.
- **Cóndor 4521** = avatar de María, la heroína del demo.

---

## Si tienes 5 minutos antes de arrancar

Lee:
1. PLAN_DEFINITIVO.md secciones 17 (decisiones) y 18 (próximos 90 min).
2. DIVISION_TAREAS.md tu rol específico.
3. El megaprompt 00 si te toca ejecutarlo.

Si tienes solo 1 minuto: lee tu megaprompt #1 y arranca.

---

## Frase que vale más que todo este documento

> **"La hackathon no se gana porque hagamos el código perfecto. Se gana porque hagamos
> exactamente lo que decidimos hacer y nada más, durante 30 horas seguidas."**

Buena suerte. A construirlo.

---

*Fin del README de megaprompts.*
