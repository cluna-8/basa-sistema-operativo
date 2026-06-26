from sqlalchemy import text
from app.db import get_engine


def node_persistence_unit(state: dict) -> dict:
    """Ejecuta todas las escrituras en una única transacción atómica (Principio III)."""
    op_type = state.get("op_type", "")

    with get_engine().begin() as conn:

        if op_type == "UC1_UBICACION":
            elemento_id = state["elemento_id"]
            posicion_id = state["posicion_id"]
            conn.execute(
                text("UPDATE dbo.elemento SET posicion_id = :pid WHERE id = :eid"),
                {"pid": posicion_id, "eid": elemento_id},
            )
            conn.execute(
                text("UPDATE dbo.posicion SET estado = 'OCUPADO' WHERE id = :pid"),
                {"pid": posicion_id},
            )
            result = conn.execute(
                text(
                    "INSERT INTO dbo.movimiento (elemento_id, tipo_movimiento, estado_nuevo, operario_id) "
                    "VALUES (:eid, 'UBICACION_FISICA', 'UBICADO', :oid) RETURNING id"
                ),
                {"eid": elemento_id, "oid": state.get("operario_id")},
            )
            mov_id = result.scalar()
            return {**state, "movimiento_id": mov_id, "resultado": "ok"}

        elif op_type == "UC2_CONSULTA_CAJA":
            sub_op = state.get("sub_op", "CREAR")
            if sub_op == "CREAR":
                result = conn.execute(
                    text(
                        "INSERT INTO dbo.requerimiento (requerimiento_tipo_id, estado, cliente_id, direccion_entrega_id, observaciones) "
                        "VALUES (4, 'PENDIENTE', :cid, :did, :obs) RETURNING id"
                    ),
                    {"cid": state["cliente_id"], "did": state.get("direccion_entrega_id"), "obs": state.get("observaciones", "")},
                )
                req_id = result.scalar()
                return {**state, "requerimiento_id": req_id}
            elif sub_op == "DIGITALIZAR":
                conn.execute(
                    text("UPDATE dbo.requerimiento SET estado = 'FINALIZADO' WHERE id = :rid"),
                    {"rid": state["requerimiento_id"]},
                )
                conn.execute(
                    text("INSERT INTO dbo.movimiento (requerimiento_id, tipo_movimiento, estado_nuevo) VALUES (:rid, 'FINALIZADO', 'FINALIZADO')"),
                    {"rid": state["requerimiento_id"]},
                )
                return {**state, "estado_final": "FINALIZADO"}

        elif op_type == "UC3_CONSULTA_LEGAJOS":
            encontrados = [l["codigo"] for l in state.get("legajos_escaneados", []) if l.get("encontrado")]
            faltantes = [l["codigo"] for l in state.get("legajos_escaneados", []) if not l.get("encontrado")]

            conn.execute(
                text("UPDATE dbo.requerimiento SET cantidad = :c WHERE id = :rid"),
                {"c": len(encontrados), "rid": state["requerimiento_id"]},
            )
            hijo_id = None
            if faltantes:
                result = conn.execute(
                    text(
                        "INSERT INTO dbo.requerimiento (requerimiento_tipo_id, estado, cliente_id, parent_requerimiento_id) "
                        "VALUES (16, 'PENDIENTE_BUSQUEDA', :cid, :pid) RETURNING id"
                    ),
                    {"cid": state["cliente_id"], "pid": state["requerimiento_id"]},
                )
                hijo_id = result.scalar()
            for codigo in encontrados:
                conn.execute(
                    text("INSERT INTO dbo.movimiento (requerimiento_id, tipo_movimiento, estado_nuevo) VALUES (:rid, 'EN_TRANSITO', 'en transito')"),
                    {"rid": state["requerimiento_id"]},
                )
            return {**state, "requerimiento_hijo_id": hijo_id, "legajos_despachados": encontrados, "legajos_pendientes": faltantes}

        elif op_type == "UC4_RETIRO":
            result = conn.execute(
                text("INSERT INTO dbo.lectura (remito, requerimiento_id, tipo) VALUES (:r, :rid, :t) RETURNING id"),
                {"r": state.get("remito_nombre", ""), "rid": state["requerimiento_id"], "t": state.get("tipo_lectura", "PLANTA")},
            )
            lectura_id = result.scalar()
            for codigo in state.get("codigos_leidos", []):
                conn.execute(
                    text("INSERT INTO dbo.lectura_detalle (lectura_id, codigo_barra, resultado) VALUES (:lid, :c, 'ENCONTRADO')"),
                    {"lid": lectura_id, "c": codigo},
                )
            conn.execute(
                text("UPDATE dbo.requerimiento SET cantidad = :c, fletes = :f WHERE id = :rid"),
                {"c": state.get("cantidad_final", 0), "f": state.get("fletes_calculados", 0), "rid": state["requerimiento_id"]},
            )
            conn.execute(
                text("INSERT INTO dbo.movimiento (requerimiento_id, tipo_movimiento, estado_nuevo) VALUES (:rid, 'INGRESO_PLANTA', 'en guarda')"),
                {"rid": state["requerimiento_id"]},
            )
            return {**state, "lectura_id": lectura_id}

        elif op_type == "UC5_BUSQUEDA":
            sub_op = state.get("sub_op", "")
            if sub_op == "CREAR":
                result = conn.execute(
                    text(
                        "INSERT INTO dbo.requerimiento (requerimiento_tipo_id, estado, cliente_id, observaciones) "
                        "VALUES (16, 'PENDIENTE', :cid, :obs) RETURNING id"
                    ),
                    {"cid": state["cliente_id"], "obs": state["observaciones"]},
                )
                return {**state, "requerimiento_id": result.scalar()}
            elif sub_op == "TRANSFORMAR":
                tipo_destino = state["tipo_destino"]
                conn.execute(
                    text("UPDATE dbo.requerimiento SET requerimiento_tipo_id = :td, horas_archivista = :h WHERE id = :rid"),
                    {"td": tipo_destino, "h": state["horas_archivista"], "rid": state["requerimiento_id"]},
                )
                result = conn.execute(
                    text(
                        "INSERT INTO dbo.movimiento (requerimiento_id, tipo_movimiento, estado_anterior, estado_nuevo) "
                        "VALUES (:rid, 'INVESTIGACION_EXITOSA', '16', :td) RETURNING id"
                    ),
                    {"rid": state["requerimiento_id"], "td": str(tipo_destino)},
                )
                proximo = "consulta-legajos" if tipo_destino == 2 else "consulta-digital"
                return {**state, "movimiento_id": result.scalar(), "proximo_flujo": proximo}

    return state
