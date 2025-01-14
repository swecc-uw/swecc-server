from abc import ABC, abstractmethod
from django.core.cache import cache


class CacheHandler(ABC):
    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def set(self, key: str, value):
        pass


class CachedView(ABC):
    @abstractmethod
    def generate_key(**kwargs):
        pass


class DjangoCacheHandler(CacheHandler):
    def __init__(self, expiration):
        super().__init__()
        self.expiration = expiration

    def get(self, key: str):
        return cache.get(key)

    def set(self, key: str, value):
        return cache.set(key, value, timeout=self.expiration)
