# Guía y Especificaciones del Proyecto: Aceleración Operativa Visual-First
**Cliente:** BASA Argentina (Banco de Archivos S.A.)  
**Fecha:** 2026-06-26  
**Documento:** Guía de Desarrollo e Interfaces Interactivas para Agentes  

---

## 1. Introducción y Enfoque de Aceleración (Necesidades del Cliente)

El objetivo comercial de este documento es doble:
1. **Demostrar aceleración al cliente final y directores de BASA**: La visualización rápida del progreso es prioritaria. Los directores necesitan ver pantallas operativas e interactivas lo antes posible.
2. **Definir una guía clara para otros agentes de desarrollo**: Este documento establece el contrato de datos, lógica visual y comportamiento de interfaz para que los agentes encargados del desarrollo de frontend y backend puedan programar de forma ordenada.

### Estrategia "Visual-First" y Lógica de Mockups:
* Se implementará la interfaz de usuario (React) completa para cada uno de los casos de uso.
* **Principio de Simulación Controlada**: Aquellos elementos que aún no guarden información o no estén cableados al backend representarán "información pendiente de persistencia". El usuario podrá interactuar con la interfaz (por ejemplo, escanear, hacer clic, cambiar dropdowns), y si el sistema no persiste, mostrará una alerta visual o un log detallando: *"Acción simulada: Datos listos para grabación en `[nombre_tabla]`"*. Esto permite validar la experiencia de usuario (UX) inmediatamente mientras los agentes del backend completan las rutas de base de datos.

---

## 2. Especificación Detallada de los 5 Casos de Uso

---

### Caso de Uso 1: Ordenamiento y Ubicación de Cajas en Planta

#### A. Necesidades del Cliente (Customer Needs)
* **Problema:** Pérdida física de cajas en el galpón, lo que genera retrasos críticos en entregas y multas comerciales.
* **Necesidad:** Saber con precisión milimétrica en qué estante, fila y módulo vertical/horizontal se encuentra cada caja al instante de ser clasificada en planta.

#### B. Reglas de Negocio Cruzadas
* Una posición (`dbo.posicion`) solo puede tener una caja (`dbo.elemento`) asignada.
* Los códigos de barras de posiciones corresponden a etiquetas físicas autoadhesivas de 14 dígitos en los módulos (`dbo.modulos.codigoBarra`).
* Al escanear una posición en uso, la interfaz debe mostrar una advertencia restrictiva.

#### C. Ciclo de Vida del Requerimiento
1. **Recepción:** Caja ingresa a zona de clasificación.
2. **Emparejamiento:** Operario escanea caja + posición física.
3. **Persistencia:** La posición pasa a `'OCUPADO'` en base de datos.

#### D. Mapeo de Datos (PostgreSQL)
* **`dbo.posicion`**:
  * `id` (BigInt, PK)
  * `estado` (Varchar(50), valores: `'DISPONIBLE'`, `'OCUPADO'`)
  * `estanteria` (Numeric)
  * `codigo_modulo` (Varchar(12))
* **`dbo.elemento`**:
  * `id` (BigInt, PK)
  * `codigo` (Varchar(100) — Código de la caja física)
  * `posicion_id` (BigInt, FK -> `dbo.posicion.id`)

#### E. Especificación de la Interfaz Visual (Mockup Interactivo)
* **Nombre de la Vista:** `PlantLocations.tsx`
* **Layout:** Doble panel de escaneo rápido con autofoco automático.
  1. **Input "Escanear Caja"**: Input de texto grande con animación de borde parpadeante. Al ingresar datos, pasa el foco al siguiente campo.
  2. **Input "Escanear Ubicación"**: Entrada de 14 dígitos.
* **Comportamiento Interactivo (Placeholder):**
  * Si la base de datos no responde, la grilla temporal muestra una tarjeta en amarillo con el texto: *"Simulado: Caja X mapeada a Estante Y. Pendiente de grabación en base de datos."*

