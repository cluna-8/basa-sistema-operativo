# Handoff — BASA Sistema Operativo v0.1.0

> **Para el equipo que continúa**: Leer este archivo primero. Luego `README.md`, luego `docs/DESCUBRIMIENTO-BASE-DE-DATOS.md`. Con eso Claude y tu colega tienen todo el contexto para seguir sin preguntas.

---

## Estado actual (2026-06-26)

El sistema está en estado **Visual-First completo**: las 7 pantallas React están construidas y funcionan con simulación controlada. El backend levanta, responde en `/health` y tiene los endpoints definidos, pero las llamadas a los casos de uso reales fallan porque la base de datos de BASA aún no está conectada (no hay migrations ni tablas reales).

### Qué funciona hoy

| Componente | Estado | Detalle |
|---|---|---|
| Frontend React — 7 pantallas | ✅ Funciona | Simulación completa, alertas amarillas cuando el backend no responde |
| Backend FastAPI — arranque | ✅ Funciona | `GET /health` responde, Swagger en `/docs` |
| Auth JWT | ✅ Funciona | Login con credenciales hardcodeadas (ver abajo) |
| `GET /api/bundle` | ✅ Funciona | Retorna info del proyecto + 6 UCs |
| Redis Stack | ✅ Funciona | `redis/redis-stack-server:latest` con RediSearch |
| PostgreSQL | ✅ Levanta | Pero sin tablas — migrations pendientes |
| Endpoints UC1–UC6 | ⚠️ Simulados | Devuelven error de tabla hasta conectar DB real |
| UC6 IA (jefes) | ⚠️ Requiere API Key | Necesita `ANTHROPIC_API_KEY` real en `.env` |

### Credenciales de desarrollo

```
admin    / admin123  → rol jefe
jefe     / jefe2024  → rol jefe
operario / basa2024  → rol operario
```

Hardcodeadas en `app/main.py` dict `DEV_USERS`. Cambiar por auth real contra tabla `dbo.usuario` (ver `docs/PENDIENTES-PARA-BASA.md` sección 5).

### URLs cuando los Dockers están corriendo

```
http://localhost:5173       → Frontend React
http://localhost:8000       → Backend API
http://localhost:8000/docs  → Swagger interactivo
```

---

## Cómo levantar todo

```bash
# Solo Docker, no instalar nada local
git clone https://github.com/cluna-8/basa-sistema-operativo
cd basa-sistema-operativo
cp .env.example .env
# Editar .env y poner ANTHROPIC_API_KEY real si querés UC6 con IA real
docker compose up --build -d

# Verificar
curl http://localhost:8000/health
# → {"ok":true,"postgres":"up","redis":"up"}
```

El frontend está en un repo separado pero el Docker Compose del backend lo construye y sirve por nginx en el puerto 5173.

---

## Pantallas implementadas

| Ruta | Pantalla | UC | Archivo |
|---|---|---|---|
| `/operaciones/ubicacion` | Ubicación de cajas en planta | UC1 | `src/pages/PlantLocations.tsx` |
| `/operaciones/consulta-caja` | Pedido web — cliente | UC2 | `src/pages/WebBoxOrder.tsx` |
| `/operaciones/picking` | Picking — operario | UC2 | `src/pages/PickingDashboard.tsx` |
| `/operaciones/legajos` | Control de legajos + splitting | UC3 | `src/pages/LegajosControl.tsx` |
| `/operaciones/retiros` | Conciliación de retiros | UC4 | `src/pages/IntakeConciliation.tsx` |
| `/operaciones/busqueda` | Trámite de búsqueda | UC5 | `src/pages/SearchInvestigation.tsx` |
| `/operaciones/jefes` | Consulta IA para jefes | UC6 | `src/pages/JefesConsulta.tsx` |

### Cómo funciona la simulación

Toda comunicación con el backend pasa por `basaFetch()` en `src/services/basaApi.ts`. Si el backend falla (red caída, endpoint no implementado), `basaFetch` intercepta el error y retorna `{ ok: true, simulated: true }`. Cada pantalla detecta `res.simulated === true` y muestra una alerta amarilla. Así el flujo visual es completamente demostrable sin backend.

Para cablear un endpoint real: simplemente implementar el endpoint en FastAPI y ejecutar las migrations. La pantalla React no necesita cambios, solo deja de recibir `simulated: true`.

---

## Arquitectura del backend

### Pipeline LangGraph (UC1–UC5)

```
request → state_preparer → node_validator → node_commercial_logic → node_persistence_unit → response
                                │ (si hay errores)
                                └──────────────────────────────────────────────────────→ END
```

- `state_preparer` (`app/nodes/state_preparer.py`): normaliza el input, identifica tipo de operación
- `node_validator` (`app/nodes/node_validator.py`): valida prefijos de código, estados, disponibilidad
- `node_commercial_logic` (`app/nodes/node_commercial_logic.py`): cálculo de fletes `ceil(n/20)`, reglas de negocio, splitting de legajos
- `node_persistence_unit` (`app/nodes/node_persistence_unit.py`): escribe en DB dentro de `engine.begin()` atómico

### UC6 — canal de jefes (separado)

