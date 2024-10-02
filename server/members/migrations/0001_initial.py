# Generated by Django 5.1.1 on 2024-09-08 19:00

import django.contrib.auth.validators
import django.utils.timezone
import members.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('first_name', models.CharField(blank=True, max_length=20)),
                ('last_name', models.CharField(blank=True, max_length=20)),
                ('created', models.DateTimeField(auto_now_add=True)),
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
                ('discord_id', models.BigIntegerField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'permissions': (('is_verified', 'Users discord is verified'), ('is_admin', 'User is an admin')),
            },
            managers=[
                ('objects', members.models.CustomUserManager()),
            ],
        ),
    ]
