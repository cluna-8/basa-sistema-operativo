# API Contracts Overview: BASA Sistema Operativo

**Base URL**: `http://localhost:8000/api/v1` (Docker: servicio `backend`)
**Auth**: Bearer token (header `Authorization: Bearer <token>`)
**Format**: JSON, UTF-8
**Error envelope**:
```json
{
  "ok": false,
  "errors": [{"code": "VALIDATION_ERROR", "field": "codigo", "message": "..."}]
}
```
**Success envelope**:
```json
{
  "ok": true,
  "data": { ... },
  "simulated": false
}
```
> Cuando `simulated: true`, la operación fue interceptada por placeholder logic y no persistió en base de datos.

## Endpoints por caso de uso

| Caso de Uso | Archivo | Prefijo de ruta |
|-------------|---------|-----------------|
| UC1: Ubicación de cajas | [uc1-ubicacion.md](./uc1-ubicacion.md) | `/ubicacion` |
| UC2: Consulta caja | [uc2-consulta-caja.md](./uc2-consulta-caja.md) | `/consulta-caja` |
| UC3: Consulta legajos | [uc3-consulta-legajos.md](./uc3-consulta-legajos.md) | `/consulta-legajos` |
| UC4: Retiros | [uc4-retiros.md](./uc4-retiros.md) | `/retiros` |
| UC5: Búsqueda | [uc5-busqueda.md](./uc5-busqueda.md) | `/busqueda` |
| UC6: Consulta Jefes | [uc6-consulta-jefes.md](./uc6-consulta-jefes.md) | `/jefes` |

> **UC6 es un grafo independiente** (`query_graph.py`) con tools de solo lectura. No comparte código con el pipeline operativo de 4 nodos (`operational_graph.py`).

## TypeScript DTOs (ubicación en frontend)

Todos los tipos viven en `DASH-cli/dashboard/src/types/`:
- `ubicacion.ts` — UC1
- `consulta-caja.ts` — UC2
- `consulta-legajos.ts` — UC3
- `retiro.ts` — UC4
- `busqueda.ts` — UC5
