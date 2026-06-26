# BASA Argentina — Cuestionario de Descubrimiento Técnico
## Máximo Nivel de Detalle para Integración con Base de Datos Existente

**Fecha:** 2026-06-26  
**Propósito:** Antes de escribir una sola línea de integración, necesitamos respuesta a CADA UNA de estas preguntas. Una respuesta faltante puede costarnos semanas de trabajo en la dirección equivocada.

**Formato de respuesta:** Completar este documento y devolvérnoslo, o enviarlo por reunión técnica con el DBA y el desarrollador del ABM presente.

---

## BLOQUE 1 — Infraestructura de base de datos

### 1.1 Motor y versión

- ¿Qué motor de base de datos usan? (marcar uno)
  - [ ] Microsoft SQL Server → ¿Versión exacta? (ej: SQL Server 2019, 2022)
  - [ ] Oracle Database → ¿Versión?
  - [ ] PostgreSQL → ¿Versión?
  - [ ] MySQL / MariaDB → ¿Versión?
  - [ ] Otro: _______________

- ¿El motor corre en Windows o Linux?
- ¿Es una instancia dedicada o compartida con otros sistemas?
- ¿Está en la red interna de BASA, en un datacenter propio, o en la nube? (AWS, Azure, GCP, otro)

### 1.2 Ambientes disponibles

- ¿Tienen ambiente de **desarrollo/testing** separado de producción?
  - [ ] Sí → ¿Con datos reales o datos de prueba?
  - [ ] No → ¿Pueden crear uno? ¿O trabajamos sobre producción con acceso de solo lectura?

- ¿El ambiente de dev tiene los mismos datos que producción? (o es una copia parcial)

- ¿Con qué frecuencia se sincroniza dev con producción?

### 1.3 Conectividad

- ¿La base de datos es accesible desde fuera de la red de BASA?
  - [ ] Sí, directo (IP pública o dominio)
  - [ ] No, requiere VPN
  - [ ] No, requiere estar en la red interna de BASA

- Si requiere VPN:
  - ¿Qué cliente VPN usan? (Cisco AnyConnect, OpenVPN, WireGuard, otro)
  - ¿Tienen licencias/cuentas disponibles para darnos?
  - ¿Hay que generar certificados o es usuario/contraseña?

- Puerto de la base de datos: ______ (default: SQL Server=1433, PostgreSQL=5432, Oracle=1521)

- ¿Hay firewall que limite qué IPs pueden conectarse? Si es así, darnos una IP fija o rango para whitelist.

### 1.4 Credenciales de acceso

Necesitamos **dos usuarios** separados:

**Usuario de solo lectura** (para el agente IA y para la fase de exploración):
```
Host:     _______________________________
Puerto:   _______________________________
Base:     _______________________________
Usuario:  _______________________________
Password: _______________________________
Schema:   _______________________________
```

**Usuario de aplicación** (para los UC operativos — escribe datos):
```
Host:     _______________________________
Puerto:   _______________________________
Base:     _______________________________
Usuario:  _______________________________
Password: _______________________________
Permisos: SELECT, INSERT, UPDATE (sin DELETE ni DROP)
Schema:   _______________________________
```

---

## BLOQUE 2 — Schema y modelo de datos

### 2.1 Panorama general

- ¿Cuántas tablas tiene la base de datos aproximadamente? ______

- ¿Hay un schema (namespace) específico para los datos operativos?
  - ¿O todo está en el schema por defecto (`dbo` en SQL Server, `public` en Postgres)?
  - Lista de schemas disponibles: _______________

- ¿Existe documentación del modelo de datos? (ERD, Word, PDF, cualquier cosa)
  - [ ] Sí → adjuntar al responder este documento
  - [ ] No

- ¿Existe un diccionario de datos? (descripción de cada tabla y columna)
  - [ ] Sí → adjuntar
  - [ ] No

### 2.2 Tablas principales — necesitamos nombre EXACTO

Completar con los nombres reales de las tablas en su base:

| Entidad conceptual | Nombre real de la tabla | Schema |
|---|---|---|
| Cajas físicas (elementos) | | |
| Legajos físicos | | |
| Posiciones / ubicaciones en depósito | | |
| Módulos / estanterías | | |
| Clientes | | |
| Pedidos / requerimientos / órdenes | | |
| Remitos | | |
| Movimientos / auditoría | | |
| Retiros | | |
| Usuarios / operarios del sistema | | |
| Hoja de ruta / despacho | | |
| Trámites administrativos / búsqueda | | |

