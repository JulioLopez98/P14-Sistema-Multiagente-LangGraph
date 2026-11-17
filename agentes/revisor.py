import json
import re

from langchain_ollama import ChatOllama

from estado import EstadoAgentes

# ============================================================
# CONFIGURACIÓN
# ============================================================

llm = ChatOllama(
    model="llama3.1",
    temperature=0,
    format="json",
    num_predict=200
)

SECCIONES = [
    "Introducción",
    "Situación en España",
    "Ventajas y desafíos",
    "Conclusión"
]


# ============================================================
# INSTRUCCIONES DEL REVISOR
# ============================================================

PROMPT_REVISOR = """
Eres un revisor de calidad de informes técnicos.

Evalúa el informe sobre el TEMA utilizando las FUENTES.

CRITERIOS DE REVISIÓN:
1. El informe responde al tema solicitado.
2. Las afirmaciones importantes están respaldadas por las fuentes.
3. No contiene contradicciones evidentes con las fuentes.
4. No repite innecesariamente las mismas ideas.
5. Distingue entre hechos, opiniones y previsiones.
6. La sección de ventajas y desafíos presenta ambos aspectos.
7. No contiene enumeraciones copiadas dentro de los párrafos.
8. La conclusión resume el informe sin introducir información nueva.
9. El lenguaje es claro, profesional y objetivo.

Si el informe cumple los criterios, responde:
{{"aprobado": true, "cambios": ""}}

Si necesita correcciones, responde:
{{"aprobado": false, "cambios": "Explica los problemas concretos que deben corregirse"}}

Responde exclusivamente con un objeto JSON válido.

TEMA:
{tema}

FUENTES:
{fuentes}

INFORME:
{borrador}
"""

# ============================================================
# AGENTE REVISOR
# ============================================================

def agente_revisor(estado: EstadoAgentes) -> dict:
    """Evalúa el informe y solicita correcciones cuando es necesario."""

    print("\n[REVISOR] Evaluando el informe...")

    borrador = estado.get("borrador", "")
    fuentes = estado.get("fuentes", [])

    if not borrador:
        return {
            "revision": {
                "aprobado": False,
                "cambios": "No existe un informe para revisar."
            },
            "historial": estado.get("historial", []) + [
                "REVISOR · No hay informe"
            ]
        }

    # 1. Comprobamos mediante Python las secciones obligatorias.
    secciones_faltantes = [
        seccion
        for seccion in SECCIONES
        if not re.search(
            rf"^##\s+{re.escape(seccion)}\s*$",
            borrador,
            re.MULTILINE | re.IGNORECASE
        )
    ]

    # 2. Preparamos las fuentes para que Ollama revise el contenido.
    texto_fuentes = "\n\n".join(
        f"[{numero}] {fuente['titulo']}\n"
        f"{fuente['descripcion'][:800]}"
        for numero, fuente in enumerate(fuentes, start=1)
    )

    prompt = PROMPT_REVISOR.format(
        tema=estado["tema"],
        fuentes=texto_fuentes,
        borrador=borrador
    )

    # 3. Ollama devuelve una decisión en formato JSON.
    try:
        respuesta = llm.invoke(prompt)
        contenido = respuesta.content

        if not isinstance(contenido, str):
            raise ValueError("El modelo no devolvió texto JSON.")

        evaluacion = json.loads(contenido)

        aprobado_llm = evaluacion.get("aprobado") is True
        cambios_llm = str(evaluacion.get("cambios", ""))

    except (ValueError, TypeError, json.JSONDecodeError) as error:
        aprobado_llm = False
        cambios_llm = f"No se pudo interpretar la revisión: {error}"

    
    # 4. Comprobamos las citas del informe.
    citas = [
        int(numero)
        for numero in re.findall(r"\[(\d+)\]", borrador)
    ]

    citas_validas = bool(citas) and all(
        1 <= numero <= len(fuentes)
        for numero in citas
    )

    
    # Identificamos qué secciones no contienen citas.
    secciones_sin_citas = []
    for seccion in SECCIONES:
        patron = (
            rf"^##\s+{re.escape(seccion)}\s*$"
            rf"(.*?)(?=^##\s+|\Z)"
        )

        coincidencia = re.search(
            patron,
            borrador,
            re.MULTILINE | re.IGNORECASE | re.DOTALL
        )

        # Comprobamos las citas únicamente dentro de la sección.
        if coincidencia:
            citas_seccion = re.findall(
                r"\[(\d+)\]",
                coincidencia.group(1)
            )

            if not citas_seccion:
                secciones_sin_citas.append(seccion)

    citas_por_seccion = not secciones_sin_citas

    # 5. Combinamos la evaluación de Ollama con las reglas de Python.
    problemas = []

    if secciones_faltantes:
        problemas.append(
            f"Faltan secciones: {', '.join(secciones_faltantes)}."
        )

    if not citas_validas:
        problemas.append("Faltan citas o existen referencias incorrectas.")

    if not aprobado_llm:
        problemas.append(cambios_llm or "El contenido necesita revisión.")

    aprobado = not problemas
    cambios = " ".join(problemas)

    print(
        "[REVISOR] Informe aprobado."
        if aprobado
        else f"[REVISOR] Correcciones necesarias: {cambios}"
    )

    return {
        "revision": {
            "aprobado": aprobado,
            "cambios": cambios
        },
        "llamadas_llm": estado.get("llamadas_llm", 0) + 1,
        "historial": estado.get("historial", []) + [
            "REVISOR · Aprobado" if aprobado else "REVISOR · Solicita cambios"
        ]
    }