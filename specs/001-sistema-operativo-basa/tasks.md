---
description: "Task list — Sistema Operativo Integral BASA Argentina"
---

# Tasks: Sistema Operativo Integral BASA Argentina

**Input**: Design documents from `specs/001-sistema-operativo-basa/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅ | quickstart.md ✅

**Tests**: No TDD explícito solicitado. Se incluyen validaciones de integración mínimas por historia.

**Organization**: Tareas agrupadas por User Story para implementación y demo independiente.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Puede correr en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: US1–US6 mapeados a las User Stories del spec.md
- Todos los paths son relativos a la raíz del repositorio (`SOFTWARE/`)

---

## Phase 1: Setup (Infraestructura Base)

**Purpose**: Inicialización del proyecto y estructura Docker

- [x] T001 Crear estructura de directorios del backend: `app/nodes/`, `app/tools/`, `app/graphs/`, `app/models/`, `app/api/`
- [x] T002 Crear `pyproject.toml` con dependencias: `langgraph`, `langchain`, `langchain-anthropic`, `fastapi`, `sqlalchemy`, `redis`, `langgraph-checkpoint-redis`, `httpx`, `python-dotenv`
- [x] T003 [P] Crear `.env.example` con todas las variables requeridas: `DATABASE_URL`, `REDIS_URL`, `ANTHROPIC_API_KEY`, `NOTEBOOKLM_MCP_URL`, `NOTEBOOKLM_BASA_ID`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `JWT_SECRET`
- [x] T004 [P] Crear `Dockerfile` del backend Python (imagen base `python:3.11-slim`, instala uv, copia app, expone puerto 8000)
- [x] T005 [P] Crear `Dockerfile.frontend` en `../DASH-cli/dashboard/` (imagen base `node:20-alpine`, build Vite, sirve con nginx)
- [x] T006 Crear `docker-compose.yml` con 4 servicios: `postgres` (postgres:15, healthcheck), `redis` (redis:7, healthcheck), `backend` (depends_on postgres+redis con `condition: service_healthy`), `frontend` (depends_on backend)
- [x] T007 [P] Crear `app/main.py` con instancia FastAPI, registrar todos los routers, CORS configurado para frontend en `localhost:5173`
- [x] T008 [P] Crear `app/memory.py`: inicializar `RedisSaver` (checkpointer) y `RedisStore` (store) con `.setup()` en startup, usando `REDIS_URL` del entorno

**Checkpoint**: `docker compose up` levanta los 4 contenedores sin errores. `http://localhost:8000/docs` responde.

---

## Phase 2: Foundational (Prerequisitos Bloqueantes)

**Purpose**: Base de datos, ORM y autenticación — DEBEN completarse antes de cualquier User Story

⚠️ **CRÍTICO**: Ninguna historia puede comenzar hasta completar esta fase.

