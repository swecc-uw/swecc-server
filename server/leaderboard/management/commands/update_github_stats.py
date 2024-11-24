from django.utils import timezone
from django.core.management.base import BaseCommand
from members.models import User
from leaderboard.models import GitHubStats
from django.db import transaction
import logging
import requests
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Updates GitHub statistics for all users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=60,  # high default timeout for rate limits
            help="Timeout between API requests in seconds",
        )
        parser.add_argument(
            "--username", type=str, help="Update stats for specific username only"
        )
        parser.add_argument(
            "--force", action="store_true", help="Force update even if recently updated"
        )

    def get_github_stats(self, username):
        """Fetch GitHub statistics using public API and web scraping for contributions"""
        try:
            # contribution count
            contributions_url = f"https://github.com/users/{username}/contributions"
            response = requests.get(contributions_url)
            contributions = 0

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                h2_tag = soup.find('h2', class_='f4 text-normal mb-2')
                if h2_tag:
                    contributions_text = h2_tag.text.strip().split()[0]
                    contributions = int(contributions_text.replace(',', ''))

            # basic user info
            user_response = requests.get(
                f"https://api.github.com/users/{username}",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10
            )

            if user_response.status_code != 200:
                logger.error(f"Failed to fetch user data for {username}: {user_response.status_code}")
                return None

            user_data = user_response.json()

            # PR count
            pr_response = requests.get(
                f"https://api.github.com/search/issues?q=author:{username}+type:pr",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10
            )

            total_prs = 0
            if pr_response.status_code == 200:
                pr_data = pr_response.json()
                total_prs = pr_data.get("total_count", 0)
            else:
                logger.warning(f"Failed to fetch PR data for {username}: {pr_response.status_code}")

            return {
                "total_prs": total_prs,
                "total_commits": contributions,  # contributions count from profile
                "followers": user_data.get("followers", 0)
            }

        except Exception as e:
            logger.error(f"Error fetching GitHub data for {username}: {str(e)}")
            return None

    def handle(self, *args, **options):
        timeout = options["timeout"]
        username = options["username"]
        force = options["force"]

        def update_user_stats(user):
            if not user.github or not user.github.get("username"):
                return False

            try:
                stats = GitHubStats.objects.get(user=user)
                if not force and (timezone.now() - stats.last_updated).total_seconds() < 3600:
                    return False
            except GitHubStats.DoesNotExist:
                stats = GitHubStats(user=user)

            github_data = self.get_github_stats(user.github["username"])
            if not github_data:
                return False

            with transaction.atomic():
                stats.total_prs = github_data["total_prs"]
                stats.total_commits = github_data["total_commits"]
                stats.followers = github_data["followers"]
                stats.last_updated = timezone.now()
                stats.save()
                return True

        users = User.objects.filter(username=username) if username else User.objects.all()

        for user in users:
            if not user.github or not user.github.get("username"):
                continue
            try:
                if update_user_stats(user):
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated GitHub stats for {user.username}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Skipped {user.username}")
                    )
                time.sleep(timeout)  # hopefully respect rate limits, needs to be run async though
            except Exception as e:
                logger.error(f"Failed to update stats for {user.username}: {str(e)}")
                continue