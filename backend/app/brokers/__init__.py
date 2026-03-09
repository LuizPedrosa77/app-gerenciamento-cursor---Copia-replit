"""
Broker adapters for different trading platforms.
"""

from .base import (
    BrokerAdapter,
    BrokerAccountInfo,
    BrokerTrade,
    BrokerSymbol,
    BrokerConnectionConfig,
    BrokerConnectionError,
    BrokerAuthenticationError,
    BrokerDataError,
)
from .exceptions import (
    BrokerError,
    BrokerConnectionError,
    BrokerAuthenticationError,
    BrokerPermissionError,
    BrokerDataError,
    BrokerTimeoutError,
    BrokerRateLimitError,
    BrokerMaintenanceError,
    BrokerInvalidSymbolError,
    BrokerInsufficientFundsError,
    BrokerInvalidOrderError,
    BrokerPositionError,
)
from .mt5 import MT5Adapter
from .mt4 import MT4Adapter
from .ctrader import CTraderAdapter
from .tradovate import TradovateAdapter
from .ninjatrader import NinjaTraderAdapter

__all__ = [
    "BrokerAdapter",
    "BrokerAccountInfo",
    "BrokerTrade",
    "BrokerSymbol",
    "BrokerConnectionConfig",
    "BrokerConnectionError",
    "BrokerAuthenticationError",
    "BrokerDataError",
    "BrokerError",
    "BrokerPermissionError",
    "BrokerTimeoutError",
    "BrokerRateLimitError",
    "BrokerMaintenanceError",
    "BrokerInvalidSymbolError",
    "BrokerInsufficientFundsError",
    "BrokerInvalidOrderError",
    "BrokerPositionError",
    "MT5Adapter",
    "MT4Adapter",
    "CTraderAdapter",
    "TradovateAdapter",
    "NinjaTraderAdapter",
]
