"""
MetaTrader 4 broker adapter (stub implementation).
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from .base import (
    BrokerAccountInfo,
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerConnectionError,
    BrokerTrade,
    BrokerSymbol,
)
from .exceptions import BrokerAuthenticationError, BrokerDataError


class MT4Adapter(BrokerAdapter):
    """MetaTrader 4 broker adapter (stub implementation)."""

    def __init__(self, config: BrokerConnectionConfig):
        super().__init__(config)
        self.validate_config()

    @property
    def broker_name(self) -> str:
        return "MetaTrader 4"

    @property
    def supported_platforms(self) -> List[str]:
        return ["mt4"]

    def validate_config(self) -> None:
        super().validate_config()
        if not self.config.login or not self.config.password:
            raise BrokerConnectionError("MT4 requires login and password")
        if not self.config.server:
            raise BrokerConnectionError("MT4 requires server address")

    async def test_connection(self) -> bool:
        """Test connection to MT4 (mock implementation)."""
        # MT4 doesn't have official Python API
        # This would require third-party libraries or bridge solutions
        return await self._mock_test_connection()

    async def get_account_info(self) -> BrokerAccountInfo:
        """Get account information from MT4 (mock implementation)."""
        return await self._mock_account_info()

    async def sync_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BrokerTrade]:
        """Sync trade history from MT4 (mock implementation)."""
        return await self._mock_history(start_date, end_date)

    async def list_symbols(self) -> List[BrokerSymbol]:
        """List available symbols from MT4 (mock implementation)."""
        return await self._mock_symbols()

    # Mock methods (MT4 integration would require third-party solutions)
    async def _mock_test_connection(self) -> bool:
        """Mock test connection."""
        return True

    async def _mock_account_info(self) -> BrokerAccountInfo:
        """Mock account info."""
        return BrokerAccountInfo(
            account_id=self.config.login or "12345678",
            account_name="MT4 Demo Account",
            broker_name=self.config.server or "MetaQuotes-Demo",
            currency="USD",
            balance=Decimal("10000.00"),
            equity=Decimal("10500.00"),
            margin=Decimal("500.00"),
            free_margin=Decimal("10000.00"),
            leverage=100,
            is_demo=True,
            server=self.config.server or "MetaQuotes-Demo",
            platform="mt4",
        )

    async def _mock_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BrokerTrade]:
        """Mock trade history."""
        return [
            BrokerTrade(
                external_id="MT4-123456",
                symbol="EUR/USD",
                side="buy",
                volume=Decimal("0.1"),
                open_time=datetime.now() - timedelta(hours=3),
                close_time=datetime.now() - timedelta(hours=2),
                open_price=Decimal("1.08400"),
                close_price=Decimal("1.08500"),
                stop_loss=Decimal("1.08300"),
                take_profit=Decimal("1.08600"),
                commission=Decimal("0.5"),
                swap=Decimal("0.0"),
                profit=Decimal("10.00"),
                status="closed",
                comment="MT4 mock trade",
                magic_number=456,
            )
        ]

    async def _mock_symbols(self) -> List[BrokerSymbol]:
        """Mock symbols list."""
        return [
            BrokerSymbol(
                symbol="EUR/USD",
                description="Euro vs US Dollar",
                digits=4,  # MT4 typically uses 4 digits for forex
                point=Decimal("0.0001"),
                tick_size=Decimal("0.0001"),
                contract_size=Decimal("100000"),
                min_lot=Decimal("0.01"),
                max_lot=Decimal("100"),
                lot_step=Decimal("0.01"),
                spread=2,
                is_tradeable=True,
            ),
            BrokerSymbol(
                symbol="GBP/USD",
                description="British Pound vs US Dollar",
                digits=4,
                point=Decimal("0.0001"),
                tick_size=Decimal("0.0001"),
                contract_size=Decimal("100000"),
                min_lot=Decimal("0.01"),
                max_lot=Decimal("100"),
                lot_step=Decimal("0.01"),
                spread=3,
                is_tradeable=True,
            ),
        ]
