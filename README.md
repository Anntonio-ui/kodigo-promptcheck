# PromptCheck

**KODIGO · FastAPI & Agent Skills Integration**  
William Antonio Hernández Iraheta

PromptCheck analiza borradores de prompts en español. La API cuenta caracteres y palabras. Cuando se solicita una revisión, el agente local aplica una skill para detectar señales de objetivo, audiencia y formato, y sugiere qué añadir cuando falta un marcador.

## Ejecutar en Windows desde PowerShell

Abre esta carpeta en VS Code con `code .` y ejecuta lo siguiente desde su terminal. Requiere Python 3.10 o superior. Los comandos usan el Python del entorno virtual directamente.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

En Linux o macOS, crea el entorno con `python3 -m venv .venv` y ejecuta esos mismos módulos con `.venv/bin/python`.

Abre [Swagger UI](http://127.0.0.1:8000/docs), selecciona **POST /api/v1/prompts/analizar** y pulsa **Try it out**. El esquema OpenAPI también está disponible en [openapi.json](http://127.0.0.1:8000/openapi.json).

## Demostración de la skill

Ejecuta las dos solicitudes en Swagger para comparar la misma entrada:

**Análisis básico**

```json
{"prompt": "Resume el capítulo 2.", "modo": "analisis"}
```

**Revisión con la skill**

```json
{"prompt": "Resume el capítulo 2.", "modo": "revision"}
```

| Campo | Análisis | Revisión |
| --- | --- | --- |
| `caracteres` | 21 | 21 |
| `palabras` | 4 | 4 |
| `skill_aplicada` | `null` | `auditar-prompts` |
| `estado` | `analizado` | `requiere_revision` |
| `hallazgos` | Lista vacía | Objetivo detectado. Faltan audiencia y formato, cada uno con su sugerencia. |

Para probar una revisión completa, envía `{"prompt":"Explica la fotosíntesis para principiantes en una tabla."}`. El modo predeterminado es `revision` y la respuesta tendrá estado `listo`. El campo `prompt` acepta texto de 1 a 3000 caracteres después de quitar espacios en los extremos. Un cuerpo inválido devuelve HTTP 422 con el detalle del error.

## Estructura y responsabilidades

| Archivo | Responsabilidad |
| --- | --- |
| `app/main.py` | Crea la aplicación, registra las rutas y carga la política al arrancar. |
| `app/routes.py` | Publica el endpoint y delega el procesamiento al agente. |
| `app/schemas.py` | Valida la entrada y define el contrato de respuesta. |
| `app/config.py` | Ubica la skill y su política dentro del proyecto. |
| `app/agent.py` | Selecciona el comportamiento según el modo y aplica los criterios en la revisión. |
| [SKILL.md](.github/skills/auditar-prompts/SKILL.md) | Define cuándo usar la skill, qué solicitud enviar y cómo interpretar el resultado. |
| [criterios.json](.github/skills/auditar-prompts/references/criterios.json) | Configura los marcadores y las sugerencias que utiliza el agente local. |

## Cómo se integra la skill

El archivo `SKILL.md` incluye los metadatos YAML `name` y `description` del [estándar Agent Skills](https://agentskills.io/specification). Su nombre coincide con el directorio. Un asistente compatible con skills de repositorio, con acceso a la API local, puede seguir ese procedimiento cuando se le pide revisar un borrador. Por ejemplo, la instrucción de demostración en el asistente es «Usa la skill auditar-prompts para revisar este borrador: Resume el capítulo 2.».

Al recibir `modo: revision`, el agente local ejecuta la política enlazada desde la skill. Si se edita `criterios.json` y se reinicia el servidor, cambian los hallazgos de revisión sin modificar las rutas ni el código del agente. La prueba con una política temporal verifica esta relación usando un criterio distinto, `idioma`.

El procesamiento local es determinista y funciona sin un proveedor de IA, claves ni conexión externa después de instalar las dependencias. El prompt se inspecciona como texto. La presencia de un marcador solo da una señal léxica, por lo que el estado `listo` indica que se reconocieron los criterios configurados.

## Pruebas y uso de IA

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

**Resultado verificado durante el desarrollo:** 6 pruebas correctas. La suite inicia Uvicorn y realiza peticiones HTTP reales. Cubre OpenAPI, la comparación con y sin skill, la revisión completa, coincidencias de palabras completas, entradas inválidas y el efecto de cambiar la política. La comprobación de un asistente externo se puede realizar con la instrucción de demostración anterior.

Se utilizó ChatGPT como apoyo para diseñar la estructura, generar la implementación inicial y proponer casos de prueba. La validación se hizo ejecutando la API y contrastando sus respuestas con resultados concretos. Entre las decisiones comprobadas:

- Se separaron los criterios de la skill del código de la ruta y se verificó que el agente responde a una política distinta.
- Se usaron límites de palabra para que «tableta» no active el marcador «tabla» y se comprobó ese caso por HTTP.
- Se compararon dos solicitudes con el mismo texto para medir qué cambios introduce la skill y se comprobaron errores 422 con entradas inválidas.
