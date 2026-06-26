# Implementation Plan: Sistema Operativo Integral BASA Argentina

**Branch**: `001-sistema-operativo-basa` | **Date**: 2026-06-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-sistema-operativo-basa/spec.md`

---

## Summary

Sistema operativo completo para BASA Argentina que implementa 5 casos de uso críticos de gestión de archivos físicos: ubicación de cajas en planta, consulta de cajas, consulta de legajos (con splitting automático de faltantes), retiros por cantidad/referencia (con conciliación y cálculo de fletes), y trámites de búsqueda con transformación dinámica de requerimiento.

La estrategia de implementación es **Visual-First**: los 5 componentes React con placeholders de simulación se construyen primero y se demuestran al cliente antes de que el backend esté cableado. El backend usa un orquestador LangGraph de 4 nodos (`state_preparer → node_validator → node_commercial_logic → node_persistence_unit`) con transacciones atómicas sobre PostgreSQL (`dbo` schema) y memoria Redis dual-layer. Todo el stack corre en Docker Compose.

---

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5+ strict mode (frontend)

**Primary Dependencies**:
- Backend: `langgraph`, `langchain`, `langchain-anthropic`, `fastapi`, `sqlalchemy`, `redis`, `langgraph-checkpoint-redis`
- Frontend: React 18, Tailwind CSS 3, Vite 5, `axios`

**Storage**: PostgreSQL 15 (Docker, schema `dbo`), Redis 7 (Docker, dual-layer memory)

**Testing**: `pytest` + `httpx` (backend integration), `vitest` (frontend unit/component)

**Target Platform**: Linux server (Docker Compose), web browser moderno (Chrome/Edge)

**Project Type**: web-service (FastAPI backend) + web-app (React frontend) + agent (LangGraph)

**Performance Goals**: Respuestas de agente < 10s, validación de prefijos en tiempo real (< 50ms), hasta 200 requerimientos concurrentes diarios

**Constraints**: Sin DELETE físicos, transacciones atómicas obligatorias, BigInt en todas las PKs/FKs, despliegue exclusivo por Docker Compose, `.env` como única fuente de configuración

**Scale/Scope**: 5 pantallas React, 13 FRs, ~8 nodos LangGraph, ~7 tablas `dbo`, 1 stack Docker Compose

---

## Constitution Check

*GATE: Evaluado antes de Phase 0. Re-evaluado después de Phase 1.*

| Principio | Gate | Estado |
|-----------|------|--------|
| I. Visual-First | Las 5 pantallas React DEBEN existir con placeholders antes de cablear API | ✅ Todas las vistas especificadas con lógica de simulación |
| II. No Physical Deletes | Prohibido DELETE en tablas de negocio | ✅ FR-003 + Soft-delete via campo `estado` |
| III. Atomic Transactions | Todo write multi-tabla en `engine.begin()` | ✅ FR-004 + `node_persistence_unit` encapsula todo |
| IV. LangGraph Architecture | 4 nodos fijos, sin writes fuera del pipeline | ✅ Arquitectura definida con roles por nodo |
| V. BigInt PKs | Todos los IDs como `BigInt` | ✅ Documentado en data-model.md |
| VI. Redis Dual-Layer | `RedisSaver` (short-term) + `RedisStore` (long-term) | ✅ FR-012, ambas capas especificadas |
| VII. PostgreSQL Discipline | Schema `dbo`, queries parametrizadas, no f-string SQL | ✅ FR-003 + FR-004 + data model en `dbo` |
| VIII. TS+React+Tailwind | TypeScript strict, React 18, Tailwind exclusivo | ✅ FR-011, nombres de componentes especificados |

**Resultado**: ✅ Todos los gates pasan. Sin violaciones que justificar.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-sistema-operativo-basa/
├── plan.md              # Este archivo
├── research.md          # Decisiones técnicas resueltas
├── data-model.md        # Entidades, campos, relaciones, estados
├── quickstart.md        # Guía de validación end-to-end
├── checklists/
│   └── requirements.md  # Checklist de calidad del spec
├── contracts/
│   ├── api-overview.md  # Visión general de la API REST
│   ├── uc1-ubicacion.md
│   ├── uc2-consulta-caja.md
│   ├── uc3-consulta-legajos.md
│   ├── uc4-retiros.md
│   └── uc5-busqueda.md
└── tasks.md             # Generado por /speckit-tasks
```

### Source Code (repository root)

```text
SOFTWARE/                         # Raíz del proyecto backend + orquestación
├── app/
│   ├── nodes/                    # Nodos LangGraph por caso de uso
│   │   ├── state_preparer.py
│   │   ├── node_validator.py
│   │   ├── node_commercial_logic.py
│   │   └── node_persistence_unit.py
│   ├── tools/                    # LangChain Tools (skills del agente)
│   │   ├── notebooklm_tool.py
│   │   ├── postgres_tool.py          # Read+Write — solo para pipeline operativo
│   │   └── postgres_readonly_tool.py # SELECT only — solo para canal de jefes
│   ├── graphs/
│   │   ├── operational_graph.py  # Pipeline 4-nodos (UC1-UC5)
│   │   └── query_graph.py        # Grafo read-only para jefes (UC6)
│   ├── models/                   # SQLAlchemy ORM models (dbo schema)
│   │   ├── base.py
│   │   ├── elemento.py
│   │   ├── posicion.py
│   │   ├── requerimiento.py
│   │   ├── referencia.py
│   │   ├── movimiento.py
│   │   ├── hoja_ruta.py
│   │   └── lectura.py
│   ├── api/                      # FastAPI routers por caso de uso
│   │   ├── uc1_ubicacion.py
│   │   ├── uc2_consulta_caja.py
│   │   ├── uc3_consulta_legajos.py
│   │   ├── uc4_retiros.py
│   │   ├── uc5_busqueda.py
│   │   └── jefes.py              # UC6: canal read-only para jefes
│   ├── graph.py                  # StateGraph compilado con Redis
│   ├── memory.py                 # RedisSaver + RedisStore setup
│   └── main.py                   # FastAPI app entry point
├── docker-compose.yml            # Orquestación completa del stack
├── Dockerfile                    # Imagen backend Python
├── .env.example                  # Template de variables de entorno
├── pyproject.toml
└── specs/                        # Documentación spec-kit

../DASH-cli/dashboard/            # Frontend React (proyecto existente)
├── src/
│   ├── pages/
│   │   ├── PlantLocations.tsx    # UC1: Ubicación de cajas
│   │   ├── WebBoxOrder.tsx       # UC2: Pedido de caja (cliente)
│   │   ├── PickingDashboard.tsx  # UC2: Picking operario
│   │   ├── LegajosControl.tsx    # UC3: Control de legajos
│   │   ├── IntakeConciliation.tsx # UC4: Conciliación retiros
│   │   └── SearchInvestigation.tsx # UC5: Trámite de búsqueda
│   ├── types/                    # DTOs TypeScript
│   │   ├── ubicacion.ts
│   │   ├── consulta-caja.ts
│   │   ├── consulta-legajos.ts
│   │   ├── retiro.ts
│   │   └── busqueda.ts
│   └── services/
│       └── api.ts                # Cliente HTTP centralizado
└── Dockerfile.frontend           # Imagen frontend React
```

**Structure Decision**: Arquitectura web-service + web-app separados. Backend Python en `SOFTWARE/app/`, frontend React en `DASH-cli/dashboard/`. Docker Compose en raíz de `SOFTWARE/` orquesta ambos contenedores más PostgreSQL y Redis.

---

## Complexity Tracking

> No hay violaciones de constitution. Tabla vacía intencionalmente.
