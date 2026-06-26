import math


def node_commercial_logic(state: dict) -> dict:
    """Calcula valores comerciales derivados. Para UC4: fletes = ceil(cantidad / 20)."""
    op_type = state.get("op_type", "")

    if op_type == "UC4_RETIRO":
        cantidad = state.get("cantidad_final") or state.get("cantidad_declarada") or 0
        fletes = math.ceil(cantidad / 20) if cantidad > 0 else 0
        return {**state, "fletes_calculados": fletes}

    return state
