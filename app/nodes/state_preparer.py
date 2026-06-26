from typing import Any


def state_preparer(state: dict) -> dict:
    """Normaliza el payload y define las tablas afectadas según el tipo de operación."""
    payload = state.get("payload", {})
    op_type = state.get("op_type", "")

    updates = {"errors": [], "tablas_afectadas": []}

    if op_type == "UC1_UBICACION":
        updates["codigo_caja"] = payload.get("codigo_caja", "")
        updates["codigo_posicion"] = payload.get("codigo_posicion", "")
        updates["operario_id"] = payload.get("operario_id")
        updates["tablas_afectadas"] = ["dbo.elemento", "dbo.posicion", "dbo.movimiento"]

    elif op_type == "UC2_CONSULTA_CAJA":
        updates["cliente_id"] = payload.get("cliente_id")
        updates["direccion_entrega_id"] = payload.get("direccion_entrega_id")
        updates["codigos_caja"] = payload.get("codigos_caja", [])
        updates["observaciones"] = payload.get("observaciones", "")
        updates["operario_id"] = payload.get("operario_id")
        updates["tablas_afectadas"] = ["dbo.requerimiento", "dbo.elemento", "dbo.movimiento"]

    elif op_type == "UC3_CONSULTA_LEGAJOS":
        updates["cliente_id"] = payload.get("cliente_id")
        updates["codigos_legajo"] = payload.get("codigos_legajo", [])
        updates["requerimiento_id"] = payload.get("requerimiento_id")
        updates["operario_id"] = payload.get("operario_id")
        updates["tablas_afectadas"] = ["dbo.requerimiento", "dbo.referencia", "dbo.movimiento"]

    elif op_type == "UC4_RETIRO":
        updates["cliente_id"] = payload.get("cliente_id")
        updates["tipo"] = payload.get("tipo", "CANTIDAD")
        updates["cantidad_declarada"] = payload.get("cantidad_declarada")
        updates["codigos_referencia"] = payload.get("codigos_referencia", [])
        updates["requerimiento_id"] = payload.get("requerimiento_id")
        updates["codigos_leidos"] = payload.get("codigos_leidos", [])
        updates["remito_nombre"] = payload.get("remito_nombre", "")
        updates["tablas_afectadas"] = ["dbo.requerimiento", "dbo.lectura", "dbo.lectura_detalle", "dbo.movimiento"]

    elif op_type == "UC5_BUSQUEDA":
        updates["requerimiento_id"] = payload.get("requerimiento_id")
        updates["horas_archivista"] = payload.get("horas_archivista")
        updates["codigo_elemento"] = payload.get("codigo_elemento_encontrado", "")
        updates["tipo_destino"] = payload.get("tipo_destino")
        updates["observaciones"] = payload.get("observaciones", "")
        updates["cliente_id"] = payload.get("cliente_id")
        updates["operario_id"] = payload.get("operario_id")
        updates["tablas_afectadas"] = ["dbo.requerimiento", "dbo.movimiento"]

    return {**state, **updates}
