from langchain_ollama import ChatOllama
import re
from estado import EstadoAgentes

# ============================================================
# CONFIGURACIÓN DEL MODELO
# ============================================================

llm = ChatOllama(
    model="llama3.1",
    temperature=0,
    num_predict=1000
)

# ============================================================
# INSTRUCCIONES DEL REDACTOR
# ============================================================

PROMPT_REDACTOR = """
Eres un redactor técnico especializado en informes objetivos.

- Si el tema contiene acusaciones o controversias, distingue
  claramente entre hechos documentados, opiniones y alegaciones.
- No presentes acusaciones como hechos demostrados.
- Si las fuentes son insuficientes, indícalo expresamente.
- No inventes ejemplos concretos para completar el informe.

Redacta un informe en español sobre el TEMA utilizando
exclusivamente la información de las FUENTES proporcionadas.

ESTRUCTURA OBLIGATORIA:

## Introducción
Explica el concepto y su contexto en 2 o 3 frases.

## Situación en España
Describe la situación específica en España en 2 o 3 frases.

## Ventajas y desafíos
Explica al menos una ventaja y un desafío real en 2 o 3 frases.

## Conclusión
Resume los hallazgos en 2 o 3 frases, sin introducir datos nuevos.

REGLAS DE CALIDAD:
- Utiliza exactamente los cuatro encabezados indicados.
- Escribe párrafos completos, sin listas numeradas.
- Evita repetir la misma información en distintas secciones.
- No copies literalmente enumeraciones de las fuentes.
- No inventes cifras, fechas, leyes ni declaraciones.
- No afirmes que algo es seguro, renovable, obligatorio o aprobado
  si las fuentes no lo respaldan claramente.
- Distingue entre hechos, opiniones, propuestas y previsiones.
- Si las fuentes discrepan, explica brevemente la discrepancia.
- No presentes previsiones antiguas como hechos actuales.
- Si no existe información suficiente sobre España, indícalo.
- Incluye citas numéricas [1], [2], etc. para respaldar los datos.
- Utiliza únicamente números de fuentes proporcionadas.
- No añadas un título general ni secciones adicionales.
- Termina la conclusión con una frase completa.
- Devuelve únicamente el informe en Markdown.

ANTES DE RESPONDER, COMPRUEBA:
- ¿Las cuatro secciones están completas?
- ¿Hay ventajas y desafíos, no solo ventajas?
- ¿Las afirmaciones importantes tienen fuentes?
- ¿Hay repeticiones o contradicciones?
- ¿La conclusión termina correctamente?

CORRECCIONES DEL REVISOR:
{cambios}

TEMA:
{tema}

FUENTES:
{fuentes}
"""

# ============================================================
# AGENTE REDACTOR
# ============================================================

def comprobar_citas(borrador: str) -> list[str]:
    """Identifica las secciones del informe que no tienen citas."""

    secciones = [
        "Introducción",
        "Situación en España",
        "Ventajas y desafíos",
        "Conclusión"
    ]

    sin_citas = []

    for seccion in secciones:
        patron = (
            rf"^##\s+{re.escape(seccion)}\s*$"
            rf"(.*?)(?=^##\s+|\Z)"
        )

        coincidencia = re.search(
            patron,
            borrador,
            re.MULTILINE | re.IGNORECASE | re.DOTALL
        )

        if coincidencia and not re.search(
            r"\[\d+\]",
            coincidencia.group(1)
        ):
            sin_citas.append(seccion)

    return sin_citas


def agente_redactor(estado: EstadoAgentes) -> dict:
    """Redacta un informe utilizando las fuentes del investigador."""

    print("\n[REDACTOR] Preparando el informe...")

    fuentes = estado.get("fuentes", [])

    if not fuentes:
        print("[REDACTOR] No hay fuentes disponibles.")

        return {
            "borrador": "",
            "historial": estado.get("historial", []) + [
                "REDACTOR · Sin fuentes disponibles"
            ]
        }

    # 1. Preparamos las fuentes numeradas para que el LLM pueda citarlas.
    texto_fuentes = "\n\n".join(
        f"[{numero}] {fuente['titulo']}\n"
        f"URL: {fuente['url']}\n"
        f"Contenido: {fuente['descripcion'][:1200]}"
        for numero, fuente in enumerate(fuentes, start=1)
    )

    # 2. Recuperamos los cambios solicitados por el revisor.
    revision = estado.get("revision")

    cambios = ""

    if revision and not revision["aprobado"]:
        cambios = (
            "El revisor ha solicitado las siguientes correcciones:\n"
            f"{revision['cambios']}\n"
            "Corrige el informe teniendo en cuenta estas indicaciones."
        )

        print("[REDACTOR] Aplicando correcciones del revisor.")

    # 3. Construimos el prompt con el tema, las fuentes y las correcciones.
    prompt = PROMPT_REDACTOR.format(
        tema=estado["tema"],
        fuentes=texto_fuentes,
        cambios=cambios
    )

    # 4. Ollama genera el informe.
    respuesta = llm.invoke(prompt)

    # Extraemos el texto de la respuesta.
    contenido = respuesta.content

    if isinstance(contenido, str):
        borrador = contenido.strip()
    else:
        borrador = "\n".join(
            bloque if isinstance(bloque, str) else str(bloque.get("text", ""))
            for bloque in contenido
        ).strip()

    print("[REDACTOR] Informe generado correctamente.")

    secciones_sin_citas = comprobar_citas(borrador)

    if secciones_sin_citas:
        print(
            "[REDACTOR] Secciones sin citas: "
            + ", ".join(secciones_sin_citas)
        )

    # 5. Registramos si hemos generado una corrección.
    reescrituras = estado.get("reescrituras", 0)

    if cambios:
        reescrituras += 1

    return {
        "borrador": borrador,
        "revision": None,
        "reescrituras": reescrituras,
        "llamadas_llm": estado.get("llamadas_llm", 0) + 1,
        "historial": estado.get("historial", []) + [
            f"REDACTOR · Informe generado ({len(borrador.split())} palabras)"
        ]
    }