- [x] T009 Crear `app/models/base.py`: `DeclarativeBase` de SQLAlchemy 2.x con `metadata` fijo al schema `dbo`. Todos los modelos heredan de aquí.
- [x] T010 [P] Crear `app/models/elemento.py`: clase `Elemento` con campos `id` (BigInteger PK), `codigo` (String 100, unique), `estado` (String 50), `posicion_id` (BigInteger FK nullable), `elemento_tipo_id` (BigInteger FK), `cliente_id` (BigInteger FK), `created_at` (DateTime default now)
- [x] T011 [P] Crear `app/models/posicion.py`: clase `Posicion` con `id` (BigInteger PK), `estado` (String 50, default `'DISPONIBLE'`), `estanteria` (Numeric), `codigo_modulo` (String 12), `modulo_id` (BigInteger FK)
- [x] T012 [P] Crear `app/models/requerimiento.py`: clase `Requerimiento` con `id` (BigInteger PK), `requerimiento_tipo_id` (BigInteger FK), `estado` (String 50), `cliente_id` (BigInteger FK), `direccion_entrega_id` (BigInteger FK nullable), `cantidad` (Numeric nullable), `fletes` (Integer default 0), `horas_archivista` (Numeric 18,2 nullable), `observaciones` (String 8000 nullable), `parent_requerimiento_id` (BigInteger FK self-ref nullable), `created_at` (DateTime)
- [x] T013 [P] Crear `app/models/movimiento.py`: clase `Movimiento` con `id` (BigInteger PK), `elemento_id` (BigInteger FK nullable), `requerimiento_id` (BigInteger FK nullable), `tipo_movimiento` (String 100), `estado_anterior` (String 50 nullable), `estado_nuevo` (String 50 nullable), `operario_id` (BigInteger nullable), `created_at` (DateTime), `metadata` (JSON nullable)
- [x] T014 [P] Crear `app/models/referencia.py`: clase `Referencia` con `id` (BigInteger PK), `elemento_contenedor_id` (BigInteger FK → Elemento), `texto1` (String 500 nullable), `texto2` (String 500 nullable), `numero1` (Numeric nullable)
- [x] T015 [P] Crear `app/models/hoja_ruta.py`: clase `HojaRuta` con `id` (BigInteger PK), `fecha` (Date), `estado` (String 50), `transportista_id` (BigInteger FK nullable)
- [x] T016 [P] Crear `app/models/lectura.py`: clases `Lectura` y `LecturaDetalle` según data-model.md (`remito`, `tipo`, `codigo_barra`, `resultado`)
- [x] T017 Crear `app/db.py`: `create_engine` con `DATABASE_URL`, función `get_engine()` y `get_session()` context manager. Verificar que el engine conecta en startup de FastAPI.
- [x] T018 Crear `app/middleware/auth.py`: middleware FastAPI que valida Bearer token del header `Authorization`, extrae `user_id` y `rol` del JWT, los inyecta en `request.state`. Rechaza con 401 si token inválido.
- [x] T019 [P] Crear `app/tools/notebooklm_tool.py`: LangChain `@tool` `notebooklm_search_tool(query: str)` que hace POST a `NOTEBOOKLM_MCP_URL` con `notebook_id` y `query`, retorna string con la respuesta o mensaje de error controlado
- [x] T020 [P] Crear `app/tools/postgres_tool.py`: LangChain `@tool` `postgres_db_tool(sql_query: str, parameters: dict)` que ejecuta queries parametrizadas via `engine.begin()`. Prohíbe DELETE físico (lanza error si detecta keyword DELETE sin WHERE o sobre tablas de negocio).

**Checkpoint**: Foundational completo — modelos importables sin errores, engine conecta a Postgres, middleware carga, tools instancian sin error.

---

## Phase 3: US1 — Ordenamiento y Ubicación de Cajas en Planta (Priority: P1) 🎯 MVP

**Goal**: Operario puede escanear caja + posición y el sistema vincula y actualiza estado a OCUPADO.

**Independent Test**: `POST /api/v1/ubicacion/asignar` con caja existente + posición DISPONIBLE → respuesta con `estado_posicion: OCUPADO` y registro en `dbo.movimiento`.

### Implementación US1

