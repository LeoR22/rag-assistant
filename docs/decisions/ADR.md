# Architecture Decision Records (ADR)

Decisiones técnicas tomadas durante el desarrollo del RAG Assistant para Bancolombia.
Cada decisión incluye contexto, justificación, alternativas descartadas, impacto de negocio y riesgos.

---

## ADR-001 — Proveedor de IA (LLM y Embeddings)

### Contexto
Se necesita un proveedor de LLM y embeddings gratuito para la prueba técnica que no requiera tarjeta de crédito ni costos al evaluador.

### Decisión
Usar **Groq** con `GPT OSS 20B` para el agente conversacional y **GitHub Models** con `text-embedding-3-large` para los embeddings del MCP Server.

### Justificación
- Groq ofrece 14,400 requests/día gratuitos vs 50 de GitHub Models para LLM
- GPT OSS 20B tiene function calling estable — crítico para invocar tools MCP
- 1000 T/seg de velocidad de inferencia en Groq — respuestas más fluidas
- Compatible con API OpenAI — cero cambios de código al migrar
- `text-embedding-3-large` de GitHub Models — 3072 dimensiones, multilingüe, superior en benchmarks MTEB para español

### Agnóstico al proveedor
El sistema está diseñado para ser agnóstico al proveedor de LLM. Cambiar a Azure OpenAI, AWS Bedrock o Google Vertex AI requiere solo modificar 2 variables de entorno:
- `LLM_BASE_URL`
- `LLM_MODEL`

### Alternativas descartadas
- **Anthropic Claude:** Excelente LLM pero sin modelo de embeddings propio
- **sentence-transformers local:** Gratuito pero menor calidad en español y requiere descarga del modelo
- **OpenAI directo:** Requiere tarjeta de crédito
- **Gemini:** Buena alternativa pero menos documentación para embeddings en español
- **GitHub Models para LLM:** Rate limit de 50 req/día — insuficiente para pruebas y demo

### Impacto de negocio
Permite demostrar capacidades enterprise sin costos. Migrable a Azure OpenAI directo en producción sin cambiar código.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Rate limits en tier gratuito | Baja | Groq ofrece 300K TPM — suficiente para uso normal |
| Token expuesto | Media | Secrets en Railway y GitHub Actions, nunca en código |
| Deprecación del modelo | Baja | Variable de entorno `LLM_MODEL` — cambio sin tocar código |

---

## ADR-002 — ChromaDB como base vectorial

### Contexto
Se necesita almacenar y consultar embeddings de 108 documentos con filtrado por metadatos.

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

### Impacto de negocio
Permite indexar y consultar el conocimiento de Bancolombia sin costos de infraestructura. La interfaz `VectorRepository` garantiza migración a Qdrant o Pinecone sin cambiar lógica de negocio.

### Para producción
Migrar a Qdrant (self-hosted) o Pinecone (managed) para escalar horizontalmente.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| No escala horizontalmente | Media | Interfaz `VectorRepository` permite migrar a Qdrant |
| Corrupción de datos | Baja | Volúmenes Docker + backups automáticos via GitHub Actions |

---

## ADR-003 — Streamable HTTP como transporte MCP principal

### Contexto
El servidor MCP necesita un transporte para comunicarse con el agente. La prueba requiere stdio obligatoriamente y valora positivamente transportes adicionales.

### Decisión
Implementar **ambos transportes** — stdio (obligatorio) y Streamable HTTP (producción), seleccionables via variable de entorno `MCP_TRANSPORT`.

### Justificación
- **stdio** — obligatorio según la prueba, permite pruebas locales con MCP Inspector
- **Streamable HTTP** — permite múltiples clientes simultáneos, más robusto en contenedores
- Selección via `.env` sin cambiar código
- Compatible con MCP Inspector para debugging visual

### Alternativas descartadas
- **Solo stdio:** No escala para múltiples clientes simultáneos
- **SSE:** Deprecated en favor de Streamable HTTP en MCP spec

### Impacto de negocio
Streamable HTTP permite que múltiples agentes o aplicaciones consuman el MCP Server simultáneamente — reutilizable como servicio de conocimiento para otros sistemas de Bancolombia.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Clientes simultáneos saturan el servidor | Media | Railway auto-scaling + rate limiting por tool |

---

## ADR-004 — LangGraph para el agente conversacional

### Contexto
Se necesita un framework para el agente conversacional con memoria en múltiples niveles y conexión al servidor MCP. El patrón ReAct (Yao et al., 2022) es el estándar para agentes con herramientas.

### Decisión
Usar LangGraph con `create_react_agent` y `MemorySaver` integrado.

### Justificación
- Grafos de estado — control explícito del flujo de conversación
- `MemorySaver` integrado para memoria corto plazo por `thread_id`
- `create_react_agent` implementa el patrón ReAct — razona y actúa invocando tools MCP
- Integración nativa con `langchain-mcp-adapters` para conexión MCP
- Más robusto que LangChain simple para agentes con múltiples herramientas

