# Generated by Django 5.0.6 on 2024-07-06 22:50

import interview.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "interview",
            "0002_alter_interviewavailability_interview_availability_slots_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="interviewavailability",
            name="interview_availability_slots",
            field=models.JSONField(
                default=interview.models.default_availability,
                validators=[interview.models.validate_availability],
            ),
        ),
        migrations.AlterField(
            model_name="interviewavailability",
            name="mentor_availability_slots",
            field=models.JSONField(
                default=interview.models.default_availability,
                validators=[interview.models.validate_availability],
            ),
        ),
    ]