- [x] T021 [P] [US1] Crear `app/nodes/state_preparer.py`: función `state_preparer(state)` que recibe payload JSON, identifica `requerimiento_tipo_id` y define `tablas_afectadas`. Para UC1: extrae `codigo_caja` y `codigo_posicion` del payload.
- [x] T022 [P] [US1] Crear `app/nodes/node_validator.py`: función `node_validator(state)` que valida existencia de `dbo.elemento` por `codigo`, existencia de `dbo.posicion` por `codigo_modulo` y que `posicion.estado == 'DISPONIBLE'`. Retorna array `errors` si falla; nunca lanza excepción.
- [x] T023 [US1] Crear `app/nodes/node_persistence_unit.py`: función `node_persistence_unit(state)` que dentro de `engine.begin()`: (1) actualiza `dbo.elemento.posicion_id`, (2) cambia `dbo.posicion.estado` a `'OCUPADO'`, (3) inserta en `dbo.movimiento` con `tipo_movimiento='UBICACION_FISICA'`. Rollback automático si cualquier paso falla.
- [x] T024 [US1] Crear `app/graphs/operational_graph.py`: `StateGraph` con nodos `state_preparer → node_validator → node_persistence_unit`, compilado con `checkpointer` y `store` de `app/memory.py`. Edges condicionales: si `errors` no vacío → END con error; si vacío → continúa.
- [x] T025 [US1] Crear `app/api/uc1_ubicacion.py`: router FastAPI con `POST /api/v1/ubicacion/asignar` y `GET /api/v1/ubicacion/posicion/{codigo_modulo}`. Invoca `operational_graph` con `config = {"configurable": {"thread_id": ..., "user_id": ...}}`. Serializa respuesta con envelope `{"ok": true, "data": {...}, "simulated": false}`.
- [x] T026 [US1] Registrar router de UC1 en `app/main.py` con prefijo `/api/v1/ubicacion`.
- [x] T027 [P] [US1] Crear `../DASH-cli/dashboard/src/types/ubicacion.ts`: interfaces `AsignarUbicacionRequest`, `AsignarUbicacionResponse`, `ApiError` según contrato `contracts/uc1-ubicacion.md`.
- [x] T028 [P] [US1] Crear `../DASH-cli/dashboard/src/services/api.ts`: cliente axios con `baseURL=http://localhost:8000`, interceptor de respuesta que detecta errores de red y retorna `SimulatedResponse` con mensaje `"Simulado: [acción] completada. Pendiente de grabación en [tabla]."`.
- [x] T029 [US1] Crear `../DASH-cli/dashboard/src/pages/PlantLocations.tsx`: dos inputs de escaneo con autofoco secuencial (caja → posición), grid de confirmación con tarjetas verde/rojo/amarillo según resultado, botón de confirmación masiva. Usa `AsignarUbicacionRequest/Response` de `tipos/ubicacion.ts`. Placeholder logic: si `response.simulated === true`, muestra tarjeta amarilla con el mensaje simulado.

**Checkpoint**: Demo UC1 funcional. Escaneo en `PlantLocations` vincula caja a posición. Con backend detenido, muestra placeholder amarillo.

---

## Phase 4: US2 — Consulta Normal de Caja (Priority: P1) 🎯 MVP

**Goal**: Cliente crea pedido web con validación de prefijos; operario procesa picking, genera remito y digitaliza al cierre.

**Independent Test**: Crear pedido con caja `en guarda` → picking → remito → digitalización → requerimiento en estado `FINALIZADO`.

### Implementación US2

- [x] T030 [P] [US2] Crear `../DASH-cli/dashboard/src/hooks/usePrefixValidator.ts`: hook React que recibe `codigo: string` y `tipo: 'caja' | 'legajo'`, retorna `{ codigoCompleto: string, valido: boolean, error: string | null }` aplicando las reglas de prefijo de 12 dígitos del research.md (11000/110000 para cajas, 12000/120000 para legajos).
- [x] T031 [P] [US2] Crear `../DASH-cli/dashboard/src/types/consulta-caja.ts`: interfaces `CrearConsultaCajaRequest`, `ElementoValidado`, `CrearConsultaCajaResponse` según `contracts/uc2-consulta-caja.md`.
- [x] T032 [US2] Extender `app/nodes/node_validator.py`: agregar validación UC2 — verifica formato de 12 dígitos, comprueba `dbo.elemento.estado == 'en guarda'`, detecta elementos internos catalogados (requiere supervisor).
- [x] T033 [US2] Extender `app/nodes/node_persistence_unit.py`: agregar lógica UC2 — crea registro en `dbo.requerimiento` con `requerimiento_tipo_id=4`, inserta detalle de elementos, registra movimiento `PICKING_INICIADO`.
- [x] T034 [US2] Crear `app/nodes/node_commercial_logic.py`: función `node_commercial_logic(state)` — para UC2 no aplica lógica comercial, pasa el estado sin cambios (preparado para UC4).
- [x] T035 [US2] Crear `app/api/uc2_consulta_caja.py`: router con endpoints `POST /crear`, `POST /picking/iniciar`, `POST /picking/confirmar`, `POST /remito/generar`, `POST /digitalizar` según contrato `contracts/uc2-consulta-caja.md`.
- [x] T036 [US2] Registrar router UC2 en `app/main.py` con prefijo `/api/v1/consulta-caja`.
- [x] T037 [US2] Crear `../DASH-cli/dashboard/src/pages/WebBoxOrder.tsx`: input inteligente con `usePrefixValidator`, autocompletado de prefijo en tiempo real, grilla de cajas agregadas con validación de estado (rojo si no disponible), botón de envío. Placeholder logic activa si backend no responde.
- [x] T038 [US2] Crear `../DASH-cli/dashboard/src/pages/PickingDashboard.tsx`: dashboard con iconos secuenciales de estado (Asignar → Leer → Remito → Ruta → Digitalizar), banner amarillo cuando `requiere_autorizacion_supervisor: true`, botón de generación de remito habilitado solo si `puede_generar_remito: true`.

