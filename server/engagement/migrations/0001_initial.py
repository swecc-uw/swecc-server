# Generated by Django 4.2.17 on 2024-12-29 06:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscordMessageStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(max_length=100)),
                ('message_count', models.PositiveIntegerField(default=0)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AttendanceSession',
            fields=[
                ('session_id', models.AutoField(primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=10)),
                ('title', models.CharField(max_length=100)),
                ('expires', models.DateTimeField()),
                ('attendees', models.ManyToManyField(related_name='attendance_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['-expires'], name='engagement__expires_ec4207_idx')],
            },
        ),
    ]
