# Generated by Django 4.2.17 on 2025-02-12 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("engagement", "0006_cohortstats"),
    ]

    operations = [
        migrations.AddField(
            model_name="cohortstats",
            name="last_updated",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="cohortstats",
            name="streak",
            field=models.IntegerField(default=0),
        ),
    ]
