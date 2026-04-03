# Architecture Decision Records (ADR)

Decisiones técnicas tomadas durante el desarrollo del RAG Assistant para Bancolombia.
Cada decisión incluye contexto, justificación y alternativas descartadas.

---

## ADR-001 — GitHub Models como proveedor de IA

### Contexto
Se necesita un proveedor de LLM y embeddings gratuito para la prueba técnica que no requiera tarjeta de crédito ni costos al evaluador.

### Decisión
Usar GitHub Models (Azure OpenAI) con `gpt-4o` para generación y `text-embedding-3-large` para embeddings.

### Justificación
- Gratuito con token de GitHub — sin costos para el evaluador
- Stack enterprise de Microsoft/Azure — mismo que usan empresas como Bancolombia
- `text-embedding-3-large` supera sentence-transformers en benchmarks MTEB español
- Dimensionalidad 3072d vs 768d — 4x mejor separación semántica
- Toda la configuración via variables de entorno — sin valores hardcodeados

### Alternativas descartadas
- **Anthropic Claude:** Excelente LLM pero sin modelo de embeddings propio
- **sentence-transformers local:** Gratuito pero menor calidad en español y requiere descarga del modelo
- **OpenAI directo:** Requiere tarjeta de crédito
- **Gemini:** Buena alternativa pero menos documentación para embeddings en español

---

## ADR-002 — ChromaDB como base vectorial

### Contexto
Se necesita almacenar y consultar embeddings de 97 documentos con filtrado por metadatos.

### Decisión
Usar ChromaDB con persistencia local en disco via `PersistentClient`.

### Justificación
- Sin costo ni dependencias externas
- Persistencia en disco — los vectores sobreviven reinicios del contenedor
- Filtrado por metadatos — soporta `where` clauses para filtrar por categoría y URL
- Fácil de dockerizar con volúmenes Docker
- Migrable sin cambiar el dominio — `VectorRepository` es una interfaz/puerto
- Métrica coseno (`hnsw:space: cosine`) — estándar para embeddings normalizados

### Alternativas descartadas
- **Pinecone:** Requiere cuenta y tiene límites en tier gratuito
- **Qdrant:** Excelente para producción pero más complejo de configurar localmente
- **pgvector:** Requiere PostgreSQL — overhead innecesario para esta escala
- **Weaviate:** Mayor complejidad de configuración para el scope de la prueba

### Para producción
Migrar a Qdrant (self-hosted) o Pinecone (managed) para escalar horizontalmente. El cambio solo afecta `ChromaRepository` en infrastructure — el dominio no cambia.

---

## ADR-003 — Streamable HTTP como transporte MCP principal

### Contexto
El servidor MCP necesita un transporte para comunicarse con el agente. La prueba requiere stdio obligatoriamente y valora positivamente transportes adicionales.

### Decisión
Implementar **ambos transportes** — stdio (obligatorio) y Streamable HTTP (producción), seleccionables via variable de entorno `MCP_TRANSPORT`.

### Justificación
- **stdio** — obligatorio según la prueba, permite pruebas locales simples
- **Streamable HTTP** — permite múltiples clientes simultáneos, más robusto en contenedores
- Selección via `.env` sin cambiar código — `MCP_TRANSPORT=stdio` o `MCP_TRANSPORT=streamable-http`
- Compatible con MCP Inspector para debugging visual

### Alternativas descartadas
- **Solo stdio:** No escala para múltiples clientes simultáneos
- **SSE:** Deprecated en favor de Streamable HTTP en MCP spec

---

## ADR-004 — LangGraph para el agente conversacional

### Contexto
Se necesita un framework para el agente conversacional con memoria en múltiples niveles y conexión al servidor MCP.

### Decisión
Usar LangGraph con `create_react_agent` y `MemorySaver` integrado.

### Justificación
- Grafos de estado — control explícito del flujo de conversación
- `MemorySaver` integrado para memoria corto plazo por `thread_id`
- `create_react_agent` decide automáticamente cuándo invocar tools MCP
- Integración nativa con `langchain-mcp-adapters` para conexión MCP
- Más robusto que LangChain simple para agentes con múltiples herramientas

### Alternativas descartadas
- **LangChain simple:** Menos control sobre el flujo del agente, sin grafos de estado
- **CrewAI:** Orientado a multi-agentes, overkill para este caso de uso
- **Autogen:** Mayor complejidad de configuración para un solo agente
- **SDK Anthropic con tool use:** No tiene integración nativa con MCP

