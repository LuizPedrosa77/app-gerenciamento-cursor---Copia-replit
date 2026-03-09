"""
Broker-specific exceptions.
"""


class BrokerError(Exception):
    """Base exception for broker-related errors."""
    pass


class BrokerConnectionError(BrokerError):
    """Raised when broker connection fails."""
    def __init__(self, message: str, broker_name: str = None, error_code: str = None):
        self.broker_name = broker_name
        self.error_code = error_code
        super().__init__(message)


class BrokerAuthenticationError(BrokerConnectionError):
    """Raised when broker authentication fails."""
    pass


class BrokerPermissionError(BrokerError):
    """Raised when broker operation is not permitted."""
    pass


class BrokerDataError(BrokerError):
    """Raised when broker data retrieval or parsing fails."""
    pass


class BrokerTimeoutError(BrokerError):
    """Raised when broker operation times out."""
    pass


class BrokerRateLimitError(BrokerError):
    """Raised when broker rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message)


class BrokerMaintenanceError(BrokerError):
    """Raised when broker is under maintenance."""
    pass


class BrokerInvalidSymbolError(BrokerError):
    """Raised when symbol is invalid or not found."""
    def __init__(self, symbol: str, message: str = None):
        self.symbol = symbol
        super().__init__(message or f"Invalid symbol: {symbol}")


class BrokerInsufficientFundsError(BrokerError):
    """Raised when insufficient funds for operation."""
    pass


class BrokerInvalidOrderError(BrokerError):
    """Raised when order parameters are invalid."""
    pass


class BrokerPositionError(BrokerError):
    """Raised when position operations fail."""
    pass
