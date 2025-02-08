# Generated by Django 4.2.17 on 2025-02-08 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cohort', '0003_cohortstats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cohortstats',
            name='applications',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='cohortstats',
            name='dailyChecks',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='cohortstats',
            name='interviews',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='cohortstats',
            name='offers',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='cohortstats',
            name='onlineAssessments',
            field=models.IntegerField(default=0),
        ),
    ]
