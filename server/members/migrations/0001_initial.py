# Generated by Django 5.0.6 on 2024-07-04 21:36

import django.db.models.deletion
import members.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(max_length=100)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('preview', models.TextField(blank=True, null=True)),
                ('major', models.CharField(blank=True, max_length=100, null=True)),
                ('grad_date', models.DateField(blank=True, null=True)),
                ('discord_username', models.CharField(max_length=100)),
                ('linkedin', models.JSONField(blank=True, null=True, validators=[members.models.validate_social_field])),
                ('github', models.JSONField(blank=True, null=True, validators=[members.models.validate_social_field])),
                ('leetcode', models.JSONField(blank=True, null=True, validators=[members.models.validate_social_field])),
                ('resume_url', models.URLField(blank=True, null=True)),
                ('local', models.CharField(blank=True, max_length=100, null=True)),
                ('bio', models.TextField(blank=True, null=True)),
                ('discord_id', models.IntegerField()),
            ],
        ),
    ]