**Checkpoint**: Demo UC2 funcional. Cliente crea pedido en `WebBoxOrder`; operario procesa en `PickingDashboard`; remito generado; ciclo cierra con estado `FINALIZADO`.

---

## Phase 5: US3 — Consulta Normal de Legajos con Splitting (Priority: P2)

**Goal**: Operario escanea legajos; los no encontrados generan automáticamente un requerimiento hijo en una transacción atómica.

**Independent Test**: Pedido de 3 legajos, escanear 1 → `POST /remito/procesar` → `splitting_realizado: true`, requerimiento hijo creado con tipo 16.

### Implementación US3

- [x] T039 [P] [US3] Crear `../DASH-cli/dashboard/src/types/consulta-legajos.ts`: interfaces `CrearConsultaLegajosRequest`, `ProcesarRemitoLegajosResponse` según `contracts/uc3-consulta-legajos.md`.
- [x] T040 [US3] Extender `app/nodes/node_validator.py`: agregar validación UC3 — verifica prefijos de legajo (12000/120000/14XXXX), comprueba existencia en `dbo.referencia` y estado `'en guarda'`, rechaza legajos en estado `'de baja'` o `'en consulta'`.
- [x] T041 [US3] Extender `app/nodes/node_persistence_unit.py`: agregar lógica UC3 de splitting — dentro de un único `engine.begin()`: (1) actualiza requerimiento padre con `cantidad = len(encontrados)`, (2) si `len(faltantes) > 0` inserta requerimiento hijo con `requerimiento_tipo_id=16` y `estado='PENDIENTE_BUSQUEDA'`, (3) registra movimiento por cada legajo encontrado. Si INSERT hijo falla, rollback total.
- [x] T042 [US3] Crear `app/api/uc3_consulta_legajos.py`: router con `POST /crear`, `POST /picking/escanear`, `POST /remito/procesar` según contrato UC3.
- [x] T043 [US3] Registrar router UC3 en `app/main.py` con prefijo `/api/v1/consulta-legajos`.
- [x] T044 [US3] Crear `../DASH-cli/dashboard/src/pages/LegajosControl.tsx`: panel izquierdo con lista de legajos pedidos (checkbox dinámico), input de escaneo con coloreo verde inmediato al confirmar, panel derecho mostrando legajos faltantes con alerta de splitting pendiente, botón "Procesar Remito Incompleto" con placeholder logic si backend no responde.

**Checkpoint**: Demo UC3 funcional. Pedido con 3 legajos, escanear 2 → remito para 2 + requerimiento hijo para 1 faltante. Sin backend: placeholder muestra "Splitting realizado en memoria temporal."

---

## Phase 6: US4 — Retiros por Cantidad o Referencia (Priority: P2)

**Goal**: Operario concilia cantidades leídas vs. declaradas; el sistema calcula fletes automáticamente y envía email al cliente.

