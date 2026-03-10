"""
Endpoints de IA do Trade com streaming e contexto completo.
"""
import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_session
from app.models.profile import AIConversation
from app.models.user import User
from app.services.ai_service import ai_service
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_history: List[dict] = []
    workspace_id: str | None = None
    user_id: str | None = None


class ConversationCreate(BaseModel):
    title: str
    workspace_id: str
    messages: List[dict]


class ConversationResponse(BaseModel):
    id: str
    title: str
    workspace_id: str
    messages: List[dict]
    created_at: str
    updated_at: str


@router.post("/api/v1/ai/chat")
async def chat_with_ai(
    request: ChatRequest,
    authorization: str = Header(None),
    x_api_key: str = Header(None),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Endpoint principal de chat com IA do Trade.
    Suporta autenticação via Bearer token ou API Key.
    """
    # Autenticação via Bearer token
    if authorization and authorization.startswith("Bearer "):
        current_user = await get_current_user(
            token=authorization.replace("Bearer ", ""),
            db=db
        )
        if not current_user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        workspace_id = request.workspace_id or str(current_user.owned_workspaces[0].id) if current_user.owned_workspaces else None
        user_id = str(current_user.id)
    
    # Autenticação via API Key (para n8n)
    elif x_api_key:
        # Validar API Key (implementar lógica de validação)
        if x_api_key != "gpfx-api-key-2024":  # Temporário - implementar validação real
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        workspace_id = request.workspace_id
        user_id = request.user_id or "system-user"
        
        # Criar usuário temporário para contexto
        current_user = None
    
    else:
        raise HTTPException(
            status_code=401, 
            detail="Authorization required: Bearer token or X-API-Key header"
        )
    
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    
    try:
        # Buscar contexto completo do trader
        context = ai_service.build_trading_context(workspace_id, user_id, db)
        
        if "error" in context:
            raise HTTPException(status_code=400, detail=context["error"])
        
        # Gerar streaming response
        async def generate_stream():
            try:
                async for chunk in ai_service.chat_with_ai(
                    message=request.message,
                    context=context,
                    history=request.conversation_history
                ):
                    yield chunk
                    
            except Exception as e:
                yield f"data: {{\"type\": \"error\", \"content\": \"Streaming error: {str(e)}\"}}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.get("/api/v1/ai/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> List[ConversationResponse]:
    """
    Lista histórico de conversas do usuário.
    """
    from sqlalchemy import select, desc
    
    result = await db.execute(
        select(AIConversation)
        .where(AIConversation.user_id == current_user.id)
        .order_by(desc(AIConversation.updated_at))
    )
    conversations = result.scalars().all()
    
    return [
        ConversationResponse(
            id=str(conv.id),
            title=conv.title or "Sem título",
            workspace_id=str(conv.workspace_id),
            messages=conv.messages,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat()
        )
        for conv in conversations
    ]


@router.post("/api/v1/ai/conversations")
async def save_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> ConversationResponse:
    """
    Salva nova conversa no banco.
    """
    try:
        # Validar workspace_id
        workspace_uuid = uuid.UUID(conversation.workspace_id)
        
        # Verificar se usuário tem acesso ao workspace
        user_workspaces = [ws.id for ws in current_user.owned_workspaces]
        if workspace_uuid not in user_workspaces:
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        
        # Criar nova conversa
        new_conversation = AIConversation(
            user_id=current_user.id,
            workspace_id=workspace_uuid,
            title=conversation.title,
            messages=conversation.messages
        )
        
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)
        
        return ConversationResponse(
            id=str(new_conversation.id),
            title=new_conversation.title,
            workspace_id=str(new_conversation.workspace_id),
            messages=new_conversation.messages,
            created_at=new_conversation.created_at.isoformat(),
            updated_at=new_conversation.updated_at.isoformat()
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workspace_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving conversation: {str(e)}")


@router.get("/api/v1/ai/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> ConversationResponse:
    """
    Obtém detalhes de uma conversa específica.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
        
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conv_uuid,
                AIConversation.user_id == current_user.id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title or "Sem título",
            workspace_id=str(conversation.workspace_id),
            messages=conversation.messages,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat()
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")


@router.put("/api/v1/ai/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> ConversationResponse:
    """
    Atualiza uma conversa existente.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
        workspace_uuid = uuid.UUID(conversation_update.workspace_id)
        
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conv_uuid,
                AIConversation.user_id == current_user.id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Atualizar campos
        conversation.title = conversation_update.title
        conversation.workspace_id = workspace_uuid
        conversation.messages = conversation_update.messages
        
        await db.commit()
        await db.refresh(conversation)
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            workspace_id=str(conversation.workspace_id),
            messages=conversation.messages,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat()
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating conversation: {str(e)}")


@router.delete("/api/v1/ai/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Remove uma conversa.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
        
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conv_uuid,
                AIConversation.user_id == current_user.id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        await db.delete(conversation)
        await db.commit()
        
        return {"message": "Conversation deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")


@router.get("/api/v1/ai/context/{workspace_id}")
async def get_trading_context(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Obtém o contexto completo de trading para debugging.
    """
    try:
        # Verificar acesso ao workspace
        workspace_uuid = uuid.UUID(workspace_id)
        user_workspaces = [ws.id for ws in current_user.owned_workspaces]
        if workspace_uuid not in user_workspaces:
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        
        context = ai_service.build_trading_context(workspace_id, str(current_user.id), db)
        
        if "error" in context:
            raise HTTPException(status_code=400, detail=context["error"])
        
        return context
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workspace_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building context: {str(e)}")


@router.get("/api/v1/ai/health")
async def ai_health_check() -> dict:
    """
    Verifica saúde do serviço de IA.
    """
    from app.core.config import settings
    
    return {
        "status": "healthy",
        "model": ai_service.model,
        "openai_configured": bool(hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY),
        "service_version": "1.0.0"
    }
