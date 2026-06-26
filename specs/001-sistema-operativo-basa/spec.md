# Feature Specification: Sistema Operativo Integral BASA Argentina

**Feature Branch**: `001-sistema-operativo-basa`

**Created**: 2026-06-26

**Status**: Draft

**Input**: Sistema completo de gestión operativa para Banco de Archivos S.A. — 5 casos de uso críticos con estrategia Visual-First, stack containerizado en Docker.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ordenamiento y Ubicación de Cajas en Planta (Priority: P1)

Un operario de planta recibe cajas físicas en la zona de clasificación. Utiliza un colector de datos láser para escanear el código de barras de cada caja y luego el código de barras de la posición física (estantería/módulo) donde debe almacenarse. El sistema vincula la caja a la posición y actualiza el estado de la posición a "OCUPADO". Si la posición ya estaba ocupada, el sistema lo advierte antes de permitir la asignación.

**Why this priority**: Es el fundamento del inventario físico. Sin ubicación precisa, todos los demás casos de uso (consultas, retiros) son imposibles de ejecutar con exactitud. Es la causa histórica de extravíos y multas comerciales.

**Independent Test**: Escanear una caja existente y una posición libre en `PlantLocations`: el sistema vincula la caja, cambia el estado a OCUPADO y muestra confirmación en verde. No requiere ningún otro caso de uso activo.

**Acceptance Scenarios**:

1. **Given** una caja con código existente y una posición en estado DISPONIBLE, **When** el operario escanea ambos en `PlantLocations`, **Then** el sistema vincula la caja a la posición, actualiza el estado a OCUPADO y muestra confirmación en verde.
2. **Given** una posición en estado OCUPADO, **When** el operario intenta asignar una nueva caja, **Then** el sistema muestra una advertencia restrictiva y bloquea la asignación.
3. **Given** que el backend no está disponible, **When** el operario completa el escaneo, **Then** la pantalla muestra: *"Simulado: Caja X mapeada a Estante Y. Pendiente de grabación en base de datos"* en amarillo.
4. **Given** un código de caja que no existe en el sistema, **When** se escanea, **Then** el sistema muestra error en rojo y no permite continuar.

---

### User Story 2 - Consulta Normal de Caja (Priority: P1)

Un cliente solicita la consulta de cajas físicas a través del portal web. El sistema valida el formato de 12 dígitos del código de caja con autocompletado de prefijo según la longitud ingresada, y verifica que la caja esté en estado "en guarda". En planta, el operario recibe la tarea de picking, escanea las cajas, genera el remito, las asocia a una Hoja de Ruta, las entrega al cliente (quien firma el remito), y al regresar el remito firmado se digitaliza cerrando el ciclo.

**Why this priority**: Es el caso de uso de mayor volumen diario. Impacta directamente en el SLA de 48 horas y en la satisfacción de los clientes finales.

**Independent Test**: Crear un pedido web con una caja en estado "en guarda", procesar el picking y verificar que el remito se genere con el estado de la caja actualizado.

**Acceptance Scenarios**:

1. **Given** el cliente ingresa un código de 7 dígitos en `WebBoxOrder`, **When** el sistema detecta la longitud, **Then** autocompletó con prefijo `11000` formando 12 dígitos totales.
2. **Given** una caja en estado "en consulta", **When** el cliente intenta agregarla al pedido, **Then** el sistema colorea la fila en rojo y muestra alerta de estado no disponible.
3. **Given** que la caja contiene elementos individuales catalogados, **When** el operario intenta generar el remito en `PickingDashboard`, **Then** aparece un banner amarillo requiriendo autorización de supervisor antes de continuar.
4. **Given** el remito firmado retorna a planta y se digitaliza, **When** se procesa el cierre, **Then** el requerimiento pasa a estado FINALIZADO y las cajas vuelven a "en guarda".

---

### User Story 3 - Consulta Normal de Legajos (Priority: P2)

Un cliente solicita legajos específicos por código de barras. El operario busca y escanea físicamente los legajos en las cajas contenedoras. Si algún legajo no se encuentra, el sistema no frena el pedido: despacha los encontrados y genera automáticamente un requerimiento hijo (tipo 16 - Búsqueda) con los legajos faltantes.

**Why this priority**: El splitting automático es la solución al problema más frecuente de operación diaria. Sin él, un legajo faltante paraliza pedidos enteros.

