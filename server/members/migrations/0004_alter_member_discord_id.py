# Generated by Django 5.0.6 on 2024-08-05 00:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0003_remove_member_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='discord_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