#### F. Integración Backend
* **`state_preparer`**: Inicializa el mapeo entre el ID de la caja y el ID de la posición.
* **`node_validator`**: Verifica si la posición tiene `estado = 'DISPONIBLE'`.

---

### Caso de Uso 2: Consulta Normal de Caja

#### A. Necesidades del Cliente (Customer Needs)
* **Problema:** El cliente final (banco, empresa, etc.) necesita recuperar cajas guardadas para auditorías, pero no sabe si están disponibles o ya están en consulta, o carga códigos con formatos erróneos.
* **Necesidad:** Una interfaz cliente que valide el formato de 12 dígitos de forma automática en el cliente y alerte si el estado actual en planta no es `'en guarda'`.

#### B. Reglas de Negocio Cruzadas
* **Prefijos de 12 dígitos obligatorios:**
  * Caja de 7 dígitos: Anteponer `11000`.
  * Caja de 6 dígitos: Anteponer `110000`.
  * Caja vieja (4 dígitos): Prefijo `13` + código del cliente (4 dígitos) + `00` + número de caja.
* Estado requerido de la caja para permitir la carga: `'en guarda'`.

#### C. Ciclo de Vida del Requerimiento
1. **Solicitud:** Cliente solicita vía web.
2. **Picking:** Operario realiza la recolección física en planta.
3. **Autorización:** Si la caja contiene elementos individuales catalogados unitariamente, la interfaz muestra alerta amarilla y requiere que un supervisor pase los elementos internos a `'en transito'` o `'en salida'`.
4. **Despacho:** Impresión de Remito, asignación a Hoja de Ruta, entrega física y digitalización del remito firmado.

#### D. Mapeo de Datos (PostgreSQL)
* **`dbo.requerimiento`**:
  * `id` (BigInt, PK)
  * `requerimiento_tipo_id` (BigInt, FK, valor = `4` [Consulta Caja])
  * `estado` (Varchar(50), valores: `'PENDIENTE'`, `'PICKING'`, `'EN TRANSITO'`, `'FINALIZADO'`)
* **`dbo.elemento`**:
  * `id` (BigInt, PK)
  * `codigo` (Varchar(100))
  * `estado` (Varchar(50), valor: `'en guarda'`)

#### E. Especificación de la Interfaz Visual (Mockup Interactivo)
* **Nombre de la Vista:** `WebBoxOrder.tsx` (ASP Web cliente) y `PickingDashboard.tsx` (Aconcagua operario).
* **Campos clave (Cliente):**
  * Input inteligente de número de caja con auto-completado de prefijo en tiempo real (según la cantidad de dígitos tipeados).
* **Flujo Operario (Aconcagua):**
  * Banner superior destacado en amarillo: *"Esta caja contiene elementos individuales. Solicite autorización de supervisor para cambiar estado a 'en transito'."*
  * **Placeholder logic:** Si el botón "Cambiar Estado" es presionado por un no-supervisor, la pantalla responde: *"Simulando autorización de supervisor. Cambiando estado de elementos internos a 'en salida' en memoria local."*

#### F. Integración Backend
* **`node_validator`**: Rechaza payloads con códigos de caja que no tengan exactamente 12 dígitos o que no estén en estado `'en guarda'`.

---

### Caso de Uso 3: Consulta Normal de Legajos

#### A. Necesidades del Cliente (Customer Needs)
* **Problema:** Solicitar una carpeta y que no se encuentre físicamente en la caja contenedora frena todo el pedido de despacho diario.
* **Necesidad:** Poder despachar lo que sí se encontró y generar automáticamente un reclamo o tarea de investigación por los legajos faltantes sin requerir interacción manual del cliente.

#### B. Reglas de Negocio Cruzadas
* **Prefijos de 12 dígitos obligatorios:**
  * Legajo de 7 dígitos: Anteponer `12000`.
  * Legajo de 6 dígitos: Anteponer `120000`.
  * Legajos viejos: Prefijo `14` + código de cliente (4 dígitos) + `00` + número de legajo.
* **Splitting Automático:** Al controlar el pedido en planta, el sistema detecta los legajos no escaneados y crea de forma automática un requerimiento secundario (hijo).