**Independent Test**: Crear un pedido de 3 legajos, escanear solo 2, y verificar que el sistema genera remito para los 2 encontrados más un requerimiento hijo con el 1 faltante.

**Acceptance Scenarios**:

1. **Given** un pedido de legajos en `LegajosControl`, **When** el operario escanea todos, **Then** cada legajo escaneado se colorea en verde en tiempo real.
2. **Given** que 1 legajo del pedido no se encuentra físicamente, **When** el operario presiona "Procesar Remito Incompleto", **Then** el sistema genera el requerimiento hijo de Búsqueda y procesa el remito con los encontrados.
3. **Given** un legajo con código de 6 dígitos, **When** se ingresa al sistema, **Then** se valida y completa automáticamente con prefijo `120000`.
4. **Given** que el backend falla al crear el requerimiento hijo, **Then** la transacción completa revierte (el pedido padre tampoco se modifica).

---

### User Story 4 - Retiros por Cantidad o Referencia (Priority: P2)

El cliente programa el retiro físico de sus cajas desde sus oficinas. El transportista retira y escanea en el cliente; las cajas ingresan a planta donde el operario concilia cantidades declaradas vs. recibidas. Si hay discrepancia, el sistema ajusta la facturación automáticamente y envía email al cliente con el detalle real.

**Why this priority**: Las discrepancias de retiro afectan directamente la facturación de fletes y el inventario. El cálculo automático elimina errores manuales de cobro.

**Independent Test**: Simular un retiro declarado de 15 cajas con solo 11 leídas en planta. El sistema debe mostrar la discrepancia, calcular 1 flete (`ceil(11/20)`) y preparar el email de confirmación.

**Acceptance Scenarios**:

1. **Given** un remito con 15 cajas declaradas y 11 leídas en `IntakeConciliation`, **When** el operario procesa la conciliación, **Then** el sistema muestra "Cant. Pedida: 15 vs. Cant. Ingresada: 11" en naranja/rojo y asigna 1 flete.
2. **Given** un pedido de 21 elementos, **When** se calcula el flete, **Then** el sistema asigna 2 fletes (`ceil(21/20) = 2`).
3. **Given** que las cantidades coinciden exactamente, **When** se procesa, **Then** no aparece alerta de discrepancia y el flujo continúa sin confirmación adicional.
4. **Given** la conciliación aprobada, **When** el operario confirma, **Then** el sistema envía automáticamente un email al cliente con el detalle de cajas ingresadas.

---

### User Story 5 - Trámite Administrativo de Búsqueda / Investigación (Priority: P3)

El cliente no sabe en qué caja está un documento. Abre un trámite de búsqueda con observaciones detalladas. El operario investiga en planta y en sistemas, registra las horas empleadas y, al encontrar el documento, transforma dinámicamente el requerimiento al tipo de despacho que corresponde (consulta física o digital).

**Why this priority**: Menor volumen que consultas normales, pero crítico para auditorías y reclamos. La transformación dinámica evita duplicar pedidos.

**Independent Test**: Crear un trámite de búsqueda con observaciones, registrar 2 horas de archivista, vincular un elemento encontrado y transformar a Consulta Física. El sistema debe cambiar el tipo de requerimiento y habilitar el flujo de despacho.

**Acceptance Scenarios**:

1. **Given** un trámite de búsqueda en `SearchInvestigation`, **When** el operario intenta finalizar sin ingresar `horas_archivista`, **Then** el sistema bloquea con validación obligatoria.
2. **Given** el documento encontrado y etiquetado, **When** el operario selecciona "Transformar a Consulta Física de Legajo", **Then** el tipo de requerimiento cambia de Búsqueda (16) a Consulta Física (02) y se habilita el flujo de despacho.
3. **Given** la transformación completada, **Then** el movimiento queda registrado como `INVESTIGACION_EXITOSA` en auditoría sin perder el historial del trámite original.
4. **Given** el campo Observaciones vacío al crear el trámite, **When** el cliente intenta enviar, **Then** el sistema rechaza con error de campo obligatorio.

---

### User Story 6 - Consulta Conversacional para Jefes (Priority: P2)

Un jefe de operaciones necesita conocer el estado del sistema sin abrir ninguna interfaz gráfica. Puede preguntar en lenguaje natural sobre el estado de cajas, pedidos pendientes, legajos en tránsito, posiciones ocupadas, o cualquier dato operativo. El sistema responde con información real de la base de datos. Esta capa es estrictamente de lectura: no puede modificar datos ni disparar operaciones.

