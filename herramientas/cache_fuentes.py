
import hashlib
import json
from pathlib import Path

from estado import Fuente


# ============================================================
# CONFIGURACIÓN DE LA CACHÉ
# ============================================================

# Guardamos los archivos dentro de la carpeta del proyecto.
CARPETA_CACHE = Path(__file__).resolve().parent.parent / "cache"


def obtener_ruta_cache(tema: str) -> Path:
    """Genera un nombre de archivo único a partir del tema."""

    # El hash evita problemas con espacios, tildes y caracteres especiales.
    identificador = hashlib.sha256(
        tema.strip().casefold().encode("utf-8")
    ).hexdigest()[:16]

    return CARPETA_CACHE / f"fuentes_{identificador}.json"


# ============================================================
# GUARDAR Y CARGAR FUENTES
# ============================================================

def guardar_fuentes(tema: str, fuentes: list[Fuente]) -> None:
    """Guarda las fuentes recuperadas en un archivo JSON."""

    CARPETA_CACHE.mkdir(parents=True, exist_ok=True)

    ruta = obtener_ruta_cache(tema)

    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(fuentes, archivo, ensure_ascii=False, indent=2)

    print(f"[CACHÉ] Guardadas {len(fuentes)} fuentes en {ruta.name}")


def cargar_fuentes(tema: str) -> list[Fuente]:
    """Recupera las fuentes guardadas para un tema."""

    ruta = obtener_ruta_cache(tema)

    if not ruta.exists():
        print("[CACHÉ] No hay fuentes guardadas para este tema.")
        return []

    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        # Comprobamos la estructura básica antes de utilizarla.
        if not isinstance(datos, list):
            raise ValueError("El archivo no contiene una lista.")

        for fuente in datos:
            if (
                not isinstance(fuente, dict)
                or not all(
                    isinstance(fuente.get(campo), str)
                    for campo in ("titulo", "url", "descripcion")
                )
                or not fuente["descripcion"].strip()
            ):
                raise ValueError("Se encontró una fuente inválida.")

        print(f"[CACHÉ] Recuperadas {len(datos)} fuentes guardadas.")

        return datos

    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"[CACHÉ] No se pudo cargar el archivo: {error}")
        return []