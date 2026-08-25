from abc import ABC, abstractmethod
from typing import List
import httpx
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    description: str
    source: str

class BaseProvider(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        """
        Asynchronously search the provider and return a list of SearchResult objects.
        """
        pass