**Why this priority**: Los directivos de BASA necesitan visibilidad del estado operativo en cualquier momento sin depender de que un operario les muestre una pantalla. Es también el canal de validación de reglas de negocio contra la base de conocimiento de 75 documentos.

**Independent Test**: Enviar la pregunta "¿Cuántas cajas están en tránsito ahora?" al endpoint de consulta y verificar que la respuesta incluye un número real extraído de la base de datos, sin modificar ningún registro.

**Acceptance Scenarios**:

1. **Given** un jefe autenticado con rol `jefe`, **When** pregunta "¿Cuántos pedidos están pendientes hoy?", **Then** el agente consulta `dbo.requerimiento` y responde con el número exacto y un breve resumen.
2. **Given** una pregunta sobre la ubicación de una caja específica, **When** el jefe escribe "¿Dónde está la caja 110001234567?", **Then** el agente responde con estantería, módulo y estado actual sin modificar ningún dato.
3. **Given** una pregunta sobre reglas de negocio, **When** el jefe pregunta "¿Cuál es el SLA para consultas urgentes de legajos?", **Then** el agente consulta la base de conocimiento (NotebookLM) y responde con la regla documentada.
4. **Given** que el jefe intenta una acción de escritura ("eliminá la caja 110001234567"), **When** el agente recibe el mensaje, **Then** rechaza la acción explicando que el canal de consulta es solo lectura.
5. **Given** una conversación de múltiples turnos, **When** el jefe hace una pregunta de seguimiento ("¿Y cuántos de esos son urgentes?"), **Then** el agente mantiene el contexto de la pregunta anterior dentro de la sesión.

---

### Edge Cases

- ¿Qué ocurre si se escanea el mismo código de caja dos veces en el mismo pedido?
- ¿Cómo maneja el sistema un código de barras dañado o parcialmente ilegible?
- ¿Qué pasa si el servicio de memoria (Redis) no está disponible al iniciar el agente?
- ¿Qué sucede si el email de confirmación falla al enviarse en el Caso de Uso 4?
- ¿Puede un operario ver los elementos internos de una caja aunque no tenga permiso para cambiarles el estado?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE validar y autocompletar prefijos de 12 dígitos para cajas (11000 / 110000 / 13XXXX) y legajos (12000 / 120000 / 14XXXX) según la longitud del código ingresado, en tiempo real antes del envío.
- **FR-002**: El sistema DEBE implementar lógica de simulación controlada en el frontend: cuando una operación de persistencia falla o no está implementada, DEBE mostrar una alerta descriptiva con el nombre de la tabla destino en lugar de un error genérico.
- **FR-003**: El sistema DEBE prohibir toda operación de eliminación física en tablas de negocio; toda baja DEBE implementarse como soft-delete mediante campo de estado.
- **FR-004**: El sistema DEBE encapsular en una sola transacción atómica todas las operaciones que afecten más de una tabla, incluyendo los registros de auditoría.
- **FR-005**: El sistema DEBE calcular automáticamente la cantidad de fletes como `ceil(cantidad / 20)` al procesar retiros por cantidad.
- **FR-006**: El sistema DEBE generar automáticamente un requerimiento hijo (tipo 16 - Búsqueda) con los legajos no encontrados al procesar un remito de Consulta de Legajos incompleto.
- **FR-007**: El sistema DEBE enviar un email automático al cliente con el detalle real de cajas ingresadas al conciliar un retiro con discrepancia de cantidad.
- **FR-008**: El sistema DEBE permitir la transformación dinámica de un requerimiento tipo 16 (Búsqueda) a tipo 02 (Consulta Física) o tipo 08 (Consulta Digital), preservando el historial de auditoría completo.
- **FR-009**: El sistema DEBE registrar las horas de archivista como campo obligatorio al finalizar un Trámite de Búsqueda con resultado exitoso.
- **FR-010**: El sistema DEBE alertar visualmente y bloquear la asignación cuando se intenta asignar una caja a una posición ya ocupada.
- **FR-011**: Todos los servicios del sistema (frontend, backend, base de datos, memoria, agente inteligente) DEBEN ejecutarse en contenedores Docker orquestados mediante un único comando de arranque.
- **FR-012**: El sistema DEBE mantener dos capas de memoria persistente del agente: memoria de sesión (por conversación) y memoria de operario entre sesiones (por usuario).
- **FR-013**: El sistema DEBE exponer una interfaz de consulta semántica sobre la base de conocimiento de BASA (75 documentos) a través del agente inteligente.
- **FR-014**: El sistema DEBE proveer un canal de consulta conversacional en lenguaje natural para usuarios con rol `jefe`, que acceda en modo **solo lectura** a la base de datos y a la base de conocimiento, sin pasar por el pipeline de orquestación operativa (los 4 nodos de LangGraph). Ninguna consulta a través de este canal puede modificar datos.
- **FR-015**: El canal de consulta para jefes DEBE mantener contexto de conversación entre turnos dentro de una misma sesión (memoria short-term por `thread_id`), y rechazar explícitamente cualquier instrucción de escritura o modificación de datos.

