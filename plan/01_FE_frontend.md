# 01 — MEGAPROMPTS FRONTEND (FE)

> **Quién:** persona FE del equipo.
> **Stack:** SolidJS / SolidStart + Tailwind + TypeScript.
> **Pre-requisito:** Megaprompt 00 (setup) ejecutado. Repo clonado. `npm run dev` corriendo.
> **Total de megaprompts:** 5, secuenciales.

---

## Reglas para usar estos megaprompts

1. Ejecutar uno a la vez. Esperar a que termine antes del siguiente.
2. Cada megaprompt incluye su contexto — pegar entero a Claude Code o a tu agente de coding.
3. No inventes features fuera de scope. Si algo no está en el megaprompt, no lo hagas.
4. Después de cada megaprompt: `git add . && git commit -m "feat(fe): [resumen]" && git push`.

---

## CONTEXTO COMÚN (incluir al inicio de cada megaprompt)

```
PROYECTO: Defensor — Concierge financiero con IA.
ROL: Frontend único del equipo. Responsable de las 7 pantallas, polish visual, integración con backend.

API CONTRACT:
- POST /ingest (multipart con file PDF) → IngestResult
- POST /chat/{anon_id} (SSE stream) → mensajes del concierge
- POST /carta/{anon_id} → blob PDF
- GET /alerts → array de alertas (mock)

TIPOS:
type Segment = "unbanked" | "recently_banked" | "vulnerable" | "functional"

interface IngestResult {
  anon_id: string;
  avatar: { name: string; image_url: string };
  segment: Segment;
  features: {
    total_debt: number;
    consumo_ratio: number;
    past_due_ratio: number;
    num_institutions: number;
    num_refinancings: number;
    has_mortgage: boolean;
    carga_financiera_pct: number;
    dominant_signal: string;
  };
  recommendations: Array<{
    id: string;
    title: string;
    trigger: string;
    action: string;
    priority: number;
  }>;
}

USUARIO PROTAGONISTA: María Silva, avatar "Cóndor 4521", Nivel 2 - Bancarizado Vulnerable.
TONO VISUAL: profesional, sobrio, confiable. Paleta: azul profundo + acento cálido. Mobile-first.
```

---

## MEGAPROMPT FE-1: Pantallas mock funcional (90 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: tener un flow clickeable end-to-end con datos mockeados. Sin backend real.
Todo debe funcionar contra src/lib/api.ts que retorna fixtures de María.

TAREAS:

1. Configurar SolidStart con routing:
   - / (landing + upload)
   - /diagnostico
   - /concierge
   - /carta
   - /plan
   - /comparador
   - /alertas

