from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from discord.models import AuthKey

class Command(BaseCommand):
    help = 'Delete AuthKey entries older than 24 hours'

    def handle(self, *args, **kwargs):
        expiration_time = timezone.now() - timedelta(hours=24)
        expired_keys = AuthKey.objects.filter(created_at__lt=expiration_time)
        expired_count = expired_keys.count()
        expired_keys.delete()
        self.stdout.write(f'Successfully deleted {expired_count} expired auth keys')