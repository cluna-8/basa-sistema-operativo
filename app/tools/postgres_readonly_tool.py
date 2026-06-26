from langchain_core.tools import tool
from sqlalchemy import text
from app.db import get_engine

_FORBIDDEN_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE"}


@tool
def postgres_readonly_tool(sql_query: str) -> str:
    """
    Ejecuta consultas SELECT de solo lectura sobre la base de datos de BASA.
    Úsala para responder preguntas sobre estado de cajas, pedidos, posiciones, etc.
    Cualquier intento de escritura será rechazado automáticamente.
    """
    words = set(sql_query.upper().split())
    if words & _FORBIDDEN_KEYWORDS:
        return (
            "Operación de escritura rechazada. Este canal es solo para consultas de información. "
            "Para modificar datos, utilizá el sistema Aconcagua o contactá a un operario autorizado."
        )

    try:
        with get_engine().connect() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result]
            if not rows:
                return "La consulta no devolvió resultados."
            return str(rows)
    except Exception as e:
        return f"Error al consultar la base de datos: {str(e)}"