**Independent Test**: Retiro de 15 declaradas, leer 11 → conciliar → `fletes_calculados: 1`, `email_enviado: true`.

### Implementación US4

- [x] T045 [P] [US4] Crear `../DASH-cli/dashboard/src/types/retiro.ts`: interfaces `CrearRetiroRequest`, `ConciliarRetiroResponse`, tipos `TipoRetiro` y `TipoLectura` según contrato UC4.
- [x] T046 [US4] Extender `app/nodes/node_commercial_logic.py`: implementar cálculo de fletes UC4 — `fletes = math.ceil(cantidad / 20)`. Si `cantidad = 0` retorna `fletes = 0`. Si `cantidad = None` el validator ya rechazó el payload; no llegar aquí.
- [x] T047 [US4] Extender `app/nodes/node_persistence_unit.py`: agregar lógica UC4 — dentro de `engine.begin()`: (1) crea `dbo.lectura` y `dbo.lectura_detalle` con los códigos leídos, (2) actualiza `dbo.requerimiento.cantidad` y `dbo.requerimiento.fletes`, (3) cambia estado de elementos a `'en guarda'`, (4) registra movimiento `INGRESO_PLANTA`, (5) dispara envío de email (función async no bloqueante).
- [x] T048 [P] [US4] Crear `app/services/email_service.py`: función `send_intake_confirmation(cliente_email: str, detalle: dict)` usando SMTP configurado en `.env`. Si falla el envío, loguea el error pero NO rollbackea la transacción (email es best-effort).
- [x] T049 [US4] Crear `app/api/uc4_retiros.py`: router con `POST /crear`, `POST /lectura/procesar`, `POST /conciliar` según contrato UC4.
- [x] T050 [US4] Registrar router UC4 en `app/main.py` con prefijo `/api/v1/retiros`.
- [x] T051 [US4] Crear `../DASH-cli/dashboard/src/pages/IntakeConciliation.tsx`: buscador de número de remito, panel comparativo "Declarado vs. Ingresado" en naranja/rojo si hay discrepancia, cálculo de flete mostrado en tiempo real, botón "Confirmar e Ingresar Cajas" con re-confirmación si discrepancia, placeholder logic para email simulado.

**Checkpoint**: Demo UC4 funcional. Retiro 15 declaradas / 11 leídas → discrepancia mostrada → 1 flete calculado → email enviado (o simulado).

---

## Phase 7: US5 — Trámite Administrativo de Búsqueda (Priority: P3)

**Goal**: Operario investiga, registra horas, vincula documento encontrado y transforma el requerimiento dinámicamente.

**Independent Test**: Crear trámite tipo 16, registrar 2.5h, vincular elemento, `POST /transformar` con `tipo_destino: 2` → `tipo_nuevo: 2`, movimiento `INVESTIGACION_EXITOSA` en DB.

### Implementación US5

- [x] T052 [P] [US5] Crear `../DASH-cli/dashboard/src/types/busqueda.ts`: interfaces `CrearBusquedaRequest`, `TransformarBusquedaRequest`, `TransformarBusquedaResponse`, tipo `TipoDestino` según contrato UC5.
- [x] T053 [US5] Extender `app/nodes/node_validator.py`: validación UC5 — (1) `observaciones` obligatorio y mínimo 10 chars al crear, (2) `horas_archivista > 0` obligatorio al transformar, (3) al menos un elemento vinculado antes de transformar, (4) `tipo_destino` debe ser 2 u 8.
- [x] T054 [US5] Extender `app/nodes/node_persistence_unit.py`: lógica UC5 de transformación — dentro de `engine.begin()`: (1) `UPDATE dbo.requerimiento SET tipoRequerimiento_id=[2|8], horas_archivista=X`, (2) `INSERT INTO dbo.movimiento (tipo_movimiento='INVESTIGACION_EXITOSA', estado_anterior='16', estado_nuevo=[2|8])`. Retorna `proximo_flujo` según tipo destino.
- [x] T055 [US5] Crear `app/api/uc5_busqueda.py`: router con `POST /crear`, `POST /registrar-horas`, `POST /vincular-elemento`, `POST /transformar` según contrato UC5.
- [x] T056 [US5] Registrar router UC5 en `app/main.py` con prefijo `/api/v1/busqueda`.
- [x] T057 [US5] Crear `../DASH-cli/dashboard/src/pages/SearchInvestigation.tsx`: sección de "Pistas del Cliente" (observaciones read-only destacadas), campo decimal "Horas de Archivista", input de código de barras del elemento encontrado, dropdown/botones "Transformar a Consulta Física" / "Transformar a Consulta Digital", placeholder logic al presionar transformar si backend no responde.