#### C. Ciclo de Vida del Requerimiento
1. El cliente pide legajos específicos en la web.
2. El operario escanea en planta.
3. Los legajos ausentes se dividen automáticamente al procesar el remito, creando un nuevo pedido hijo con estado `'PENDIENTE_BUSQUEDA'`.

#### D. Mapeo de Datos (PostgreSQL)
* **`dbo.referencia`** (Metadatos de legajos):
  * `id` (BigInt, PK)
  * `elemento_contenedor_id` (BigInt, FK -> `dbo.elemento.id`)
  * `texto1` (Identificador o nombre del legajo)
* **`dbo.requerimiento`**:
  * Tipo requerimiento = `2` (Consulta Legajo) y el requerimiento hijo se crea con tipo `16` (Búsqueda Documentación).

#### E. Especificación de la Interfaz Visual (Mockup Interactivo)
* **Nombre de la Vista:** `LegajosControl.tsx`
* **UI Components:**
  * Panel izquierdo: Lista de legajos pedidos con checkbox digital.
  * Lector simulado: Botón "Escanear Legajo Seleccionado". Al hacer clic, la fila se colorea de verde.
  * Panel derecho: Alerta destacada: *"Faltan 2 legajos por leer. Al procesar el remito, se generará el requerimiento hijo automático de Búsqueda."*
  * **Placeholder logic:** Si el operario presiona "Procesar Remito Incompleto", la pantalla simula la división: *"Splitting realizado. Pedido principal procesado. Generado Requerimiento Hijo #99988 en memoria temporal."*

#### F. Integración Backend
* **`node_persistence_unit`**: Encapsula en una transacción única la actualización del pedido padre y la creación del pedido hijo.

---

### Caso de Uso 4: Retiros por Cantidad o Referencia

#### A. Necesidades del Cliente (Customer Needs)
* **Problema:** Clientes que envían más o menos cajas físicas de las declaradas en el pedido web, lo que distorsiona la facturación de fletes y el inventario.
* **Necesidad:** Una interfaz de recepción en planta que muestre de forma visual y clara las diferencias entre lo retirado vs. lo pedido, con cálculo automático del cargo por fletes.

#### B. Reglas de Negocio Cruzadas
* **Límite de Flete:** 1 flete cubre hasta 20 elementos. El backend calcula `fletes = ceil(cantidad / 20)`.
* **Nomenclaturas de Archivos de Lectura:**
  * Lectura en cliente (chofer): `0002-000[remito]-[requerimiento]`
  * Ingreso a planta (operario): `0001-[fecha]-[provincia]`
* Conciliación con ajuste automático del pedido al procesar discrepancias.

#### C. Ciclo de Vida del Requerimiento
1. Solicitud de retiro programada.
2. Chofer retira y escanea en cliente.
3. Cajas ingresan a planta y se escanean.
4. El operador concilia discrepancias e inicia el proceso del remito.
5. Se envía email automático al cliente con cantidades reales ingresadas.

#### D. Mapeo de Datos (PostgreSQL)
* **`dbo.requerimiento`**:
  * `cantidad` (Numeric — Cantidad total conciliada)
  * `fletes` (Int — Cantidad de fletes calculados)
* **`dbo.lectura_detalle`**:
  * `codigo_barra` (Varchar)
  * `remito` (Varchar)

#### E. Especificación de la Interfaz Visual (Mockup Interactivo)
* **Nombre de la Vista:** `IntakeConciliation.tsx`
* **UI Components:**
  * Campo de búsqueda de número de remito (con icono de lupa).
  * Panel de comparación cuantitativa:
    * Caja A: "Declarado por Cliente: 15"
    * Caja B: "Leído en Planta (Ingreso): 11"
    * Caja C: "Cargo Fletes Automático: 1"
  * Alerta de Discrepancia: *"Advertencia: Se detectó una diferencia de -4 cajas. Se facturará en base a las 11 recibidas."*
  * **Placeholder logic:** Al presionar "Confirmar e Ingresar Cajas", el sistema responde: *"Simulando ingreso físico. Enviando email de confirmación a cliente@empresa.com con el detalle de 11 cajas ingresadas en guarda."*

