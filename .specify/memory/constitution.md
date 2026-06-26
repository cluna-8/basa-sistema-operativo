<!--
SYNC IMPACT REPORT
==================
Version change: [UNVERSIONED] → 1.0.0
Bump rationale: MINOR — Initial population of all principles from project specs.

Added sections:
  - Core Principles (8 principles derived from spec docs)
  - Technology Stack
  - Development Workflow
  - Governance

Modified principles: N/A (first version)
Removed sections: N/A

Templates checked:
  ✅ .specify/templates/plan-template.md — Constitution Check gates aligned
  ✅ .specify/templates/spec-template.md — No changes needed; structure compatible
  ✅ .specify/templates/tasks-template.md — No changes needed; phase structure compatible

Deferred TODOs:
  - RATIFICATION_DATE set to project start inferred from spec docs (2026-06-26)
-->

# BASA Argentina Constitution

## Core Principles

### I. Visual-First Development (NON-NEGOTIABLE)

React UI components MUST be built before backend persistence is wired. Every
screen MUST implement controlled simulation placeholders: when a backend
call fails or does not exist, the UI MUST display a descriptive simulation
alert (e.g., *"Acción simulada: Datos listos para grabación en `[tabla]`"*)
instead of a generic error. This allows UX validation with real clients
independently of backend completion status.

**Rationale**: BASA directors require visible, interactive progress at all
times. Blocking frontend on backend readiness has historically delayed
client sign-off.

### II. No Physical Deletes (NON-NEGOTIABLE)

Physical `DELETE` statements are strictly prohibited on any business entity
table. All logical removal MUST be implemented as soft-deletes via status
flags (e.g., `estado = 'BAJA'`) or boolean tombstone columns. The
`dbo.movimiento` audit table MUST never lose referential integrity.

**Rationale**: The system requires full historical traceability for
compliance and billing reconstruction. Orphaned audit records caused by
hard deletes are unacceptable.

### III. Atomic Transactions (NON-NEGOTIABLE)

Every operation that touches more than one table MUST be wrapped in a single
`with engine.begin() as connection:` block. If any step within the
transaction fails (including audit log writes or email triggers), the entire
operation MUST roll back to avoid partial state corruption. This applies to
all LangGraph `node_persistence_unit` implementations.

**Rationale**: Prior system incidents resulted in elements changing state
without corresponding `dbo.movimiento` entries, making audits impossible.

### IV. LangGraph Orchestrator Architecture

All backend business logic MUST flow through a 4-node StateGraph:
`state_preparer` → `node_validator` → `node_commercial_logic` →
`node_persistence_unit`. No direct database writes are permitted outside
this pipeline. Each node has a single responsibility and MUST NOT call
the database for writes outside `node_persistence_unit`.

- `state_preparer`: Receives JSON payload, identifies `requerimiento_tipo_id`,
  defines affected tables.
- `node_validator`: Validates business rules and element states. Returns
  structured error array on failure — never raises unhandled exceptions.
- `node_commercial_logic`: Calculates derived values (fletes, horas, costs).
- `node_persistence_unit`: Executes atomic DB writes and audit entries.

**Rationale**: The ABM Agéntico de Clientes proved this pattern enables
atomic, testable, traceable transactions. All new use cases extend it.

### V. BigInt for All Primary and Foreign Keys

All `id`, `*_id`, and cross-table reference columns MUST be typed as
`BigInt` (Python: `int`, SQLAlchemy: `BigInteger`). Numeric or Integer
types are prohibited for PK/FK columns.

**Rationale**: Historical overflow issues with 32-bit integers as the
archive grows past millions of records. PostgreSQL `bigint` prevents
rekey migrations.

### VI. Redis Dual-Layer Memory

The LangGraph agent MUST use two Redis-backed memory layers:
- **Short-term** (`RedisSaver` checkpointer): Persists conversation state
  per `thread_id` across turns within a session.
- **Long-term** (`RedisStore`): Persists operator preferences and client
  configurations across sessions, namespaced by `user_id`.

Both stores MUST call `.setup()` on first initialization. Thread IDs MUST
follow the pattern `[operario]_sesion_[N]` for traceability.

**Rationale**: Without dual-layer memory, repeated context re-injection
degrades LLM accuracy on long operational sessions and loses cross-session
operator personalization.

### VII. PostgreSQL Schema Discipline

All tables MUST reside under the `dbo` schema. Raw `DELETE` is banned
(see Principle II). All queries MUST use parameterized statements via
SQLAlchemy `text()` — no f-string SQL interpolation is permitted. Schema
changes MUST be backward-compatible or accompanied by a migration script.

**Rationale**: The existing BASA database uses `dbo` schema conventions
from a prior SQL Server migration. Consistency is required for tooling
compatibility.

### VIII. TypeScript + React + Tailwind Frontend

All UI components MUST be written in TypeScript (strict mode). React is the
mandatory framework. Tailwind CSS is the exclusive styling mechanism — no
inline styles or additional CSS frameworks. Component filenames MUST match
the view specification exactly (e.g., `PlantLocations.tsx`, `WebBoxOrder.tsx`).
All API payloads MUST have corresponding TypeScript DTOs defined in `src/types/`.

**Rationale**: Strict typing prevents payload mismatches between frontend
and the LangGraph backend. The dashboard project (`DASH-cli`) enforces this
stack and agents must not deviate.

## Technology Stack

- **Backend**: Python 3.11+, LangGraph, LangChain, SQLAlchemy, FastAPI
- **Frontend**: TypeScript (strict), React 18+, Tailwind CSS
- **Database**: PostgreSQL (Docker), schema `dbo`, BigInt PKs
- **Memory**: Redis — `langgraph-checkpoint-redis` + `langgraph.store.redis`
- **Knowledge base**: NotebookLM MCP (local server at `localhost:18789`)
- **Package manager**: `uv` (Python), `npm` (frontend)
- **LLM**: Claude (via Anthropic API) as the agent model

## Development Workflow

1. **UI First**: Build and demo React screen with simulation placeholders.
2. **DTO Contract**: Define TypeScript payload types in `src/types/`.
3. **Graph Node**: Implement the LangGraph node pipeline for the use case.
4. **Database Wire**: Replace frontend placeholders with real API calls.
5. **Validation**: Run end-to-end flow with a real `thread_id` in Redis.

All new use cases follow this order. Steps 1–2 may be demoed to BASA
directors before Steps 3–5 are complete.

## Governance

- This constitution supersedes all prior verbal agreements and informal
  conventions. Any deviation requires an explicit amendment.
- Amendments require: (a) documented rationale, (b) version bump, (c)
  update to all affected templates and this file.
- Compliance is verified at each `/speckit-plan` Constitution Check gate.
- Complexity violations MUST be documented in the plan's Complexity Tracking
  table with justification.
- Guidance file for runtime development: `.specify/memory/constitution.md`
  (this file).

**Version**: 1.0.0 | **Ratified**: 2026-06-26 | **Last Amended**: 2026-06-26
