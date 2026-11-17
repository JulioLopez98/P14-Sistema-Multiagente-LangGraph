from typing import TypedDict
from typing_extensions import Required

# ============================================================
# ESTRUCTURAS DE DATOS
# ============================================================

class Fuente(TypedDict):
    """Información recuperada de una página web."""

    titulo: str
    url: str
    descripcion: str


class Revision(TypedDict):
    """Resultado de la evaluación del revisor."""

    aprobado: bool
    cambios: str


# ============================================================
# ESTADO COMPARTIDO DE LANGGRAPH
# ============================================================

class EstadoAgentes(TypedDict, total=False):
    """Memoria compartida entre el supervisor y los agentes."""

    # Dato obligatorio para iniciar la investigación.
    tema: Required[str]

    # Información compartida entre los agentes.
    fuentes: list[Fuente]
    borrador: str
    revision: Revision | None

    # Control del flujo de trabajo.
    siguiente: str
    turnos: int
    reescrituras: int

    # Seguimiento de la ejecución.
    historial: list[str]
    llamadas_llm: int