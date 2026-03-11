"""
Gustavo Pedrosa FX - API principal.
Ponto de entrada: uvicorn app.main:app
"""
from fastapi import FastAPI, WebSocket, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import get_db
from app.websocket.replay import handle_replay_websocket

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS - permitir frontend em produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.websocket("/ws/replay/{session_id}")
async def websocket_replay(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(None),
    db=Depends(get_db),
):
    """WebSocket endpoint for market replay sessions."""
    import uuid
    
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        await websocket.close(code=4000, reason="Invalid session ID")
        return
    
    await handle_replay_websocket(websocket, session_uuid, token, db)


@app.get("/")
def root():
    return {"service": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/health")
def health():
    return {"status": "ok"}
