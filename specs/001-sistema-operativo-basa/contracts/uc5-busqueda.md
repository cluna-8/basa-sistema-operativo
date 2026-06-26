# Contrato API: UC5 — Trámite Administrativo de Búsqueda

## POST `/api/v1/busqueda/crear`

Abre un trámite de búsqueda. El campo `observaciones` es obligatorio.

**Request**:
```json
{
  "cliente_id": 10,
  "observaciones": "Buscar contrato de préstamo firmado en 2019, cliente apellido García, DNI 28.123.456. Posiblemente en cajas del cliente 1025.",
  "metadata_busqueda": {
    "apellido": "García",
    "dni": "28123456",
    "anio_aproximado": 2019
  }
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "requerimiento_id": 8001,
    "tipo": 16,
    "estado": "PENDIENTE"
  }
}
```

**Errores posibles**:
- `OBSERVACIONES_REQUERIDAS` — El campo `observaciones` está vacío.

---

## POST `/api/v1/busqueda/registrar-horas`

Registra las horas de archivista consumidas durante la investigación.

**Request**:
```json
{
  "requerimiento_id": 8001,
  "horas_archivista": 2.5,
  "operario_id": 42
}
```

**Response 200**:
```json
{ "ok": true, "data": { "horas_registradas": 2.5 } }
```

---

## POST `/api/v1/busqueda/vincular-elemento`

Vincula el documento encontrado al requerimiento de búsqueda.

**Request**:
```json
{
  "requerimiento_id": 8001,
  "codigo_elemento_encontrado": "120005678901",
  "operario_id": 42
}
```

---

## POST `/api/v1/busqueda/transformar`

Transforma dinámicamente el requerimiento de tipo 16 al tipo de despacho seleccionado. Operación atómica: actualiza tipo, registra horas y crea movimiento de auditoría en una sola transacción.

**Request**:
```json
{
  "requerimiento_id": 8001,
  "tipo_destino": 2,
  "operario_id": 42
}
```
> `tipo_destino`: `2` (Consulta Física de Legajo) | `8` (Consulta Digital)

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "requerimiento_id": 8001,
    "tipo_anterior": 16,
    "tipo_nuevo": 2,
    "movimiento_auditoria_id": 12345,
    "proximo_flujo": "consulta-legajos"
  }
}
```

**Errores posibles**:
- `HORAS_ARCHIVISTA_REQUERIDAS` — No se pueden registrar 0 horas al finalizar con éxito.
- `ELEMENTO_NO_VINCULADO` — No se vinculó ningún elemento antes de transformar.
- `TIPO_DESTINO_INVALIDO` — Solo se aceptan tipos 2 u 8.

---

## TypeScript DTO (`busqueda.ts`)

```typescript
export interface CrearBusquedaRequest {
  cliente_id: number;
  observaciones: string;  // Mínimo 10 caracteres
  metadata_busqueda?: Record<string, unknown>;
}

export type TipoDestino = 2 | 8;

export interface TransformarBusquedaRequest {
  requerimiento_id: number;
  tipo_destino: TipoDestino;
  operario_id: number;
}

export interface TransformarBusquedaResponse {
  ok: boolean;
  data?: {
    requerimiento_id: number;
    tipo_anterior: number;
    tipo_nuevo: number;
    movimiento_auditoria_id: number;
    proximo_flujo: string;
  };
  simulated: boolean;
  errors?: ApiError[];
}
```
