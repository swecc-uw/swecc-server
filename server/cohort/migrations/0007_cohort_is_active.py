# Generated by Django 4.2.20 on 2025-03-24 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cohort", "0006_alter_cohort_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="cohort",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