#### F. Integración Backend
* **`node_commercial_logic`**: Calcula la cantidad final de fletes comerciales.

---

### Caso de Uso 5: Trámite Administrativo de Búsqueda (Investigación)

#### A. Necesidades del Cliente (Customer Needs)
* **Problema:** El cliente no sabe en qué caja está un documento, lo que exige tiempo de búsqueda manual y en sistemas de bases de datos por parte del personal de BASA.
* **Necesidad:** Registrar detalladamente las pistas del documento, facturar de forma transparente las horas empleadas por el archivista y permitir transformar dinámicamente el pedido una vez localizado.

#### B. Reglas de Negocio Cruzadas
* El campo `Observaciones` es obligatorio al crear el pedido.
* Se debe registrar obligatoriamente `horas_archivista` en el requerimiento.
* Al encontrar el elemento, el requerimiento se transforma a tipo `02` (Consulta Física de Legajo) o `08` (Consulta Digital).

#### C. Ciclo de Vida del Requerimiento
1. Solicitud de búsqueda con observaciones/pistas.
2. Operario busca físicamente y en sistemas.
3. Se encuentra el archivo, se ingresan las horas empleadas y se asocia el código.
4. El operario transforma el requerimiento al tipo de despacho seleccionado.

#### D. Mapeo de Datos (PostgreSQL)
* **`dbo.requerimiento`**:
  * `tipoRequerimiento_id` (Numeric, original = `16` [Búsqueda], modificado a `02` o `08` al finalizar)
  * `horas_archivista` (Decimal)
  * `observaciones` (Varchar(8000))

#### E. Especificación de la Interfaz Visual (Mockup Interactivo)
* **Nombre de la Vista:** `SearchInvestigation.tsx`
* **UI Components:**
  * Sección superior: Caja de información con las "Pistas de Búsqueda del Cliente".
  * Formulario central:
    * Campo de entrada: "Horas de Archivista Empleadas" (tipo decimal).
    * Campo de escaneo: "Código de Barra Asignado al Documento".
  * Dropdown selector de destino: "Transformar a Consulta Física de Legajo" / "Transformar a Consulta Digital".
  * **Placeholder logic:** Al presionar "Transformar Flujo", la pantalla muestra: *"Trámite administrativo finalizado. Requerimiento mutado a Tipo 02 (Consulta Física). Creado ticket de despacho en Aconcagua."*

#### F. Integración Backend
* **`node_persistence_unit`**: Modifica el `tipoRequerimiento_id` de forma atómica y escribe la auditoría de cambio de flujo.

---

## 3. Guía de Implementación para Otros Agentes (Blueprint)

Cuando los agentes de desarrollo asuman el control de la implementación, deberán seguir estrictamente el siguiente orden de tareas:

1. **Paso 1: Implementar las Vistas React en el Dashboard (`DASH-cli/dashboard/src/pages/`)**
   * Crear los componentes y pantallas descritos en las especificaciones utilizando Tailwind CSS y TypeScript.
   * Utilizar la **lógica de simulación controlada (placeholder)**: las llamadas a API de persistencia que den error o no existan deben ser interceptadas en el frontend para mostrar las alertas de éxito simulado detalladas en el documento. Esto permite presentar inmediatamente interfaces interactivas funcionales al cliente sin depender del backend.
2. **Paso 2: Desarrollar los Contratos de Datos y DTOs**
   * Definir los tipos e interfaces TypeScript en `src/types/` correspondientes a los payloads JSON que las vistas enviarán (ej: `BoxOrderPayload`, `UbicacionPayload`).
3. **Paso 3: Cablear las API y Conexiones PostgreSQL**
   * Implementar las consultas SQLAlchemy y los nodos del Grafo en el backend (`app/nodes/`) de forma no destructiva, sustituyendo progresivamente los placeholders del frontend con llamadas reales.
