from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Import and include auth router
from app.api.v1.endpoints import auth
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# Import and include accounts router
from app.api.v1.endpoints import accounts
api_router.include_router(
    accounts.router,
    prefix="/accounts",
    tags=["accounts"]
)

# Import and include trades router
from app.api.v1.endpoints import trades
api_router.include_router(
    trades.router,
    prefix="/trades",
    tags=["trades"]
)

# Add endpoint routers here when they are created
# Example:
# from app.api.v1.endpoints.analytics import router as analytics_router
# api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
