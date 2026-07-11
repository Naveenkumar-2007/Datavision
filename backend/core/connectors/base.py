from abc import ABC, abstractmethod
from typing import AsyncGenerator

class LiveConnector(ABC):
    """
    Abstract base class for live data streaming connectors.
    """
    def __init__(self, host: str, database_name: str, credentials: str, target_table: str = ""):
        self.host = host
        self.database_name = database_name
        self.credentials = credentials
        self.target_table = target_table
        
    @abstractmethod
    async def get_metrics_stream(self) -> AsyncGenerator[dict, None]:
        """
        Yields live telemetry metrics indefinitely.
        Expected dict format:
        {
            "timestamp": str (isoformat),
            "active_users": int,
            "cpu_usage": float,
            "transactions_per_sec": int,
            "error_rate": float,
            "connector_source": str,
            "status": str
        }
        """
        pass
