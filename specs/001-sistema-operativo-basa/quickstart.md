# Quickstart: Validación End-to-End BASA Sistema Operativo

**Date**: 2026-06-26
**Prerequisite**: Docker Engine 24+, Docker Compose v2, archivo `.env` configurado.

---

## 1. Setup del entorno

```bash
# Clonar / entrar al repo
cd /home/drexgen/Documents/BASA/SOFTWARE

# Copiar variables de entorno
cp .env.example .env
# Editar .env con credenciales reales de DB, Redis, API key de Claude, SMTP

# Levantar el stack completo
docker compose up --build
```

**Servicios esperados**:
- `http://localhost:5173` — Frontend React (Vite dev server)
- `http://localhost:8000` — Backend FastAPI
- `http://localhost:8000/docs` — OpenAPI Swagger UI
- `localhost:5432` — PostgreSQL (puerto interno)
- `localhost:6379` — Redis (puerto interno)

**Healthcheck**: El backend no arranca hasta que Postgres y Redis respondan al healthcheck de Docker Compose.

---

## 2. Variables de entorno requeridas (`.env`)

```env
# Base de datos
DATABASE_URL=postgresql://basa_user:basa_pass@postgres:5432/basa_db

# Redis
REDIS_URL=redis://redis:6379/0

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# NotebookLM MCP
NOTEBOOKLM_MCP_URL=http://host.docker.internal:18789/tools/notebook_query
NOTEBOOKLM_BASA_ID=52b20bd8-f9c0-4409-b17f-95e0df393d67

# Email
SMTP_HOST=smtp.basa.com.ar
SMTP_PORT=587
SMTP_USER=sistema@basa.com.ar
SMTP_PASS=...

# Auth (consumir del sistema existente)
JWT_SECRET=...
```

---

## 3. Validación UC1 — Ubicación de Caja

**Escenario**: Asignar caja `110001234567` a posición con código de módulo `12345678901234`.

```bash
# Verificar estado inicial de la posición
curl http://localhost:8000/api/v1/ubicacion/posicion/12345678901234

# Asignar
curl -X POST http://localhost:8000/api/v1/ubicacion/asignar \
  -H "Content-Type: application/json" \
  -d '{"codigo_caja": "110001234567", "codigo_posicion": "12345678901234", "operario_id": 1}'
```

**Resultado esperado**:
- `"estado_posicion": "OCUPADO"` en la respuesta.
- Fila en `dbo.movimiento` con `tipo_movimiento = 'UBICACION_FISICA'`.
- Posición bloqueada: el mismo request devuelve `POSICION_OCUPADA`.

**Validación UI**: Abrir `http://localhost:5173/plant-locations`, escanear los códigos y verificar confirmación verde.

---

## 4. Validación UC2 — Consulta de Caja (modo simulado)

**Escenario**: Crear pedido con backend desconectado para verificar placeholder logic.

1. Detener el backend: `docker compose stop backend`.
2. Abrir `http://localhost:5173/web-box-order`.
3. Ingresar código de 7 dígitos `1234567` → verificar que el campo muestra `110001234567`.
4. Agregar al carrito y confirmar pedido.

**Resultado esperado**: Alerta amarilla *"Simulado: Pedido creado. Pendiente de grabación en dbo.requerimiento."*

5. Reiniciar backend: `docker compose start backend`.
6. Repetir el flujo → resultado real con `requerimiento_id` numérico.

---

## 5. Validación UC3 — Splitting de Legajos

**Escenario**: Pedido de 3 legajos, solo 1 encontrado en planta.

```bash
# Crear pedido con 3 legajos
curl -X POST http://localhost:8000/api/v1/consulta-legajos/crear \
  -d '{"cliente_id": 1, "direccion_entrega_id": 1, "codigos_legajo": ["120001111111","120002222222","120003333333"]}'

# Escanear solo el primero
curl -X POST http://localhost:8000/api/v1/consulta-legajos/picking/escanear \
  -d '{"requerimiento_id": <ID>, "codigo_legajo": "120001111111", "operario_id": 1}'

# Procesar remito (splitting automático)
curl -X POST http://localhost:8000/api/v1/consulta-legajos/remito/procesar \
  -d '{"requerimiento_id": <ID>, "operario_id": 1}'
```

**Resultado esperado**:
- `"splitting_realizado": true`
- `"legajos_despachados": ["120001111111"]`
- `"legajos_pendientes_busqueda": ["120002222222", "120003333333"]`
- Nuevo requerimiento hijo en DB con `requerimiento_tipo_id = 16` y `estado = 'PENDIENTE_BUSQUEDA'`.

---

## 6. Validación UC4 — Conciliación de Retiro

**Escenario**: Retiro declarado de 15 cajas, solo 11 ingresaron a planta.

```bash
# Crear retiro
curl -X POST http://localhost:8000/api/v1/retiros/crear \
  -d '{"cliente_id": 1, "tipo": "CANTIDAD", "cantidad_declarada": 15, "direccion_origen_id": 1}'

# Procesar lectura de planta (11 unidades)
curl -X POST http://localhost:8000/api/v1/retiros/lectura/procesar \
  -d '{"requerimiento_id": <ID>, "tipo_lectura": "PLANTA", "remito_nombre": "0001-26062026-MZA", "codigos_leidos": [...]}'

# Conciliar con confirmación de discrepancia
curl -X POST http://localhost:8000/api/v1/retiros/conciliar \
  -d '{"requerimiento_id": <ID>, "operario_id": 1, "confirmar_discrepancia": true}'
```

**Resultado esperado**:
- `"cantidad_final": 11`
- `"fletes_calculados": 1` (`ceil(11/20) = 1`)
- `"email_enviado": true`

---

## 7. Validación UC5 — Transformación de Requerimiento

```bash
# Crear trámite de búsqueda
curl -X POST http://localhost:8000/api/v1/busqueda/crear \
  -d '{"cliente_id": 1, "observaciones": "Buscar contrato García DNI 28123456 año 2019"}'

# Registrar horas
curl -X POST http://localhost:8000/api/v1/busqueda/registrar-horas \
  -d '{"requerimiento_id": <ID>, "horas_archivista": 2.5, "operario_id": 1}'

# Vincular elemento encontrado
curl -X POST http://localhost:8000/api/v1/busqueda/vincular-elemento \
  -d '{"requerimiento_id": <ID>, "codigo_elemento_encontrado": "120005678901", "operario_id": 1}'

# Transformar a Consulta Física
curl -X POST http://localhost:8000/api/v1/busqueda/transformar \
  -d '{"requerimiento_id": <ID>, "tipo_destino": 2, "operario_id": 1}'
```

**Resultado esperado**:
- `"tipo_anterior": 16, "tipo_nuevo": 2`
- Movimiento `INVESTIGACION_EXITOSA` en `dbo.movimiento`.
- `"proximo_flujo": "consulta-legajos"` para continuar con el despacho.

---

## 8. Validación de Memoria del Agente

```bash
# Consultar al agente (thread 1)
curl -X POST http://localhost:8000/api/v1/agente/consultar \
  -d '{"thread_id": "operario_1_sesion_1", "user_id": "operario_1", "mensaje": "¿Cuáles son los prefijos de cajas de 7 dígitos?"}'

# Reiniciar backend y consultar con el mismo thread
docker compose restart backend
curl -X POST http://localhost:8000/api/v1/agente/consultar \
  -d '{"thread_id": "operario_1_sesion_1", "user_id": "operario_1", "mensaje": "¿Qué me preguntaste antes?"}'
```

**Resultado esperado**: El agente recuerda el contexto de la sesión anterior gracias a Redis short-term memory.
