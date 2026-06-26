# Contrato API: UC1 — Ordenamiento y Ubicación de Cajas

## POST `/api/v1/ubicacion/asignar`

Vincula una caja a una posición física. Operación atómica.

**Request**:
```json
{
  "codigo_caja": "110001234567",
  "codigo_posicion": "12345678901234",
  "operario_id": 42
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "elemento_id": 1001,
    "posicion_id": 55,
    "estado_posicion": "OCUPADO",
    "movimiento_id": 9900
  },
  "simulated": false
}
```

**Errores posibles**:
- `ELEMENTO_NO_ENCONTRADO` — El código de caja no existe en `dbo.elemento`.
- `POSICION_OCUPADA` — La posición ya tiene un elemento asignado.
- `POSICION_NO_ENCONTRADA` — El código de módulo de 14 dígitos no existe.

---

## GET `/api/v1/ubicacion/posicion/{codigo_modulo}`

Consulta el estado actual de una posición.

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "posicion_id": 55,
    "estado": "DISPONIBLE",
    "estanteria": 3,
    "codigo_modulo": "MOD-A-003-01",
    "elemento_actual": null
  }
}
```

---

## TypeScript DTO (`ubicacion.ts`)

```typescript
export interface AsignarUbicacionRequest {
  codigo_caja: string;      // 12 dígitos
  codigo_posicion: string;  // 14 dígitos
  operario_id: number;
}

export interface AsignarUbicacionResponse {
  ok: boolean;
  data?: {
    elemento_id: number;
    posicion_id: number;
    estado_posicion: 'OCUPADO' | 'DISPONIBLE';
    movimiento_id: number;
  };
  simulated: boolean;
  errors?: ApiError[];
}

export interface ApiError {
  code: string;
  field?: string;
  message: string;
}
```
