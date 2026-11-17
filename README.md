# P14 — Sistema Multiagente con LangGraph

Sistema de generación de informes en español mediante un equipo de agentes coordinados por **LangGraph** y modelos locales ejecutados con **Ollama**.

El usuario introduce un tema en una conversación por terminal. El sistema investiga, redacta y revisa un informe, muestra el resultado y lo guarda en formato Markdown. Permite generar varios informes durante una misma sesión.

## Características

- **Supervisor:** decide qué agente debe intervenir y valida la decisión del modelo con reglas de Python.
- **Investigador:** busca fuentes web y reutiliza resultados almacenados en caché.
- **Redactor:** elabora un informe estructurado con referencias numéricas a las fuentes.
- **Revisor:** evalúa la calidad y aplica comprobaciones automáticas de estructura y citas.
- **Control del flujo:** máximo de una reescritura y límite de turnos para evitar bucles.
- **Chat por terminal:** admite consultas sucesivas hasta escribir `salir`.
- **Historial y métricas:** muestra los pasos ejecutados, llamadas al modelo, reescrituras y tiempo.
- **Salidas independientes:** cada informe se guarda como un archivo `.md` diferente en `salidas/`.

## Arquitectura

```text
                  ┌──────────────────┐
          START → │    Supervisor    │ ──→ FIN
                  └────────┬─────────┘
                           │ decide
                 ┌─────────┼─────────┐
                 ▼         ▼         ▼
           Investigador  Redactor  Revisor
                 │         │         │
                 └─────────┴─────────┘
                           │
                  Vuelven al supervisor
```

Todos los agentes comparten un estado definido en `estado.py`, que incluye tema, fuentes, borrador, revisión, contadores e historial. Las transiciones se configuran en `grafo.py`.

## Estructura del proyecto

```text
P14-Sistema-Multiagente-LangGraph/
├── agentes/
│   ├── investigador.py
│   ├── redactor.py
│   ├── revisor.py
│   └── supervisor.py
├── herramientas/
│   ├── busqueda_web.py
│   └── cache_fuentes.py
├── salidas/                # Informes Markdown generados
├── estado.py               # Estado compartido
├── grafo.py                # Nodos y transiciones LangGraph
├── main.py                 # Interfaz interactiva por terminal
├── requirements.txt
├── .gitignore
└── README.md
```

La carpeta `cache/` se crea/utiliza durante la ejecución y no necesita incluirse en el repositorio.

## Requisitos

- Python 3.10 o superior.
- [Ollama](https://ollama.com/) instalado y en ejecución.
- Modelo local `llama3.1` descargado.
- Conexión a Internet para investigar temas no presentes en caché.

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/JulioLopez98/P14-Sistema-Multiagente-LangGraph.git
cd P14-Sistema-Multiagente-LangGraph
```

> La URL anterior será válida cuando se cree el repositorio con ese nombre.

Crear y activar un entorno virtual en Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
pip install -r requirements.txt
```

Descargar el modelo:

```powershell
ollama pull llama3.1
```

Comprobar que Ollama está ejecutándose antes de iniciar el programa.

## Uso

```powershell
python main.py
```

Ejemplo de sesión:

```text
P14 - ASISTENTE MULTIAGENTE

Tú: ¿Cuáles son las aplicaciones y desafíos de la IA en el diagnóstico médico en España?
[SUPERVISOR] Siguiente paso: investigador
[INVESTIGADOR] Investigando...
[SUPERVISOR] Siguiente paso: redactor
[REDACTOR] Preparando el informe...
[SUPERVISOR] Siguiente paso: revisor
[REVISOR] Evaluando el informe...
...
[ARCHIVO] Informe guardado en: salidas/...

Tú: salir
```

Cada nueva consulta inicia un estado independiente. El programa conserva los informes anteriores y utiliza nombres de archivo con marca temporal para evitar sobrescrituras.

## Formato del informe

Los informes incluyen estas secciones:

1. Introducción
2. Situación en España
3. Ventajas y desafíos
4. Conclusión

El texto puede incorporar referencias como `[1]`, `[2]`, etc., que corresponden a las fuentes mostradas en la ejecución.

## Informes de ejemplo

La carpeta [`salidas/`](salidas/) contiene ejemplos generados por el sistema. Se recomienda incluir dos casos representativos:

- Inteligencia artificial aplicada al diagnóstico médico en España.
- Energía solar fotovoltaica en España.

Los archivos se generan al ejecutar el programa; **no se incluyen informes ficticios** en este proyecto.

## Límites y consideraciones

- La aprobación del revisor significa que el informe superó los controles implementados; **no equivale a una auditoría factual independiente**.
- El modelo puede omitir citas, interpretar mal una fuente o reproducir información desactualizada.
- La búsqueda depende de la disponibilidad y calidad de las páginas recuperadas.
- Si el informe no supera la revisión, también se guarda, y la terminal muestra una advertencia.
- Los límites de turnos y reescrituras impiden ciclos indefinidos.

## Tecnologías

- **Python** — lógica de la aplicación.
- **LangGraph** — orquestación del grafo multiagente.
- **LangChain / langchain-ollama** — integración con el modelo.
- **Ollama (`llama3.1`)** — inferencia local.
- **DuckDuckGo Search** — recuperación de fuentes web.
- **Markdown** — formato de los informes generados.

## Objetivo académico

Proyecto práctico del Máster AI Engineer, centrado en el diseño de agentes especializados, la coordinación mediante un supervisor, el estado compartido y los flujos de revisión con LangGraph.