Si una entidad no tiene tabla propia (está embebida en otra), indicarlo.

### 2.3 Columnas críticas — por cada tabla relevante

Para **cada tabla** de la lista anterior, necesitamos:

- Nombre exacto de la **clave primaria** y su tipo (INT, BIGINT, VARCHAR, GUID/UUID, autoincremental o no)
- Nombre de la columna que guarda el **código de caja/legajo** (ej: `cod_elemento`, `codigo`, `barcode`)
- Nombre de la columna de **estado** y los **valores posibles** exactos (ej: 'EN_GUARDA', 'EN_CONSULTA', o números: 1, 2, 3)
- Nombre de las **claves foráneas** principales (FK a cliente, FK a posición, etc.)
- ¿Hay columna `deleted_at` o `activo` para soft-delete?
- ¿Hay columnas `created_at` / `updated_at`?

Ejemplo del formato que esperamos:

```
Tabla: TB_ELEMENTOS
  PK: ID_ELEMENTO (BIGINT, autoincremental)
  Código barcode: COD_BARRAS (VARCHAR 12)
  Estado: EST_ELEMENTO (CHAR 2) → valores: 'EG'=en guarda, 'EC'=en consulta, 'ET'=en tránsito, 'CL'=en cliente, 'BA'=baja
  FK cliente: ID_CLIENTE (INT)
  FK posición: ID_POSICION (INT, nullable)
  Soft delete: ACTIVO (BIT) → 0=borrado, 1=activo
  Timestamps: FEC_ALTA (DATETIME), FEC_MOD (DATETIME)
```

### 2.4 Prefijos de códigos de caja y legajo

Esta es una de las preguntas más críticas. Los prefijos determinan la validación de todos los UCs.

- ¿Los códigos de caja son siempre de 12 dígitos? ______
- ¿Los códigos de legajo son siempre de 12 dígitos? ______
- ¿Cómo se forma el código completo de 12 dígitos? (describir la estructura)
  
  Ejemplo de lo que suponemos actualmente:
  ```
  Código de 7 dígitos ingresado → prefijo "11000" + 7 dígitos = 12 dígitos total
  Código de 6 dígitos ingresado → prefijo "110000" + 6 dígitos = 12 dígitos total
  Código de 4 dígitos viejo    → "13" + código_cliente (2 dígitos) + 4 dígitos = 12 dígitos total
  ```
  ¿Esto es correcto? ¿Hay más casos? ¿El prefijo varía según el cliente?

- ¿Cómo se distingue un código de caja de uno de legajo? (¿por los primeros dígitos? ¿por campo tipo en la tabla?)

- ¿Los clientes tienen un código de 2 dígitos que forma parte del prefijo? ______

- Ejemplos reales de códigos válidos (si no son datos sensibles):
  - Caja: ____________
  - Legajo: ____________

### 2.5 Estados y transiciones

Para la tabla de elementos/cajas, necesitamos el mapa completo de estados:

- Listado de **todos los estados posibles** con su significado:
  ```
  Estado en DB → Significado de negocio
  __________ → en guarda (en el depósito de BASA, sin movimiento)
  __________ → en consulta (pedido activo)
  __________ → en tránsito (en camino al cliente)
  __________ → en cliente (en las instalaciones del cliente)
  __________ → baja (dado de baja, no se usa más)
  (agregar los que falten)
  ```

- ¿Hay estados intermedios que nosotros no modelamos?
- ¿Las transiciones de estado están controladas por la app, por triggers, o por stored procedures?

### 2.6 Stored procedures

- ¿El ABM usa stored procedures para las operaciones principales?
  - [ ] No, escribe directo a las tablas
  - [ ] Sí → listar los más importantes:

| Nombre del SP | Para qué sirve | Parámetros de entrada | Parámetros de salida |
|---|---|---|---|
| | | | |
| | | | |

- ¿Hay stored procedures que **debemos llamar obligatoriamente** para mantener la consistencia?
  (ej: un SP que actualiza contadores, genera auditoría, notifica a otro sistema)

- ¿Hay **triggers** en las tablas principales que disparan lógica automática?
  Lista de triggers por tabla: _______________

