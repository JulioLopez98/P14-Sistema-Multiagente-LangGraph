from estado import EstadoAgentes, Fuente

from herramientas.busqueda_web import buscar_informacion, extraer_contenido
from herramientas.cache_fuentes import cargar_fuentes, guardar_fuentes

# ============================================================
# AGENTE INVESTIGADOR
# ============================================================

def agente_investigador(estado: EstadoAgentes) -> dict:
    """Busca información sobre el tema y la comparte con los agentes."""

    tema = estado["tema"]

    print(f"\n[INVESTIGADOR] Investigando: {tema}")

    # 1. Comprobamos si ya tenemos fuentes guardadas.
    fuentes_cache = cargar_fuentes(tema)

    if fuentes_cache:
        print("[INVESTIGADOR] Utilizando fuentes de la caché.")

        return {
            "fuentes": fuentes_cache,
            "historial": estado.get("historial", []) + [
                f"INVESTIGADOR · {len(fuentes_cache)} fuentes recuperadas de caché"
            ]
        }

    # 2. Buscamos nuevas fuentes en internet.
    resultados = buscar_informacion(tema, max_resultados=6)

    fuentes: list[Fuente] = []

    for resultado in resultados:

        # Recuperamos el contenido de la página.
        contenido = extraer_contenido(resultado["url"])

        # Descartamos páginas sin suficiente información.
        if len(contenido.strip()) < 500:
            continue

        fuentes.append({
            "titulo": resultado["titulo"],
            "url": resultado["url"],
            "descripcion": contenido
        })

    # 3. Guardamos las fuentes para futuras ejecuciones.
    if fuentes:
        guardar_fuentes(tema, fuentes)

    print(f"[INVESTIGADOR] Fuentes disponibles: {len(fuentes)}")

    return {
        "fuentes": fuentes,
        "historial": estado.get("historial", []) + [
            f"INVESTIGADOR · {len(fuentes)} fuentes encontradas"
        ]
    }
