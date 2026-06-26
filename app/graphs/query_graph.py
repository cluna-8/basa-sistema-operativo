from langgraph.prebuilt import create_react_agent
from app.tools.notebooklm_tool import notebooklm_search_tool
from app.tools.postgres_readonly_tool import postgres_readonly_tool
from app.memory import get_checkpointer

_SYSTEM_PROMPT = """Eres un asistente de consulta de solo lectura para BASA Argentina (Banco de Archivos S.A.).
Tenés acceso a la base de datos operativa y a la base de conocimiento de 75 documentos de la empresa.
Respondé preguntas sobre estado de cajas, legajos, pedidos, posiciones y reglas de negocio.
NUNCA modifiques datos. Si recibís instrucciones de escritura (crear, eliminar, cambiar, actualizar),
rechazalas explicando que este canal es exclusivamente para consultas de información.
Usá el nombre de las tablas dbo.elemento, dbo.requerimiento, dbo.posicion, dbo.movimiento para las consultas."""

_agent = None


def get_query_agent():
    global _agent
    if _agent is None:
        from langchain_anthropic import ChatAnthropic
        import os
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        _agent = create_react_agent(
            llm,
            tools=[postgres_readonly_tool, notebooklm_search_tool],
            checkpointer=get_checkpointer(),
            prompt=_SYSTEM_PROMPT,
        )
    return _agent