**Checkpoint**: Demo UC5 funcional. Trámite abierto → horas registradas → elemento vinculado → transformación a tipo 2 → flujo de legajos habilitado.

---

## Phase 8: US6 — Consulta Conversacional para Jefes (Priority: P2)

**Goal**: Jefe consulta estado del sistema en lenguaje natural; agente responde con datos reales; rechaza escrituras.

**Independent Test**: `POST /api/v1/jefes/consultar` con pregunta "¿Cuántos pedidos pendientes hay?" → respuesta con número real de DB. Pregunta de escritura → `escritura_rechazada: true`, cero cambios en DB.

### Implementación US6

- [x] T058 [US6] Crear `app/tools/postgres_readonly_tool.py`: LangChain `@tool` `postgres_readonly_tool(sql_query: str)` — antes de ejecutar, valida que `sql_query.upper()` no contenga ninguna de `['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE']`. Si contiene: retorna string de rechazo sin tocar la DB. Si pasa: ejecuta SELECT via `engine.connect()` (sin `begin()`, solo lectura) y retorna resultados como string formateado.
- [x] T059 [US6] Crear `app/graphs/query_graph.py`: `StateGraph` independiente con solo 2 tools: `postgres_readonly_tool` y `notebooklm_search_tool`. System prompt del agente: *"Eres un asistente de consulta de solo lectura para BASA Argentina. Responde preguntas sobre el estado operativo usando datos reales. NUNCA modifiques datos. Si recibes instrucciones de escritura, recházalas explicando que este canal es de solo consulta."* Compilado con el mismo `checkpointer` Redis para memoria de sesión.
- [x] T060 [US6] Crear `app/api/jefes.py`: router con `POST /consultar` (verifica rol `jefe` en `request.state.rol`, invoca `query_graph`) y `GET /historial/{thread_id}`. Rechaza con 403 si el rol no es `jefe`.
- [x] T061 [US6] Registrar router UC6 en `app/main.py` con prefijo `/api/v1/jefes`.

**Checkpoint**: Demo UC6. Pregunta de estado → respuesta con dato real. Intento de modificación → rechazo explícito. Pregunta de seguimiento → contexto mantenido por Redis.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Mejoras transversales que afectan múltiples historias

