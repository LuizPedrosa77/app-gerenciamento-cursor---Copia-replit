"""
WebSocket handler for market replay sessions.
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models import ReplaySession, ReplayStatus, User, Workspace
from app.services import market_data_service
from app.dependencies import get_current_user_from_token


class ReplayConnectionManager:
    """Manages WebSocket connections for replay sessions."""
    
    def __init__(self):
        # Mapping: session_id -> {user_id: websocket}
        self.active_connections: Dict[uuid.UUID, Dict[uuid.UUID, WebSocket]] = {}
        # Mapping: session_id -> asyncio.Task (replay engine)
        self.active_replays: Dict[uuid.UUID, asyncio.Task] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Connect a user to a replay session."""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        
        self.active_connections[session_id][user_id] = websocket
    
    def disconnect(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Disconnect a user from a replay session."""
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(user_id, None)
            
            # Clean up empty sessions
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                
                # Stop replay if running
                if session_id in self.active_replays:
                    self.active_replays[session_id].cancel()
                    del self.active_replays[session_id]
    
    async def send_to_user(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        message: Dict[str, Any],
    ) -> None:
        """Send message to specific user in session."""
        if (
            session_id in self.active_connections
            and user_id in self.active_connections[session_id]
        ):
            websocket = self.active_connections[session_id][user_id]
            await websocket.send_text(json.dumps(message))
    
    async def broadcast_to_session(
        self,
        session_id: uuid.UUID,
        message: Dict[str, Any],
        exclude_user: Optional[uuid.UUID] = None,
    ) -> None:
        """Broadcast message to all users in session."""
        if session_id not in self.active_connections:
            return
        
        for user_id, websocket in self.active_connections[session_id].items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await websocket.send_text(json.dumps(message))
            except:
                # Remove dead connections
                self.disconnect(session_id, user_id)
    
    def get_session_users(self, session_id: uuid.UUID) -> list[uuid.UUID]:
        """Get all connected users for a session."""
        if session_id in self.active_connections:
            return list(self.active_connections[session_id].keys())
        return []


# Global connection manager
replay_manager = ReplayConnectionManager()


async def handle_replay_websocket(
    websocket: WebSocket,
    session_id: uuid.UUID,
    token: Optional[str] = Query(None),
    db: AsyncSession = None,
) -> None:
    """
    Handle WebSocket connection for replay session.
    
    WebSocket events:
    - Client → Server: play, pause, stop, seek, set_speed
    - Server → Client: replay_tick, replay_candle, replay_status, replay_progress
    """
    # Authenticate user
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    try:
        user = await get_current_user_from_token(token, db)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Get session and verify access
    session = await market_data_service.get_replay_session(db, session_id, user.workspace_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    # Connect user to session
    await replay_manager.connect(websocket, session_id, user.id)
    
    try:
        # Send initial status
        await replay_manager.send_to_user(session_id, user.id, {
            "type": "replay_status",
            "status": session.status,
            "current_time": session.current_time.isoformat() if session.current_time else None,
            "speed": float(session.speed),
            "progress": (session.processed_ticks / session.total_ticks * 100) if session.total_ticks > 0 else 0,
        })
        
        # Handle messages
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                await handle_client_message(
                    db, session_id, user.id, user.workspace_id, data
                )
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await replay_manager.send_to_user(session_id, user.id, {
                    "type": "error",
                    "message": "Invalid JSON format",
                })
            except Exception as e:
                await replay_manager.send_to_user(session_id, user.id, {
                    "type": "error",
                    "message": str(e),
                })
    
    finally:
        replay_manager.disconnect(session_id, user.id)


async def handle_client_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: Dict[str, Any],
) -> None:
    """Handle client WebSocket message."""
    message_type = data.get("type")
    
    if message_type == "play":
        await handle_play_command(db, session_id, user_id, workspace_id, data)
    elif message_type == "pause":
        await handle_pause_command(db, session_id, user_id, workspace_id)
    elif message_type == "stop":
        await handle_stop_command(db, session_id, user_id, workspace_id)
    elif message_type == "seek":
        await handle_seek_command(db, session_id, user_id, workspace_id, data)
    elif message_type == "set_speed":
        await handle_set_speed_command(db, session_id, user_id, workspace_id, data)
    else:
        await replay_manager.send_to_user(session_id, user_id, {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
        })


async def handle_play_command(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: Dict[str, Any],
) -> None:
    """Handle play command."""
    session = await market_data_service.get_replay_session(db, session_id, workspace_id)
    if not session:
        return
    
    if session.status == ReplayStatus.RUNNING:
        return  # Already running
    
    # Update session status
    await market_data_service.update_replay_session(
        db, session_id, workspace_id,
        status=ReplayStatus.RUNNING,
        started_at=datetime.now(timezone.utc) if not session.started_at else None,
    )
    
    # Start replay engine if not already running
    if session_id not in replay_manager.active_replays:
        task = asyncio.create_task(
            run_replay_engine(db, session_id, workspace_id)
        )
        replay_manager.active_replays[session_id] = task
    
    # Broadcast status to all users
    await replay_manager.broadcast_to_session(session_id, {
        "type": "replay_status",
        "status": ReplayStatus.RUNNING,
        "action": "play",
    })


async def handle_pause_command(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> None:
    """Handle pause command."""
    session = await market_data_service.get_replay_session(db, session_id, workspace_id)
    if not session:
        return
    
    if session.status != ReplayStatus.RUNNING:
        return  # Not running
    
    # Update session status
    await market_data_service.update_replay_session(
        db, session_id, workspace_id,
        status=ReplayStatus.PAUSED,
    )
    
    # Stop replay engine
    if session_id in replay_manager.active_replays:
        replay_manager.active_replays[session_id].cancel()
        del replay_manager.active_replays[session_id]
    
    # Broadcast status to all users
    await replay_manager.broadcast_to_session(session_id, {
        "type": "replay_status",
        "status": ReplayStatus.PAUSED,
        "action": "pause",
    })


async def handle_stop_command(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> None:
    """Handle stop command."""
    session = await market_data_service.get_replay_session(db, session_id, workspace_id)
    if not session:
        return
    
    # Update session status
    await market_data_service.update_replay_session(
        db, session_id, workspace_id,
        status=ReplayStatus.COMPLETED,
        completed_at=datetime.now(timezone.utc),
        current_time=session.start_time,  # Reset to start
        processed_ticks=0,
    )
    
    # Stop replay engine
    if session_id in replay_manager.active_replays:
        replay_manager.active_replays[session_id].cancel()
        del replay_manager.active_replays[session_id]
    
    # Broadcast status to all users
    await replay_manager.broadcast_to_session(session_id, {
        "type": "replay_status",
        "status": ReplayStatus.COMPLETED,
        "action": "stop",
    })


async def handle_seek_command(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: Dict[str, Any],
) -> None:
    """Handle seek command."""
    target_time_str = data.get("target_time")
    if not target_time_str:
        await replay_manager.send_to_user(session_id, user_id, {
            "type": "error",
            "message": "Missing target_time",
        })
        return
    
    try:
        target_time = datetime.fromisoformat(target_time_str.replace('Z', '+00:00'))
    except ValueError:
        await replay_manager.send_to_user(session_id, user_id, {
            "type": "error",
            "message": "Invalid target_time format",
        })
        return
    
    session = await market_data_service.get_replay_session(db, session_id, workspace_id)
    if not session:
        return
    
    # Update session current time
    await market_data_service.update_replay_session(
        db, session_id, workspace_id,
        current_time=target_time,
    )
    
    # Broadcast to all users
    await replay_manager.broadcast_to_session(session_id, {
        "type": "replay_status",
        "status": session.status,
        "action": "seek",
        "current_time": target_time.isoformat(),
    })


async def handle_set_speed_command(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: Dict[str, Any],
) -> None:
    """Handle set_speed command."""
    speed = data.get("speed")
    if speed is None:
        await replay_manager.send_to_user(session_id, user_id, {
            "type": "error",
            "message": "Missing speed",
        })
        return
    
    try:
        speed_decimal = Decimal(str(speed))
        if speed_decimal < Decimal("0.1") or speed_decimal > Decimal("10"):
            raise ValueError("Speed must be between 0.1 and 10")
    except (ValueError, TypeError):
        await replay_manager.send_to_user(session_id, user_id, {
            "type": "error",
            "message": "Invalid speed value (must be between 0.1 and 10)",
        })
        return
    
    session = await market_data_service.get_replay_session(db, session_id, workspace_id)
    if not session:
        return
    
    # Update session speed
    await market_data_service.update_replay_session(
        db, session_id, workspace_id,
        speed=speed_decimal,
    )
    
    # Broadcast to all users
    await replay_manager.broadcast_to_session(session_id, {
        "type": "replay_status",
        "status": session.status,
        "action": "set_speed",
        "speed": float(speed_decimal),
    })


async def run_replay_engine(
    db: AsyncSession,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> None:
    """
    Run the replay engine for a session.
    This runs in the background and sends ticks/candles to connected clients.
    """
    try:
        session = await market_data_service.get_replay_session(db, session_id, workspace_id)
        if not session:
            return
        
        # Get ticks for the session
        ticks = await market_data_service.get_ticks(
            db, session.symbol_id, session.start_time, session.end_time
        )
        
        if not ticks:
            await replay_manager.broadcast_to_session(session_id, {
                "type": "replay_status",
                "status": ReplayStatus.ERROR,
                "message": "No ticks found for this session",
            })
            return
        
        # Find current position
        current_time = session.current_time or session.start_time
        current_index = 0
        
        for i, tick in enumerate(ticks):
            if tick.timestamp >= current_time:
                current_index = i
                break
        
        # Replay ticks
        processed = 0
        for tick in ticks[current_index:]:
            # Check if session is still running
            current_session = await market_data_service.get_replay_session(db, session_id, workspace_id)
            if not current_session or current_session.status != ReplayStatus.RUNNING:
                break
            
            # Calculate delay based on speed
            if current_index > 0:
                prev_tick = ticks[current_index - 1]
                time_diff = (tick.timestamp - prev_tick.timestamp).total_seconds()
                delay = time_diff / float(current_session.speed)
                if delay > 0:
                    await asyncio.sleep(delay)
            
            # Send tick to all connected users
            await replay_manager.broadcast_to_session(session_id, {
                "type": "replay_tick",
                "timestamp": tick.timestamp.isoformat(),
                "bid": float(tick.bid),
                "ask": float(tick.ask),
                "volume": tick.volume,
                "symbol_id": str(tick.symbol_id),
            })
            
            # Update progress
            processed += 1
            progress = (processed / len(ticks)) * 100
            
            # Update session every 10 ticks
            if processed % 10 == 0:
                await market_data_service.update_replay_session(
                    db, session_id, workspace_id,
                    current_time=tick.timestamp,
                    processed_ticks=processed,
                )
                
                # Send progress update
                await replay_manager.broadcast_to_session(session_id, {
                    "type": "replay_progress",
                    "progress": progress,
                    "processed_ticks": processed,
                    "total_ticks": len(ticks),
                    "current_time": tick.timestamp.isoformat(),
                })
            
            current_index += 1
        
        # Session completed
        await market_data_service.update_replay_session(
            db, session_id, workspace_id,
            status=ReplayStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
            processed_ticks=processed,
        )
        
        await replay_manager.broadcast_to_session(session_id, {
            "type": "replay_status",
            "status": ReplayStatus.COMPLETED,
            "action": "completed",
            "progress": 100,
        })
        
    except asyncio.CancelledError:
        # Replay was cancelled (paused/stopped)
        pass
    except Exception as e:
        # Error occurred
        await market_data_service.update_replay_session(
            db, session_id, workspace_id,
            status=ReplayStatus.ERROR,
            error_message=str(e),
        )
        
        await replay_manager.broadcast_to_session(session_id, {
            "type": "replay_status",
            "status": ReplayStatus.ERROR,
            "message": str(e),
        })
    finally:
        # Clean up
        if session_id in replay_manager.active_replays:
            del replay_manager.active_replays[session_id]
