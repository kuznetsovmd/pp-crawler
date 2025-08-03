from abc import ABC, abstractmethod


class Engine(ABC):
    @abstractmethod
    def search(self, manufacturer: str, keyword: str):
        pass