2. Configurar Tailwind con paleta:
   - bg-primary: azul profundo (#0A2540)
   - bg-accent: cálido (#FF7A59)
   - bg-surface: gris claro (#F6F8FA)
   - text-primary: oscuro (#1A1F36)
   - text-muted: gris (#6B7280)
   - Fuente: Inter o system-ui.

3. Implementar src/lib/api.ts:
   - ingest(file: File): retorna fixture de fixtures/personas/maria.json (importar JSON).
   - chat(anonId, message): generador async que yield strings (simular streaming con setTimeout).
   - generarCarta(anonId): retorna Blob con texto plano de carta hardcodeada.
   - getAlerts(): retorna 3-4 alertas mock con título, fecha, fuente.

4. Pantalla / (landing + upload):
   - Hero centrado con logo "Defensor" y tagline "Tu concierge financiero anónimo".
   - Subtítulo: "Sube tu informe de deudas CMF y recibe un diagnóstico claro, con citas
     a la ley chilena."
   - Drop zone para PDF con drag & drop. Texto: "Arrastra tu informe CMF aquí" + botón
     "O selecciona un archivo".
   - Al subir: simulación de carga 3 segundos con loader, luego redirige a /diagnostico.
   - Footer con "Sin venta. Sin registro. Privacidad por arquitectura."

5. Pantalla /diagnostico (LA MÁS IMPORTANTE — wow moment):
   - Header con avatar (placeholder SVG genérico circular) + nombre "Cóndor 4521" +
     badge "Nivel 2 - Bancarizado Vulnerable".
   - Resumen de carga financiera: barra horizontal con porcentaje 52% en rojo + texto
     "Tu deuda mensual representa el 52% de tu ingreso. Ideal: <30%."
   - Sección "Detecté 3 problemas" con 3 cards expandibles:
     a) "Tasa al límite legal" — descripción corta + botón "Ver fundamento legal"
     b) "Refinanciamientos repetidos" — idem
     c) "Cláusula potencialmente abusiva" — idem
   - Cada botón "Ver fundamento legal" abre un panel lateral (drawer) con:
     - Título de la ley/artículo: "Art. 17 B - Ley 19.496"
     - Cita textual hardcodeada (15 palabras o menos)
     - Link a "Ver ley completa"
   - 4 botones inferiores grandes: "Hablar con Concierge", "Generar carta de reclamo",
     "Ver plan de salida", "Ver alternativas".

6. Pantalla /concierge:
   - Layout chat estándar. Header con avatar.
   - Primer mensaje del concierge hardcodeado (el de "Hola, Cóndor 4521..." de la sección
     7 del PLAN_DEFINITIVO).
   - Input al fondo. Al enviar mensaje: simular respuesta streaming usando api.chat().
   - Cuando el mensaje del concierge incluye una cita legal, renderizarla en un blockquote
     con borde azul y link "[Ver artículo completo]".

7. Pantalla /carta:
   - Vista previa de carta de reclamo a SERNAC con:
     - Encabezado: "RECLAMO ANTE SERNAC"
     - Datos del usuario: solo "Cóndor 4521" (anonimato)
     - Cuerpo: 3 párrafos con artículos invocados.
     - Firma: "Cóndor 4521 — vía Defensor"
   - Botón "Descargar PDF" que llama api.generarCarta() y descarga el blob.

8. Pantalla /plan (mock):
   - Tabla de 4 deudas priorizadas con: institución, monto, tasa, prioridad de pago,
     acción recomendada.
   - Estrategia destacada: "Avalancha: paga primero la deuda con tasa más alta".

9. Pantalla /comparador (mock):
   - Tabla con 3 alternativas mejores que productos actuales: institución, producto, CAE,
     ahorro estimado mensual.

10. Pantalla /alertas:
    - Feed vertical de cards. Cada card: ícono + título + descripción + fecha + fuente.
    - Ejemplos:
      "Nueva tasa máxima convencional vigente — CMF — hace 2 días"
      "SERNAC inicia mediación contra retail X — SERNAC — hace 1 semana"

ENTREGABLES:
- Flow completo navegable: landing → upload → diagnóstico → cualquier sección.
- Todo con mocks, sin necesidad de backend.
- Diseño responsive: funciona en móvil 375px y desktop 1440px.
- Sin errores en consola.

NO HAGAS:
- No conectes a backend real todavía.
- No uses imágenes externas (usa SVG inline o placeholders).
- No agregues animaciones complejas todavía.
- No agregues login, signup, autenticación.

AL TERMINAR:
git add . && git commit -m "feat(fe): mock flow with 7 screens" && git push
```

---

## MEGAPROMPT FE-2: Componentes reusables y polish visual (90 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: extraer componentes reusables, mejorar diseño visual, hacer responsive impecable.

TAREAS:

1. Crear componentes en src/components/:

   a) Avatar.tsx: SVG procedural basado en hash. Recibe prop "name" (ej. "Cóndor 4521").
      Genera ave estilizada con colores derivados del hash. Tamaños: sm (32px), md (64px),
      lg (128px).

   b) DeudaCard.tsx: card expandible con título, descripción corta, cita legal opcional,
      botón de acción. Animación de expand/collapse suave.

   c) Semaforo.tsx: barra horizontal con valor 0-100. Verde <30, amarillo 30-50, rojo >50.

   d) ChatMessage.tsx: bubble de chat con variantes "user" y "concierge". Soporta
      blockquote para citas legales con estilo destacado.

   e) BadgeNivel.tsx: badge colorido según segment ("vulnerable" rojo, "functional" verde,
      etc.).

   f) Drawer.tsx: panel lateral derecho con backdrop. Animación slide-in.

   g) LoadingSpinner.tsx: spinner consistente para todas las pantallas.

2. Refactorizar las 7 pantallas para usar los componentes nuevos.

3. Polish visual:
   - Espaciado consistente (sistema de 4/8/16/24/32px).
   - Tipografía jerárquica: h1 (32px), h2 (24px), h3 (20px), body (16px), small (14px).
   - Sombras suaves en cards: shadow-md.
   - Transiciones: 200ms ease-out en hovers y interacciones.
   - Estados vacíos elegantes: si no hay datos, mensaje + ilustración SVG simple.

4. Responsive móvil:
   - Breakpoints: sm (640px), md (768px), lg (1024px).
   - En móvil: navegación tabs en bottom bar para las pantallas principales.
   - Drawer en móvil ocupa pantalla completa.

5. Accesibilidad básica:
   - Contraste WCAG AA en todos los textos.
   - Focus visible en interactivos.
   - aria-labels en botones con solo íconos.

ENTREGABLES:
- 7 componentes reusables en src/components/.
- 7 pantallas refactorizadas usando los componentes.
- Responsive perfecto en móvil y desktop.
- Sin warnings en consola.

NO HAGAS:
- No introduzcas librerías de UI externas (Radix, MUI, etc.). Solo Tailwind.
- No agregues animaciones de framer-motion u otras librerías. Tailwind transitions.

AL TERMINAR:
git add . && git commit -m "refactor(fe): reusable components and visual polish" && git push
```

---

## MEGAPROMPT FE-3: Integración con backend real (60 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: cambiar mocks por llamadas reales al backend. El backend está corriendo en
localhost:8000. La integración debe ser sin cambios en componentes — solo en src/lib/api.ts.

PRE-REQUISITO: BE-1 confirma que /ingest funciona con curl.

TAREAS:

1. Actualizar src/lib/api.ts:

   a) ingest(file): hacer POST real a http://localhost:8000/ingest con FormData.
      Manejar errores (red, formato PDF inválido, 500). Retornar IngestResult tipado.

   b) chat(anonId, message): consumir SSE de POST /chat/{anon_id}. Usar EventSource o fetch
      con ReadableStream. Yield cada chunk. Manejar reconexión si se corta.

   c) generarCarta(anonId): POST a /carta/{anon_id}, retornar blob PDF, abrir en navegador
      con URL.createObjectURL.

   d) getAlerts(): GET /alerts.