### Alternativas descartadas
- **LangChain simple:** Menos control sobre el flujo del agente, sin grafos de estado
- **CrewAI:** Orientado a multi-agentes, overkill para este caso de uso
- **Autogen:** Mayor complejidad de configuración para un solo agente
- **SDK Anthropic con tool use:** No tiene integración nativa con MCP

### Impacto de negocio
El patrón ReAct permite al agente decidir autónomamente cuándo buscar información — mejora la experiencia de usuario al responder saludos directamente sin llamar innecesariamente a la base de conocimiento.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Agente invoca tools innecesariamente | Media | Descripciones de tools optimizadas con casos de uso/no uso |
| Latencia alta por múltiples tool calls | Media | top_k=5 por defecto — balance entre calidad y velocidad |

---

## ADR-005 — Chunking 500 palabras con overlap 50

### Contexto
Se necesita dividir el contenido web en chunks para retrieval semántico eficiente. Liu et al. (2023) demuestran que los LLMs tienen dificultades con contextos muy largos.

### Decisión
Chunks de 500 palabras con overlap de 50 palabras, segmentación HTML-Aware.

### Justificación
- **500 palabras** — suficiente contexto para responder preguntas sobre productos bancarios sin exceder el contexto útil del retrieval
- **Overlap de 50** — evita perder información semántica en los bordes del chunk
- **HTML-Aware** — preserva estructura semántica del contenido web, divide por párrafos
- **Por palabras vs caracteres** — más estable para español donde las palabras tienen longitud variable

### Resultado
66 páginas → 108 chunks indexados en 7 categorías

### Alternativas descartadas
- **RecursiveCharacterTextSplitter:** Pierde estructura semántica del HTML
- **Chunks por párrafo:** Tamaño inconsistente, difícil de controlar para retrieval uniforme
- **Chunks de 200 palabras:** Muy pequeños, pierden contexto necesario para responder
- **Chunks de 1000 palabras:** Muy grandes, menor precisión en el retrieval semántico
- **SemanticChunking:** Costoso computacionalmente para el pipeline diario automatizado

### Impacto de negocio
Chunks bien dimensionados = respuestas más precisas y relevantes para el usuario final.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Chunks muy pequeños para temas complejos | Baja | `get_article_by_url` permite obtener el artículo completo |

---

## ADR-006 — SQLite para memoria largo plazo del agente

### Contexto
Se necesita persistir el historial de conversaciones entre sesiones y generar resúmenes para memoria mediano plazo.

### Decisión
Usar SQLite via SQLAlchemy ORM para memoria largo y mediano plazo.

### Justificación
- Sin servidor adicional — archivo local dockerizable con volúmenes
- SQLAlchemy permite migrar a PostgreSQL sin cambiar código de dominio
- Suficiente para la escala de la prueba

### Tipologías de memoria implementadas

| Tipo | Implementación | Alcance |
|---|---|---|
| Corto plazo | `MemorySaver` LangGraph (RAM) | Mensajes de la sesión activa — trim automático a 8 mensajes para respetar token limits |
| Mediano plazo | Resúmenes en SQLite | Contexto de conversaciones anteriores — se genera cuando supera 10 mensajes |
| Largo plazo | SQLite via SQLAlchemy | Historial completo persistente |

### Para producción
Migrar a PostgreSQL o Redis con TTL para manejo de sesiones concurrentes.

### Impacto de negocio
La memoria en 3 niveles permite al agente mantener contexto conversacional — el usuario no necesita repetir información en cada mensaje.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| SQLite no escala con usuarios concurrentes | Alta en producción | Interfaz `MemoryRepository` — migrar a PostgreSQL |
| Pérdida de datos en reinicio sin volumen | Media | Volúmenes Docker + Railway persistent storage |

---

## ADR-007 — LLM en el agente, no en el servidor MCP

### Contexto
El servidor MCP podría construir el prompt y llamar al LLM internamente, o delegar esa responsabilidad al agente cliente.

### Decisión
El servidor MCP es una capa de **retrieval pura** — retorna documentos con fuentes y metadatos. La construcción del prompt y la invocación del LLM ocurren en el agente.

### Modelo actual
GPT OSS 20B via Groq API (compatible con API OpenAI) — seleccionable via variable de entorno `LLM_MODEL`.

### Justificación
- **Reutilizabilidad** — el MCP Server puede ser consumido por cualquier cliente sin acoplarse a un LLM específico
- **Separación de responsabilidades** — retrieval vs generación son concerns distintos
- **Flexibilidad** — el agente puede cambiar de GPT OSS 20B a Claude o Llama sin tocar el servidor MCP
- **Testabilidad** — cada capa se puede testear independientemente

### Alternativas de modelo descartadas
- **Llama 3.3 70B (Groq)** — inestable en function calling con FastMCP tools
- **GPT OSS 120B (Groq)** — rate limit de 8,000 TPM en plan gratuito — insuficiente para RAG
- **GPT-4o (GitHub Models)** — rate limit de 50 req/día — insuficiente para pruebas

### Trade-offs considerados
- El agente debe construir el prompt correctamente — mayor responsabilidad en el cliente
- Latencia ligeramente mayor por un round-trip adicional — aceptable para uso conversacional