### 2.7 Vistas

- ¿Hay vistas (VIEWS) que el ABM o los reportes usan para leer datos?
  - Lista de vistas con descripción de para qué se usan:

| Nombre de la vista | Descripción | ¿El ABM la usa? |
|---|---|---|
| | | |

---

## BLOQUE 3 — El ABM existente

### 3.1 Tecnología

- ¿En qué lenguaje/framework está construido el ABM?
  - [ ] VB.NET / C# / .NET Framework / .NET Core → ¿versión?
  - [ ] Delphi / Pascal
  - [ ] Java
  - [ ] PHP
  - [ ] Node.js / web moderno
  - [ ] Otro: _______________

- ¿Es una aplicación de escritorio (Windows Forms, WPF) o web?
- ¿Dónde corre el ABM? (en los equipos de cada operario, en un servidor compartido, en la nube)

### 3.2 Acceso al código fuente

- ¿Podemos ver el código fuente del ABM?
  - [ ] Sí, tienen repositorio Git/SVN → ¿URL?
  - [ ] Sí, pero no está en un repositorio → ¿pueden mandarnos un ZIP?
  - [ ] No, el código es de un proveedor externo

- Si el ABM es de un proveedor externo: ¿tienen contacto técnico con ese proveedor al que podamos consultar?

- ¿Tienen el connection string del ABM? (para ver exactamente cómo se conecta)
  ```
  Ejemplo: Server=192.168.1.10;Database=BASA_PROD;User Id=app_user;Password=xxx;
  ```
  Connection string real (si pueden compartirlo): _______________

### 3.3 Funcionalidades del ABM — qué hace exactamente

Para cada funcionalidad, marcar si existe y describir cómo está implementada:

**Gestión de clientes:**
- [ ] Alta de cliente → ¿campos obligatorios? _______________
- [ ] Modificación de cliente
- [ ] Baja de cliente → ¿es soft delete o físico?
- [ ] Búsqueda/filtros de clientes

**Gestión de elementos (cajas/legajos):**
- [ ] Alta individual de caja/legajo → ¿cómo se genera el código? ¿automático o manual?
- [ ] Carga masiva de elementos → ¿por CSV, Excel, escáner, otro?
- [ ] Modificación de datos de un elemento
- [ ] Baja de elemento
- [ ] Búsqueda por código, por cliente, por estado

**Gestión de posiciones/depósito:**
- [ ] Alta de módulo/estantería
- [ ] Alta de posición individual
- [ ] Vista del mapa del depósito
- [ ] ¿El ABM muestra qué posiciones están ocupadas?

**¿Hay funcionalidades del ABM que SOLAPAN con los UC que estamos implementando?**

Por ejemplo:
- ¿El ABM ya tiene un módulo de "pedidos" o "retiros"?
- ¿El ABM ya registra movimientos de cajas?
- ¿El ABM ya calcula fletes?

Si hay solapamiento, necesitamos decidir si:
a) Nuestro sistema reemplaza esa funcionalidad del ABM
b) Convivimos con el ABM (duplicidad de datos, hay que sincronizar)
c) Llamamos al ABM como servicio (si expone API)

---

## BLOQUE 4 — Lógica de negocio crítica

### 4.1 Cálculo de fletes

Actualmente implementamos: `fletes = ceil(cantidad_cajas / 20)`

- ¿Esto es correcto? [ ] Sí [ ] No
- Si no, ¿cuál es la fórmula real?
- ¿Varía según el cliente, tipo de caja, distancia, u otro factor?
- ¿El precio del flete también se calcula en el sistema o es fijo por contrato con cada cliente?

### 4.2 Splitting automático de legajos

Cuando un legajo no se encuentra en el depósito, creamos un "requerimiento hijo" de tipo Búsqueda.

- ¿Este proceso existe actualmente? [ ] Sí (manual) [ ] Sí (automático) [ ] No existe
- ¿Cómo se resuelve hoy cuando falta un legajo?
- ¿El requerimiento hijo debe tener algún campo específico que lo vincule al padre?

### 4.3 Tipos de requerimiento

Tenemos modelados los siguientes tipos (números):

