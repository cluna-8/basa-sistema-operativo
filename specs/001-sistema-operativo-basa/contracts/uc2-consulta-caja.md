# Contrato API: UC2 — Consulta Normal de Caja

## POST `/api/v1/consulta-caja/crear`

Crea un nuevo requerimiento de consulta de caja (desde portal web cliente).

**Request**:
```json
{
  "cliente_id": 10,
  "direccion_entrega_id": 3,
  "codigos_caja": ["110001234567", "110009876543"],
  "observaciones": "Urgente - auditoría interna"
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "requerimiento_id": 5001,
    "estado": "PENDIENTE",
    "elementos_validados": [
      { "codigo": "110001234567", "estado": "en guarda", "valido": true },
      { "codigo": "110009876543", "estado": "en consulta", "valido": false, "motivo": "No disponible" }
    ]
  },
  "simulated": false
}
```

**Errores posibles**:
- `CODIGO_FORMATO_INVALIDO` — El código no tiene exactamente 12 dígitos.
- `ELEMENTO_NO_DISPONIBLE` — La caja no está en estado `en guarda`.

---

## POST `/api/v1/consulta-caja/picking/iniciar`

Asigna operario y cambia estado a INICIADO.

**Request**:
```json
{ "requerimiento_id": 5001, "operario_id": 42 }
```

---

## POST `/api/v1/consulta-caja/picking/confirmar`

Confirma el escaneo físico de las cajas y verifica elementos internos.

**Request**:
```json
{
  "requerimiento_id": 5001,
  "codigos_escaneados": ["110001234567"],
  "supervisor_id": null
}
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "requiere_autorizacion_supervisor": true,
    "elementos_internos_pendientes": [{"elemento_id": 2020, "codigo": "LEGAJO-XYZ"}],
    "puede_generar_remito": false
  }
}
```

---

## POST `/api/v1/consulta-caja/remito/generar`

Genera el remito de salida. Solo disponible si `puede_generar_remito = true`.

**Request**:
```json
{ "requerimiento_id": 5001, "observaciones_remito": "Sin novedades" }
```

**Response 200**:
```json
{
  "ok": true,
  "data": {
    "remito_id": 8888,
    "remito_numero": "0001-00008888",
    "pdf_url": "/remitos/8888.pdf"
  }
}
```

---

## POST `/api/v1/consulta-caja/digitalizar`

Cierra el ciclo al regresar el remito firmado.

**Request**:
```json
{ "remito_id": 8888, "operario_id": 42 }
```

**Response 200**: `{ "ok": true, "data": { "requerimiento_estado": "FINALIZADO" } }`

---

## TypeScript DTO (`consulta-caja.ts`)

```typescript
export interface CrearConsultaCajaRequest {
  cliente_id: number;
  direccion_entrega_id: number;
  codigos_caja: string[];   // Cada uno debe tener exactamente 12 dígitos
  observaciones?: string;
}

export interface ElementoValidado {
  codigo: string;
  estado: string;
  valido: boolean;
  motivo?: string;
}

export interface CrearConsultaCajaResponse {
  ok: boolean;
  data?: {
    requerimiento_id: number;
    estado: string;
    elementos_validados: ElementoValidado[];
  };
  simulated: boolean;
  errors?: ApiError[];
}
```
