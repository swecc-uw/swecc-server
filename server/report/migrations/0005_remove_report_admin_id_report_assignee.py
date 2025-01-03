# Generated by Django 4.2.17 on 2024-12-28 21:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("report", "0004_rename_associated_id_report_associated_interview_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="report",
            name="admin_id",
        ),
        migrations.AddField(
            model_name="report",
            name="assignee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assigned_report",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
