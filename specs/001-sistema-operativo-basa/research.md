# Research: Sistema Operativo Integral BASA Argentina

**Date**: 2026-06-26
**Feature**: [spec.md](./spec.md)

---

## Decisiones Técnicas Resueltas

### 1. Orquestador de Agente: LangGraph StateGraph

**Decision**: LangGraph con `StateGraph` compilado con `RedisSaver` (checkpointer) y `RedisStore` (store).

**Rationale**: El proyecto ya usa este patrón en el ABM Agéntico de Clientes. LangGraph garantiza transiciones de estado determinísticas, permite rollback limpio si un nodo falla, y soporta nativo el patrón de memoria dual que requiere el sistema.

**Alternatives considered**:
- LangChain AgentExecutor: descartado por falta de control granular de flujo entre nodos.
- Custom pipeline sin framework: descartado por costo de mantenimiento y ausencia de checkpointing built-in.

---

### 2. API Gateway: FastAPI

**Decision**: FastAPI como capa HTTP entre el frontend React y el orquestador LangGraph.

**Rationale**: FastAPI es async-native (compatible con LangGraph async), genera OpenAPI docs automáticamente (útil para los contratos de cada UC), y tiene serialización/validación con Pydantic integrada. El proyecto usa Python 3.11+ donde FastAPI tiene mejor rendimiento.

**Alternatives considered**:
- Flask: descartado por ser síncrono y carecer de validación de tipos nativa.
- Django REST Framework: descartado por overhead excesivo para un backend agéntico.

---

### 3. ORM: SQLAlchemy 2.x con `engine.begin()`

**Decision**: SQLAlchemy 2.x usando el context manager `engine.begin()` para todas las transacciones multi-tabla.

**Rationale**: `engine.begin()` garantiza el rollback automático si cualquier sentencia dentro del bloque lanza excepción, cumpliendo el Principio III de la Constitution. SQLAlchemy 2.x tiene soporte nativo para `BigInteger` (cumple Principio V) y permite queries parametrizadas via `text()` (cumple Principio VII).

**Alternatives considered**:
- asyncpg directo: descartado por ausencia de ORM layer y gestión manual de transacciones.
- Tortoise ORM: descartado por menor madurez y ecosistema más pequeño.

---

### 4. Memoria: Redis con `langgraph-checkpoint-redis`

**Decision**: Redis 7 con `RedisSaver` para short-term (por `thread_id`) y `RedisStore` para long-term (por `user_id`).

**Rationale**: La biblioteca `langgraph-checkpoint-redis` es el backend oficial soportado por LangGraph para Redis. Permite `.setup()` en primera inicialización y limpia la configuración de checkpointing. Redis 7 tiene mejor rendimiento en operaciones de hash que versiones anteriores.

**Alternatives considered**:
- PostgreSQL como checkpointer (`langgraph-checkpoint-postgres`): técnicamente válido pero agrega carga a la misma base de datos transaccional. Redis mantiene la separación de concerns.
- In-memory checkpointer: descartado porque no persiste entre reinicios del contenedor.

---

### 5. Contenedorización: Docker Compose multi-service

**Decision**: `docker-compose.yml` único en raíz de `SOFTWARE/` orquestando 4 servicios: `backend` (FastAPI+LangGraph), `frontend` (React/Nginx), `postgres` (PostgreSQL 15), `redis` (Redis 7).

**Rationale**: FR-011 requiere arranque con un único comando. Docker Compose v2 (plugin nativo) soporta `depends_on` con `condition: service_healthy` para asegurar que Postgres y Redis estén listos antes de que el backend intente conectarse.

**Alternatives considered**:
- Kubernetes: descartado por complejidad operativa excesiva para el servidor local de BASA.
- Docker Swarm: descartado por menor adopción y documentación respecto a Compose para ambientes single-node.

---

### 6. Lógica de Prefijos de 12 Dígitos (Validación Frontend)

**Decision**: Validación implementada en el frontend como hook React reutilizable `usePrefixValidator(codigo: string)` que calcula el prefijo en tiempo real según la longitud del input.

**Reglas resueltas**:

| Tipo | Longitud | Prefijo | Ejemplo resultado |
|------|----------|---------|-------------------|
| Caja 7 dígitos | 7 | `11000` | `110001234567` |
| Caja 6 dígitos | 6 | `110000` | `110000123456` |
| Caja vieja 4 dígitos | 4 | `13` + código_cliente(4) + `00` | `131025001234` |
| Legajo 7 dígitos | 7 | `12000` | `120001234567` |
| Legajo 6 dígitos | 6 | `120000` | `120000123456` |
| Legajo viejo 4 dígitos | 4 | `14` + código_cliente(4) + `00` | `141025001234` |

El hook rechaza cualquier longitud no contemplada con error visual inmediato.

---

### 7. Estrategia de Simulación Controlada (Placeholder Logic)

**Decision**: Patrón de interceptor en el cliente HTTP (`services/api.ts`): si el backend retorna error o no está disponible, el interceptor captura la excepción y retorna un objeto `SimulatedResponse` con el mensaje estandarizado.

**Formato del mensaje de simulación**:
```
"Simulado: [Acción] completada. Pendiente de grabación en [nombre_tabla]."
```

Cada pantalla tiene su propio mapeo de tabla destino hardcodeado. El interceptor diferencia entre errores de red (simula) y errores de validación del backend (propaga al usuario).

---

### 8. Cálculo de Fletes

**Decision**: `fletes = math.ceil(cantidad / 20)` calculado en `node_commercial_logic`. El resultado se persiste en `dbo.requerimiento.fletes`.

**Casos borde resueltos**:
- `cantidad = 0`: `fletes = 0` (retiro vacío, se alerta pero no bloquea).
- `cantidad = 20`: `fletes = 1`.
- `cantidad = 21`: `fletes = 2`.
- `cantidad = None`: `node_validator` rechaza el payload antes de llegar a `node_commercial_logic`.

---

### 9. Splitting de Legajos Faltantes

**Decision**: El splitting ocurre dentro del `node_persistence_unit` en una transacción única:
1. Se actualiza el requerimiento padre con `cantidad = len(legajos_encontrados)`.
2. Si `len(legajos_faltantes) > 0`, se inserta un nuevo requerimiento hijo con `requerimiento_tipo_id = 16` y `estado = 'PENDIENTE_BUSQUEDA'`.
3. Ambas operaciones van en el mismo `engine.begin()`. Si el INSERT hijo falla, el UPDATE padre revierte.

---

### 10. Transformación Dinámica de Requerimiento (UC5)

**Decision**: `node_persistence_unit` ejecuta en una transacción:
1. `UPDATE dbo.requerimiento SET tipoRequerimiento_id = [02|08], horas_archivista = X WHERE id = Y`.
2. `INSERT INTO dbo.movimiento (tipo_movimiento = 'INVESTIGACION_EXITOSA', ...)`.
3. El nodo retorna el nuevo tipo para que el frontend redirija al flujo de despacho correspondiente.

La auditoría del tipo original se preserva en `dbo.movimiento` (el registro de tipo 16 previo no se borra).
