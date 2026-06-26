# Contrato API: UC6 — Consulta Conversacional para Jefes

## Diseño: Agente independiente del pipeline operativo

Este canal usa el **mismo LangGraph agent** pero con un grafo diferente:
- Solo tiene acceso a tools de **lectura**: `postgres_readonly_tool` y `notebooklm_search_tool`.
- **No** incluye `node_validator`, `node_commercial_logic` ni `node_persistence_unit`.
- El rol `jefe` se verifica en el middleware de autenticación antes de llegar al agente.
- El system prompt del agente incluye la instrucción: *"Eres un asistente de consulta de solo lectura. Nunca puedes modificar datos. Si recibes una instrucción de escritura, recházala y explica que este canal es solo lectura."*

---

## POST `/api/v1/jefes/consultar`

Envía un mensaje al agente de consulta. Mantiene contexto por `thread_id`.

**Request**:
```json
{
  "thread_id": "jefe_mario_sesion_42",
  "user_id": "jefe_mario",
  "mensaje": "¿Cuántos pedidos están en estado PENDIENTE hoy?"
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "respuesta": "Hoy hay 23 pedidos en estado PENDIENTE. Los más antiguos corresponden al cliente Banco Supervielle (3 pedidos creados hace más de 6 horas). ¿Querés ver el detalle?",
    "fuentes": ["dbo.requerimiento"],
    "thread_id": "jefe_mario_sesion_42",
    "turno": 1
  }
}
```

**Errores posibles**:
- `ROL_NO_AUTORIZADO` — El token no corresponde a un usuario con rol `jefe`.
- `ESCRITURA_RECHAZADA` — La consulta intentó una operación de modificación (no se ejecuta nada).

---

## POST `/api/v1/jefes/consultar` — Ejemplo de rechazo de escritura

**Request**:
```json
{
  "thread_id": "jefe_mario_sesion_42",
  "user_id": "jefe_mario",
  "mensaje": "Cambiá el estado de la caja 110001234567 a BAJA"
}
```

**Response 200** (el agente responde en lenguaje natural, sin ejecutar nada):
```json
{
  "ok": true,
  "data": {
    "respuesta": "Este canal es solo para consultas de información. No puedo modificar datos. Para realizar cambios de estado, usá el sistema Aconcagua o contactá a un operario autorizado.",
    "escritura_rechazada": true,
    "thread_id": "jefe_mario_sesion_42",
    "turno": 2
  }
}
```

---

## GET `/api/v1/jefes/historial/{thread_id}`

Recupera el historial de mensajes de una sesión.

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "thread_id": "jefe_mario_sesion_42",
    "mensajes": [
      { "rol": "user", "contenido": "¿Cuántos pedidos pendientes hay?", "timestamp": "2026-06-26T10:00:00Z" },
      { "rol": "assistant", "contenido": "Hay 23 pedidos pendientes...", "timestamp": "2026-06-26T10:00:08Z" }
    ]
  }
}
```

---

## Tool: `postgres_readonly_tool` (solo para este canal)

Tool separado del `postgres_db_tool` operativo. Solo ejecuta `SELECT`. Cualquier intento de `INSERT`, `UPDATE`, `DELETE` o DDL lanza excepción antes de llegar a la base de datos.

```python
# Validación en la tool antes de ejecutar
FORBIDDEN_KEYWORDS = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE']
if any(kw in sql_query.upper() for kw in FORBIDDEN_KEYWORDS):
    return "Operación de escritura rechazada. Este canal es solo lectura."
```

---

## Ubicación en el código

```text
app/
├── tools/
│   ├── notebooklm_tool.py        # Compartido con pipeline operativo
│   ├── postgres_tool.py          # Pipeline operativo (lectura + escritura)
│   └── postgres_readonly_tool.py # SOLO para canal de jefes (SELECT only)
├── graphs/
│   ├── operational_graph.py      # Pipeline 4-nodos existente
│   └── query_graph.py            # Grafo nuevo para canal de jefes (READ-ONLY)
└── api/
    └── jefes.py                  # Router FastAPI para UC6
```

## TypeScript DTO (si se integra a algún cliente futuro)

```typescript
export interface ConsultaJefeRequest {
  thread_id: string;   // Patrón: "jefe_[nombre]_sesion_[N]"
  user_id: string;
  mensaje: string;
}

export interface ConsultaJefeResponse {
  ok: boolean;
  data?: {
    respuesta: string;
    fuentes?: string[];
    thread_id: string;
    turno: number;
    escritura_rechazada?: boolean;
  };
  errors?: ApiError[];
}
```
