# BASA Argentina — Sesión de Descubrimiento Técnico
## Conectar el Sistema Operativo a la Base de Datos Existente

**Fecha:** 2026-06-26  
**Contexto:** BASA tiene una base de datos operativa con millones de registros y un ABM ya conectado. Antes de escribir una sola línea más de código, necesitamos entender qué tienen.

---

## Objetivo de la sesión

Salir con todo lo necesario para reemplazar la simulación actual por conexiones reales a la base de datos de BASA — sin romper lo que ya funciona.

---

## 1. Acceso a la base de datos

### Preguntas

- ¿Motor de base de datos? (SQL Server, Oracle, PostgreSQL, MySQL, otro)
- ¿Versión exacta?
- ¿Hay un ambiente de **desarrollo/testing** al que podamos conectarnos sin riesgo?
- ¿O solo hay producción? (en ese caso, necesitamos un dump de schema + datos de prueba)
- ¿La conexión es directa o requiere VPN?
- Si requiere VPN: ¿qué cliente VPN usan? ¿Proveen credenciales?

### Lo que necesitamos para conectarnos

```
Host:     _________________________
Puerto:   _________________________
Base:     _________________________
Usuario:  _________________________ (solo lectura primero)
Password: _________________________
Schema:   _________________________ (ej: dbo, public, BASA_PROD)
VPN:      Sí / No
```

---

## 2. Schema existente

### Lo que necesitamos

La forma más rápida es que nos den:

```sql
-- En SQL Server:
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION

-- En Oracle:
SELECT OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE OWNER NOT IN ('SYS','SYSTEM')
ORDER BY OWNER, TABLE_NAME, COLUMN_ID

-- En PostgreSQL:
\d+ (en psql) o SELECT * FROM information_schema.columns
```

**Alternativa:** exportar el ERD desde SQL Server Management Studio / DBeaver / cualquier herramienta que usen. Un PDF o imagen del diagrama ya sirve para arrancar.

### Preguntas sobre el schema

- ¿Cuántas tablas tiene la base aproximadamente?
- ¿Hay un schema o namespace específico para los datos operativos? (ej: `dbo`, `operaciones`, etc.)
- ¿Hay stored procedures que el ABM llama en vez de queries directas?
- ¿Hay vistas que abstraen lógica de negocio?
- ¿Hay triggers en las tablas principales?

---

## 3. El ABM existente

El ABM ya está conectado a la base. Necesitamos entender exactamente cómo.

### Preguntas

