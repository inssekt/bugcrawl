from abc import ABC, abstractmethod

class BaseScraper(ABC):

    @abstractmethod
    def fetch_listings(self, keyword: str):
        """
        Fetch the listings for a given keyword.
        This method should be implemented by each scraper.
        """
        pass