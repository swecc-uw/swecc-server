# Generated by Django 4.2.19 on 2025-02-09 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cohort', '0005_delete_cohortstats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cohort',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
