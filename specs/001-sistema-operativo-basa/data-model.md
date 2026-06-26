# Data Model: Sistema Operativo Integral BASA Argentina

**Date**: 2026-06-26
**Schema**: PostgreSQL — `dbo`

---

## Entidades y Campos

### `dbo.elemento`
Representa cualquier unidad física archivable: caja o legajo.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | BIGINT | PK, NOT NULL | Identificador único |
| `codigo` | VARCHAR(100) | NOT NULL, UNIQUE | Código de barras de 12 dígitos |
| `estado` | VARCHAR(50) | NOT NULL | Ver estados abajo |
| `posicion_id` | BIGINT | FK → `dbo.posicion.id`, NULLABLE | Posición física asignada |
| `elemento_tipo_id` | BIGINT | FK → `dbo.elemento_tipo.id` | Caja vs. Legajo |
| `cliente_id` | BIGINT | FK → `dbo.cliente.id`, NOT NULL | Propietario del archivo |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de ingreso al sistema |

**Estados válidos de `elemento`**:
- `en guarda` — Almacenado en planta, disponible para consulta.
- `en consulta` — Retirado temporalmente, en poder del cliente.
- `en transito` — En traslado (entre planta y cliente o viceversa).
- `en cliente` — Entregado; pendiente devolución o retiro definitivo.
- `BAJA` — Soft-delete lógico. No disponible para operaciones.

**Transiciones de estado**:
```
en guarda → en transito (picking aprobado)
en transito → en cliente (entrega confirmada)
en cliente → en transito (retiro iniciado)
en transito → en guarda (ingreso a planta confirmado)
cualquier_estado → BAJA (soft-delete, solo supervisores)
```

---

### `dbo.posicion`
Espacio físico en estantería. Relación 1-a-1 exclusiva con `dbo.elemento`.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | BIGINT | PK, NOT NULL | Identificador único |
| `estado` | VARCHAR(50) | NOT NULL, DEFAULT 'DISPONIBLE' | DISPONIBLE / OCUPADO |
| `estanteria` | NUMERIC(18,0) | NOT NULL | Número de estantería |
| `codigo_modulo` | VARCHAR(12) | NOT NULL | Código del módulo/bloque |
| `modulo_id` | BIGINT | FK → `dbo.modulos.id` | Referencia al módulo físico |

**Regla de exclusión**: Una posición con `estado = 'OCUPADO'` no puede recibir otro elemento. `node_validator` verifica esto antes de cualquier asignación.

---

### `dbo.modulos`
Estructura de coordenadas físicas del galpón.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | BIGINT | PK, NOT NULL | Identificador único |
| `codigoBarra` | VARCHAR(14) | NOT NULL, UNIQUE | Código de barras de la etiqueta física del módulo |
| `estante_id` | NUMERIC | FK → `dbo.estanterias.id` | Estantería contenedora |

---

### `dbo.requerimiento`
Pedido operativo del cliente. Entidad central del sistema.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | BIGINT | PK, NOT NULL | Identificador único |
| `requerimiento_tipo_id` | BIGINT | FK → `dbo.requerimiento_tipo.id`, NOT NULL | Tipo de operación (ver abajo) |
| `estado` | VARCHAR(50) | NOT NULL | Ver estados abajo |
| `cliente_id` | BIGINT | FK → `dbo.cliente.id`, NOT NULL | Cliente solicitante |
| `direccion_entrega_id` | BIGINT | FK → `dbo.direccion.id`, NULLABLE | Solo para consultas con entrega |
| `cantidad` | NUMERIC | NULLABLE | Cantidad de elementos del pedido |
| `fletes` | INT | NULLABLE, DEFAULT 0 | Fletes calculados por `node_commercial_logic` |
| `horas_archivista` | DECIMAL(18,2) | NULLABLE | Horas empleadas en búsqueda (UC5) |
| `observaciones` | VARCHAR(8000) | NULLABLE | Obligatorio en UC5 |
| `parent_requerimiento_id` | BIGINT | FK → `dbo.requerimiento.id`, NULLABLE | Requerimiento padre (splitting) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de creación |

**Tipos de requerimiento (`requerimiento_tipo_id`)**:

| ID | Nombre |
|----|--------|
| 2 | Consulta Normal de Legajo |
| 4 | Consulta Normal de Caja |
| 8 | Consulta Digital |
| 16 | Búsqueda / Trámite Administrativo |
| (retiro) | Retiro por Cantidad / Referencia |

**Estados válidos de `requerimiento`**:
- `PENDIENTE` — Creado, sin asignar.
- `INICIADO` — Operario asignado, picking en curso.
- `EN RUTA` — Asociado a Hoja de Ruta, en traslado.
- `ENTREGADO` — Entregado al cliente, remito pendiente de digitalización.
- `FINALIZADO` — Ciclo completo cerrado.
- `PENDIENTE_BUSQUEDA` — Estado especial para requerimientos hijo de splitting (UC3).

