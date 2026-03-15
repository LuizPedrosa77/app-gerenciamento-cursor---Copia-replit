from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.websocket.trade_ws import websocket_trades

app = FastAPI(title="Gustavo Pedrosa FX API", redirect_slashes=False)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://fx.hubnexusai.com",
        "https://fx.painelzap.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

app.add_api_websocket_route("/ws/trades", websocket_trades)


@app.get("/")
def health_check():
    return {"status": "ok"}
