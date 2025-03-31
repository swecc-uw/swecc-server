# Generated by Django 4.2.17 on 2025-03-30 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0005_user_school_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="school_email",
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
    ]
