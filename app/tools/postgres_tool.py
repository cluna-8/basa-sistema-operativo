from langchain_core.tools import tool
from sqlalchemy import text
from app.db import get_engine

_FORBIDDEN = {"DELETE", "DROP", "TRUNCATE"}


@tool
def postgres_db_tool(sql_query: str, parameters: dict = None) -> str:
    """
    Ejecuta una consulta SQL parametrizada sobre la base de datos PostgreSQL de BASA.
    Úsala para consultar posiciones, estados de elementos o registrar movimientos.
    DELETE físico está prohibido; usar soft-deletes con campo estado.
    """
    upper = sql_query.upper().split()
    if any(kw in upper for kw in _FORBIDDEN):
        return "Operación prohibida: DELETE/DROP/TRUNCATE no permitidos. Usar soft-delete."

    params = parameters or {}
    try:
        with get_engine().begin() as conn:
            result = conn.execute(text(sql_query), params)
            if result.returns_rows:
                rows = [dict(row._mapping) for row in result]
                return str(rows)
            return f"Operación exitosa. Filas afectadas: {result.rowcount}"
    except Exception as e:
        return f"Error en base de datos: {str(e)}"
