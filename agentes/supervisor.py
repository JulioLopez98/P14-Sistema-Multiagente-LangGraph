
import json

from langchain_ollama import ChatOllama

from estado import EstadoAgentes


# ============================================================
# CONFIGURACIÓN
# ============================================================

llm = ChatOllama(
    model="llama3.1",
    temperature=0,
    format="json",
    num_predict=150
)

MAX_TURNOS = 8
MAX_REESCRITURAS = 1


# ============================================================
# INSTRUCCIONES DEL SUPERVISOR
# ============================================================

PROMPT_SUPERVISOR = """
Eres el supervisor de un equipo de tres agentes:

- investigador: busca información sobre el tema.
- redactor: escribe un informe utilizando las fuentes.
- revisor: comprueba el informe y solicita correcciones.

Tu trabajo es decidir qué agente debe actuar a continuación.

REGLAS:
- Si no hay fuentes, debe actuar el investigador.
- Si hay fuentes pero no existe un borrador, debe actuar el redactor.
- Si existe un borrador pendiente de revisión, debe actuar el revisor.
- Si el revisor solicita cambios y quedan reescrituras, debe actuar el redactor.
- Si el informe está aprobado, debes finalizar.
- Si se ha alcanzado el límite de reescrituras, debes finalizar.

Responde únicamente con un JSON válido:
{{"siguiente": "investigador", "motivo": "Explicación breve"}}

El campo "siguiente" solo puede ser:
investigador, redactor, revisor o FIN.

TEMA:
{tema}

ESTADO:
- Fuentes disponibles: {fuentes}
- Existe borrador: {borrador}
- Revisión: {revision}
- Reescrituras realizadas: {reescrituras}
- Reescrituras máximas: {max_reescrituras}
"""


# ============================================================
# REGLAS DE SEGURIDAD DEL FLUJO
# ============================================================

def decidir_por_reglas(estado: EstadoAgentes) -> str:
    """Determina el siguiente agente permitido según el estado."""

    # 1. Sin fuentes no podemos elaborar el informe.
    if not estado.get("fuentes"):
        return "investigador"

    # 2. Si tenemos fuentes, pero no informe, debemos redactarlo.
    if not estado.get("borrador"):
        return "redactor"

    revision = estado.get("revision")

    # 3. Si el informe todavía no se ha revisado, pasa al revisor.
    if revision is None:
        return "revisor"

    # 4. Si el revisor solicita cambios, comprobamos el límite.
    if not revision["aprobado"]:
        if estado.get("reescrituras", 0) < MAX_REESCRITURAS:
            return "redactor"

    # 5. Finalizamos si está aprobado o se agotaron las correcciones.
    return "FIN"


# ============================================================
# AGENTE SUPERVISOR
# ============================================================

def agente_supervisor(estado: EstadoAgentes) -> dict:
    """Selecciona el siguiente agente y valida la decisión del LLM."""

    print("\n[SUPERVISOR] Analizando el estado del equipo...")

    turnos = estado.get("turnos", 0) + 1

    # 1. Evitamos ejecuciones indefinidas.
    if turnos > MAX_TURNOS:
        print("[SUPERVISOR] Límite de turnos alcanzado.")

        return {
            "siguiente": "FIN",
            "turnos": turnos,
            "historial": estado.get("historial", []) + [
                "SUPERVISOR · Límite de turnos alcanzado"
            ]
        }

    # 2. Preparamos un resumen del estado para Ollama.
    revision = estado.get("revision")

    if revision is None:
        estado_revision = "Pendiente"
    elif revision["aprobado"]:
        estado_revision = "Aprobado"
    else:
        estado_revision = f"Solicita cambios: {revision['cambios']}"

    prompt = PROMPT_SUPERVISOR.format(
        tema=estado["tema"],
        fuentes=len(estado.get("fuentes", [])),
        borrador=bool(estado.get("borrador")),
        revision=estado_revision,
        reescrituras=estado.get("reescrituras", 0),
        max_reescrituras=MAX_REESCRITURAS
    )

    # 3. El LLM propone el siguiente agente mediante un JSON.
    try:
        respuesta = llm.invoke(prompt)

        if not isinstance(respuesta.content, str):
            raise ValueError("El supervisor no devolvió texto JSON.")

        decision = json.loads(respuesta.content)

        if not isinstance(decision, dict):
            raise ValueError("La respuesta JSON debe ser un objeto.")

        siguiente = decision.get("siguiente", "")

    except (ValueError, TypeError) as error:
        siguiente = ""
        print(f"[SUPERVISOR] Respuesta no válida: {error}")

    # 4. Python comprueba que la decisión sea coherente.
    siguiente_permitido = decidir_por_reglas(estado)

    if siguiente != siguiente_permitido:
        print(
            f"[SUPERVISOR] Decisión corregida: "
            f"{siguiente} -> {siguiente_permitido}"
        )

        siguiente = siguiente_permitido

    # 5. Generamos un motivo basado en el estado real.
    # No dependemos de las explicaciones que pueda inventar Ollama.
    if siguiente == "investigador":
        motivo = "Es necesario recuperar fuentes."

    elif siguiente == "redactor":
        if revision and not revision["aprobado"]:
            motivo = "El revisor ha solicitado correcciones."
        else:
            motivo = "Hay fuentes disponibles, pero falta el informe."

    elif siguiente == "revisor":
        motivo = "El informe está pendiente de revisión."

    elif revision and revision["aprobado"]:
        motivo = "El informe ha sido aprobado."

    elif revision and not revision["aprobado"]:
        motivo = "Se ha alcanzado el límite de reescrituras."

    else:
        motivo = "El sistema ha finalizado."

    print(f"[SUPERVISOR] Siguiente paso: {siguiente}")
    print(f"[SUPERVISOR] Motivo: {motivo}")

    # 6. Actualizamos la memoria compartida del equipo.
    return {
        "siguiente": siguiente,
        "turnos": turnos,
        "llamadas_llm": estado.get("llamadas_llm", 0) + 1,
        "historial": estado.get("historial", []) + [
            f"SUPERVISOR · {siguiente} ({motivo})"
        ]
    }