2. Manejo de errores en pantallas:
   - Si /ingest falla: mostrar mensaje "No pudimos procesar tu informe. Verifica que sea
     un informe CMF válido en PDF."
   - Si /chat se corta: mostrar "Conexión perdida. Recargar."
   - Si /carta falla: mostrar "Error al generar carta. Intenta de nuevo."

3. Loading states:
   - /ingest: progress bar durante 3-8 segundos.
   - /chat: typing indicator (3 puntos animados) mientras streaming.
   - /carta: spinner en botón de descarga.

4. Verificación end-to-end:
   - Subir PDF de María (que BE-1 tiene en fixtures/informes_pdf/).
   - Ver diagnóstico real con datos del backend.
   - Conversar con concierge y ver respuestas con citas reales.
   - Generar carta y descargar PDF.

ENTREGABLES:
- src/lib/api.ts conectado a backend real.
- Manejo de errores en todas las pantallas.
- Loading states consistentes.
- Demo end-to-end funcionando.

NO HAGAS:
- No cambies tipos sin actualizar el backend con BE-1.
- No agregues retry logic compleja. Errores se muestran al usuario directamente.

AL TERMINAR:
git add . && git commit -m "feat(fe): integrate with real backend" && git push
```

---

## MEGAPROMPT FE-4: Animaciones y micro-interacciones (60 minutos)

```
[CONTEXTO COMÚN]

OBJETIVO: agregar las animaciones que convierten una app correcta en una app memorable.
El demo necesita transmitir profesionalismo en 3 minutos.

TAREAS:

1. Animación del avatar:
   - Al aparecer en /diagnostico: fade-in + scale desde 0.9 a 1.0 en 400ms.
   - Sutil "respiración" continua: scale 1.0 ↔ 1.02 en 3 segundos.

2. Reveal progresivo en /diagnostico:
   - Header avatar: 0ms.
   - Carga financiera (semáforo): 200ms.
   - Cards de problemas: 400ms, 600ms, 800ms (stagger).
   - Botones inferiores: 1000ms.
   - Cada uno fade-in + slide-up de 8px.

3. Drawer de citas legales:
   - Slide desde derecha en 300ms.
   - Backdrop fade-in en 200ms.
   - Cita textual aparece con typewriter effect (carácter por carácter, 30ms cada uno).
     Esto es el wow visual: la cita LITERALMENTE aparece desde la ley.

4. Chat del concierge:
   - Mensajes aparecen con scale-in pequeño.
   - Streaming visual: cursor parpadeante al final del mensaje en construcción.
   - Cuando el concierge cita una ley: el blockquote aparece con highlight amarillo
     que se desvanece a azul en 1 segundo.

