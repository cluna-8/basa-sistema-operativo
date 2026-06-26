# BASA Argentina — Sistema Operativo Integral

Sistema operativo para **Banco de Archivos S.A.** — gestión de cajas, legajos, retiros, búsqueda e investigación con orquestación LangGraph y consulta conversacional con IA para jefes.

## Stack

| Capa | Tecnología |
|---|---|
| Orquestación IA | LangGraph `StateGraph` + LangChain |
| LLM | Anthropic Claude (Sonnet 4.6) |
| API | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.x |
| Base de datos | PostgreSQL 15 (schema `dbo` — **conectar a DB existente de BASA**) |
| Memoria | Redis Stack (RedisSaver checkpoints + RedisStore largo plazo) |
| Frontend | React 18 + TypeScript + Tailwind CSS + Vite |
| Contenedores | Docker Compose (4 servicios) |

## Estructura del repositorio

```
SOFTWARE/
├── app/
│   ├── api/          # Routers FastAPI (UC1–UC6)
│   ├── graphs/       # LangGraph: operational_graph.py + query_graph.py
│   ├── middleware/   # Auth JWT + error handler
│   ├── models/       # SQLAlchemy models (dbo schema)
│   ├── nodes/        # 4 nodos del pipeline: preparer, validator, logic, persistence
│   ├── services/     # email_service.py
│   └── tools/        # notebooklm_tool, postgres_tool, postgres_readonly_tool
├── specs/
│   └── 001-sistema-operativo-basa/
│       ├── spec.md           # 6 User Stories + requisitos funcionales
│       ├── plan.md           # Plan técnico completo
│       ├── data-model.md     # Modelo de datos (7 entidades)
│       ├── research.md       # Decisiones técnicas tomadas
│       ├── tasks.md          # 68 tareas (todas marcadas como completadas)
│       ├── quickstart.md     # Escenarios de validación con curl
│       └── contracts/        # Contratos de API por UC
├── docs/
│   ├── PENDIENTES-PARA-BASA.md       # ABM, auth, integraciones
│   └── DESCUBRIMIENTO-BASE-DE-DATOS.md  # ← LEER PRIMERO — plan de conexión a DB existente
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

El **frontend** está en un repositorio separado:
```
../DASH-cli/dashboard/src/
├── pages/         # PlantLocations, WebBoxOrder, PickingDashboard,
│                  # LegajosControl, IntakeConciliation,
│                  # SearchInvestigation, JefesConsulta
├── services/      # basaApi.ts — interceptor de simulación
├── hooks/         # usePrefixValidator.ts
└── types/         # basa.ts — interfaces TypeScript
```

## Levantar en local

### Requisitos
- Docker + Docker Compose
- Git

### Pasos

```bash
# 1. Clonar
git clone <url-del-repo>
cd SOFTWARE

# 2. Variables de entorno
cp .env.example .env
# Editar .env con la ANTHROPIC_API_KEY real si se quiere UC6 con IA real

# 3. Levantar todo
docker compose up --build -d

# 4. Verificar
curl http://localhost:8000/health
# → {"ok":true,"postgres":"up","redis":"up"}
```

### URLs

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

### Credenciales de desarrollo

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | jefe |
| `jefe` | `jefe2024` | jefe |
| `operario` | `basa2024` | operario |

> ⚠️ Credenciales hardcodeadas solo para desarrollo. Ver `docs/PENDIENTES-PARA-BASA.md` sección 5 para migrar a auth real.

## Casos de uso implementados

| UC | Pantalla | Ruta | Estado |
|---|---|---|---|
| UC1 | Ubicación de cajas en planta | `/operaciones/ubicacion` | ✅ Simulación |
| UC2 | Pedido de caja — cliente | `/operaciones/consulta-caja` | ✅ Simulación |
| UC2 | Picking — operario | `/operaciones/picking` | ✅ Simulación |
| UC3 | Control de legajos + splitting | `/operaciones/legajos` | ✅ Simulación |
| UC4 | Conciliación de retiros | `/operaciones/retiros` | ✅ Simulación |
| UC5 | Trámite de búsqueda | `/operaciones/busqueda` | ✅ Simulación |
| UC6 | Consulta IA para jefes | `/operaciones/jefes` | ✅ Simulación (requiere API Key para IA real) |

**"Simulación"** significa que el frontend funciona completo y muestra alertas amarillas. Los datos no persisten hasta conectar la base de datos real de BASA.

## ⚠️ Próximo paso crítico

**Leer `docs/DESCUBRIMIENTO-BASE-DE-DATOS.md`** antes de escribir más código.

BASA tiene una base de datos existente con millones de cajas y un ABM ya conectado. Necesitamos:

1. Obtener acceso (lectura) al ambiente de desarrollo de BASA
2. Explorar el schema existente
3. Mapear sus tablas a los modelos en `app/models/`
4. Adaptar las queries de los nodos LangGraph

No crear tablas nuevas hasta confirmar con el DBA de BASA qué ya existe.

## Pipeline LangGraph

```
request
  │
  ▼
state_preparer     → normaliza input, identifica tipo de operación
  │
  ▼
node_validator     → valida prefijos, estados, disponibilidad
  │
  ├─[errores]──→ END (respuesta con errores)
  │
  ▼
node_commercial_logic   → cálculo de fletes, reglas de negocio
  │
  ▼
node_persistence_unit   → escribe en DB (engine.begin() atómico)
  │
  ▼
response
```

UC6 usa un grafo separado (`query_graph.py`) con `create_react_agent` + herramientas de solo lectura. Nunca comparte nodos con el pipeline operativo.

## Variables de entorno

Ver `.env.example` para la lista completa. Variables críticas:

```env
DATABASE_URL=postgresql://user:pass@host:5432/db   # ← DB real de BASA
REDIS_URL=redis://redis:6379/0
ANTHROPIC_API_KEY=sk-ant-...                        # ← Para UC6 IA real
JWT_SECRET=<string-aleatorio-256-bits>              # ← Cambiar en producción
```

## Documentación técnica

- **Especificación:** `specs/001-sistema-operativo-basa/spec.md`
- **Plan técnico:** `specs/001-sistema-operativo-basa/plan.md`
- **Modelo de datos:** `specs/001-sistema-operativo-basa/data-model.md`
- **Contratos API:** `specs/001-sistema-operativo-basa/contracts/`
- **Pendientes:** `docs/PENDIENTES-PARA-BASA.md`
- **Conexión a DB existente:** `docs/DESCUBRIMIENTO-BASE-DE-DATOS.md`