| Número | Descripción |
|---|---|
| 1 | UC1 — Ubicación en planta |
| 2 | UC2 — Consulta de caja |
| 3 | UC3 — Consulta de legajos |
| 5 | UC4 — Retiro |
| 16 | UC5 — Búsqueda/investigación |
| 8 | Destino de transformación — consulta digital |

- ¿Estos tipos/números coinciden con lo que tienen en la base?
- ¿Hay más tipos que no estamos contemplando?
- Tabla real de tipos de requerimiento (si existe):

| Código en DB | Descripción en BASA |
|---|---|
| | |

### 4.4 SLA y tiempos

- Consulta de caja: ¿cuántas horas hábiles tiene el operario para despacharla? (asumimos 48hs) ______
- Consulta de legajo: ¿cuántas horas? ______
- Retiro: ¿cuántas horas para que pasen a buscarlas? ______
- Búsqueda/investigación: ¿hay SLA? ______

### 4.5 Autorización de supervisor

Cuando una caja tiene legajos individuales catalogados, el sistema pide autorización de supervisor antes de despachar.

- ¿Cómo se sabe que una caja tiene "elementos individuales catalogados"? (¿campo en la tabla? ¿relación con otra tabla?)
- ¿Quién puede autorizar? (¿cualquier jefe? ¿un rol específico?)
- ¿Esta autorización se registra en alguna tabla?

### 4.6 Reglas de los códigos — confirmación

Marcar si cada regla es correcta:

| Regla | ¿Correcto? | Corrección si no |
|---|---|---|
| Código de 7 dígitos → prefijo "11000" para caja | ☐ Sí ☐ No | |
| Código de 6 dígitos → prefijo "110000" para caja | ☐ Sí ☐ No | |
| Código de 7 dígitos → prefijo "12000" para legajo | ☐ Sí ☐ No | |
| Código de 6 dígitos → prefijo "120000" para legajo | ☐ Sí ☐ No | |
| Código antiguo de 4 dígitos → "13" + cód_cliente + 4 dígitos | ☐ Sí ☐ No | |
| Código de posición tiene 14 dígitos | ☐ Sí ☐ No | |
| Toda caja ocupa exactamente UNA posición (1 a 1) | ☐ Sí ☐ No | |

### 4.7 Retiro — tipos

Tenemos modelados dos tipos de retiro:
- **Por cantidad:** el cliente declara N cajas, retiramos lo que llega y conciliamos
- **Por referencia:** el cliente declara los códigos exactos que va a entregar

- ¿Esto es correcto?
- ¿Hay más tipos de retiro?
- ¿Cuando hay diferencia entre lo declarado y lo recibido, quién decide cómo resolverla?

---

## BLOQUE 5 — Integración con otros sistemas

### 5.1 Sistema Aconcagua (despacho/transporte)

- ¿Qué es Aconcagua exactamente? (software de terceros, sistema propio, empresa de transporte)
- ¿Aconcagua expone API? [ ] Sí, REST [ ] Sí, SOAP/WSDL [ ] No, es manual [ ] No sé
- ¿Qué datos necesita Aconcagua para registrar un despacho?
  - Número de remito, fecha, cliente, cantidad de bultos, dirección, otros
- ¿Actualmente la comunicación con Aconcagua es manual (alguien carga en el sistema de ellos)?
- Si hay integración automática: ¿quién la implementó? ¿está documentada?

### 5.2 Sistema de email

- ¿Usan servidor SMTP propio de BASA? [ ] Sí [ ] No (usan Gmail/Outlook/otro)
- Servidor SMTP: _______________
- Puerto: ______  TLS/SSL: [ ] Sí [ ] No
- Email del remitente para notificaciones: _______________
- ¿Hay templates de email para las notificaciones a clientes? (si los tienen, compartirlos)
- ¿Los clientes reciben email solo para retiros, o también para otros UCs?

### 5.3 Sistema de impresión de remitos

- ¿Los remitos actuales se imprimen?
- ¿Desde qué sistema? (el ABM, Word, Crystal Reports, otro)
- ¿Tenemos que generar el PDF nosotros o alcanza con mostrar los datos en pantalla?
- ¿Hay un formato/template específico del remito que debamos respetar? (si existe, compartir un ejemplo)
- ¿Los remitos tienen número correlativo? ¿Quién lo genera?

### 5.4 Lectores de código de barras / escáneres

