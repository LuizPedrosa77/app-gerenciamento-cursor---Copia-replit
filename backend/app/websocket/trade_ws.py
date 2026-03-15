import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)


class TradeConnectionManager:
    def __init__(self):
        self.active: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active:
            self.active[user_id] = set()
        self.active[user_id].add(websocket)
        logger.info(f"[WS] Conectado: user={user_id} | conexoes={len(self.active[user_id])}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active:
            self.active[user_id].discard(websocket)
            if not self.active[user_id]:
                del self.active[user_id]
        logger.info(f"[WS] Desconectado: user={user_id}")

    async def send_to_user(self, user_id: str, event: dict):
        connections = self.active.get(str(user_id), set())
        if not connections:
            return
        dead = set()
        payload = json.dumps(event, default=str)
        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active[str(user_id)].discard(ws)

    def is_connected(self, user_id: str) -> bool:
        return bool(self.active.get(str(user_id)))


manager = TradeConnectionManager()


def get_user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    except JWTError:
        return None


async def websocket_trades(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    user = get_user_from_token(token, db)
    if not user:
        await websocket.close(code=4001, reason="Token inválido")
        return

    user_id = str(user.id)
    await manager.connect(user_id, websocket)

    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": user_id,
        }))

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[WS] Erro user={user_id}: {e}")
    finally:
        manager.disconnect(user_id, websocket)
