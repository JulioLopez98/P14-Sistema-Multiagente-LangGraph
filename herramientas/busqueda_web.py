import time
import requests

from bs4 import BeautifulSoup
from ddgs import DDGS
from ddgs.exceptions import DDGSException

from estado import Fuente

# ============================================================
# 1. LIMPIEZA DE TEXTOS
# ============================================================

def limpiar_texto(texto: str, max_caracteres: int) -> str:
    """
    Elimina espacios innecesarios y limita la longitud del texto.

    Se utiliza para limpiar los títulos y las descripciones
    que devuelve el buscador.
    """

    # split() separa las palabras y join() las une con un único espacio.
    texto = " ".join(texto.split())

    # Recortamos los textos demasiado largos sin cortar la última palabra.
    if len(texto) > max_caracteres:
        texto = texto[:max_caracteres].rsplit(" ", 1)[0] + "..."

    return texto


# ============================================================
# 2. BÚSQUEDA DE INFORMACIÓN
# ============================================================

def buscar_informacion(consulta: str, max_resultados: int = 6) -> list[Fuente]:
    """
    Busca información en Internet utilizando DDGS.

    Prueba varias consultas si no consigue suficientes fuentes
    y devuelve resultados limpios, completos y sin URLs repetidas.
    """

    # Generamos variantes del tema sin cambiar su significado.
    consultas = [
        consulta,
        f'"{consulta}"',
        f"{consulta} ejemplos experiencias empresas"
    ]

    # Almacenamos las fuentes y las URLs para evitar duplicados.
    fuentes: list[Fuente] = []
    urls_encontradas: set[str] = set()

    # enumerate() permite obtener el número de intento y la consulta.
    for intento, consulta_actual in enumerate(consultas, start=1):

        print(f"[BÚSQUEDA] Intento {intento}: {consulta_actual}")

        try:
            # DDGS realiza la búsqueda; timeout limita el tiempo de espera.
            with DDGS(timeout=20) as buscador:
                resultados = buscador.text(
                    consulta_actual,
                    max_results=max_resultados,
                    backend="auto"
                )

            # Procesamos cada resultado devuelto por el buscador.
            for resultado in resultados:

                # get() obtiene un campo o devuelve "" si no existe.
                titulo = limpiar_texto(resultado.get("title", ""), 120)
                url = resultado.get("href", "").strip()
                descripcion = limpiar_texto(resultado.get("body", ""), 400)

                # Descartamos resultados incompletos o repetidos.
                if not titulo or not url or not descripcion:
                    continue

                if url in urls_encontradas:
                    continue

                # Guardamos la fuente con la estructura definida en estado.py.
                fuentes.append({
                    "titulo": titulo,
                    "url": url,
                    "descripcion": descripcion
                })

                # Un set permite comprobar rápidamente si una URL ya existe.
                urls_encontradas.add(url)

                # Dejamos de recopilar cuando alcanzamos el límite.
                if len(fuentes) >= max_resultados:
                    break

        # Capturamos los errores del buscador sin detener el programa.
        except DDGSException as error:
            print(f"[BÚSQUEDA] Falló el intento {intento}: {error}")

        # Si ya tenemos suficientes fuentes, no hacemos más búsquedas.
        if len(fuentes) >= max_resultados:
            break

        # Introducimos una pausa antes de la siguiente consulta.
        if intento < len(consultas):
            print("[BÚSQUEDA] Esperando 3 segundos...")
            time.sleep(3)

    print(f"[BÚSQUEDA] Fuentes recuperadas: {len(fuentes)}")

    return fuentes

# ============================================================
# 3. EXTRACCIÓN DE CONTENIDO WEB
# ============================================================

def extraer_contenido(url: str, max_caracteres: int = 3000) -> str:
    """
    Descarga una página web y extrae su contenido textual.

    Elimina elementos innecesarios y limita la cantidad
    de texto que posteriormente recibirá el redactor.
    """

    print(f"[EXTRACCIÓN] Leyendo: {url}")

    try:
        # Descargamos el HTML con un tiempo máximo de espera.
        respuesta = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "P14-AgenteInvestigador/1.0"}
        )

        # Lanza una excepción si la respuesta HTTP indica un error.
        respuesta.raise_for_status()

        # BeautifulSoup convierte el HTML en una estructura navegable.
        sopa = BeautifulSoup(respuesta.text, "html.parser")

        # Eliminamos elementos que normalmente no aportan información.
        for elemento in sopa(["script", "style", "nav", "footer", "header"]):
            elemento.decompose()

        # Priorizamos el artículo principal; si no existe, usamos main o body.
        contenido = (
            sopa.find("article")
            or sopa.find("main")
            or sopa.body
        )

        if contenido is None:
            print("[EXTRACCIÓN] No se encontró contenido.")
            return ""

        # get_text() extrae texto y strip=True elimina espacios sobrantes.
        texto = contenido.get_text(separator=" ", strip=True)

        # Reutilizamos nuestra función para limpiar y recortar el texto.
        texto = limpiar_texto(texto, max_caracteres)

        print(f"[EXTRACCIÓN] Recuperados {len(texto)} caracteres.")

        return texto

    except requests.RequestException as error:
        print(f"[EXTRACCIÓN] Error al acceder a la página: {error}")
        return ""

