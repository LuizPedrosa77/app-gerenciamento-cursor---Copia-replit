"""
Replay service - engine for managing market replay sessions.
"""
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReplaySession, ReplayStatus
from app.services import market_data_service

logger = logging.getLogger(__name__)


class ReplayEngine:
    """
    Core replay engine that manages playback of market data.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.is_running = False
        self.is_paused = False
        self.current_position = 0
        self.speed_multiplier = Decimal("1.0")
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
    
    async def start(
        self,
        db: AsyncSession,
        workspace_id: str,
        websocket_manager,
    ) -> None:
        """Start the replay engine."""
        if self.is_running:
            return
        
        self.is_running = True
        self.is_paused = False
        self._stop_event.clear()
        
        # Start the replay task
        self._task = asyncio.create_task(
            self._run_replay_loop(db, workspace_id, websocket_manager)
        )
    
    async def pause(self) -> None:
        """Pause the replay engine."""
        self.is_paused = True
    
    async def resume(self) -> None:
        """Resume the replay engine."""
        self.is_paused = False
    
    async def stop(self) -> None:
        """Stop the replay engine."""
        self.is_running = False
        self._stop_event.set()
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def seek_to_position(self, position: int) -> None:
        """Seek to a specific position in the data."""
        self.current_position = max(0, position)
    
    async def seek_to_time(
        self,
        db: AsyncSession,
        workspace_id: str,
        target_time: datetime,
    ) -> None:
        """Seek to a specific time in the data."""
        session = await market_data_service.get_replay_session(
            db, self.session_id, workspace_id
        )
        if not session:
            return
        
        # Get ticks and find position
        ticks = await market_data_service.get_ticks(
            db, session.symbol_id, session.start_time, session.end_time
        )
        
        for i, tick in enumerate(ticks):
            if tick.timestamp >= target_time:
                self.current_position = i
                break
    
    async def set_speed(self, speed: Decimal) -> None:
        """Set the playback speed multiplier."""
        self.speed_multiplier = speed
    
    async def _run_replay_loop(
        self,
        db: AsyncSession,
        workspace_id: str,
        websocket_manager,
    ) -> None:
        """Main replay loop."""
        try:
            session = await market_data_service.get_replay_session(
                db, self.session_id, workspace_id
            )
            if not session:
                return
            
            # Get all ticks for the session
            ticks = await market_data_service.get_ticks(
                db, session.symbol_id, session.start_time, session.end_time
            )
            
            if not ticks:
                await websocket_manager.broadcast_to_session(self.session_id, {
                    "type": "replay_status",
                    "status": ReplayStatus.ERROR,
                    "message": "No ticks found for this session",
                })
                return
            
            # Start from current position
            total_ticks = len(ticks)
            processed = 0
            
            while (
                self.is_running
                and self.current_position < total_ticks
                and not self._stop_event.is_set()
            ):
                # Check if paused
                if self.is_paused:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get current tick
                tick = ticks[self.current_position]
                
                # Calculate delay based on speed
                if self.current_position > 0:
                    prev_tick = ticks[self.current_position - 1]
                    time_diff = (tick.timestamp - prev_tick.timestamp).total_seconds()
                    delay = time_diff / float(self.speed_multiplier)
                    
                    if delay > 0:
                        # Use stop_event for responsive stopping
                        try:
                            await asyncio.wait_for(
                                self._stop_event.wait(), timeout=delay
                            )
                            break  # Stop event was set
                        except asyncio.TimeoutError:
                            pass  # Normal timeout, continue
                
                # Send tick to all connected users
                await websocket_manager.broadcast_to_session(
                    self.session_id,
                    {
                        "type": "replay_tick",
                        "timestamp": tick.timestamp.isoformat(),
                        "bid": float(tick.bid),
                        "ask": float(tick.ask),
                        "volume": tick.volume,
                        "symbol_id": str(tick.symbol_id),
                    }
                )
                
                # Update progress
                processed += 1
                self.current_position += 1
                
                # Update session and send progress every 10 ticks
                if processed % 10 == 0:
                    await self._update_progress(
                        db, workspace_id, tick.timestamp, processed, total_ticks
                    )
                    
                    await websocket_manager.broadcast_to_session(
                        self.session_id,
                        {
                            "type": "replay_progress",
                            "progress": (processed / total_ticks) * 100,
                            "processed_ticks": processed,
                            "total_ticks": total_ticks,
                            "current_time": tick.timestamp.isoformat(),
                        }
                    )
            
            # Session completed
            if self.current_position >= total_ticks:
                await self._complete_session(db, workspace_id)
        
        except asyncio.CancelledError:
            logger.info(f"Replay engine {self.session_id} cancelled")
        except Exception as e:
            logger.error(f"Replay engine {self.session_id} error: {str(e)}")
            await self._error_session(db, workspace_id, str(e))
        finally:
            self.is_running = False
    
    async def _update_progress(
        self,
        db: AsyncSession,
        workspace_id: str,
        current_time: datetime,
        processed: int,
        total: int,
    ) -> None:
        """Update session progress in database."""
        try:
            await market_data_service.update_replay_session(
                db,
                self.session_id,
                workspace_id,
                current_time=current_time,
                processed_ticks=processed,
            )
        except Exception as e:
            logger.error(f"Failed to update progress: {str(e)}")
    
    async def _complete_session(
        self,
        db: AsyncSession,
        workspace_id: str,
    ) -> None:
        """Mark session as completed."""
        try:
            await market_data_service.update_replay_session(
                db,
                self.session_id,
                workspace_id,
                status=ReplayStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            
            # Import here to avoid circular imports
            from app.websocket.replay import replay_manager
            
            await replay_manager.broadcast_to_session(
                self.session_id,
                {
                    "type": "replay_status",
                    "status": ReplayStatus.COMPLETED,
                    "action": "completed",
                    "progress": 100,
                }
            )
        except Exception as e:
            logger.error(f"Failed to complete session: {str(e)}")
    
    async def _error_session(
        self,
        db: AsyncSession,
        workspace_id: str,
        error_message: str,
    ) -> None:
        """Mark session as errored."""
        try:
            await market_data_service.update_replay_session(
                db,
                self.session_id,
                workspace_id,
                status=ReplayStatus.ERROR,
                error_message=error_message,
            )
            
            # Import here to avoid circular imports
            from app.websocket.replay import replay_manager
            
            await replay_manager.broadcast_to_session(
                self.session_id,
                {
                    "type": "replay_status",
                    "status": ReplayStatus.ERROR,
                    "message": error_message,
                }
            )
        except Exception as e:
            logger.error(f"Failed to error session: {str(e)}")


# Global registry of replay engines
replay_engines: Dict[str, ReplayEngine] = {}


def get_replay_engine(session_id: str) -> ReplayEngine:
    """Get or create a replay engine for a session."""
    if session_id not in replay_engines:
        replay_engines[session_id] = ReplayEngine(session_id)
    return replay_engines[session_id]


def remove_replay_engine(session_id: str) -> None:
    """Remove a replay engine from the registry."""
    if session_id in replay_engines:
        engine = replay_engines[session_id]
        asyncio.create_task(engine.stop())
        del replay_engines[session_id]


class CandleBuilder:
    """
    Builds candles from tick data for different timeframes.
    """
    
    def __init__(self, timeframe: str):
        self.timeframe = timeframe
        self.current_candle = None
        self.candles: List[Dict[str, Any]] = []
    
    def add_tick(self, tick: Any) -> Optional[Dict[str, Any]]:
        """Add a tick and return completed candle if available."""
        from datetime import timedelta
        
        if not self.current_candle:
            self.current_candle = self._create_new_candle(tick)
            return None
        
        # Check if tick belongs to current candle
        candle_time = self._get_candle_time(tick.timestamp)
        
        if candle_time == self.current_candle["open_time"]:
            # Update current candle
            self.current_candle["high"] = max(self.current_candle["high"], float(tick.bid))
            self.current_candle["low"] = min(self.current_candle["low"], float(tick.bid))
            self.current_candle["close"] = float(tick.bid)
            self.current_candle["volume"] = self.current_candle.get("volume", 0) + (tick.volume or 0)
            self.current_candle["tick_volume"] = self.current_candle.get("tick_volume", 0) + 1
            
            # Calculate spread
            if tick.ask and tick.bid:
                spread = int((float(tick.ask) - float(tick.bid)) * 10000)  # Convert to pips
                if self.current_candle.get("spread") is None:
                    self.current_candle["spread"] = spread
                else:
                    # Average spread
                    self.current_candle["spread"] = (self.current_candle["spread"] + spread) // 2
            
            return None
        else:
            # Complete current candle and start new one
            completed_candle = self.current_candle.copy()
            self.current_candle = self._create_new_candle(tick)
            self.candles.append(completed_candle)
            return completed_candle
    
    def _create_new_candle(self, tick: Any) -> Dict[str, Any]:
        """Create a new candle from tick."""
        candle_time = self._get_candle_time(tick.timestamp)
        
        return {
            "open_time": candle_time,
            "close_time": candle_time + self._get_timeframe_delta(),
            "open": float(tick.bid),
            "high": float(tick.bid),
            "low": float(tick.bid),
            "close": float(tick.bid),
            "volume": tick.volume or 0,
            "tick_volume": 1,
            "spread": int((float(tick.ask) - float(tick.bid)) * 10000) if tick.ask and tick.bid else None,
        }
    
    def _get_candle_time(self, timestamp: datetime) -> datetime:
        """Get the candle start time for a given timestamp."""
        from datetime import timedelta
        
        if self.timeframe == "M1":
            return timestamp.replace(second=0, microsecond=0)
        elif self.timeframe == "M5":
            minute = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif self.timeframe == "M15":
            minute = (timestamp.minute // 15) * 15
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif self.timeframe == "M30":
            minute = (timestamp.minute // 30) * 30
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif self.timeframe == "H1":
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif self.timeframe == "H4":
            hour = (timestamp.hour // 4) * 4
            return timestamp.replace(hour=hour, minute=0, second=0, microsecond=0)
        elif self.timeframe == "D1":
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to M1 for unknown timeframes
            return timestamp.replace(second=0, microsecond=0)
    
    def _get_timeframe_delta(self) -> timedelta:
        """Get the time delta for the current timeframe."""
        from datetime import timedelta
        
        timeframe_deltas = {
            "M1": timedelta(minutes=1),
            "M5": timedelta(minutes=5),
            "M15": timedelta(minutes=15),
            "M30": timedelta(minutes=30),
            "H1": timedelta(hours=1),
            "H4": timedelta(hours=4),
            "D1": timedelta(days=1),
        }
        
        return timeframe_deltas.get(self.timeframe, timedelta(minutes=1))
    
    def get_current_candle(self) -> Optional[Dict[str, Any]]:
        """Get the current (in-progress) candle."""
        return self.current_candle
    
    def get_completed_candles(self) -> List[Dict[str, Any]]:
        """Get all completed candles."""
        return self.candles.copy()
    
    def finish(self) -> Optional[Dict[str, Any]]:
        """Finish candle building and return the last candle."""
        if self.current_candle:
            self.candles.append(self.current_candle)
            last_candle = self.current_candle
            self.current_candle = None
            return last_candle
        return None
