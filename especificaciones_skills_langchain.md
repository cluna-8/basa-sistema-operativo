# Especificación Técnica: Skills para LangChain y Búsqueda en NotebookLM
**Proyecto:** BASA Argentina (Banco de Archivos S.A.)  
**Fecha:** 2026-06-26  
**Documento:** Diseño de Agentes, Skills (Tools) y Persistencia en Redis  

---

## 1. Arquitectura General del Agente

Para automatizar e integrar los procesos operativos de BASA Argentina, se implementará un modelo de **Agente Inteligente** utilizando **LangChain** y **LangGraph**. En esta arquitectura, las capacidades operativas del agente se modularizan en forma de **Skills (Tools)**, permitiendo que el modelo LLM decida autónomamente cuándo es necesario consultar información externa, actualizar registros o interactuar con bases de datos.

```mermaid
graph TD
    User[Usuario / Operario] -->|Prompt + thread_id| Agent[Agente LangGraph]
    Agent -->|Decisión de herramienta| ToolManager[Manejador de Skills / Tools]
    ToolManager -->|Búsqueda RAG| NotebookLMTool[NotebookLM Query Tool]
    ToolManager -->|Picking / DB| PostgreSQLTool[PostgreSQL Database Tool]
    Agent -->|Short-Term Memory| RedisCheckpointer[Redis Checkpointer Saver]
    Agent -->|Long-Term Memory| RedisStore[Redis Profile Store]
    NotebookLMTool -->|Resultados Contexto| Agent
    PostgreSQLTool -->|Operaciones Confirmadas| Agent
```

---

## 2. Definición de las Skills (Tools) en LangChain

En LangChain, las "skills" del agente se definen mediante la abstracción de **Tools**. A continuación se detallan las especificaciones y el código Python necesario para implementar las herramientas principales.

### A. Skill de Búsqueda en NotebookLM (`notebooklm_search_tool`)
Esta herramienta permite al agente realizar búsquedas semánticas y de lenguaje natural sobre las fuentes de conocimiento del cliente (75 documentos relevados de BASA en el Notebook).

```python
from langchain_core.tools import tool
import httpx
import os

@tool
def notebooklm_search_tool(query: str, notebook_id: str = None) -> str:
    """
    Realiza una consulta de búsqueda semántica en la base de conocimiento de NotebookLM.
    Utilízala para recuperar reglas de negocio cruzadas, prefijos de cajas/legajos,
    tiempos de entrega (SLA) y especificaciones operativas del galpón de BASA.
    """
    # Se utiliza el ID de notebook por defecto de BASA Argentina si no se suministra uno
    nb_id = notebook_id or os.getenv("NOTEBOOKLM_BASA_ID", "52b20bd8-f9c0-4409-b17f-95e0df393d67")
    
    # URL del servidor local MCP o API wrapper de NotebookLM
    mcp_url = os.getenv("NOTEBOOKLM_MCP_URL", "http://localhost:18789/tools/notebook_query")
    
    payload = {
        "notebook_id": nb_id,
        "query": query
    }
    
    try:
        response = httpx.post(mcp_url, json=payload, timeout=60.0)
        response.raise_for_status()
        result = response.json()
        return result.get("answer", "No se encontró respuesta.")
    except Exception as e:
        return f"Error al conectar con la base de conocimiento de NotebookLM: {str(e)}"
```

### B. Skill de Persistencia Operacional en PostgreSQL (`postgres_db_tool`)
Esta herramienta permite al agente interactuar directamente con el esquema relacional (`dbo.requerimiento`, `dbo.elemento`, etc.) para verificar la disponibilidad o actualizar estados de pickings.

```python
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
import os

# Inicializar motor de base de datos PostgreSQL
db_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/basa_db")
engine = create_engine(db_url)

@tool
def postgres_db_tool(sql_query: str, parameters: dict = None) -> str:
    """
    Ejecuta una consulta SQL parametrizada de manera segura sobre la base de datos PostgreSQL de BASA.
    Utilízala para consultar posiciones de cajas (dbo.posicion), verificar estados de elementos (dbo.elemento)
    o registrar movimientos históricos (dbo.movimiento).
    Restricción: Las eliminaciones físicas (DELETE) están estrictamente prohibidas; usar soft-deletes.
    """
    params = parameters or {}
    try:
        with engine.begin() as connection:
            result = connection.execute(text(sql_query), params)
            if result.returns_rows:
                rows = [dict(row) for row in result]
                return f"Resultado: {str(rows)}"
            return f"Operación ejecutada con éxito. Filas afectadas: {result.rowcount}"
    except Exception as e:
        return f"Error en la ejecución de base de datos: {str(e)}"
```