5. Generación de carta:
   - Botón "Generar carta" muestra spinner.
   - Al completar: animación de "documento" que se materializa (escala + opacity).
   - Botón cambia a "Descargar PDF" con bounce sutil.

6. Transiciones entre rutas:
   - Fade-out 100ms + fade-in 200ms.

ENTREGABLES:
- Todas las animaciones implementadas con CSS y transitions de Tailwind.
- Sin librerías externas.
- Animaciones funcionan en móvil sin lag.

NO HAGAS:
- No uses GSAP, framer-motion ni similares.
- No animaciones que duren más de 1 segundo (excepto typewriter de citas).
- No abuses de animaciones — restraint > exuberancia.

AL TERMINAR:
git add . && git commit -m "feat(fe): animations and micro-interactions" && git push
```

---

## MEGAPROMPT FE-5: Demo data, video respaldo y deck (último día)

```
[CONTEXTO COMÚN]

OBJETIVO: preparar todo lo necesario para el pitch. La app debe verse perfecta con los 3
fixtures (María, Carlos, Pedro). Grabar video respaldo. Armar slides del deck.

TAREAS:

1. Selector de fixture (URL param):
   - /?persona=maria → carga fixture de María al subir cualquier PDF.
   - /?persona=carlos → carga fixture de Carlos.
   - /?persona=pedro → carga fixture de Pedro.
   - /?persona=cero → muestra pantalla de Nivel 0 (mock).
   - Esto permite que TÚ (el que presenta) cambies persona en escena para el demo.

2. Pantalla de Nivel 0 (mock):
   - Cuando segment === "unbanked" o no hay datos.
   - Muestra mensaje: "Detectamos que aún no tienes productos financieros formales."
   - 3 cards de recursos básicos: "Cómo abrir tu primera cuenta vista", "Cómo evitar
     prestamistas informales", "Construye tu historial paso a paso".
   - Texto: "Estamos diseñando un flujo completo para acompañarte. Vuelve pronto."

3. Roadmap de los 4 niveles (sección visible en /diagnostico):
   - Visualización horizontal con 4 nodos: 0 → 1 → 2 → 3.
   - El nivel actual del usuario destacado (con avatar pequeño encima).
   - Los anteriores marcados como ✓.
   - El siguiente: "Tu próximo objetivo" con CTA.

4. Pre-cache de respuestas del concierge:
   - Para los 3 fixtures, pre-grabar las respuestas exactas que se dirán en demo.
   - Si el backend tarda en responder (red lenta en demo), usar el cache.
   - Esto NO es trampa: es ingeniería de demo.

5. Grabar video respaldo del demo (3 minutos):
   - Usar OBS o Loom.
   - Flow completo: upload de María → diagnóstico → cita legal → carta → plan → comparador
     → chat con concierge.
   - Voz en off opcional (lo dirás tú en vivo, el video es solo para pantalla si crashea).
   - Guardar en docs/demo_video.mp4.

6. Armar deck de 10 slides (Google Slides o Keynote):
   - Usar las slides de la sección 12 del PLAN_DEFINITIVO.
   - Slides minimalistas: foto/diagrama + 1 frase máximo.
   - Slide 4 (Demo) con embed del video respaldo o solo el título "Cóndor 4521".

ENTREGABLES:
- App con selector de fixture funcionando.
- Pantalla Nivel 0 implementada.
- Roadmap visible en /diagnostico.
- Pre-cache de respuestas en src/lib/cache.ts.
- Video respaldo grabado.
- Deck de 10 slides listo.

NO HAGAS:
- No cambies estructura de componentes a esta altura.
- No introduzcas features nuevos.

AL TERMINAR:
git add . && git commit -m "chore(fe): demo data, backup video, deck" && git push
git tag v1.0-demo
git push --tags
```

---

## Resumen de tu trayecto FE en 30 horas

| Hora | Megaprompt | Entregable |
|------|-----------|-----------|
| 0–1.5 | FE-1 | Flow mock completo, 7 pantallas navegables |
| 1.5–3 | FE-2 | Componentes reusables + polish visual |
| 4–6 | FE-3 | Integración con backend real |
| 9–11 | FE-4 | Animaciones y micro-interacciones |
| 18–22 día 2 | FE-5 | Demo data, video, deck |

Entre megaprompts: syncs con BE-1 y BE-2, ajustes según feedback del equipo.

---

*Fin de los megaprompts FE.*
