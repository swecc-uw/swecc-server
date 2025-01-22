from cache import CacheHandler
from engagement.models import AttendanceSessionStats
import logging
from members.serializers import UsernameSerializer


logger = logging.getLogger(__name__)


class AttendanceLeaderboardManager:
    def __init__(self, cache_handler: CacheHandler, generate_key):
        self.cache_handler = cache_handler
        self.generate_key = generate_key
        pass

    def refresh_key(self, key, value):
        self.cache_handler.set(key, value)

    def get_all(self):
        key = self.generate_key()
        cached_info = self.cache_handler.get(key)

        if cached_info:
            self.refresh_key(key, cached_info)
            return cached_info

        value = self.get_all_from_db()
        self.cache_handler.set(key, value)

        return value

    def get_all_from_db(self):
        queryset = AttendanceSessionStats.objects.all()

        cached_value = []

        for stat in queryset:
            cached_value.append(
                {
                    "sessions_attended": stat.sessions_attended,
                    "last_updated": stat.last_updated,
                    "member": UsernameSerializer(stat.member).data,
                }
            )

        return cached_value
