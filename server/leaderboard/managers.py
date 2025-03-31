import logging

from cache import CacheHandler
from cohort.serializers import CohortHydratedPublicSerializer
from engagement.models import AttendanceSessionStats, CohortStats
from members.serializers import UsernameSerializer

from .models import GitHubStats, LeetcodeStats

logger = logging.getLogger(__name__)


class LeetcodeLeaderboardManager:
    def __init__(self, cache_handler: CacheHandler, generate_key):
        self.cache_handler = cache_handler
        self.generate_key = generate_key

    def get_all(self):
        key = self.generate_key()
        cached_info = self.cache_handler.get(key)

        if cached_info:
            return cached_info

        value = self.get_all_from_db()
        self.cache_handler.set(key, value)

        return value

    def get_all_from_db(self):
        queryset = LeetcodeStats.objects.all()

        cached_value = []

        for stat in queryset:
            cached_value.append(
                {
                    "total_solved": stat.total_solved,
                    "easy_solved": stat.easy_solved,
                    "medium_solved": stat.medium_solved,
                    "hard_solved": stat.hard_solved,
                    "last_updated": stat.last_updated,
                    "user": UsernameSerializer(stat.user).data,
                }
            )

        return cached_value


class AttendanceLeaderboardManager:
    def __init__(self, cache_handler: CacheHandler, generate_key):
        self.cache_handler = cache_handler
        self.generate_key = generate_key

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


class GitHubLeaderboardManager:
    def __init__(self, cache_handler: CacheHandler, generate_key):
        self.cache_handler = cache_handler
        self.generate_key = generate_key

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
        queryset = GitHubStats.objects.all()

        cached_value = []

        for stat in queryset:
            cached_value.append(
                {
                    "total_prs": stat.total_prs,
                    "total_commits": stat.total_commits,
                    "followers": stat.followers,
                    "last_updated": stat.last_updated,
                    "user": UsernameSerializer(stat.user).data,
                }
            )

        return cached_value


class CohortStatsLeaderboardManager:
    def __init__(self, cache_handler: CacheHandler, generate_key):
        self.cache_handler = cache_handler
        self.generate_key = generate_key

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
        queryset = CohortStats.objects.all()

        cached_value = []

        for stat in queryset:
            cached_value.append(
                {
                    "cohort": CohortHydratedPublicSerializer(stat.cohort).data,
                    "member": UsernameSerializer(stat.member).data,
                    "applications": stat.applications,
                    "online_assessments": stat.onlineAssessments,
                    "interviews": stat.interviews,
                    "offers": stat.offers,
                    "daily_checks": stat.dailyChecks,
                }
            )

        return cached_value