`app/graphs/query_graph.py` usa `create_react_agent` con herramientas de **solo lectura** (`postgres_readonly_tool`). Nunca comparte nodos ni write-access con el pipeline operativo.

### Memoria Redis dual-layer

- `RedisSaver` (checkpoints de corto plazo): toma **URL string** como argumento — `RedisSaver(url_string)`
- `RedisStore` (memoria de largo plazo): toma **cliente Redis** como argumento — `RedisStore(redis_lib.from_url(url))`
- Ambos definidos en `app/memory.py`
- **Requiere `redis/redis-stack-server:latest`** — el `redis:7-alpine` estándar no tiene RediSearch y rompe `langgraph-checkpoint-redis`

---

## Decisiones técnicas tomadas (y por qué)

| Decisión | Razón | Archivo afectado |
|---|---|---|
| `redis/redis-stack-server:latest` en vez de `redis:7-alpine` | `redisvl` requiere RediSearch (`FT._LIST`) que no existe en Alpine | `docker-compose.yml` |
| `RedisSaver(url_string)` — NO `.from_conn_string()` | `.from_conn_string()` retorna context manager, no se le puede llamar `.setup()` directamente | `app/memory.py` |
| `RedisStore(redis_client)` — NO `RedisStore(url_string)` | La API de `RedisStore` exige un cliente Redis, no una URL | `app/memory.py` |
| `python-multipart` en dependencias | FastAPI necesita este paquete para recibir form data (`Form(...)`) en el endpoint de login | `pyproject.toml` |
| Frontend en nginx prod build, no en dev server | Docker Compose sirve el build estático de Vite, más liviano y sin hot-reload | `docker-compose.yml` + `Dockerfile target: prod` |
| `nginx.conf` proxy a `backend:8000` — NO a `api:8000` | El servicio en docker-compose se llama `backend`, no `api` | `dashboard/nginx.conf` |
| `isOperational` flag en `App.tsx` | Las rutas `/operaciones/*` no deben esperar `fetchBundle()` para renderizar | `dashboard/src/App.tsx` |
| `usePrefixValidator` hook | Normaliza códigos de 6/7/12 dígitos a 12 dígitos con prefijos (11000/110000 cajas, 12000/120000 legajos) | `dashboard/src/hooks/usePrefixValidator.ts` |

---

## Próximos pasos (en orden)

### 1. Sesión de descubrimiento con BASA (BLOQUEANTE)

**Leer `docs/DESCUBRIMIENTO-BASE-DE-DATOS.md` completo antes de escribir cualquier migration.**

BASA tiene una base de datos existente con millones de cajas y un ABM ya conectado. No crear tablas nuevas hasta saber qué tienen. El documento tiene 7 bloques y 50+ preguntas para la sesión con el DBA.

### 2. Conectar la DB real

Después de la sesión de descubrimiento:
1. Actualizar `DATABASE_URL` en `.env` con los datos reales
2. Adaptar los modelos en `app/models/` a las tablas reales de BASA
3. Correr las migrations (o mapear a tablas existentes con `autoload_with=engine`)
4. Probar cada endpoint con datos reales

### 3. Pendientes de desarrollo

Ver `docs/PENDIENTES-PARA-BASA.md` para la lista completa. Los más críticos:

| Pendiente | Prioridad | Sección en doc |
|---|---|---|
| Migrations / schema real | CRÍTICO | Sección 1 |
| ABM de entidades (clientes, posiciones, módulos) | ALTA | Sección 2 |
| Auth real contra tabla de usuarios | ALTA | Sección 5 |
| Seed data inicial | ALTA | Sección 1 |
| ANTHROPIC_API_KEY real para UC6 | MEDIA | Sección 4 |
| Integración con Aconcagua (sistema externo) | MEDIA | Sección 3 |
| NotebookLM MCP para búsqueda semántica | BAJA | Sección 6 |

---

## Repositorios

| Repo | URL | Contenido |
|---|---|---|
| Backend | https://github.com/cluna-8/basa-sistema-operativo | FastAPI + LangGraph + specs + docs |
| Frontend | https://github.com/cluna-8/basa-dashboard | React 18 + 7 pantallas UC1–UC6 |

---

## Para Claude: contexto de sesión anterior

Esta sección es para que Claude entienda el estado sin leer el historial completo.

Se implementó una estrategia Visual-First completa: primero todas las pantallas React con simulación, luego el backend. La simulación funciona via `basaFetch()` que intercepta errores de red y retorna `{ ok: true, simulated: true }`. Las pantallas muestran alertas amarillas cuando operan en modo simulado.

El backend tiene todos los routers definidos pero los nodos LangGraph no pueden persistir porque no hay tablas en PostgreSQL. El primer `docker compose up` levanta correctamente: health check pasa, login funciona, Swagger está disponible.

El siguiente paso de código es conectar a la DB real de BASA una vez que el DBA provea acceso y schema. No implementar migrations genéricas — esperar la sesión de descubrimiento.

La memoria de largo plazo de estas decisiones vive localmente en `~/.claude/projects/.../memory/project_basa_estado.md` en la máquina original. Este archivo `HANDOFF.md` es el sustituto portable para otros equipos.