- ¿Qué tipo de códigos de barra usan? (Code 128, QR, EAN, otro)
- ¿Los operarios tienen pistolas/escáneres físicos conectados a la PC o usan cámara del celular?
- ¿Los escáneres actúan como teclado (HID) o tienen software propio con API?
- La interfaz que estamos construyendo tiene inputs de texto que reciben el escaneo — ¿eso es compatible con los escáneres que usan?

---

## BLOQUE 6 — UC6 — Agente IA para jefes

### 6.1 Casos de uso concretos

¿Qué preguntas hacen los jefes actualmente? (cuantos más ejemplos, mejor el agente)

Ejemplos del tipo de pregunta que esperamos:
- "¿Cuántas cajas entregamos esta semana?"
- "¿Dónde está la caja del cliente X con código Y?"
- "¿Cuántos pedidos tienen más de 48hs sin despachar?"
- "¿Cuántos fletes generamos en mayo?"

Preguntas reales que los jefes necesitan responder hoy: _______________

### 6.2 Aprobación del costo del LLM

El agente IA usa la API de Anthropic (Claude). El costo aproximado es:

| Uso estimado | Costo mensual aprox. |
|---|---|
| 100 consultas/día (~15 palabras cada una) | ~USD 5–10/mes |
| 500 consultas/día | ~USD 25–50/mes |

- ¿BASA aprueba este costo? [ ] Sí [ ] No [ ] Consultar
- ¿Prefieren una alternativa open-source (Llama, Mistral) corriendo en sus servidores? (requiere GPU)

### 6.3 NotebookLM para manual de procedimientos

Podemos conectar el agente a un NotebookLM con el manual de BASA para que responda preguntas sobre procedimientos.

- ¿Tienen un manual de procedimientos o reglamento interno escrito? [ ] Sí [ ] No
- ¿Tienen cuenta de Google Workspace corporativa? (necesario para NotebookLM empresarial)
- ¿Les interesa esta funcionalidad? [ ] Sí [ ] No, solo datos de la DB

---

## BLOQUE 7 — Seguridad y producción

### 7.1 Dónde corre el sistema en producción

- ¿Van a correr el sistema nuevo en los propios servidores de BASA o en la nube?
- ¿Tienen servidor Linux disponible con Docker instalado?
- ¿O prefieren que levantemos el sistema en la nube (AWS/GCP/Azure/DigitalOcean)?
- ¿Necesitan HTTPS con dominio propio? ¿Tienen dominio? (ej: sistema.basa.com.ar)

### 7.2 Usuarios del sistema

- ¿Cuántos operarios van a usar el sistema simultáneamente? (para dimensionar)
- ¿Cuántos jefes van a usar UC6?
- ¿Quién va a administrar usuarios? (crear/desactivar cuentas)
- ¿Se integra con Active Directory / LDAP de la empresa para el login?
  - [ ] Sí → darnos datos del servidor LDAP/AD
  - [ ] No, usuarios independientes en nuestra base

### 7.3 Datos sensibles

- ¿Los legajos contienen datos personales sensibles (DNI, CUIL, datos médicos, datos judiciales)?
- ¿Están bajo alguna regulación de protección de datos? (Ley 25.326, GDPR si tienen clientes en Europa)
- ¿Los datos de los clientes son confidenciales entre clientes? (que el cliente A no pueda ver los elementos del cliente B)

---

## RESUMEN EJECUTIVO — Lo mínimo indispensable para arrancar

Si no pueden responder todo ahora, priorizar esto:

### Semana 1 — Acceso

1. **Credencial de solo lectura** al ambiente de dev (o a producción)
2. **Nombre de la tabla** donde están las cajas y sus columnas principales (especialmente el campo de código y el campo de estado)
3. **Un ejemplo** de código de caja real y uno de legajo real

### Semana 2 — Entender el modelo

4. **Schema completo** exportado desde Management Studio o equivalente
5. **Código del ABM** o al menos los archivos de acceso a datos (DAL/repositorios)
6. Listado de **stored procedures** que tocan las tablas principales

### Semana 3 — Integraciones

7. Datos del **servidor SMTP**
8. Clarificación sobre **Aconcagua** (API o proceso manual)
9. Confirmación de las **reglas de negocio** (fletes, prefijos, SLA)

---

*Contacto para responder este documento:* _______________  
*Fecha de reunión técnica disponible:* _______________