---

### `dbo.referencia`
Metadatos indexados de legajos para búsqueda. Vincula el legajo a su caja contenedora.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | BIGINT | PK, NOT NULL | Identificador único |
| `elemento_contenedor_id` | BIGINT | FK → `dbo.elemento.id`, NOT NULL | Caja que contiene el legajo |
| `texto1` | VARCHAR(500) | NULLABLE | Campo de búsqueda libre (apellido, nombre, etc.) |
| `texto2` | VARCHAR(500) | NULLABLE | Campo de búsqueda libre adicional |
| `numero1` | NUMERIC | NULLABLE | Clave numérica de indexación (DNI, cuenta, etc.) |

---

### `dbo.movimiento`
Registro de auditoría **inmutable**. Nunca se modifica ni elimina.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | BIGINT | PK, NOT NULL | Identificador único |
| `elemento_id` | BIGINT | FK → `dbo.elemento.id`, NULLABLE | Elemento afectado |
| `requerimiento_id` | BIGINT | FK → `dbo.requerimiento.id`, NULLABLE | Requerimiento vinculado |
| `tipo_movimiento` | VARCHAR(100) | NOT NULL | Ver tipos abajo |
| `estado_anterior` | VARCHAR(50) | NULLABLE | Estado previo al movimiento |
| `estado_nuevo` | VARCHAR(50) | NULLABLE | Estado resultante |
| `operario_id` | BIGINT | NULLABLE | Quién realizó la acción |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp del movimiento |
| `metadata` | JSONB | NULLABLE | Datos adicionales contextuales |

**Tipos de movimiento usados en los 5 UC**:
- `UBICACION_FISICA` — UC1: asignación de caja a posición.
- `PICKING_INICIADO` — UC2/UC3: inicio de extracción.
- `EN_TRANSITO` — UC2/UC3: caja/legajo en camino al cliente.
- `ENTREGADO_CLIENTE` — UC2/UC3: confirmación de entrega.
- `FINALIZADO` — UC2/UC3: remito digitalizado y ciclo cerrado.
- `INGRESO_PLANTA` — UC4: entrada de unidades desde cliente.
- `INVESTIGACION_EXITOSA` — UC5: documento encontrado y requerimiento transformado.

---

### `dbo.hoja_ruta`
Agrupación de requerimientos para un viaje de transporte.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | BIGINT | PK, NOT NULL | Identificador único |
| `fecha` | DATE | NOT NULL | Fecha del viaje |
| `estado` | VARCHAR(50) | NOT NULL | PENDIENTE / EN RUTA / FINALIZADA |
| `transportista_id` | BIGINT | FK → `dbo.transportista.id` | Conductor asignado |

---

### `dbo.lectura` / `dbo.lectura_detalle`
Registros de escaneos realizados por colectores láser externos (archivos planos de retiros).

**`dbo.lectura`**:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGINT | PK |
| `remito` | VARCHAR(100) | Remito asociado (nomenclatura `0002-000[N]-[R]` o `0001-[fecha]-[prov]`) |
| `requerimiento_id` | BIGINT | FK → `dbo.requerimiento.id` |
| `tipo` | VARCHAR(20) | CLIENTE o PLANTA |
| `created_at` | TIMESTAMP | Timestamp de procesamiento |

**`dbo.lectura_detalle`**:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGINT | PK |
| `lectura_id` | BIGINT | FK → `dbo.lectura.id` |
| `codigo_barra` | VARCHAR(100) | Código escaneado |
| `resultado` | VARCHAR(20) | ENCONTRADO / NO_ENCONTRADO |

---

## Relaciones Clave

```
dbo.cliente ──────────────────────┐
                                  │
dbo.posicion ←── dbo.elemento ────┤
                    │             │
                    ↓             │
              dbo.referencia      │
                                  │
dbo.requerimiento ────────────────┘
      │    │
      │    └── dbo.requerimiento (hijo, self-ref, UC3 splitting)
      │
      ↓
dbo.hoja_ruta
      │
      ↓
dbo.movimiento (audit log inmutable)

dbo.lectura ──→ dbo.lectura_detalle (UC4 retiros)
```

---

## Reglas de Integridad

1. **No DELETE físico**: Toda baja usa campo `estado = 'BAJA'` o equivalente.
2. **BigInt obligatorio**: Todos los campos `id`, `*_id` son `BIGINT`.
3. **Transacción atómica**: Toda operación que toque `dbo.movimiento` + otra tabla va en `engine.begin()`.
4. **Posición 1-a-1**: `dbo.elemento.posicion_id` tiene constraint UNIQUE (una posición, un elemento).
5. **Requerimiento hijo**: `parent_requerimiento_id` solo se popula en requerimientos de splitting (UC3).
