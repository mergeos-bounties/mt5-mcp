from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseBackend(ABC):
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return trading constraints for a symbol (digits, lot_step, etc.)"""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_orders(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_history(self, days: int) -> List[Dict[str, Any]]:
        pass
