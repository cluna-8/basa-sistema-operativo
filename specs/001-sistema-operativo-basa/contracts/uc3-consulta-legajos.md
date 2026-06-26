# Contrato API: UC3 — Consulta Normal de Legajos

## POST `/api/v1/consulta-legajos/crear`

Crea un requerimiento de consulta de legajos con validación de prefijos.

**Request**:
```json
{
  "cliente_id": 10,
  "direccion_entrega_id": 3,
  "codigos_legajo": ["120001234567", "120009876543", "120005555555"]
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "requerimiento_id": 6001,
    "estado": "PENDIENTE",
    "legajos_validados": [
      { "codigo": "120001234567", "valido": true, "caja_contenedora": "110000111111" },
      { "codigo": "120009876543", "valido": false, "motivo": "No encontrado en sistema" }
    ]
  }
}
```

---

## POST `/api/v1/consulta-legajos/picking/escanear`

Registra el escaneo físico de un legajo durante el picking.

**Request**:
```json
{
  "requerimiento_id": 6001,
  "codigo_legajo": "120001234567",
  "operario_id": 42
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "legajo_encontrado": true,
    "pendientes_count": 2,
    "encontrados_count": 1
  }
}
```

---

## POST `/api/v1/consulta-legajos/remito/procesar`

Procesa el remito. Si hay faltantes, ejecuta el splitting automático en una transacción atómica.

**Request**:
```json
{
  "requerimiento_id": 6001,
  "operario_id": 42
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "remito_id": 7001,
    "legajos_despachados": ["120001234567"],
    "splitting_realizado": true,
    "requerimiento_hijo_id": 6002,
    "legajos_pendientes_busqueda": ["120009876543", "120005555555"]
  }
}
```

**Errores posibles**:
- `SPLITTING_TRANSACTION_FAILED` — Rollback completo; ni el padre se actualizó.

---

## TypeScript DTO (`consulta-legajos.ts`)

```typescript
export interface CrearConsultaLegajosRequest {
  cliente_id: number;
  direccion_entrega_id: number;
  codigos_legajo: string[];  // Cada uno 12 dígitos con prefijo 12000/120000/14XXXX
}

export interface ProcesarRemitoLegajosResponse {
  ok: boolean;
  data?: {
    remito_id: number;
    legajos_despachados: string[];
    splitting_realizado: boolean;
    requerimiento_hijo_id?: number;
    legajos_pendientes_busqueda: string[];
  };
  simulated: boolean;
  errors?: ApiError[];
}
```
