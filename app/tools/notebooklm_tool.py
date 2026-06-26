import os
import httpx
from langchain_core.tools import tool


@tool
def notebooklm_search_tool(query: str) -> str:
    """
    Realiza una búsqueda semántica en la base de conocimiento de BASA Argentina (75 documentos).
    Útil para consultar reglas de negocio, SLAs, prefijos de códigos y procedimientos operativos.
    """
    nb_id = os.getenv("NOTEBOOKLM_BASA_ID", "")
    mcp_url = os.getenv("NOTEBOOKLM_MCP_URL", "http://localhost:18789/tools/notebook_query")

    try:
        response = httpx.post(mcp_url, json={"notebook_id": nb_id, "query": query}, timeout=60.0)
        response.raise_for_status()
        return response.json().get("answer", "Sin respuesta de la base de conocimiento.")
    except Exception as e:
        return f"Error al consultar la base de conocimiento: {str(e)}"