---

## ADR-005 — Chunking 500 palabras con overlap 50

### Contexto
Se necesita dividir el contenido web en chunks para retrieval semántico eficiente.

### Decisión
Chunks de 500 palabras con overlap de 50 palabras, segmentación por palabras.

### Justificación
- **500 palabras** — suficiente contexto para responder preguntas sobre productos bancarios sin exceder el contexto útil del retrieval
- **Overlap de 50** — evita perder información semántica en los bordes del chunk. Sin overlap, una pregunta que cae entre dos chunks perdería contexto
- **Por palabras vs caracteres** — más estable para español donde las palabras tienen longitud variable
- Configurable via `CleanContentUseCase.CHUNK_SIZE` y `CHUNK_OVERLAP`

### Resultado
66 páginas → 97 chunks indexados — promedio 1.5 chunks por página

### Alternativas descartadas
- **Chunks por párrafo:** Tamaño inconsistente, difícil de controlar para retrieval uniforme
- **Chunks de 200 palabras:** Muy pequeños, pierden contexto necesario para responder
- **Chunks de 1000 palabras:** Muy grandes, menor precisión en el retrieval semántico

---

## ADR-006 — SQLite para memoria largo plazo del agente

### Contexto
Se necesita persistir el historial de conversaciones entre sesiones y generar resúmenes para memoria mediano plazo.

### Decisión
Usar SQLite via SQLAlchemy ORM para memoria largo y mediano plazo.

### Justificación
- Sin servidor adicional — archivo local dockerizable con volúmenes
- SQLAlchemy permite migrar a PostgreSQL sin cambiar código de dominio
- Suficiente para la escala de la prueba (decenas de conversaciones)
- Soporta los 3 niveles de memoria del agente

### Tipologías de memoria implementadas

| Tipo | Implementación | Alcance |
|---|---|---|
| Corto plazo | `MemorySaver` LangGraph (RAM) | Mensajes de la sesión activa |
| Mediano plazo | Resúmenes en SQLite | Contexto de conversaciones anteriores |
| Largo plazo | SQLite via SQLAlchemy | Historial completo persistente |

### Para producción
Migrar a PostgreSQL o Redis con TTL para manejo de sesiones concurrentes y mayor performance.

---

## ADR-007 — LLM en el agente, no en el servidor MCP

### Contexto
El servidor MCP podría construir el prompt y llamar al LLM internamente, o delegar esa responsabilidad al agente cliente.

### Decisión
El servidor MCP es una capa de **retrieval pura** — retorna documentos con fuentes y metadatos. La construcción del prompt y la invocación del LLM ocurren en el agente.

### Justificación
- **Reutilizabilidad** — el MCP Server puede ser consumido por cualquier cliente (Claude Desktop, otro agente, aplicación propia) sin acoplarse a un LLM específico
- **Separación de responsabilidades** — retrieval vs generación son concerns distintos
- **Flexibilidad** — el agente puede cambiar de GPT-4o a Claude o Llama sin tocar el servidor MCP
- **Testabilidad** — cada capa se puede testear independientemente

### Trade-offs considerados
- El agente debe construir el prompt correctamente — mayor responsabilidad en el cliente
- Latencia ligeramente mayor por un round-trip adicional — aceptable para el uso conversacional

---

## ADR-008 — Clean Architecture en microservicios

### Contexto
Se necesita una arquitectura que permita bajo acoplamiento, alta cohesión y facilidad de testing.

### Decisión
Aplicar Clean Architecture (hexagonal) en cada microservicio con las capas: domain → application → infrastructure.

### Justificación
- **domain** — entidades y puertos/interfaces sin dependencias externas
- **application** — casos de uso que orquestan el dominio
- **infrastructure** — implementaciones concretas (ChromaDB, crawl4ai, SQLite)
- Las dependencias siempre apuntan hacia adentro — el dominio no conoce la infraestructura
- Permite cambiar implementaciones sin tocar la lógica de negocio

### Ejemplos aplicados
- `VectorRepository` (puerto) → `ChromaRepository` (adaptador) — migrable a Qdrant
- `CrawlerRepository` (puerto) → `BancolombiaCrawler` (adaptador) — migrable a otro crawler
- `MemoryRepository` (puerto) → `LongTermMemory` (adaptador) — migrable a PostgreSQL