- ¿En qué tecnología está construido el ABM? (VB.NET, C#, Delphi, web, otro)
- ¿Se puede ver el código fuente? Especialmente las queries o el ORM que usa.
- ¿El ABM escribe directo a tablas o llama stored procedures?
- ¿El ABM tiene un archivo de configuración con el connection string? (para ver la estructura de conexión)

### Lo que buscamos entender del ABM

- ¿Cómo se llama la tabla de cajas? ¿y la de clientes? ¿y las posiciones?
- ¿Qué campos usa para el código de caja/legajo? ¿Es un VARCHAR de 12? ¿Tiene prefijos?
- ¿Cómo distingue una caja de un legajo? (¿campo tipo? ¿tabla separada?)
- ¿Cómo registra la ubicación de una caja en el depósito?
- ¿Cómo está modelado el "estado" de una caja? (¿campo texto? ¿tabla de estados? ¿número?)

---

## 4. Entidades que más nos importan

Para cada UC operativo, necesitamos saber cómo está modelado en su base:

### UC1 — Ubicación de cajas en planta
- Tabla donde se guarda la posición de una caja
- ¿La posición es un código? ¿o una FK a otra tabla?
- ¿Se registra el historial de posiciones o solo la actual?

### UC2 — Consulta de cajas (pedidos)
- Tabla de pedidos/requerimientos de cliente
- Estados posibles de un pedido
- ¿Cómo se registra el operario asignado?
- ¿Existe concepto de "remito" en la base? ¿En qué tabla?

### UC3 — Consulta de legajos
- ¿Los legajos están en la misma tabla que las cajas o separados?
- ¿Cómo se modela que un legajo no fue encontrado (splitting)?
- ¿Existe el concepto de "pedido hijo" en la base actual?

### UC4 — Retiros
- Tabla donde se registra la entrada/retiro físico de cajas
- ¿Existe tabla de "lecturas" o verificación de cantidades?
- ¿Cómo se calcula y registra el flete?
- ¿El email al cliente ya se envía desde algún módulo del sistema?

### UC5 — Búsqueda / Investigación
- ¿Existe en la base el concepto de "trámite administrativo"?
- ¿Dónde se registran las horas del archivista?
- ¿Cómo cambia el tipo de un pedido cuando se transforma?

### UC6 — Consulta IA para jefes
- Tablas de reportes o vistas que los jefes ya consultan
- ¿Tienen algún sistema de reportes actual? (Crystal Reports, SSRS, Excel, otro)
- ¿Qué preguntas hacen los jefes normalmente? (para entrenar al agente)

---

## 5. Volumen y performance

- ¿Cuántos registros tiene la tabla principal de cajas/elementos? (menciona millones)
- ¿Cuántos clientes activos hay?
- ¿Cuántos pedidos nuevos se generan por día aproximadamente?
- ¿Hay índices en los campos de búsqueda (código de caja, código de cliente)?
- ¿La base tiene réplica de lectura? (útil para el agente IA — no tocar producción)

---

## 6. Restricciones importantes

### Preguntas de seguridad y compliance

- ¿Hay datos sensibles (DNI, CUIL, datos médicos, datos judiciales)?
- ¿La base está en la red interna de BASA o en la nube?
- ¿Quién es el DBA o responsable de la base?
- ¿Hay política de backups? ¿Con qué frecuencia?
- ¿Se puede hacer SELECT libre o requiere aprobación por tabla?

### Restricciones de escritura

Para los UC operativos, necesitamos escribir. ¿Es posible crear:
- Un usuario de aplicación con permisos de SELECT + INSERT + UPDATE (sin DELETE)
- Un schema separado para las tablas nuevas que necesitemos agregar
- Acceso de solo lectura para el agente de IA (UC6)

---

## 7. Proceso sugerido para la integración

Una vez que tengamos el schema, seguimos este orden:

```
Semana 1: Acceso + Lectura
  ├── Obtener conexión de solo lectura al ambiente de dev
  ├── Explorar schema completo con queries de introspección
  ├── Mapear las tablas existentes a nuestro modelo de datos
  └── Identificar gaps (qué tablas faltan, qué campos faltan)

Semana 2: Adaptar el backend
  ├── Cambiar los modelos SQLAlchemy para apuntar a las tablas reales
  ├── Adaptar las queries de los 5 nodos del grafo LangGraph
  ├── Identificar stored procedures que debamos respetar
  └── Pruebas de lectura contra datos reales

Semana 3: Escritura controlada
  ├── Obtener usuario con permisos de escritura en dev
  ├── Ejecutar UC1 real (el más simple: ubicar una caja)
  ├── Validar que los datos quedan bien en la base
  └── Iterar por UC en orden de complejidad: UC2 → UC4 → UC3 → UC5

Semana 4: UC6 IA
  ├── Configurar ANTHROPIC_API_KEY
  ├── Darle al agente acceso de solo lectura a la base real
  ├── Probar preguntas con datos reales
  └── Ajustar el prompt del sistema según lo que encuentre
```

---

## 8. Script de diagnóstico rápido

Cuando tengamos acceso, ejecutar esto para entender la base en minutos:

```sql
-- 1. Ver todas las tablas con cantidad de filas (SQL Server)
SELECT 
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    p.rows AS cantidad_filas
FROM INFORMATION_SCHEMA.TABLES t
JOIN sys.tables st ON t.TABLE_NAME = st.name
JOIN sys.partitions p ON st.object_id = p.object_id AND p.index_id IN (0,1)
WHERE t.TABLE_TYPE = 'BASE TABLE'
ORDER BY p.rows DESC

-- 2. Ver columnas de las tablas más grandes
SELECT TOP 200
    c.TABLE_SCHEMA,
    c.TABLE_NAME,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS c
JOIN (
    -- solo las tablas con más de 1000 filas
    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
) t ON c.TABLE_NAME = t.TABLE_NAME
ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION

-- 3. Ver foreign keys (para entender relaciones)
SELECT 
    fk.name AS fk_name,
    tp.name AS tabla_padre,
    cp.name AS columna_padre,
    tr.name AS tabla_referenciada,
    cr.name AS columna_referenciada
FROM sys.foreign_keys fk
JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
ORDER BY tp.name

-- 4. Ver stored procedures existentes
SELECT ROUTINE_SCHEMA, ROUTINE_NAME, ROUTINE_TYPE
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_TYPE = 'PROCEDURE'
ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME

-- 5. Ver vistas
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.VIEWS
ORDER BY TABLE_SCHEMA, TABLE_NAME
```

> Si la base es PostgreSQL o MySQL, avisar y damos los equivalentes.

---

## 9. Qué hacemos con el schema cuando lo tengamos

1. **Mapeamos** cada tabla relevante a los 6 UCs
2. **Adaptamos** los modelos SQLAlchemy en `app/models/` para usar los nombres reales de tablas y columnas
3. **Actualizamos** el `.env` con la cadena de conexión real
4. **Descartamos** el schema SQL que propusimos (sección 2 del doc anterior) — usamos el de ellos
5. **Identificamos** qué tablas nuevas necesitamos agregar (si alguna) y lo coordinamos con el DBA de BASA

---

## Próximos pasos inmediatos

- [ ] **BASA:** Organizar reunión técnica con el DBA o quien administra la base
- [ ] **BASA:** Preparar acceso de solo lectura a ambiente dev antes de la reunión
- [ ] **BASA:** Tener disponible el código del ABM para revisar en la reunión
- [ ] **Nosotros:** Llevar este documento a la reunión como guía
- [ ] **Nosotros:** Conectar DBeaver / TablePlus en vivo durante la reunión para explorar el schema juntos
