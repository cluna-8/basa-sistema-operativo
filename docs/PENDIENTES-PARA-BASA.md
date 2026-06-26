# BASA Argentina — Sistema Operativo Integral
## Documentación de Pendientes y Requerimientos

**Versión:** 0.1.0  
**Fecha:** 2026-06-26  
**Estado del sistema:** Frontend + Backend corriendo en Docker. Simulación controlada activa.

> ⚠️ **Cambio de enfoque:** BASA ya tiene una base de datos operativa con millones de registros y un ABM conectado.
> El schema SQL de la sección 2 es **referencial**, no para ejecutar desde cero.
> Ver `DESCUBRIMIENTO-BASE-DE-DATOS.md` para el plan de integración real.

---

## Índice

1. [Estado actual](#1-estado-actual)
2. [Pendiente CRÍTICO — Base de datos](#2-pendiente-crítico--base-de-datos)
3. [Pendiente — ABM de entidades](#3-pendiente--abm-de-entidades)
4. [Pendiente — Pantalla IA (UC6)](#4-pendiente--pantalla-ia-uc6)
5. [Pendiente — Autenticación real](#5-pendiente--autenticación-real)
6. [Pendiente — Integraciones externas](#6-pendiente--integraciones-externas)
7. [Datos que BASA debe proveer](#7-datos-que-basa-debe-proveer)
8. [Checklist de entrega](#8-checklist-de-entrega)

---

## 1. Estado actual

### ✅ Implementado y corriendo

| Componente | Estado | Detalle |
|---|---|---|
| Docker Compose | ✅ Corriendo | 4 servicios: postgres, redis-stack, backend, frontend |
| Frontend React | ✅ Prod build | 7 pantallas operativas + dashboard principal |
| Backend FastAPI | ✅ Corriendo | 18 endpoints, middleware JWT, manejo de errores global |
| LangGraph pipeline | ✅ Compilado | 4 nodos: state_preparer → validator → commercial_logic → persistence |
| Redis dual-layer | ✅ Corriendo | RedisSaver (checkpoints) + RedisStore (memoria larga) |
| Auth dev | ✅ Funcional | Login con usuarios hardcodeados (ver credenciales abajo) |
| Simulación | ✅ Activa | Todas las calls devuelven `simulated: true` hasta que haya DB real |

### ⚠️ Funciona con simulación (no persiste datos)

Todas las pantallas operativas muestran alertas amarillas indicando modo simulación. Los datos se pierden al recargar. Esto es intencional hasta que la base de datos tenga el schema aplicado.

### Credenciales de desarrollo

```
admin    / admin123  → rol: jefe     (acceso total + UC6 IA)
jefe     / jefe2024  → rol: jefe
operario / basa2024  → rol: operario
```

### URLs

```
http://localhost:5173               Dashboard principal
http://localhost:5173/login         Login
http://localhost:5173/operaciones/ubicacion     UC1
http://localhost:5173/operaciones/consulta-caja UC2 (cliente)
http://localhost:5173/operaciones/picking       UC2 (operario)
http://localhost:5173/operaciones/legajos       UC3
http://localhost:5173/operaciones/retiros       UC4
http://localhost:5173/operaciones/busqueda      UC5
http://localhost:5173/operaciones/jefes         UC6 (IA)
http://localhost:8000/docs          API Swagger
```

---

## 2. Pendiente CRÍTICO — Base de datos

### Problema

El schema `dbo` de PostgreSQL **no tiene ninguna tabla creada**. El backend arranca pero cualquier operación real devuelve error de tabla inexistente.

### Qué hay que hacer

Crear y aplicar las migrations de Alembic (o script SQL equivalente) para las 8 entidades del modelo de datos.

### Script de creación recomendado

```sql
-- Ejecutar en la base: basa_db
-- Usuario: basa_user

CREATE SCHEMA IF NOT EXISTS dbo;

-- 1. Módulos (estanterías/posiciones físicas del archivo)
CREATE TABLE dbo.modulos (
    id              BIGSERIAL PRIMARY KEY,
    codigo          VARCHAR(14) NOT NULL UNIQUE,  -- 14 dígitos
    nombre          VARCHAR(100),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. Posición (ubicación individual dentro de un módulo)
CREATE TABLE dbo.posicion (
    id              BIGSERIAL PRIMARY KEY,
    codigo_modulo   VARCHAR(14) NOT NULL REFERENCES dbo.modulos(codigo),
    estado          VARCHAR(20) NOT NULL DEFAULT 'DISPONIBLE',  -- DISPONIBLE | OCUPADO
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_posicion_estado CHECK (estado IN ('DISPONIBLE', 'OCUPADO'))
);

-- 3. Elemento (caja o legajo físico)
CREATE TABLE dbo.elemento (
    id              BIGSERIAL PRIMARY KEY,
    codigo          VARCHAR(12) NOT NULL UNIQUE,  -- 12 dígitos con prefijo
    tipo            VARCHAR(10) NOT NULL,          -- CAJA | LEGAJO
    cliente_id      BIGINT NOT NULL,
    posicion_id     BIGINT UNIQUE REFERENCES dbo.posicion(id),  -- 1-a-1
    estado          VARCHAR(20) NOT NULL DEFAULT 'en guarda',
    metadata_       JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_elemento_tipo CHECK (tipo IN ('CAJA', 'LEGAJO')),
    CONSTRAINT ck_elemento_estado CHECK (estado IN (
        'en guarda', 'en consulta', 'en transito', 'en cliente', 'BAJA'
    ))
);

-- 4. Requerimiento (pedido operativo — todos los UCs generan uno)
CREATE TABLE dbo.requerimiento (
    id                      BIGSERIAL PRIMARY KEY,
    tipo                    SMALLINT NOT NULL,  -- 1=UC1, 2=UC2caja, 3=UC2leg, 5=UC4, 16=UC5
    estado                  VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    cliente_id              BIGINT NOT NULL,
    operario_id             BIGINT,
    supervisor_id           BIGINT,
    parent_requerimiento_id BIGINT REFERENCES dbo.requerimiento(id),  -- splitting UC3
    observaciones           TEXT,
    horas_archivista        NUMERIC(6,2),
    cantidad_declarada      INTEGER,
    fletes_estimados        INTEGER,
    metadata_               JSONB,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 5. Referencia (elementos asociados a un requerimiento)
CREATE TABLE dbo.referencia (
    id              BIGSERIAL PRIMARY KEY,
    requerimiento_id BIGINT NOT NULL REFERENCES dbo.requerimiento(id),
    elemento_id     BIGINT NOT NULL REFERENCES dbo.elemento(id),
    estado          VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 6. Movimiento (log de auditoría inmutable)
CREATE TABLE dbo.movimiento (
    id              BIGSERIAL PRIMARY KEY,
    requerimiento_id BIGINT REFERENCES dbo.requerimiento(id),
    elemento_id     BIGINT REFERENCES dbo.elemento(id),
    tipo_evento     VARCHAR(50) NOT NULL,
    usuario_id      BIGINT,
    metadata_       JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 7. Hoja de ruta (agrupador de remitos para transporte)
CREATE TABLE dbo.hoja_ruta (
    id              BIGSERIAL PRIMARY KEY,
    fecha           DATE NOT NULL DEFAULT CURRENT_DATE,
    estado          VARCHAR(20) NOT NULL DEFAULT 'ABIERTA',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 8. Lectura (verificación física en planta — UC4)
CREATE TABLE dbo.lectura (
    id              BIGSERIAL PRIMARY KEY,
    requerimiento_id BIGINT NOT NULL REFERENCES dbo.requerimiento(id),
    tipo_lectura    VARCHAR(20) NOT NULL,  -- PLANTA | CLIENTE
    remito_nombre   VARCHAR(100),
    cantidad_declarada INTEGER,
    cantidad_leida  INTEGER,
    diferencia      INTEGER,
    operario_id     BIGINT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE dbo.lectura_detalle (
    id              BIGSERIAL PRIMARY KEY,
    lectura_id      BIGINT NOT NULL REFERENCES dbo.lectura(id),
    elemento_id     BIGINT REFERENCES dbo.elemento(id),
    codigo_leido    VARCHAR(12) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Índices de performance
CREATE INDEX idx_elemento_codigo      ON dbo.elemento(codigo);
CREATE INDEX idx_elemento_cliente     ON dbo.elemento(cliente_id);
CREATE INDEX idx_requerimiento_estado ON dbo.requerimiento(estado);
CREATE INDEX idx_requerimiento_tipo   ON dbo.requerimiento(tipo);
CREATE INDEX idx_referencia_req       ON dbo.referencia(requerimiento_id);
CREATE INDEX idx_movimiento_req       ON dbo.movimiento(requerimiento_id);
```

### Cómo aplicarlo en Docker

```bash
# Opción A: desde el host
docker exec -i software-postgres-1 psql -U basa_user -d basa_db < schema.sql

# Opción B: copiar el archivo y ejecutar
docker cp schema.sql software-postgres-1:/tmp/schema.sql
docker exec software-postgres-1 psql -U basa_user -d basa_db -f /tmp/schema.sql
```

---

## 3. Pendiente — ABM de entidades

### Por qué es necesario

Los operarios necesitan un panel para dar de alta clientes, módulos y posiciones antes de poder operar. Sin estos datos maestros, ningún UC puede funcionar.

### Pantallas requeridas

#### 3.1 ABM Clientes

**Ruta sugerida:** `/admin/clientes`

Campos requeridos:
- `nombre_razon_social` (texto, obligatorio)
- `cuit` (11 dígitos, validación de dígito verificador)
- `direccion_fiscal` (texto)
- `email_contacto` (email, para notificaciones automáticas)
- `telefono` (texto)
- `codigo_cliente` (prefijo 2 dígitos que determina prefijos de caja/legajo)
- `activo` (booleano, soft-delete)

Operaciones: listar, crear, editar, desactivar (NO borrar físicamente).

Tabla destino: `dbo.cliente` — **aún no existe, hay que crear la tabla también.**

```sql
CREATE TABLE dbo.cliente (
    id              BIGSERIAL PRIMARY KEY,
    nombre          VARCHAR(200) NOT NULL,
    cuit            VARCHAR(11) UNIQUE,
    codigo_cliente  CHAR(2) NOT NULL UNIQUE,  -- determina prefijos de elemento
    email_contacto  VARCHAR(200),
    telefono        VARCHAR(50),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### 3.2 ABM Módulos y Posiciones

**Ruta sugerida:** `/admin/modulos`

Permite registrar las estanterías físicas del depósito.

Campos:
- `codigo` (14 dígitos, generado por el sistema: zona + pasillo + estante + posición)
- `descripcion` (texto libre)
- `capacidad_maxima` (entero)
- `activo` (booleano)

Al crear un módulo, generar automáticamente N posiciones hijas (1 por celda).

#### 3.3 ABM Usuarios / Operarios

**Ruta sugerida:** `/admin/usuarios`

Reemplaza las credenciales hardcodeadas actuales.

Campos:
- `username` (único)
- `nombre_completo`
- `email`
- `rol` (`operario` | `jefe` | `admin`)
- `activo` (booleano)
- `password_hash` (bcrypt)

Tabla destino: `dbo.usuario` — **aún no existe.**

```sql
CREATE TABLE dbo.usuario (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    nombre_completo VARCHAR(200),
    email           VARCHAR(200),
    password_hash   VARCHAR(200) NOT NULL,
    rol             VARCHAR(20) NOT NULL DEFAULT 'operario',
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_usuario_rol CHECK (rol IN ('operario', 'jefe', 'admin'))
);
```

#### 3.4 ABM Elementos (carga masiva)

**Ruta sugerida:** `/admin/elementos`

Para el ingreso inicial de cajas y legajos ya existentes en el depósito.

- Carga individual: formulario con código + cliente + tipo
- Carga masiva: importación CSV con validación de prefijos
- Vista de estado: filtros por cliente, estado, posición

---

## 4. Pendiente — Pantalla IA (UC6)

### Estado actual

La pantalla `/operaciones/jefes` existe y funciona en modo simulación. El agente devuelve respuestas ficticias cuando el backend no puede conectarse a Claude.

### Para activarla completamente

#### 4.1 Configurar API Key de Anthropic

En el archivo `.env` del servidor:

```env
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXX   # ← clave real de Anthropic
```

El modelo utilizado es `claude-sonnet-4-6` (configurable en `app/graphs/query_graph.py`).

**Costo estimado por consulta:** ~0.01–0.05 USD dependiendo de la longitud de la respuesta.

#### 4.2 Configurar NotebookLM MCP (opcional pero recomendado)

El agente puede consultar un NotebookLM con el manual de BASA para responder preguntas sobre procedimientos.

Variables requeridas:
```env
NOTEBOOKLM_MCP_URL=http://host.docker.internal:18789/tools/notebook_query
NOTEBOOKLM_BASA_ID=<ID del notebook de BASA en Google>
```

Si no se configura, el agente solo usa la base de datos (PostgreSQL) para responder.

#### 4.3 Comportamiento esperado del agente

El agente de jefes:
- **Solo lee** — ninguna consulta puede modificar datos (bloqueado a nivel de código)
- Responde en español
- Puede responder preguntas como:
  - "¿Cuántos pedidos están pendientes hoy?"
  - "¿Dónde está la caja 110001234567?"
  - "¿Cuál fue el último movimiento del cliente X?"
  - "¿Cuántos fletes se generaron esta semana?"
- Rechaza explícitamente cualquier intento de escritura

#### 4.4 Historial de conversación

Cada sesión de jefe mantiene memoria en Redis (por `thread_id`). El historial persiste entre recargas siempre que el `thread_id` sea el mismo.

---

## 5. Pendiente — Autenticación real

### Problema

Las credenciales actuales están hardcodeadas en `app/main.py`. Cualquiera que vea el código tiene acceso.

### Qué hay que hacer

1. Crear la tabla `dbo.usuario` (ver sección 3.3)
2. Implementar endpoint `POST /api/auth/register` (solo admin puede crear usuarios)
3. Cambiar `POST /api/auth/login` para validar contra la base de datos
4. Implementar `POST /api/auth/refresh` para renovar tokens sin re-login
5. Agregar pantalla `/admin/usuarios` para gestión

### Endpoint de cambio de contraseña

```
POST /api/auth/cambiar-password
Body: { password_actual, password_nuevo }
Auth: Bearer token del usuario logueado
```

---

## 6. Pendiente — Integraciones externas

### 6.1 Email SMTP

El servicio de email está implementado en `app/services/email_service.py` pero necesita configuración real.

Variables en `.env`:
```env
SMTP_HOST=smtp.basa.com.ar   # servidor SMTP de BASA
SMTP_PORT=587
SMTP_USER=sistema@basa.com.ar
SMTP_PASS=<contraseña real>
```

Se usa en:
- UC4 (Retiros): notificación al cliente cuando ingresan sus cajas con el detalle de fletes
- Extensible a UC2 cuando el pedido esté listo para despacho

### 6.2 Aconcagua (sistema de despacho)

En UC2 y UC5 se menciona "enviar a Aconcagua". Actualmente se loguea el evento pero no hay integración.

**Preguntar a BASA:**
- ¿Aconcagua tiene API REST? ¿o es integración manual/por email?
- ¿Qué datos necesita recibir por pedido?
- ¿Hay sandbox para pruebas?

### 6.3 Sistema de impresión de remitos

El sistema genera el remito en base de datos pero no lo imprime ni genera PDF.

**Opciones a decidir con BASA:**
- PDF generado por el backend (librería `reportlab` o `weasyprint`)
- Impresión directa a impresora térmica/laser en planta
- Template HTML que el navegador imprime con `window.print()`

---

## 7. Datos que BASA debe proveer

Para el primer encendido en producción, BASA necesita proveer:

### 7.1 Catálogo de clientes

Listado de todos los clientes activos con:
- Nombre / Razón Social
- CUIT
- Código de cliente (2 dígitos — determina los prefijos de sus cajas)
- Email de contacto para notificaciones

### 7.2 Inventario inicial de elementos

Para cada caja y legajo en el depósito:
- Código completo (12 dígitos)
- Cliente al que pertenece
- Tipo (CAJA / LEGAJO)
- Posición actual en el depósito (si está ubicada)

Formato CSV preferido:
```
codigo,tipo,cliente_id,posicion_codigo
110001234567,CAJA,1,14030100000001
120001234567,LEGAJO,1,
```

### 7.3 Mapa del depósito

Para crear los módulos y posiciones en el sistema:
- Listado de todas las estanterías con su código de 14 dígitos
- Capacidad de cada posición
- Zonas o sectores (si aplica)

### 7.4 Reglas de negocio a confirmar

Las siguientes reglas están implementadas con los valores actuales pero BASA debe confirmarlas:

| Regla | Implementación actual | ¿Confirmar? |
|---|---|---|
| Cálculo de fletes | `ceil(cantidad / 20)` — 1 flete cada 20 cajas | ✅ / ❌ |
| Prefijo caja 7 dígitos | `11000` + código | ✅ / ❌ |
| Prefijo caja 6 dígitos | `110000` + código | ✅ / ❌ |
| Prefijo legajo 7 dígitos | `12000` + código | ✅ / ❌ |
| Prefijo legajo 6 dígitos | `120000` + código | ✅ / ❌ |
| SLA consulta caja | 48 horas | ✅ / ❌ |
| SLA consulta legajo | ¿Cuántas horas? | ❓ |
| Splitting legajos | Auto-crear req hijo tipo 16 | ✅ / ❌ |
| Autorización supervisor | Cajas con legajos individuales | ✅ / ❌ |

---

## 8. Checklist de entrega

### Para los programadores

- [ ] Aplicar schema SQL (sección 2) en PostgreSQL
- [ ] Crear tabla `dbo.cliente` y cargar datos iniciales
- [ ] Crear tabla `dbo.usuario` y migrar auth hardcodeado
- [ ] Implementar pantallas ABM (sección 3)
- [ ] Agregar `ANTHROPIC_API_KEY` real en `.env`
- [ ] Configurar SMTP real en `.env`
- [ ] Confirmar integración Aconcagua con BASA
- [ ] Definir formato de impresión de remitos
- [ ] Seed data inicial (módulos + posiciones)
- [ ] Tests de integración end-to-end con datos reales
- [ ] Configurar variables de producción (JWT_SECRET fuerte, etc.)
- [ ] Configurar HTTPS / dominio en producción

### Para BASA

- [ ] Proveer listado de clientes (formato CSV — sección 7.1)
- [ ] Proveer inventario inicial de elementos (sección 7.2)
- [ ] Proveer mapa del depósito (sección 7.3)
- [ ] Confirmar reglas de negocio (tabla sección 7.4)
- [ ] Confirmar si Aconcagua tiene API (sección 6.2)
- [ ] Proveer credenciales SMTP corporativo
- [ ] Proveer API Key de Anthropic (o aprobar costo mensual estimado)
- [ ] Definir usuarios iniciales del sistema con sus roles

---

## Contacto técnico

Repositorio: `/home/drexgen/Documents/BASA/SOFTWARE/`  
Especificación completa: `specs/001-sistema-operativo-basa/spec.md`  
Plan técnico: `specs/001-sistema-operativo-basa/plan.md`  
Contratos API: `specs/001-sistema-operativo-basa/contracts/`
