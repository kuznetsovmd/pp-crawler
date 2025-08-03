from abc import ABC, abstractmethod
from typing import Optional


class Engine(ABC):
    @abstractmethod
    def search(self, manufacturer: str, keyword: str) -> Optional[str]:
        pass
