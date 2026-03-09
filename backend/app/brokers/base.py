"""
Base interface for all broker adapters.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class BrokerAccountInfo:
    """Account information from broker."""
    account_id: str
    account_name: str
    broker_name: str
    currency: str
    balance: Decimal
    equity: Decimal
    margin: Decimal
    free_margin: Decimal
    leverage: int
    is_demo: bool
    server: Optional[str] = None
    platform: Optional[str] = None


@dataclass
class BrokerTrade:
    """Trade information from broker."""
    external_id: str
    symbol: str
    side: str  # buy/sell
    volume: Decimal
    open_time: datetime
    close_time: Optional[datetime]
    open_price: Decimal
    close_price: Optional[Decimal]
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    commission: Decimal
    swap: Decimal
    profit: Decimal
    status: str  # open/closed
    comment: Optional[str] = None
    magic_number: Optional[int] = None
    strategy_name: Optional[str] = None


@dataclass
class BrokerSymbol:
    """Symbol information from broker."""
    symbol: str
    description: str
    digits: int
    point: Decimal
    tick_size: Decimal
    contract_size: Decimal
    min_lot: Decimal
    max_lot: Decimal
    lot_step: Decimal
    spread: Optional[int] = None
    is_tradeable: bool = True


@dataclass
class BrokerConnectionConfig:
    """Connection configuration for broker."""
    broker_type: str
    server: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_number: Optional[str] = None
    environment: str = "live"  # live/demo
    additional_params: Optional[Dict[str, Any]] = None


class BrokerConnectionError(Exception):
    """Raised when broker connection fails."""
    pass


class BrokerAuthenticationError(BrokerConnectionError):
    """Raised when broker authentication fails."""
    pass


class BrokerDataError(Exception):
    """Raised when broker data retrieval fails."""
    pass


class BrokerAdapter(ABC):
    """Abstract base class for broker adapters."""

    def __init__(self, config: BrokerConnectionConfig):
        self.config = config
        self._connected = False

    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Return the broker name."""
        pass

    @property
    @abstractmethod
    def supported_platforms(self) -> List[str]:
        """Return list of supported platforms."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to broker."""
        pass

    @abstractmethod
    async def get_account_info(self) -> BrokerAccountInfo:
        """Get account information."""
        pass

    @abstractmethod
    async def sync_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BrokerTrade]:
        """Sync trade history from broker."""
        pass

    @abstractmethod
    async def list_symbols(self) -> List[BrokerSymbol]:
        """List available symbols."""
        pass

    async def connect(self) -> None:
        """Establish connection to broker."""
        if await self.test_connection():
            self._connected = True
        else:
            raise BrokerConnectionError(f"Failed to connect to {self.broker_name}")

    async def disconnect(self) -> None:
        """Close connection to broker."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self._connected

    def validate_config(self) -> None:
        """Validate connection configuration."""
        if not self.config.broker_type:
            raise BrokerConnectionError("Broker type is required")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
