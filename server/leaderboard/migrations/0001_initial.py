# Generated by Django 5.0.7 on 2024-11-23 18:31

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LeetcodeStats",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("total_solved", models.IntegerField(default=0)),
                ("easy_solved", models.IntegerField(default=0)),
                ("medium_solved", models.IntegerField(default=0)),
                ("hard_solved", models.IntegerField(default=0)),
                (
                    "last_updated",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="leetcode_stats",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Leetcode Stats",
                "ordering": ["-total_solved", "-hard_solved", "-medium_solved"],
            },
        ),
    ]
