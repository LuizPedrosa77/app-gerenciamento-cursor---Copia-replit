"""
Broker connection management endpoints.
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import CurrentUser, CurrentWorkspace, DbSession
from app.services import broker_service

router = APIRouter()


# Request/Response schemas
class BrokerConnectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    broker_type: str = Field(..., min_length=1, max_length=50)
    is_demo: bool = Field(default=False)
    credentials: dict = Field(...)


class BrokerConnectionTest(BaseModel):
    broker_type: str = Field(..., min_length=1, max_length=50)
    credentials: dict = Field(...)


class BrokerConnectionRead(BaseModel):
    id: UUID
    name: str
    broker_type: str
    account_id: str
    currency: str
    balance: float
    is_demo: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class BrokerInfo(BaseModel):
    type: str
    name: str
    platforms: list[str]


class BrokerTradeRead(BaseModel):
    external_id: str
    symbol: str
    side: str
    volume: float
    open_time: datetime
    close_time: datetime | None = None
    open_price: float
    close_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    commission: float
    swap: float
    profit: float
    status: str
    comment: str | None = None
    magic_number: int | None = None
    strategy_name: str | None = None

    model_config = {"from_attributes": True}


class SyncHistoryRequest(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None


@router.get("/brokers", response_model=list[BrokerInfo])
def list_available_brokers():
    """List all available broker types."""
    brokers = broker_service.get_available_brokers()
    return [BrokerInfo(**broker) for broker in brokers]


@router.post("/brokers/test")
async def test_broker_connection(body: BrokerConnectionTest):
    """Test broker connection without saving."""
    try:
        success = await broker_service.test_connection(
            broker_type=body.broker_type,
            credentials=body.credentials,
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {str(e)}",
        )


@router.post("/brokers/connections", response_model=BrokerConnectionRead, status_code=status.HTTP_201_CREATED)
async def create_broker_connection(
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
    body: BrokerConnectionCreate,
):
    """Create a new broker connection."""
    workspace, _ = current_workspace
    
    try:
        connection = await broker_service.create_connection(
            db=db,
            workspace_id=workspace.id,
            broker_type=body.broker_type,
            name=body.name,
            credentials=body.credentials,
            is_demo=body.is_demo,
        )
        return BrokerConnectionRead(**connection)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create connection: {str(e)}",
        )


@router.get("/brokers/connections", response_model=list[BrokerConnectionRead])
async def list_broker_connections(
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    """List all broker connections for workspace."""
    workspace, _ = current_workspace
    
    connections = await broker_service.list_connections(
        db=db,
        workspace_id=workspace.id,
    )
    return [BrokerConnectionRead(**conn) for conn in connections]


@router.delete("/brokers/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_broker_connection(
    connection_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    """Delete a broker connection."""
    workspace, _ = current_workspace
    
    success = await broker_service.delete_connection(
        db=db,
        workspace_id=workspace.id,
        account_id=connection_id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )


@router.post("/brokers/connections/{connection_id}/test")
async def test_existing_connection(
    connection_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    """Test an existing broker connection."""
    workspace, _ = current_workspace
    
    # For now, we'll just return success since we don't have stored credentials
    # In production, this would decrypt stored credentials and test the connection
    return {"success": True}


@router.post("/brokers/connections/{connection_id}/sync", response_model=list[BrokerTradeRead])
async def sync_broker_history(
    connection_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
    body: SyncHistoryRequest,
):
    """Sync trade history from broker."""
    workspace, _ = current_workspace
    
    try:
        trades = await broker_service.sync_history(
            db=db,
            workspace_id=workspace.id,
            account_id=connection_id,
            start_date=body.start_date,
            end_date=body.end_date,
        )
        return [BrokerTradeRead(**trade) for trade in trades]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


@router.get("/brokers/connections/{connection_id}/account")
async def get_connection_account_info(
    connection_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    """Get account information for a broker connection."""
    workspace, _ = current_workspace
    
    # For now, we'll return mock data since we don't have stored credentials
    # In production, this would decrypt stored credentials and get real account info
    return {
        "id": str(connection_id),
        "account_id": "demo_account",
        "name": "Demo Account",
        "broker": "Demo Broker",
        "currency": "USD",
        "balance": 10000.0,
        "equity": 10500.0,
        "margin": 500.0,
        "free_margin": 10000.0,
        "leverage": 100,
        "is_demo": True,
    }
