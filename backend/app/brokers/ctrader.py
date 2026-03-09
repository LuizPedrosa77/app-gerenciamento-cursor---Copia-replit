"""
cTrader broker adapter (stub implementation).
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


class CTraderAdapter(BrokerAdapter):
    """cTrader broker adapter (stub implementation)."""

    def __init__(self, config: BrokerConnectionConfig):
        super().__init__(config)
        self.validate_config()

    @property
    def broker_name(self) -> str:
        return "cTrader"

    @property
    def supported_platforms(self) -> List[str]:
        return ["ctrader"]

    def validate_config(self) -> None:
        super().validate_config()
        if not self.config.login or not self.config.password:
            raise BrokerConnectionError("cTrader requires login and password")
        # cTrader typically uses account number + password
        if not self.config.account_number:
            raise BrokerConnectionError("cTrader requires account number")

    async def test_connection(self) -> bool:
        """Test connection to cTrader (mock implementation)."""
        # cTrader Open API would be implemented here
        return await self._mock_test_connection()

    async def get_account_info(self) -> BrokerAccountInfo:
        """Get account information from cTrader (mock implementation)."""
        return await self._mock_account_info()

    async def sync_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BrokerTrade]:
        """Sync trade history from cTrader (mock implementation)."""
        return await self._mock_history(start_date, end_date)

    async def list_symbols(self) -> List[BrokerSymbol]:
        """List available symbols from cTrader (mock implementation)."""
        return await self._mock_symbols()

    # Mock methods (cTrader Open API integration would go here)
    async def _mock_test_connection(self) -> bool:
        """Mock test connection."""
        return True

    async def _mock_account_info(self) -> BrokerAccountInfo:
        """Mock account info."""
        return BrokerAccountInfo(
            account_id=self.config.account_number or "12345678",
            account_name="cTrader Demo Account",
            broker_name="cTrader",
            currency="USD",
            balance=Decimal("10000.00"),
            equity=Decimal("10500.00"),
            margin=Decimal("500.00"),
            free_margin=Decimal("10000.00"),
            leverage=100,
            is_demo=self.config.environment == "demo",
            server="cTrader Demo",
            platform="ctrader",
        )

    async def _mock_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BrokerTrade]:
        """Mock trade history."""
        return [
            BrokerTrade(
                external_id="CT-123456",
                symbol="EUR/USD",
                side="buy",
                volume=Decimal("0.1"),
                open_time=datetime.now() - timedelta(hours=4),
                close_time=datetime.now() - timedelta(hours=3),
                open_price=Decimal("1.08300"),
                close_price=Decimal("1.08400"),
                stop_loss=Decimal("1.08200"),
                take_profit=Decimal("1.08500"),
                commission=Decimal("0.7"),
                swap=Decimal("0.0"),
                profit=Decimal("10.00"),
                status="closed",
                comment="cTrader mock trade",
                magic_number=789,
            )
        ]

    async def _mock_symbols(self) -> List[BrokerSymbol]:
        """Mock symbols list."""
        return [
            BrokerSymbol(
                symbol="EURUSD",
                description="Euro vs US Dollar",
                digits=5,
                point=Decimal("0.00001"),
                tick_size=Decimal("0.00001"),
                contract_size=Decimal("100000"),
                min_lot=Decimal("0.001"),
                max_lot=Decimal("1000"),
                lot_step=Decimal("0.001"),
                spread=1,
                is_tradeable=True,
            ),
            BrokerSymbol(
                symbol="GBPUSD",
                description="British Pound vs US Dollar",
                digits=5,
                point=Decimal("0.00001"),
                tick_size=Decimal("0.00001"),
                contract_size=Decimal("100000"),
                min_lot=Decimal("0.001"),
                max_lot=Decimal("1000"),
                lot_step=Decimal("0.001"),
                spread=2,
                is_tradeable=True,
            ),
        ]
