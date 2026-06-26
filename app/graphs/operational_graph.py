from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, END
from app.nodes.state_preparer import state_preparer
from app.nodes.node_validator import node_validator
from app.nodes.node_commercial_logic import node_commercial_logic
from app.nodes.node_persistence_unit import node_persistence_unit
from app.memory import get_checkpointer, get_store


class OperationalState(TypedDict, total=False):
    op_type: str
    sub_op: str
    payload: dict
    errors: list
    tablas_afectadas: list
    # UC1
    codigo_caja: str
    codigo_posicion: str
    elemento_id: int
    posicion_id: int
    movimiento_id: int
    operario_id: int
    # UC2/UC3
    cliente_id: int
    codigos_caja: list
    codigos_legajo: list
    elementos_validados: list
    legajos_validados: list
    legajos_escaneados: list
    requerimiento_id: int
    requerimiento_hijo_id: int
    # UC4
    cantidad_declarada: float
    cantidad_final: float
    fletes_calculados: int
    codigos_leidos: list
    remito_nombre: str
    tipo_lectura: str
    # UC5
    horas_archivista: float
    codigo_elemento: str
    tipo_destino: int
    observaciones: str
    proximo_flujo: str
    # resultado
    resultado: str


def _should_continue(state: OperationalState) -> str:
    return "end_with_errors" if state.get("errors") else "node_commercial_logic"


def _always_persist(state: OperationalState) -> str:
    return "node_persistence_unit"


def build_operational_graph():
    workflow = StateGraph(OperationalState)

    workflow.add_node("state_preparer", state_preparer)
    workflow.add_node("node_validator", node_validator)
    workflow.add_node("node_commercial_logic", node_commercial_logic)
    workflow.add_node("node_persistence_unit", node_persistence_unit)

    workflow.set_entry_point("state_preparer")
    workflow.add_edge("state_preparer", "node_validator")
    workflow.add_conditional_edges(
        "node_validator",
        _should_continue,
        {"end_with_errors": END, "node_commercial_logic": "node_commercial_logic"},
    )
    workflow.add_edge("node_commercial_logic", "node_persistence_unit")
    workflow.add_edge("node_persistence_unit", END)

    return workflow.compile(checkpointer=get_checkpointer(), store=get_store())


_graph = None


def get_operational_graph():
    global _graph
    if _graph is None:
        _graph = build_operational_graph()
    return _graph
