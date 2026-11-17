
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableLambda

from estado import EstadoAgentes

from agentes.investigador import agente_investigador
from agentes.redactor import agente_redactor
from agentes.revisor import agente_revisor
from agentes.supervisor import agente_supervisor

# ============================================================
# CONSTRUCCIÓN DEL GRAFO
# ============================================================

def crear_grafo():
    """Construye el sistema multiagente coordinado por un supervisor."""

    # 1. Creamos el grafo utilizando el estado compartido.
    grafo = StateGraph(EstadoAgentes)

    # 2. Registramos los agentes como nodos ejecutables.
    # RunnableLambda adapta nuestras funciones a la interfaz Runnable.
    grafo.add_node("supervisor", RunnableLambda(agente_supervisor))
    grafo.add_node("investigador", RunnableLambda(agente_investigador))
    grafo.add_node("redactor", RunnableLambda(agente_redactor))
    grafo.add_node("revisor", RunnableLambda(agente_revisor))

    # 3. El supervisor recibe el control al comenzar.
    grafo.add_edge(START, "supervisor")

    # 4. Cada trabajador devuelve el control al supervisor.
    for nombre in ("investigador", "redactor", "revisor"):
        grafo.add_edge(nombre, "supervisor")

    # 5. El supervisor decide qué agente debe actuar a continuación.
    grafo.add_conditional_edges(
        "supervisor",
        lambda estado: estado["siguiente"],
        {
            "investigador": "investigador",
            "redactor": "redactor",
            "revisor": "revisor",
            "FIN": END
        }
    )

    # 6. Compilamos el grafo para poder ejecutarlo.
    return grafo.compile()