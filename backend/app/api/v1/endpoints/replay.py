"""
Replay session management endpoints.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import CurrentUser, CurrentWorkspace, DbSession
from app.models import ReplayMode, ReplayStatus
from app.services import market_data_service

router = APIRouter()


# Request/Response schemas
class ReplaySessionCreate(BaseModel):
    symbol_id: UUID = Field(..., description="Symbol ID for replay")
    timeframe: str = Field(..., min_length=1, max_length=10, description="Timeframe (M1, M5, H1, D1, etc.)")
    start_time: datetime = Field(..., description="Start time for replay")
    end_time: datetime = Field(..., description="End time for replay")
    mode: ReplayMode = Field(default=ReplayMode.REAL_TIME, description="Replay mode")
    speed: Decimal = Field(default=Decimal("1.0"), ge=Decimal("0.1"), le=Decimal("10.0"), description="Speed multiplier")
    auto_step: bool = Field(default=True, description="Auto-step in step mode")
    step_interval: int = Field(default=1000, ge=100, le=10000, description="Step interval in milliseconds")


class ReplaySessionUpdate(BaseModel):
    speed: Decimal | None = Field(None, ge=Decimal("0.1"), le=Decimal("10.0"))
    auto_step: bool | None = None
    step_interval: int | None = Field(None, ge=100, le=10000)


class ReplaySessionRead(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    symbol_id: UUID
    timeframe: str
    mode: str
    status: str
    start_time: datetime
    end_time: datetime
    current_time: datetime | None = None
    speed: Decimal
    auto_step: bool
    step_interval: int
    total_ticks: int
    processed_ticks: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReplaySessionAction(BaseModel):
    action: str = Field(..., description="Action: play, pause, stop, seek")
    target_time: datetime | None = Field(None, description="Target time for seek action")
    speed: Decimal | None = Field(None, ge=Decimal("0.1"), le=Decimal("10.0"), description="New speed for set_speed action")


@router.post("/replay/sessions", response_model=ReplaySessionRead, status_code=status.HTTP_201_CREATED)
async def create_replay_session(
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
    body: ReplaySessionCreate,
):
    """Create a new replay session."""
    workspace, _ = current_workspace
    
    # Validate time range
    if body.start_time >= body.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be before end_time",
        )
    
    # Check if end_time is in the past (for historical data)
    if body.end_time > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be in the past for historical replay",
        )
    
    try:
        session = await market_data_service.create_replay_session(
            db=db,
            workspace_id=workspace.id,
            user_id=current_user.id,
            symbol_id=body.symbol_id,
            timeframe=body.timeframe,
            start_time=body.start_time,
            end_time=body.end_time,
            mode=body.mode.value,
            speed=body.speed,
        )
        
        # Set additional fields
        session.auto_step = body.auto_step
        session.step_interval = body.step_interval
        await db.commit()
        await db.refresh(session)
        
        return ReplaySessionRead.model_validate(session)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create replay session: {str(e)}",
        )


@router.get("/replay/sessions", response_model=list[ReplaySessionRead])
async def list_replay_sessions(
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
    user_id: UUID | None = None,
):
    """List replay sessions for workspace."""
    workspace, _ = current_workspace
    
    # Admin can see all sessions, others see only their own
    target_user_id = user_id if user_id and current_user.is_superuser else current_user.id
    
    sessions = await market_data_service.list_replay_sessions(
        db=db,
        workspace_id=workspace.id,
        user_id=target_user_id,
    )
    
    return [ReplaySessionRead.model_validate(session) for session in sessions]


@router.get("/replay/sessions/{session_id}", response_model=ReplaySessionRead)
async def get_replay_session(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    """Get replay session by ID."""
    workspace, _ = current_workspace
    
    session = await market_data_service.get_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay session not found",
        )
    
    # Check if user owns the session or is admin
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )
    
    return ReplaySessionRead.model_validate(session)


@router.post("/replay/sessions/{session_id}/start")
async def start_replay_session(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    """Start a replay session."""
    workspace, _ = current_workspace
    
    session = await market_data_service.get_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay session not found",
        )
    
    # Check if user owns the session or is admin
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )
    
    if session.status == ReplayStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already running",
        )
    
    # Update session status
    updated_session = await market_data_service.update_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
        status=ReplayStatus.RUNNING,
        started_at=datetime.now(timezone.utc) if not session.started_at else None,
    )
    
    return {"status": "started", "session_id": str(session_id)}


@router.post("/replay/sessions/{session_id}/pause")
async def pause_replay_session(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    """Pause a replay session."""
    workspace, _ = current_workspace
    
    session = await market_data_service.get_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay session not found",
        )
    
    # Check if user owns the session or is admin
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )
    
    if session.status != ReplayStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not running",
        )
    
    # Update session status
    updated_session = await market_data_service.update_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
        status=ReplayStatus.PAUSED,
    )
    
    return {"status": "paused", "session_id": str(session_id)}


@router.post("/replay/sessions/{session_id}/stop")
async def stop_replay_session(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    """Stop a replay session."""
    workspace, _ = current_workspace
    
    session = await market_data_service.get_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay session not found",
        )
    
    # Check if user owns the session or is admin
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )
    
    # Update session status
    updated_session = await market_data_service.update_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
        status=ReplayStatus.COMPLETED,
        completed_at=datetime.now(timezone.utc),
        current_time=session.start_time,  # Reset to start
        processed_ticks=0,
    )
    
    return {"status": "stopped", "session_id": str(session_id)}


@router.post("/replay/sessions/{session_id}/action")
async def execute_replay_action(
    session_id: UUID,
    body: ReplaySessionAction,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    """Execute an action on a replay session."""
    workspace, _ = current_workspace
    
    session = await market_data_service.get_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay session not found",
        )
    
    # Check if user owns the session or is admin
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )
    
    action = body.action.lower()
    
    if action == "play":
        if session.status == ReplayStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is already running",
            )
        
        updated_session = await market_data_service.update_replay_session(
            db=db,
            session_id=session_id,
            workspace_id=workspace.id,
            status=ReplayStatus.RUNNING,
            started_at=datetime.now(timezone.utc) if not session.started_at else None,
        )
        
        return {"status": "started", "action": action}
    
    elif action == "pause":
        if session.status != ReplayStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not running",
            )
        
        updated_session = await market_data_service.update_replay_session(
            db=db,
            session_id=session_id,
            workspace_id=workspace.id,
            status=ReplayStatus.PAUSED,
        )
        
        return {"status": "paused", "action": action}
    
    elif action == "stop":
        updated_session = await market_data_service.update_replay_session(
            db=db,
            session_id=session_id,
            workspace_id=workspace.id,
            status=ReplayStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
            current_time=session.start_time,
            processed_ticks=0,
        )
        
        return {"status": "stopped", "action": action}
    
    elif action == "seek":
        if not body.target_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target_time is required for seek action",
            )
        
        if body.target_time < session.start_time or body.target_time > session.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target_time must be within session range",
            )
        
        updated_session = await market_data_service.update_replay_session(
            db=db,
            session_id=session_id,
            workspace_id=workspace.id,
            current_time=body.target_time,
        )
        
        return {"status": "seeked", "action": action, "target_time": body.target_time.isoformat()}
    
    elif action == "set_speed":
        if not body.speed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="speed is required for set_speed action",
            )
        
        updated_session = await market_data_service.update_replay_session(
            db=db,
            session_id=session_id,
            workspace_id=workspace.id,
            speed=body.speed,
        )
        
        return {"status": "speed_updated", "action": action, "speed": float(body.speed)}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {action}",
        )


@router.patch("/replay/sessions/{session_id}", response_model=ReplaySessionRead)
async def update_replay_session(
    session_id: UUID,
    body: ReplaySessionUpdate,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    """Update replay session."""
    workspace, _ = current_workspace
    
    session = await market_data_service.get_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay session not found",
        )
    
    # Check if user owns the session or is admin
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )
    
    # Update fields
    update_data = {}
    if body.speed is not None:
        update_data["speed"] = body.speed
    if body.auto_step is not None:
        update_data["auto_step"] = body.auto_step
    if body.step_interval is not None:
        update_data["step_interval"] = body.step_interval
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    
    updated_session = await market_data_service.update_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
        **update_data
    )
    
    return ReplaySessionRead.model_validate(updated_session)


@router.delete("/replay/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_replay_session(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    """Delete a replay session."""
    workspace, _ = current_workspace
    
    # Check if session exists and user has access
    session = await market_data_service.get_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay session not found",
        )
    
    # Check if user owns the session or is admin
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )
    
    # Delete session
    success = await market_data_service.delete_replay_session(
        db=db,
        session_id=session_id,
        workspace_id=workspace.id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete replay session",
        )
