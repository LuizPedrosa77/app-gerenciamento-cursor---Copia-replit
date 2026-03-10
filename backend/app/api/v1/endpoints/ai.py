"""
Endpoint para IA do Trade com streaming SSE.
"""
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_async_session
from app.models.user import User
from app.services.ai_service import AIService
from pydantic import BaseModel

router = APIRouter()
ai_service = AIService()


class AIRequest(BaseModel):
    message: str
    context: dict | None = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = True


class AIResponse(BaseModel):
    id: str
    type: str  # "message", "error", "done"
    content: str | None = None
    metadata: dict | None = None


@router.post("/ai/chat")
async def ai_chat(
    request: AIRequest,
    api_key: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Endpoint principal da IA do Trade com streaming SSE.
    
    Suporta:
    - Streaming de respostas (Server-Sent Events)
    - API Key customizada
    - Contexto da conversa
    - Múltiplos modelos
    """
    
    if not api_key:
        raise HTTPException(
            status_code=403,
            detail="API Key required for AI access"
        )
    
    # Build context from user data
    from app.models.workspace import Workspace
    from sqlalchemy import select
    
    # Get user's workspace
    workspace_result = await db.execute(
        select(Workspace).where(Workspace.owner_user_id == current_user.id)
    )
    workspace = workspace_result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Build trading context
    context = ai_service.build_trading_context(
        str(workspace.id), 
        str(current_user.id), 
        db
    )
    
    if request.context:
        context.update(request.context)
    
    async def generate_stream():
        """Generator para streaming SSE."""
        try:
            conversation_id = str(uuid.uuid4())
            
            # Send initial connection message
            yield f"data: {json.dumps(AIResponse(
                id=conversation_id,
                type="message",
                content="Conectado à IA do Trade...",
                metadata={"status": "connected"}
            ).model_dump())}\n\n"
            
            # Generate AI response using real OpenAI
            async for chunk in ai_service.chat_completion_stream(
                message=request.message,
                context=context,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                yield f"data: {json.dumps(AIResponse(
                    id=conversation_id,
                    type="message",
                    content=chunk,
                    metadata={"status": "streaming"}
                ).model_dump())}\n\n"
            
            # Send completion message
            yield f"data: {json.dumps(AIResponse(
                id=conversation_id,
                type="done",
                content=None,
                metadata={"status": "completed"}
            ).model_dump())}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps(AIResponse(
                id=conversation_id,
                type="error",
                content=str(e),
                metadata={"status": "error"}
            ).model_dump())}\n\n"
    
    if request.stream:
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    else:
        # Non-streaming response
        response_text = await ai_service.chat_completion(
            message=request.message,
            context=context,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return AIResponse(
            id=str(uuid.uuid4()),
            type="message",
            content=response_text,
            metadata={"status": "completed"}
        )


@router.get("/ai/models")
async def get_available_models(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Lista modelos de IA disponíveis."""
    return {
        "models": [
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "description": "Modelo mais avançado para análises complexas",
                "max_tokens": 4096,
                "cost_per_token": 0.00003
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Rápido e econômico para análises rápidas",
                "max_tokens": 4096,
                "cost_per_token": 0.000002
            }
        ]
    }
