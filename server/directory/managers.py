import logging

from cache import CacheHandler, DjangoCacheHandler
from members.models import User

from .serializers import RegularDirectoryMemberSerializer

logger = logging.getLogger(__name__)


class DirectoryManager:
    def __init__(self, cache_handler: CacheHandler, generate_key):
        self.cache = cache_handler
        self.generate_key = generate_key

    def refresh_key(self, key, value):
        self.cache.set(key, value)

    def get(self, id, serializer=RegularDirectoryMemberSerializer):
        key = self.generate_key(id=id)
        cached_member = self.cache.get(key)

        if cached_member:
            self.refresh_key(key, cached_member)
            return cached_member

        member = User.objects.get(id=id)
        member_data = serializer(member).data
        self.cache.set(key, member_data)

        return member_data

    def get_all(self):
        key = self.generate_key()
        cached_member = self.cache.get(key)

        if cached_member:
            logging.info("Using cached data for request for all users")
            self.refresh_key(key, cached_member)
            return cached_member

        members = list(User.objects.all())
        self.cache.set(key, members)

        return members