### Key Entities

- **Elemento**: Caja o legajo físico. Atributos: código de barras, estado operativo (en guarda / en consulta / en transito / en cliente / BAJA), posición asignada.
- **Posicion**: Espacio físico en estantería. Atributos: estado (DISPONIBLE / OCUPADO), estantería, módulo. Relación exclusiva 1-a-1 con un Elemento.
- **Requerimiento**: Pedido operativo del cliente. Atributos: tipo de requerimiento, estado del ciclo de vida, cantidad, fletes calculados, horas de archivista, observaciones. Puede tener requerimientos hijos.
- **Referencia**: Metadatos indexados de legajos (campos de texto libre para búsqueda: apellido, nombre, DNI, tipo).
- **Movimiento**: Registro de auditoría inmutable de cada cambio de estado de un Elemento o Requerimiento.
- **Hoja de Ruta**: Agrupación de requerimientos asignados a un viaje de transporte en una jornada.
- **Lectura / LecturaDetalle**: Registro de escaneos realizados por colectores láser externos en cliente o planta.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un operario completa el emparejamiento caja-posición de una unidad en menos de 30 segundos desde el primer escaneo hasta la confirmación visual.
- **SC-002**: El sistema detecta prefijos incorrectos o códigos con longitud inválida antes de que el usuario envíe el formulario (validación en tiempo real, sin roundtrip al servidor).
- **SC-003**: El splitting automático de legajos faltantes se completa en una sola interacción del operario (un clic) sin pasos adicionales.
- **SC-004**: Las interfaces de los 5 casos de uso son demostrables con datos simulados al cliente antes de que el backend esté completamente implementado.
- **SC-005**: Un fallo en cualquier paso de la cadena de persistencia no deja datos en estado parcial; la base de datos siempre queda en el estado previo a la operación fallida.
- **SC-006**: El agente inteligente responde consultas sobre reglas de negocio de BASA en menos de 10 segundos consultando la base de conocimiento.
- **SC-007**: El historial de conversación del operario persiste entre reinicios del sistema sin pérdida de contexto de la sesión activa.
- **SC-008**: El entorno completo del sistema se levanta con un único comando sin configuración manual más allá de las variables de entorno en un archivo `.env`.
- **SC-009**: El canal de consulta para jefes responde preguntas sobre datos operativos en menos de 15 segundos incluyendo el acceso a base de datos y base de conocimiento.
- **SC-010**: El agente rechaza el 100% de las solicitudes de escritura recibidas a través del canal de jefes, respondiendo con un mensaje explicativo sin ejecutar ninguna modificación.

---

## Assumptions

- El portal web del cliente (ASP Web) y la consola de operarios (Aconcagua / DASH-cli) son dos frontends distintos que comparten el mismo backend de agente.
- Las credenciales y URLs de servicios (base de datos, memoria, email, base de conocimiento) se suministran vía archivo `.env` al orquestador Docker Compose; no hay configuración manual post-deploy.
- El servidor de base de conocimiento (NotebookLM MCP) ya existe y está accesible en la red interna de BASA; este desarrollo no lo construye, solo lo consume.
- Los colectores láser externos generan archivos planos que se procesan por ingesta batch; no se integran en tiempo real en esta fase.
- Los roles de "operario" y "supervisor" existen en el sistema de autenticación actual; este desarrollo consume los roles disponibles sin reimplementar autenticación.
- El módulo de envío de emails usa el servidor SMTP existente en la infraestructura de BASA, configurable vía variables de entorno.
- El volumen esperado es de hasta 200 requerimientos concurrentes por día; no se requiere alta disponibilidad geográfica en esta fase.
- Docker Compose es la herramienta de orquestación para todos los entornos (desarrollo, staging y producción en servidor local de BASA).
