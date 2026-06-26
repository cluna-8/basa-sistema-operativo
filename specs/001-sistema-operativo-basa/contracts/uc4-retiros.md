# Contrato API: UC4 — Retiros por Cantidad o Referencia

## POST `/api/v1/retiros/crear`

Crea un requerimiento de retiro (cantidad genérica o por referencia).

**Request**:
```json
{
  "cliente_id": 10,
  "tipo": "CANTIDAD",
  "cantidad_declarada": 15,
  "codigos_referencia": [],
  "direccion_origen_id": 7
}
```
> `tipo`: `"CANTIDAD"` (sin códigos previos) | `"REFERENCIA"` (códigos en `codigos_referencia`)

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "requerimiento_id": 7001,
    "estado": "PENDIENTE",
    "fletes_estimados": 1
  }
}
```

---

## POST `/api/v1/retiros/lectura/procesar`

Procesa el archivo de lectura del colector láser (ingreso a planta o retiro en cliente).

**Request**:
```json
{
  "requerimiento_id": 7001,
  "tipo_lectura": "PLANTA",
  "remito_nombre": "0001-26062026-MZA",
  "codigos_leidos": ["110001111111", "110002222222", "110003333333"]
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "lectura_id": 3001,
    "cantidad_leida": 3,
    "cantidad_declarada": 15,
    "diferencia": -12,
    "hay_discrepancia": true
  }
}
```

---

## POST `/api/v1/retiros/conciliar`

Concilia las cantidades y calcula fletes finales. Envía email al cliente si hay discrepancia.

**Request**:
```json
{
  "requerimiento_id": 7001,
  "operario_id": 42,
  "confirmar_discrepancia": true
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "cantidad_final": 11,
    "fletes_calculados": 1,
    "email_enviado": true,
    "estado_requerimiento": "FINALIZADO"
  }
}
```

---

## TypeScript DTO (`retiro.ts`)

```typescript
export type TipoRetiro = 'CANTIDAD' | 'REFERENCIA';
export type TipoLectura = 'CLIENTE' | 'PLANTA';

export interface CrearRetiroRequest {
  cliente_id: number;
  tipo: TipoRetiro;
  cantidad_declarada?: number;
  codigos_referencia?: string[];
  direccion_origen_id: number;
}

export interface ConciliarRetiroResponse {
  ok: boolean;
  data?: {
    cantidad_final: number;
    fletes_calculados: number;
    email_enviado: boolean;
    estado_requerimiento: string;
  };
  simulated: boolean;
  errors?: ApiError[];
}
```