### Impacto de negocio
El MCP Server se convierte en un servicio de conocimiento reutilizable — otros sistemas de Bancolombia pueden consumirlo con diferentes LLMs según sus necesidades.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Prompt mal construido en el agente | Baja | System prompt robusto + tests de integración |

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

### Ejemplos aplicados
- `VectorRepository` (puerto) → `ChromaRepository` (adaptador) — migrable a Qdrant
- `CrawlerRepository` (puerto) → `BancolombiaCrawler` (adaptador) — migrable a otro crawler
- `MemoryRepository` (puerto) → `LongTermMemory` (adaptador) — migrable a PostgreSQL

### Impacto de negocio
Permite cambiar tecnologías subyacentes sin impactar la lógica de negocio — reduce el costo de mantenimiento y facilita la evolución del sistema.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Overhead de capas para equipo pequeño | Baja | Las interfaces están bien definidas y documentadas |

---

## ADR-009 — Estrategia de Observabilidad

### Contexto
En producción es necesario monitorear la salud del sistema, latencia de respuestas y calidad del retrieval.

### Decisión actual
- Logging estructurado con `loguru` en todos los microservicios
- Health checks en `/health` de cada servicio
- **Langfuse** para trazabilidad completa de interacciones LLM — prompts, respuestas, tools invocadas, tokens y latencia

### Propuesta para producción
- **Trazas distribuidas:** OpenTelemetry entre los 4 microservicios
- **Métricas:** Prometheus + Grafana — latencia por tool MCP, tokens usados, cache hits
- **Alertas:** Slack cuando retrieval tarda más de 2 segundos
- **Logs centralizados:** ELK Stack o Datadog

### Impacto de negocio
Sin observabilidad los errores en producción son difíciles de diagnosticar. Langfuse permite detectar degradación en la calidad de las respuestas antes de que afecte al usuario final.

### Riesgos
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Errores silenciosos en producción | Alta sin monitoreo | Health checks + alertas en Railway + Langfuse |
| Latencia alta no detectada | Media | Métricas de latencia por endpoint en Langfuse |

---

## ADR-010 — Estrategia de Seguridad

### Decisión
Múltiples capas de seguridad implementadas:

| Capa | Implementación |
|---|---|
| Rate limiting Agent | slowapi — 10 req/min por IP en el endpoint `/chat` |
| Rate limiting MCP Server | Decorador custom — 20 req/min por tool (search, get_article, list_categories) |
| CORS restrictivo | Orígenes permitidos via variable de entorno `ALLOWED_ORIGINS` |
| Variables de entorno | API keys nunca en código — siempre en `.env` y secrets |
| Input sanitization | Queries vacíos y >500 chars rechazados en el Agent |
| Error handling LLM | Respuestas amigables para rate limits, timeouts y errores de conexión |
| robots.txt | Scraper respeta restricciones del sitio |
| HTTPS | Railway provee TLS automáticamente |

### Para producción
- Autenticación JWT entre Frontend y Agent
- API Key entre Agent y MCP Server
- Secrets rotation automática

### Impacto de negocio
Sin rate limiting un atacante podría agotar los créditos del proveedor LLM. Sin validación de inputs el sistema es vulnerable a prompt injection.

### Riesgos identificados
| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Token Groq/GitHub expuesto | Media | Alto | Secrets en Railway/GitHub Actions |
| Rate limit del proveedor LLM | Baja | Medio | Error handling amigable + Groq 300K TPM |
| ChromaDB sin auth | Baja | Alto | No expuesto públicamente — solo interno |
| Prompt injection | Media | Medio | Sanitización de inputs + system prompt robusto |

---

## ADR-011 — Impacto de Negocio General

### Problema que resuelve
Los usuarios de Bancolombia tienen dificultades para encontrar información sobre productos financieros en el sitio web. El asistente RAG permite consultas en lenguaje natural con respuestas precisas y citadas.

### Valor generado
- **Reducción de tiempo** — el usuario obtiene información en segundos vs navegar manualmente el sitio
- **Citación de fuentes** — el usuario puede verificar la información directamente en bancolombia.com
- **Disponibilidad 24/7** — sin dependencia de horarios de atención al cliente
- **Conocimiento actualizado** — scraper diario garantiza información vigente
- **Multilingüe** — responde siempre en español independientemente del idioma de la pregunta

### Métricas de éxito propuestas
- Tasa de respuestas con fuentes citadas > 90%
- Latencia de respuesta < 3 segundos
- Páginas indexadas actualizadas diariamente via GitHub Actions
- Disponibilidad del sistema > 99.5%

### Riesgos de negocio
| Riesgo | Mitigación |
|---|---|
| Información desactualizada | Scraper diario automatizado con detección de cambios MD5 |
| Respuestas incorrectas | Retrieval semántico + citación obligatoria de fuentes |
| Costos de API | Groq tier gratuito — 14,400 req/día sin costo |
| Dependencia de terceros | Variables de entorno — migrable a otro proveedor sin cambiar código |
