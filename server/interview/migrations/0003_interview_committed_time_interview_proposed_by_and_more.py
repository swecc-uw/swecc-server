# Generated by Django 5.0.7 on 2024-09-17 18:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("interview", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="interview",
            name="committed_time",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="interview",
            name="proposed_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="proposed_interviews",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="interview",
            name="proposed_time",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="interview",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("active", "Active"),
                    ("inactive_unconfirmed", "Inactive Unconfirmed"),
                    ("inactive_completed", "Inactive Completed"),
                    ("inactive_incomplete", "Inactive Incomplete"),
                ],
                default="pending",
                max_length=64,
            ),
        ),
    ]
