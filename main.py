import re
import time
import unicodedata

from datetime import datetime
from pathlib import Path

from estado import EstadoAgentes
from grafo import crear_grafo

# ============================================================
# CONFIGURACIÓN
# ============================================================

CARPETA_SALIDAS = Path(__file__).resolve().parent / "salidas"
CARPETA_SALIDAS.mkdir(parents=True, exist_ok=True)

# ============================================================
# NOMBRES DE ARCHIVOS
# ============================================================

def limpiar_nombre(tema: str) -> str:
    """Convierte el tema en un nombre válido para guardar archivos."""

    # Eliminamos tildes y otros caracteres diacríticos.
    texto = unicodedata.normalize("NFKD", tema)
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )

    # Sustituimos espacios y símbolos por guiones bajos.
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto.lower())

    return texto.strip("_")[:60] or "informe"


def guardar_informe(tema: str, informe: str) -> Path:
    """Guarda un informe sin sobrescribir los anteriores."""

    # Incluimos microsegundos para generar nombres únicos.
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    nombre = limpiar_nombre(tema)

    ruta = CARPETA_SALIDAS / f"{fecha}_{nombre}.md"

    # El modo 'x' impide sobrescribir un archivo existente.
    ruta.open("x", encoding="utf-8").write(informe)

    return ruta


# ============================================================
# GENERACIÓN DE INFORMES
# ============================================================

def generar_informe(tema: str, grafo) -> None:
    """Ejecuta los agentes y muestra el resultado de la investigación."""

    print("\n" + "=" * 60)
    print(f"GENERANDO INFORME: {tema}")
    print("=" * 60)

    # Cada consulta comienza con un estado completamente nuevo.
    estado_inicial: EstadoAgentes = {
        "tema": tema,
        "fuentes": [],
        "borrador": "",
        "revision": None,
        "siguiente": "",
        "turnos": 0,
        "reescrituras": 0,
        "historial": [],
        "llamadas_llm": 0
    }

    inicio = time.perf_counter()

    # Ejecutamos el sistema multiagente.
    resultado = grafo.invoke(
        estado_inicial,
        config={"recursion_limit": 30}
    )

    duracion = round(time.perf_counter() - inicio, 2)

    # Recuperamos los resultados del estado compartido.
    fuentes = resultado.get("fuentes", [])
    borrador = resultado.get("borrador", "")
    revision = resultado.get("revision")

    # ========================================================
    # FUENTES
    # ========================================================

    print("\n" + "=" * 60)
    print(f"FUENTES ENCONTRADAS: {len(fuentes)}")
    print("=" * 60)

    for numero, fuente in enumerate(fuentes, start=1):
        print(f"\n[{numero}] {fuente['titulo']}")
        print(f"URL: {fuente['url']}")

    # ========================================================
    # INFORME
    # ========================================================

    print("\n" + "=" * 60)
    print("INFORME FINAL")
    print("=" * 60)

    print(borrador or "No se pudo generar el informe.")

    # ========================================================
    # REVISIÓN
    # ========================================================

    print("\n" + "=" * 60)
    print("RESULTADO DE LA REVISIÓN")
    print("=" * 60)

    if revision:
        aprobado = revision["aprobado"]

        print("Estado:", "APROBADO" if aprobado else "NO APROBADO")

        if revision["cambios"]:
            print(f"Observaciones: {revision['cambios']}")
    else:
        print("El informe no ha sido revisado.")

    # ========================================================
    # MÉTRICAS
    # ========================================================

    print("\n" + "=" * 60)
    print("MÉTRICAS")
    print("=" * 60)

    print(f"Llamadas al LLM: {resultado.get('llamadas_llm', 0)}")
    print(f"Turnos del supervisor: {resultado.get('turnos', 0)}")
    print(f"Reescrituras: {resultado.get('reescrituras', 0)}")
    print(f"Tiempo total: {duracion} segundos")

    # ========================================================
    # HISTORIAL
    # ========================================================

    print("\n" + "=" * 60)
    print("HISTORIAL DEL EQUIPO")
    print("=" * 60)

    for evento in resultado.get("historial", []):
        print(f"- {evento}")

    # ========================================================
    # GUARDADO
    # ========================================================

    # Guardamos todos los informes generados, incluso si
    # el revisor solicita cambios y no llega a aprobarlos.
    if borrador:
        ruta = guardar_informe(tema, borrador)

        print(f"\n[ARCHIVO] Informe guardado en: {ruta}")

        if revision and not revision["aprobado"]:
            print(
                "[AVISO] El informe se ha guardado, "
                "pero no ha superado la revisión."
            )


# ============================================================
# CHAT INTERACTIVO
# ============================================================

def main():
    """Permite generar varios informes desde una misma sesión."""

    print("=" * 60)
    print("P14 - ASISTENTE MULTIAGENTE")
    print("=" * 60)

    print("\nEscribe un tema para generar un informe.")
    print("Escribe 'salir' para cerrar el programa.")

    # Compilamos el grafo una sola vez.
    grafo = crear_grafo()

    while True:
        try:
            tema = input("\nTú: ").strip()

            # Terminamos la conversación cuando lo solicita el usuario.
            if tema.lower() in ("salir", "exit"):
                print("\n¡Hasta pronto!")
                break

            # Ignoramos entradas vacías.
            if not tema:
                print("[SISTEMA] Introduce un tema válido.")
                continue

            generar_informe(tema, grafo)

            print("\n[SISTEMA] Puedes solicitar otro informe.")

        except (KeyboardInterrupt, EOFError):
            print("\n[SISTEMA] Sesión finalizada.")
            break

        except Exception as error:
            # Un fallo en una consulta no cierra todo el chat.
            print(f"\n[ERROR] No se pudo completar el informe: {error}")
            print("[SISTEMA] Puedes intentarlo de nuevo.")


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()