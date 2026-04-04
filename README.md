# RAG Assistant
![Python](https://img.shields.io/badge/python-3670A0?style=flat&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B35?style=flat&logo=databricks&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=flat&logo=sqlite&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat&logo=nginx&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=python&logoColor=white)
![Azure](https://img.shields.io/badge/Azure_OpenAI-0089D6?style=flat&logo=microsoft-azure&logoColor=white)

Asistente virtual del Grupo Bancolombia que responda preguntas sobre productos, servicios y contenido publicado en la sección de personas del sitio web,utilizando una arquitectura RAG con un agente conversacional accesible mediante unainterfaz de chat.

---
## Nota:

> - **Sin costos** — La solución usa exclusivamente servicios gratuitos:
> - **GitHub Models** (Azure OpenAI) — gratuito con token de GitHub
> - **ChromaDB** — base vectorial local, sin costo
> - **Railway** — tier gratuito para los 3 microservicios
> - **GitHub Actions** — CI/CD gratuito para repositorios públicos
> - **Token de GitHub:** Genera uno en https://github.com/settings/tokens

---
## ¿Cómo funciona?

![Flujo RAG](docs/architecture/Flujo-consulta.drawio.png)


---
### Opciones de ejecución

| Opción | Descripción | Requisitos |
|---|---|---|
| **Sistema en producción** | Sistema desplegado en Railway | Solo abrir el link |
| **Docker local** | `docker-compose up --build` | Docker Desktop + token GitHub |
| **Local manual** | Ejecutar cada servicio por separado | Python 3.11 + Node.js 22 |

**URLs del sistema en producción:**
- 🌐 Frontend: https://frontend-production-1bed.up.railway.app
- 🤖 Agent API Docs: https://agent-production-065e.up.railway.app/docs
- 🔧 MCP Server: https://rag-assistant-production-bb17.up.railway.app/mcp



---
## Arquitectura

### C4 Nivel 1 — Contexto
![C4 Nivel 1](docs/architecture/c4-nivel1-contexto.drawio.png)

### C4 Nivel 2 — Contenedores
![C4 Nivel 2](docs/architecture/c4-nivel2-contenedores.drawio.png)

### C4 Nivel 3 — Componentes (Clean Architecture)
![C4 Nivel 3](docs/architecture/c4-nivel3-componentes.drawio.png)

---

## Microservicios

| Servicio | Tecnología | Puerto | Descripción |
|---|---|---|---|
| **Scraper** | Python · crawl4ai | batch | Crawling y procesamiento de bancolombia.com/personas |
| **MCP Server** | Python · FastMCP | 8000 | Servidor MCP con tools RAG y base vectorial |
| **Agent** | Python · LangGraph | 8001 | Agente conversacional cliente MCP |
| **Frontend** | React · TypeScript | 3000 | Interfaz de chat con historial y fuentes |

---
## Memoria del Agente — 3 niveles

El agente implementa una arquitectura de memoria en 3 niveles para mantener contexto conversacional:

| Tipo | Implementación | Persistencia | Alcance |
|---|---|---|---|
| **Corto plazo** | MemorySaver LangGraph (RAM) | Solo sesión activa | Mensajes del turno actual por `thread_id` |
| **Mediano plazo** | Resúmenes en SQLite | Entre sesiones | Contexto resumido — se genera automáticamente cuando una conversación supera 10 mensajes |
| **Largo plazo** | SQLite via SQLAlchemy | Permanente | Historial completo de todas las conversaciones persistido en disco |

### Justificación
- **Corto plazo** — LangGraph `MemorySaver` mantiene el hilo de la conversación activa sin overhead de base de datos
- **Mediano plazo** — Los resúmenes permiten al agente recordar conversaciones anteriores sin cargar todo el historial
- **Largo plazo** — SQLite dockerizable con volúmenes — migrable a PostgreSQL para producción sin cambiar el dominio (`MemoryRepository` es una interfaz)

### Memoria del Frontend
El frontend implementa persistencia del historial en **localStorage** del navegador:
- Máximo 20 conversaciones guardadas
- Cada conversación incluye mensajes, fuentes y metadatos
- Persiste entre reinicios del navegador
- El usuario puede navegar entre conversaciones anteriores desde el sidebar


---

## Stack tecnológico

| Componente | Tecnología | Justificación |
|---|---|---|
| Web Scraping | crawl4ai + playwright | Renderizado JavaScript nativo |
| Limpieza | trafilatura | Extrae solo contenido relevante |
| Embeddings | text-embedding-3-large (GitHub Models) | 3072d, multilingüe, supera sentence-transformers en MTEB |
| Base vectorial | ChromaDB | Local, sin costo, dockerizable, migrable a Qdrant/Pinecone |
| LLM | GPT-4o (GitHub Models / Azure OpenAI) | 128k contexto, razonamiento financiero en español |
| MCP Transport | Streamable HTTP + stdio | Producción y pruebas locales |
| Agente | LangGraph | Grafos de estado, memoria estructurada, tool orchestration |
| Frontend | React + TypeScript + Vite | Moderno, tipado, rápido |
| CI/CD | GitHub Actions | Lint + test + docker build en cada push |
| Despliegue | Railway | Tier gratuito, auto-deploy en cada push |

---

## Fundamentos teóricos aplicados

| Paper | Autores | Aplicación en este proyecto |
|---|---|---|
| [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) | Lewis et al., 2020 | Base teórica de la arquitectura RAG — retrieval semántico + generación con LLM |
| [MTEB: Massive Text Embedding Benchmark](https://arxiv.org/abs/2210.07316) | Muennighoff et al., 2022 | Justifica la elección de `text-embedding-3-large` por su superioridad en benchmarks de recuperación semántica en español |
| [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) | Yao et al., 2022 | Patrón implementado en LangGraph `create_react_agent` — el agente razona y actúa invocando tools MCP |
| [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) | Liu et al., 2023 | Justifica el chunking de 500 palabras — los LLMs tienen dificultades con contextos muy largos |

---


## Decisiones técnicas

Las decisiones de arquitectura están documentadas en detalle en el archivo [ADR.md](docs/decisions/ADR.md).

Incluye 11 ADRs con contexto, justificación, alternativas descartadas, impacto de negocio, riesgos, seguridad y observabilidad.



---
## Instalación y ejecución

### Prerrequisitos
- Python 3.11+
- Node.js 22+
- Docker Desktop
- uv (`pip install uv`)
- Token de GitHub con acceso a GitHub Models

### Variables de entorno

Copia los `.env.example` de cada microservicio:
```bash
cp scraper/.env.example scraper/.env
cp mcp-server/.env.example mcp-server/.env
cp agent/.env.example agent/.env
```

### 🔐 Configuración del archivo .env para autenticación
Para habilitar el acceso a los modelos de GitHub, debes agregar tu `GITHUB_TOKEN` en `mcp-server/.env` y `agent/.env`.

🔑 Genera tu token personal en el siguiente enlace: 
[Playground de GitHub Models](https://github.com/marketplace/models/azure-openai/gpt-4o/playground)

🖼️ Ejemplo visual:
![token](docs/img/token.png)

```
GITHUB_TOKEN="[tu-github-token]"
```

### Opción 1 — Sistema en producción (Railway)

Accede directamente sin instalar nada:

🌐 https://frontend-production-1bed.up.railway.app

### Opción 2 — Docker (recomendado)
```bash
docker-compose up --build
```

Servicios disponibles:
- Frontend: http://localhost:3000
- Agent API: http://localhost:8001/docs
- MCP Server: http://localhost:8000/mcp

### Opción 3 — Ejecución local

**1. Scraper** (solo primera vez):
```bash
cd scraper
uv venv && .venv/Scripts/activate
uv sync
python src/main.py
```

**2. Indexar embeddings** (solo primera vez):
```bash
cd mcp-server
uv venv && .venv/Scripts/activate
uv sync
python src/indexer.py
```

**3. MCP Server:**
```bash
python src/server.py
```

**4. Agent** (nueva terminal):
```bash
cd agent
uv venv && .venv/Scripts/activate
uv sync
python src/main.py
```

**5. Frontend** (nueva terminal):
```bash
cd frontend
npm install
npm run dev
```

---

## Tests
```bash
# Scraper
cd scraper && uv run pytest tests/ -v

# MCP Server
cd mcp-server && uv run pytest tests/ -v

# Agent
cd agent && uv run pytest tests/ -v
```

**Resultado:** 16 tests pasando ✅


## MCP Inspector — Pruebas locales

### Streamable HTTP (producción)
Con el servidor MCP corriendo:
```bash
cd mcp-server
python src/server.py
```

En el inspector:
- **Transport Type:** `Streamable HTTP`
- **URL:** `http://localhost:8000/mcp`
- **Connection Type:** `Via Proxy`

### STDIO (pruebas locales)
Sin servidor corriendo previamente:

En el inspector:
- **Transport Type:** `STDIO`
- **Command:** `C:\rag-assistant\mcp-server\.venv\Scripts\python.exe`
- **Arguments:** `C:\rag-assistant\mcp-server\run_stdio.py`

El script `run_stdio.py` carga automáticamente el `.env` y fuerza el transporte stdio.
---

## CI/CD

### Pipeline CI (GitHub Actions)
Se ejecuta automáticamente en cada push a `main`:
-  Lint y tests de scraper, mcp-server y agent
-  Build del frontend
-  Build de imágenes Docker

### Pipeline Scraper (GitHub Actions — Scheduled)
Se ejecuta automáticamente cada día a las 2am:
- Crawling incremental de bancolombia.com/personas
- Detección de páginas nuevas, modificadas y eliminadas
- Re-indexación en ChromaDB solo de páginas con cambios
- Commit automático de datos actualizados
- Railway redeploy automático al detectar el nuevo commit

### Pipeline CD
Railway despliega automáticamente en cada push a `main`:
- MCP Server: https://rag-assistant-production-bb17.up.railway.app/mcp
- Agent: https://agent-production-065e.up.railway.app/docs
- Frontend: https://frontend-production-1bed.up.railway.app

---
---

## Decisiones de Scraping

### Profundidad de crawling
Crawling sin límite artificial de profundidad — el proceso continúa hasta alcanzar el mínimo de 60 páginas válidas (`MIN_PAGES` configurable via `.env`). Se descubren URLs en lotes de 30 (`DISCOVERY_BATCH`) para evitar sobrecarga del servidor.

### Manejo de contenido dinámico
Bancolombia.com usa JavaScript rendering. Se eligió **crawl4ai + Playwright** (Chromium headless) con `wait_until="networkidle"`. Luego **trafilatura** extrae solo el contenido principal eliminando navegación, footers y banners.

### robots.txt
Cada URL se verifica contra `RobotFileParser` antes de procesarse. Las URLs bloqueadas se omiten y el pipeline continúa — garantizando resiliencia sin intervención manual.

### Pipeline industrializado
El scraper detecta cambios incrementales via `content_hash` MD5:
- **Páginas nuevas** → se indexan en ChromaDB
- **Páginas modificadas** → se re-indexan
- **Sin cambios** → se omiten para eficiencia

---


---

## Estructura del proyecto
```
rag-assistant/
├── scraper/                    # Microservicio de crawling
│   ├── src/
│   │   ├── domain/            # Entidades y repositorios
│   │   ├── application/       # Casos de uso
│   │   └── infrastructure/    # crawl4ai, JSON persistence
│   └── Dockerfile
├── mcp-server/                 # Servidor MCP + RAG
│   ├── src/
│   │   ├── domain/
│   │   ├── application/       # search, get_article, list_categories
│   │   └── infrastructure/    # ChromaDB, GitHub Models embeddings
│   └── Dockerfile
├── agent/                      # Agente LangGraph
│   ├── src/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/    # MCP client, SQLite memory
│   └── Dockerfile
├── frontend/                   # React + TypeScript
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   └── Dockerfile
├── docs/
│   └── architecture/          # Diagramas C4
│   └── decisions/             # Desiciones técnicas
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Limitaciones conocidas

- El scraper puede no acceder a páginas con protección antibot avanzada de Bancolombia
- ChromaDB local no escala horizontalmente  pero se podria migrar a Qdrant o Pinecone
- GitHub Models tiene rate limits en el tier gratuito lo que puede ralentizar indexaciones grandes
- El historial de conversación se almacena en localStorage del navegador (máx. 20 conversaciones)
- Railway tier gratuito tiene límite de $5 USD/mes lo que es suficiente para evaluación

---

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

## Contacto

- Leandro Rivera: <leo.232rivera@gmail.com>
- Linkedin: <https://www.linkedin.com/in/leandrorivera/>

### ¡Feliz Codificación! 🚀

Si encuentras útil este proyecto, ¡dale una ⭐ en GitHub! 😊