---

## 3. Configuración de Memoria en Redis (Orquestador LangGraph)

Para gestionar la memoria de las sesiones y threads sin degradar el contexto del modelo, se implementan dos capas de memoria utilizando **Redis**:

### A. Memoria a Corto Plazo (Short-Term Memory / Checkpointer)
Retiene la historia de mensajes y cambios de estado dentro de la misma sesión de chat (Thread). Se implementa utilizando `langgraph-checkpoint-redis` para guardar instantáneas (checkpoints) del grafo.

* **Conexión e Instanciación:**
```python
import redis
from langgraph.checkpoint.redis import RedisSaver

# Cliente Redis de producción
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Checkpointer para persistencia de hilo
checkpointer = RedisSaver(redis_client)
# Preparación de tablas de almacenamiento interno en Redis (requerido en primera ejecución)
checkpointer.setup()
```

### B. Memoria a Largo Plazo (Long-Term Memory / Store)
Permite recordar preferencias del usuario, configuraciones del cliente (ej. si requiere retiro por referencia obligatorio) y metadatos históricos de operarios a través de múltiples conversaciones.

```python
from langgraph.store.redis import RedisStore

# Store cross-thread para almacenamiento semántico y de perfil
store = RedisStore(redis_client)
store.setup()
```

---

## 4. Orquestación del Grafo de Estado (`StateGraph`)

El grafo de estado centraliza el control del agente, vinculando las herramientas y la persistencia en Redis.

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from operator import add

# 1. Definición del Estado compartido por los agentes
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add]
    current_action: str
    target_id: int
    errors: list

# 2. Definición del Grafo
workflow = StateGraph(AgentState)

# Listado de herramientas a asociar al agente
tools = [notebooklm_search_tool, postgres_db_tool]
tool_node = ToolNode(tools)

# Nodos lógicos
def call_model(state: AgentState):
    # Lógica del LLM decidiendo la acción o llamada a herramienta
    pass

def should_continue(state: AgentState):
    # Lógica de enrutamiento condicional (ej: si requiere herramienta o finaliza)
    pass

# Registrar Nodos y Flujo
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"continue": "tools", "end": END})
workflow.add_edge("tools", "agent")

# 3. Compilación del Grafo inyectando ambas capas de memoria Redis
app = workflow.compile(checkpointer=checkpointer, store=store)
```

---

## 5. Invocación de Producción del Agente

Para ejecutar el agente orquestado asegurando que la memoria a corto plazo persista correctamente en Redis, cada ejecución de hilo debe enviarse con una configuración de `thread_id`:

```python
# Configuración del ID de hilo para asociarlo a la memoria Redis
config = {
    "configurable": {
        "thread_id": "operario_felipe_sesion_105",
        "user_id": "felipe_basa"
    }
}

# Entrada del operario para buscar información o procesar picking
user_input = {
    "messages": [
        {"role": "user", "content": "¿Cuáles son las reglas de prefijos para legajos de 6 dígitos en BASA?"}
    ]
}

# Ejecución transaccional del agente con memoria persistente
response = app.invoke(user_input, config=config)
print(response["messages"][-1].content)
```

### Comportamiento en Redis:
* **Short-Term:** Redis almacena el estado completo de la conversación con clave `checkpoint:[thread_id]`.
* **Long-Term:** Las preferencias recopiladas por el agente sobre el operario `felipe_basa` se persisten en namespaces del `store` para que estén disponibles la próxima vez que inicie sesión, incluso con un `thread_id` diferente.
* **Búsqueda:** Al recibir la pregunta, el modelo decide invocar la skill `notebooklm_search_tool`, devolviendo la respuesta semántica basada en las fuentes de BASA.
