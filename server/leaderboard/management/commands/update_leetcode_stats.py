import time
from django.utils import timezone
import requests
from django.core.management.base import BaseCommand
from members.models import User
from leaderboard.models import LeetcodeStats
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
class Command(BaseCommand):
    help = "Updates leetcode statistics for all users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=10,
            help="Timeout between API requests in seconds",
        )
        parser.add_argument(
            "--username", type=str, help="Update stats for specific username only"
        )
        parser.add_argument(
            "--force", action="store_true", help="Force update even if recently updated"
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        username = options["username"]
        force = options["force"]

        def get_leetcode_profile(username):
            try:
                query = """
                    query getUserProfile($username: String!) {
                        matchedUser(username: $username) {
                            submitStats {
                                acSubmissionNum {
                                    difficulty
                                    count
                                }
                            }
                        }
                    }
                """
                response = requests.post(
                    "https://leetcode.com/graphql",
                    headers={
                        "Content-Type": "application/json",
                        "Referer": "https://leetcode.com",
                    },
                    json={"query": query, "variables": {"username": username}},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data:
                        return None
                    stats = data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]
                    return {
                        "solvedProblem": next((item["count"] for item in stats if item["difficulty"] == "All"), 0),
                        "easySolved": next((item["count"] for item in stats if item["difficulty"] == "Easy"), 0),
                        "mediumSolved": next((item["count"] for item in stats if item["difficulty"] == "Medium"), 0),
                        "hardSolved": next((item["count"] for item in stats if item["difficulty"] == "Hard"), 0),
                    }
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Error fetching data for {username}: {response.text}")
                    )
                return None
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error fetching data for {username}: {str(e)}")
                )
                return None

        def update_user_stats(user):
            if not user.leetcode or not user.leetcode.get("username"):
                return False

            # skip if updated in last hour unless forced
            try:
                stats = LeetcodeStats.objects.get(user=user)
                if (
                    not force
                    and (timezone.now() - stats.last_updated).total_seconds() < 3600
                ):
                    return False
            except LeetcodeStats.DoesNotExist:
                stats = LeetcodeStats(user=user)

            leetcode_data = get_leetcode_profile(user.leetcode["username"])
            if not leetcode_data:
                return False

            with transaction.atomic():
                stats.total_solved = leetcode_data.get("solvedProblem", 0)
                stats.easy_solved = leetcode_data.get("easySolved", 0)
                stats.medium_solved = leetcode_data.get("mediumSolved", 0)
                stats.hard_solved = leetcode_data.get("hardSolved", 0)
                stats.last_updated = timezone.now()
                stats.save()
                return True

        users = (
            User.objects.filter(username=username) if username else User.objects.all()
        )

        for user in users:
            if update_user_stats(user):
                self.stdout.write(
                    self.style.SUCCESS(f"Updated stats for {user.username}")
                )
                time.sleep(timeout)
            else:
                self.stdout.write(self.style.WARNING(f"Skipped {user.username}"))