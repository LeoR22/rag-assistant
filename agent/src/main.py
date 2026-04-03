import sys
import os
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
from application.use_cases.process_message import ProcessMessageUseCase

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


load_dotenv()

# ── FastAPI App ─────────────────────────────────────────────
app = FastAPI(
    title="Bancolombia RAG Agent",
    description="Agente conversacional con memoria y tools MCP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    sources: list[dict]


# ── Use case ────────────────────────────────────────────────
process_message = ProcessMessageUseCase()


# ── Endpoints ───────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "bancolombia-rag-agent",
        "version": "1.0.0",
    }

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Demasiadas solicitudes. Intenta de nuevo en un momento."}
    )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(request: ChatRequest):
    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())

        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="La consulta no puede estar vacía")

        if len(request.query) > 500:
            raise HTTPException(status_code=400, detail="La consulta no puede superar 500 caracteres")

        result = await process_message.execute(
            query=request.query,
            conversation_id=conversation_id,
        )

        return ChatResponse(
            conversation_id=result["conversation_id"],
            response=result["response"],
            sources=result["sources"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en /chat: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    try:
        from infrastructure.memory.long_term import LongTermMemory
        memory = LongTermMemory()
        conversation = memory.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "sources": [
                        {"url": s.url, "title": s.title}
                        for s in m.sources
                    ],
                    "created_at": m.created_at.isoformat(),
                }
                for m in conversation.messages
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en /conversations: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ── Entry point ─────────────────────────────────────────────
if __name__ == "__main__":
    host = os.getenv("AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_PORT", 8001))

    logger.info(f"🚀 Iniciando Bancolombia RAG Agent")
    logger.info(f"   Host: {host}:{port}")
    logger.info(f"   Docs: http://{host}:{port}/docs")

    uvicorn.run(app, host=host, port=port)