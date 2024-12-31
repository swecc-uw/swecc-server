from django.db import models


class DiscordChannel(models.Model):
    CHANNEL_TYPES = [
        ("TEXT", "Text Channel"),
        ("VOICE", "Voice Channel"),
        ("CATEGORY", "Category"),
        ("STAGE", "Stage Channel"),
        ("FORUM", "Forum Channel"),
    ]
    channel_id = models.BigIntegerField(primary_key=True, db_index=True)
    channel_name = models.CharField(max_length=255)
    category_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    channel_type = models.CharField(max_length=255, choices=CHANNEL_TYPES)
    guild_id = models.BigIntegerField(db_index=True)

    def __str__(self):
        return self.channel_name