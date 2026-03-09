"""
Broker connection and synchronization service.
"""
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import TradingAccount
from app.brokers.base import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerAccountInfo,
    BrokerTrade,
)
from app.brokers.exceptions import BrokerConnectionError, BrokerError
from app.brokers.mt5 import MT5Adapter
from app.brokers.mt4 import MT4Adapter
from app.brokers.ctrader import CTraderAdapter
from app.brokers.tradovate import TradovateAdapter
from app.brokers.ninjatrader import NinjaTraderAdapter


# Broker adapter registry
BROKER_ADAPTERS: Dict[str, type[BrokerAdapter]] = {
    "mt5": MT5Adapter,
    "mt4": MT4Adapter,
    "ctrader": CTraderAdapter,
    "tradovate": TradovateAdapter,
    "ninjatrader": NinjaTraderAdapter,
}


def get_encryption_key() -> bytes:
    """Get encryption key for broker credentials."""
    import base64
    return base64.b64decode(settings.BROKER_CREDENTIALS_KEY.encode())


def encrypt_credentials(data: Dict[str, Any]) -> str:
    """Encrypt broker credentials."""
    key = get_encryption_key()
    fernet = Fernet(key)
    json_data = json.dumps(data)
    encrypted_data = fernet.encrypt(json_data.encode())
    return encrypted_data.decode()


def decrypt_credentials(encrypted_data: str) -> Dict[str, Any]:
    """Decrypt broker credentials."""
    key = get_encryption_key()
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data.encode())
    return json.loads(decrypted_data.decode())


def create_broker_adapter(
    broker_type: str,
    credentials: Dict[str, Any],
) -> BrokerAdapter:
    """Create broker adapter instance."""
    adapter_class = BROKER_ADAPTERS.get(broker_type.lower())
    if not adapter_class:
        raise ValueError(f"Unsupported broker type: {broker_type}")

    config = BrokerConnectionConfig(
        broker_type=broker_type,
        server=credentials.get("server"),
        login=credentials.get("login"),
        password=credentials.get("password"),
        api_key=credentials.get("api_key"),
        api_secret=credentials.get("api_secret"),
        account_number=credentials.get("account_number"),
        environment=credentials.get("environment", "live"),
        additional_params=credentials.get("additional_params"),
    )

    return adapter_class(config)


async def create_connection(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    broker_type: str,
    name: str,
    credentials: Dict[str, Any],
    is_demo: bool = False,
) -> Dict[str, Any]:
    """Create a new broker connection."""
    # Test connection first
    adapter = create_broker_adapter(broker_type, credentials)
    
    try:
        connection_success = await adapter.test_connection()
        if not connection_success:
            raise BrokerConnectionError("Failed to connect to broker")
    except Exception as e:
        raise BrokerConnectionError(f"Connection test failed: {str(e)}")

    # Get account info
    try:
        account_info = await adapter.get_account_info()
    except Exception as e:
        raise BrokerError(f"Failed to get account info: {str(e)}")

    # Encrypt credentials
    encrypted_credentials = encrypt_credentials(credentials)

    # Create trading account record
    account = TradingAccount(
        workspace_id=workspace_id,
        name=name,
        currency=account_info.currency,
        platform=broker_type,
        is_demo=is_demo or account_info.is_demo,
        initial_balance=account_info.balance,
        current_balance=account_info.balance,
        leverage=account_info.leverage,
        # Store encrypted credentials temporarily until we have broker_connections table
        # This will be moved to broker_connections table in migration 003
        external_account_id=account_info.account_id,
    )

    db.add(account)
    await db.commit()
    await db.refresh(account)

    return {
        "id": account.id,
        "name": account.name,
        "broker_type": broker_type,
        "account_id": account_info.account_id,
        "currency": account_info.currency,
        "balance": float(account_info.balance),
        "is_demo": account.is_demo,
        "created_at": account.created_at,
    }


async def test_connection(
    broker_type: str,
    credentials: Dict[str, Any],
) -> bool:
    """Test broker connection without saving."""
    adapter = create_broker_adapter(broker_type, credentials)
    
    try:
        return await adapter.test_connection()
    except Exception:
        return False


async def get_account_info(
    broker_type: str,
    credentials: Dict[str, Any],
) -> BrokerAccountInfo:
    """Get account information without saving."""
    adapter = create_broker_adapter(broker_type, credentials)
    
    try:
        await adapter.connect()
        return await adapter.get_account_info()
    finally:
        await adapter.disconnect()


async def list_connections(
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> List[Dict[str, Any]]:
    """List all broker connections for workspace."""
    result = await db.execute(
        select(TradingAccount).where(
            TradingAccount.workspace_id == workspace_id,
            TradingAccount.platform.in_(list(BROKER_ADAPTERS.keys())),
        )
    )
    accounts = result.scalars().all()

    connections = []
    for account in accounts:
        connections.append({
            "id": account.id,
            "name": account.name,
            "broker_type": account.platform,
            "account_id": account.external_account_id,
            "currency": account.currency,
            "balance": float(account.current_balance),
            "is_demo": account.is_demo,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
        })

    return connections


async def delete_connection(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    account_id: uuid.UUID,
) -> bool:
    """Delete a broker connection."""
    result = await db.execute(
        select(TradingAccount).where(
            TradingAccount.id == account_id,
            TradingAccount.workspace_id == workspace_id,
            TradingAccount.platform.in_(list(BROKER_ADAPTERS.keys())),
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        return False

    await db.delete(account)
    await db.commit()
    return True


async def sync_history(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    account_id: uuid.UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Sync trade history from broker."""
    # Get account
    result = await db.execute(
        select(TradingAccount).where(
            TradingAccount.id == account_id,
            TradingAccount.workspace_id == workspace_id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise ValueError("Account not found")

    # For now, we'll use mock data since credentials aren't stored yet
    # In production, this would decrypt stored credentials
    broker_type = account.platform
    
    # Mock credentials for demonstration
    mock_credentials = {
        "login": "demo",
        "password": "demo",
        "server": "demo-server",
        "environment": "demo" if account.is_demo else "live",
    }

    adapter = create_broker_adapter(broker_type, mock_credentials)
    
    try:
        await adapter.connect()
        trades = await adapter.sync_history(start_date, end_date)
        
        # Convert to dict format
        trade_dicts = []
        for trade in trades:
            trade_dict = {
                "external_id": trade.external_id,
                "symbol": trade.symbol,
                "side": trade.side,
                "volume": float(trade.volume),
                "open_time": trade.open_time,
                "close_time": trade.close_time,
                "open_price": float(trade.open_price),
                "close_price": float(trade.close_price) if trade.close_price else None,
                "stop_loss": float(trade.stop_loss) if trade.stop_loss else None,
                "take_profit": float(trade.take_profit) if trade.take_profit else None,
                "commission": float(trade.commission),
                "swap": float(trade.swap),
                "profit": float(trade.profit),
                "status": trade.status,
                "comment": trade.comment,
                "magic_number": trade.magic_number,
                "strategy_name": trade.strategy_name,
            }
            trade_dicts.append(trade_dict)

        return trade_dicts

    finally:
        await adapter.disconnect()


async def get_available_brokers() -> List[Dict[str, Any]]:
    """Get list of available broker types."""
    brokers = []
    
    for broker_type, adapter_class in BROKER_ADAPTERS.items():
        adapter = adapter_class(BrokerConnectionConfig(broker_type=broker_type))
        brokers.append({
            "type": broker_type,
            "name": adapter.broker_name,
            "platforms": adapter.supported_platforms,
        })

    return brokers
