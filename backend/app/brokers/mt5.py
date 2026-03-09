"""
MetaTrader 5 broker adapter.
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

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None


class MT5Adapter(BrokerAdapter):
    """MetaTrader 5 broker adapter."""

    def __init__(self, config: BrokerConnectionConfig):
        super().__init__(config)
        self.validate_config()

    @property
    def broker_name(self) -> str:
        return "MetaTrader 5"

    @property
    def supported_platforms(self) -> List[str]:
        return ["mt5"]

    def validate_config(self) -> None:
        super().validate_config()
        if not self.config.login or not self.config.password:
            raise BrokerConnectionError("MT5 requires login and password")
        if not self.config.server:
            raise BrokerConnectionError("MT5 requires server address")

    async def test_connection(self) -> bool:
        """Test connection to MT5."""
        if not MT5_AVAILABLE:
            return await self._mock_test_connection()

        try:
            # Initialize MT5
            if not mt5.initialize():
                return False

            # Login
            if not mt5.login(
                int(self.config.login),
                password=self.config.password,
                server=self.config.server,
            ):
                mt5.shutdown()
                return False

            # Get account info to verify
            account_info = mt5.account_info()
            mt5.shutdown()

            return account_info is not None

        except Exception:
            return False

    async def get_account_info(self) -> BrokerAccountInfo:
        """Get account information from MT5."""
        if not MT5_AVAILABLE:
            return await self._mock_account_info()

        try:
            if not mt5.initialize():
                raise BrokerConnectionError("Failed to initialize MT5")

            if not mt5.login(
                int(self.config.login),
                password=self.config.password,
                server=self.config.server,
            ):
                mt5.shutdown()
                raise BrokerAuthenticationError("MT5 login failed")

            account_info = mt5.account_info()
            if not account_info:
                mt5.shutdown()
                raise BrokerDataError("Failed to get account info")

            result = BrokerAccountInfo(
                account_id=str(account_info.login),
                account_name=account_info.name or "",
                broker_name=account_info.server or "",
                currency=account_info.currency,
                balance=Decimal(str(account_info.balance)),
                equity=Decimal(str(account_info.equity)),
                margin=Decimal(str(account_info.margin)),
                free_margin=Decimal(str(account_info.margin_free)),
                leverage=account_info.leverage,
                is_demo=account_info.margin_mode == 0,  # Approximation
                server=account_info.server,
                platform="mt5",
            )

            mt5.shutdown()
            return result

        except Exception as e:
            if MT5_AVAILABLE and mt5.terminal_info():
                mt5.shutdown()
            raise BrokerConnectionError(f"MT5 connection error: {str(e)}")

    async def sync_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BrokerTrade]:
        """Sync trade history from MT5."""
        if not MT5_AVAILABLE:
            return await self._mock_history(start_date, end_date)

        try:
            if not mt5.initialize():
                raise BrokerConnectionError("Failed to initialize MT5")

            if not mt5.login(
                int(self.config.login),
                password=self.config.password,
                server=self.config.server,
            ):
                mt5.shutdown()
                raise BrokerAuthenticationError("MT5 login failed")

            # Default to last 30 days if no dates provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()

            # Get deals from MT5
            deals = mt5.history_deals_get(
                date_from=start_date,
                date_to=end_date,
            )

            if not deals:
                mt5.shutdown()
                return []

            trades = []
            for deal in deals:
                # Only include closed trades
                if deal.type != mt5.POSITION_TYPE_BUY and deal.type != mt5.POSITION_TYPE_SELL:
                    continue

                trade = BrokerTrade(
                    external_id=str(deal.ticket),
                    symbol=deal.symbol,
                    side="buy" if deal.type == mt5.POSITION_TYPE_BUY else "sell",
                    volume=Decimal(str(deal.volume)),
                    open_time=deal.time,
                    close_time=deal.time,
                    open_price=Decimal(str(deal.price)),
                    close_price=Decimal(str(deal.price)),
                    stop_loss=Decimal(str(deal.stop_loss)) if deal.stop_loss else None,
                    take_profit=Decimal(str(deal.tp)) if deal.tp else None,
                    commission=Decimal(str(deal.commission)),
                    swap=Decimal(str(deal.swap)),
                    profit=Decimal(str(deal.profit)),
                    status="closed",
                    comment=deal.comment,
                    magic_number=deal.magic,
                )
                trades.append(trade)

            mt5.shutdown()
            return trades

        except Exception as e:
            if MT5_AVAILABLE and mt5.terminal_info():
                mt5.shutdown()
            raise BrokerDataError(f"MT5 history sync error: {str(e)}")

    async def list_symbols(self) -> List[BrokerSymbol]:
        """List available symbols from MT5."""
        if not MT5_AVAILABLE:
            return await self._mock_symbols()

        try:
            if not mt5.initialize():
                raise BrokerConnectionError("Failed to initialize MT5")

            symbols = mt5.symbols_get()
            if not symbols:
                mt5.shutdown()
                return []

            result = []
            for symbol in symbols[:100]:  # Limit to first 100 symbols
                broker_symbol = BrokerSymbol(
                    symbol=symbol.name,
                    description=symbol.description or "",
                    digits=symbol.digits,
                    point=Decimal(str(symbol.point)),
                    tick_size=Decimal(str(symbol.trade_tick_size)),
                    contract_size=Decimal(str(symbol.trade_contract_size)),
                    min_lot=Decimal(str(symbol.volume_min)),
                    max_lot=Decimal(str(symbol.volume_max)),
                    lot_step=Decimal(str(symbol.volume_step)),
                    spread=int(symbol.spread) if symbol.spread else None,
                    is_tradeable=symbol.visible,
                )
                result.append(broker_symbol)

            mt5.shutdown()
            return result

        except Exception as e:
            if MT5_AVAILABLE and mt5.terminal_info():
                mt5.shutdown()
            raise BrokerDataError(f"MT5 symbols error: {str(e)}")

    # Mock methods for when MT5 is not available
    async def _mock_test_connection(self) -> bool:
        """Mock test connection."""
        return True

    async def _mock_account_info(self) -> BrokerAccountInfo:
        """Mock account info."""
        return BrokerAccountInfo(
            account_id=self.config.login or "12345678",
            account_name="MT5 Demo Account",
            broker_name=self.config.server or "MetaQuotes-Demo",
            currency="USD",
            balance=Decimal("10000.00"),
            equity=Decimal("10500.00"),
            margin=Decimal("500.00"),
            free_margin=Decimal("10000.00"),
            leverage=100,
            is_demo=True,
            server=self.config.server or "MetaQuotes-Demo",
            platform="mt5",
        )

    async def _mock_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BrokerTrade]:
        """Mock trade history."""
        return [
            BrokerTrade(
                external_id="123456",
                symbol="EUR/USD",
                side="buy",
                volume=Decimal("0.1"),
                open_time=datetime.now() - timedelta(hours=2),
                close_time=datetime.now() - timedelta(hours=1),
                open_price=Decimal("1.08500"),
                close_price=Decimal("1.08600"),
                stop_loss=Decimal("1.08400"),
                take_profit=Decimal("1.08700"),
                commission=Decimal("0.5"),
                swap=Decimal("0.0"),
                profit=Decimal("10.00"),
                status="closed",
                comment="Mock trade",
                magic_number=123,
            )
        ]

    async def _mock_symbols(self) -> List[BrokerSymbol]:
        """Mock symbols list."""
        return [
            BrokerSymbol(
                symbol="EUR/USD",
                description="Euro vs US Dollar",
                digits=5,
                point=Decimal("0.00001"),
                tick_size=Decimal("0.00001"),
                contract_size=Decimal("100000"),
                min_lot=Decimal("0.01"),
                max_lot=Decimal("100"),
                lot_step=Decimal("0.01"),
                spread=1,
                is_tradeable=True,
            ),
            BrokerSymbol(
                symbol="GBP/USD",
                description="British Pound vs US Dollar",
                digits=5,
                point=Decimal("0.00001"),
                tick_size=Decimal("0.00001"),
                contract_size=Decimal("100000"),
                min_lot=Decimal("0.01"),
                max_lot=Decimal("100"),
                lot_step=Decimal("0.01"),
                spread=2,
                is_tradeable=True,
            ),
        ]
