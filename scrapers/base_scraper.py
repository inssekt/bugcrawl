from abc import ABC, abstractmethod

class BaseScraper(ABC):

    @abstractmethod
    def fetch_listings(self, keyword: str):

        pass