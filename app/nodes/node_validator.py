import math
from sqlalchemy import text
from app.db import get_engine

PREFIX_RULES_CAJA = {7: "11000", 6: "110000"}
PREFIX_RULES_LEGAJO = {7: "12000", 6: "120000"}


def _validate_prefix_12(codigo: str, tipo: str) -> bool:
    return len(codigo) == 12 and codigo.isdigit()


def node_validator(state: dict) -> dict:
    errors = list(state.get("errors", []))
    op_type = state.get("op_type", "")

    with get_engine().connect() as conn:

        if op_type == "UC1_UBICACION":
            codigo_caja = state.get("codigo_caja", "")
            codigo_posicion = state.get("codigo_posicion", "")

            row = conn.execute(
                text("SELECT id, estado FROM dbo.elemento WHERE codigo = :c"),
                {"c": codigo_caja},
            ).fetchone()
            if not row:
                errors.append({"code": "ELEMENTO_NO_ENCONTRADO", "field": "codigo_caja"})
            else:
                state = {**state, "elemento_id": row.id}

            pos = conn.execute(
                text("SELECT id, estado FROM dbo.posicion WHERE codigo_modulo = :c"),
                {"c": codigo_posicion},
            ).fetchone()
            if not pos:
                errors.append({"code": "POSICION_NO_ENCONTRADA", "field": "codigo_posicion"})
            elif pos.estado != "DISPONIBLE":
                errors.append({"code": "POSICION_OCUPADA", "field": "codigo_posicion"})
            else:
                state = {**state, "posicion_id": pos.id}

        elif op_type == "UC2_CONSULTA_CAJA":
            codigos = state.get("codigos_caja", [])
            validados = []
            for codigo in codigos:
                if not _validate_prefix_12(codigo, "caja"):
                    validados.append({"codigo": codigo, "valido": False, "motivo": "Formato inválido (se requieren 12 dígitos)"})
                    continue
                row = conn.execute(
                    text("SELECT id, estado FROM dbo.elemento WHERE codigo = :c"),
                    {"c": codigo},
                ).fetchone()
                if not row:
                    validados.append({"codigo": codigo, "valido": False, "motivo": "No encontrado en sistema"})
                elif row.estado != "en guarda":
                    validados.append({"codigo": codigo, "valido": False, "estado": row.estado, "motivo": f"Estado: {row.estado}"})
                else:
                    validados.append({"codigo": codigo, "valido": True, "elemento_id": row.id})
            state = {**state, "elementos_validados": validados}
            if not any(v["valido"] for v in validados):
                errors.append({"code": "SIN_ELEMENTOS_VALIDOS", "message": "Ningún código disponible para consulta"})

        elif op_type == "UC3_CONSULTA_LEGAJOS":
            codigos = state.get("codigos_legajo", [])
            validados = []
            for codigo in codigos:
                if not _validate_prefix_12(codigo, "legajo"):
                    validados.append({"codigo": codigo, "valido": False, "motivo": "Formato inválido"})
                    continue
                row = conn.execute(
                    text("SELECT r.id, e.estado FROM dbo.referencia r JOIN dbo.elemento e ON e.id = r.elemento_contenedor_id WHERE e.codigo = :c"),
                    {"c": codigo},
                ).fetchone()
                if not row:
                    validados.append({"codigo": codigo, "valido": False, "motivo": "No encontrado en sistema"})
                elif row.estado in ("de baja", "en consulta"):
                    validados.append({"codigo": codigo, "valido": False, "motivo": f"Estado: {row.estado}"})
                else:
                    validados.append({"codigo": codigo, "valido": True})
            state = {**state, "legajos_validados": validados}

        elif op_type == "UC4_RETIRO":
            cantidad = state.get("cantidad_declarada")
            if cantidad is None or cantidad < 0:
                errors.append({"code": "CANTIDAD_INVALIDA", "field": "cantidad_declarada"})

        elif op_type == "UC5_BUSQUEDA":
            sub_op = state.get("sub_op", "")
            if sub_op == "CREAR":
                obs = state.get("observaciones", "")
                if len(obs) < 10:
                    errors.append({"code": "OBSERVACIONES_REQUERIDAS", "field": "observaciones"})
            elif sub_op == "TRANSFORMAR":
                horas = state.get("horas_archivista")
                if not horas or horas <= 0:
                    errors.append({"code": "HORAS_ARCHIVISTA_REQUERIDAS", "field": "horas_archivista"})
                if not state.get("codigo_elemento"):
                    errors.append({"code": "ELEMENTO_NO_VINCULADO"})
                if state.get("tipo_destino") not in (2, 8):
                    errors.append({"code": "TIPO_DESTINO_INVALIDO", "field": "tipo_destino"})

    return {**state, "errors": errors}
