from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Optional


@dataclass
class Item(ABC):
    _counter: ClassVar[int] = 0

    id: Optional[int] = None
    page: Optional[str] = None

    def __post_init__(self) -> None:
        cls = self.__class__
        if self.id is None:
            self.id = cls._counter
            cls._counter += 1
        else:
            cls._counter = max(cls._counter, self.id + 1)

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @abstractmethod
    def to_json(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, data: str) -> "Item":
        pass