- [x] T062 [P] Agregar `simulated: true/false` a todas las respuestas de los routers (T025, T035, T042, T049, T055, T060) — el interceptor de `api.ts` ya lo consume
- [x] T063 [P] Crear `app/middleware/error_handler.py`: handler global de excepciones FastAPI que convierte cualquier excepción no controlada en el envelope `{"ok": false, "errors": [{"code": "INTERNAL_ERROR", "message": "..."}]}`
- [x] T064 [P] Crear `../DASH-cli/dashboard/src/services/simulationInterceptor.ts`: extraer la lógica de simulación del interceptor de `api.ts` a función reutilizable `buildSimulatedResponse(action: string, tabla: string): SimulatedResponse`
- [x] T065 Agregar `healthcheck` endpoint `GET /health` en `app/main.py` que verifica conectividad a Postgres y Redis; usado por Docker Compose.
- [x] T066 [P] Agregar validación de `BigInteger` en `app/models/base.py`: custom validator de SQLAlchemy que lanza error en desarrollo si alguna FK se define como `Integer` en lugar de `BigInteger`
- [x] T067 Validar escenario completo del `quickstart.md`: ejecutar los 8 escenarios de validación end-to-end con `docker compose up` y confirmar que todos responden según lo esperado
- [x] T068 [P] Actualizar `specs/001-sistema-operativo-basa/checklists/requirements.md` con resultado final de validación

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — empezar ya.
- **Foundational (Phase 2)**: Depende de Phase 1 — BLOQUEA todas las historias.
- **US1 (Phase 3)**: Depende de Phase 2. Primera historia en implementar (MVP mínimo).
- **US2 (Phase 4)**: Depende de Phase 2. Extiende nodos creados en US1 — iniciar después de T024.
- **US3 (Phase 5)**: Depende de Phase 2. Extiende nodos de US1/US2 — iniciar después de T033.
- **US4 (Phase 6)**: Depende de Phase 2 + `node_commercial_logic` (T034) de US2.
- **US5 (Phase 7)**: Depende de Phase 2. Extiende nodos de US1-US4.
- **US6 (Phase 8)**: Depende de Phase 2 + `app/memory.py` (T008). **Independiente de US1-US5** (grafo separado).
- **Polish (Phase 9)**: Depende de todas las historias deseadas completas.

### Dentro de Cada Historia

- Frontend types [P] y backend nodes pueden desarrollarse en paralelo.
- Router depende de los nodos.
- Página React depende del tipo TS y del servicio `api.ts`.

### Oportunidades de Paralelismo

- T003, T004, T005 → en paralelo (archivos distintos).
- T010–T016 → todos los modelos en paralelo (un archivo cada uno).
- T019, T020 → tools en paralelo.
- T027, T028 → tipos TS y servicio api.ts en paralelo con T021, T022 (backend nodes).
- T058, T059 → readonly tool y query graph en paralelo.

---

## Parallel Example: US1

```bash
# Ejecutar en paralelo (archivos distintos):
Task T021: "app/nodes/state_preparer.py"
Task T022: "app/nodes/node_validator.py"
Task T027: "src/types/ubicacion.ts"
Task T028: "src/services/api.ts"

# Secuencial después:
T023 → T024 → T025 → T026 → T029
```

---

## Implementation Strategy

### MVP (US1 + US2 — Phases 1-4)

1. Completar Phase 1: Setup.
2. Completar Phase 2: Foundational.
3. Completar Phase 3: US1 (ubicación de cajas).
4. **DEMO**: Mostrar `PlantLocations` a directivos de BASA — operativo con datos reales.
5. Completar Phase 4: US2 (consulta de caja).
6. **DEMO**: Flujo completo cliente → picking → remito.

### Entrega Incremental

- **Sprint 1**: Phases 1-3 → Demo UC1.
- **Sprint 2**: Phase 4 → Demo UC2.
- **Sprint 3**: Phases 5-6 → Demo UC3 + UC4 (splitting + retiros).
- **Sprint 4**: Phase 7 → Demo UC5 (búsqueda).
- **Sprint 5**: Phase 8 → Demo UC6 (canal jefes).
- **Sprint 6**: Phase 9 → Polish + validación quickstart.

### Estrategia Paralela (2 desarrolladores)

- **Dev A**: Backend (Phases 1-2, luego nodes/routers de cada US).
- **Dev B**: Frontend (tipos TS, hooks, páginas React) — puede arrancar en Phase 1 con estructura y api.ts.
- Sincronizan en los checkpoints de cada phase.

---

## Notes

- `[P]` = archivos distintos, sin dependencias incompletas → pueden ejecutarse en paralelo.
- `[USN]` mapea la tarea a la User Story N del spec.md para trazabilidad.
- Cada historia es independientemente demostrable con placeholder logic activo.
- UC6 (`query_graph.py`) es **completamente independiente** del pipeline operativo (`operational_graph.py`); no comparte nodos.
- Todos los tests de integración del `quickstart.md` son la validación final de cada checkpoint.
- Confirmar que `simulated: false` en producción antes de demo con cliente.
