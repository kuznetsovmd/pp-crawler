from abc import ABC, abstractmethod
from multiprocessing.pool import Pool


class Plugin(ABC):
    @abstractmethod
    def scrap_records(self, pool: Pool) -> None:
        pass
