# Generated by Django 5.0.7 on 2024-11-11 05:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("interview", "0004_remove_interview_technical_question_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="interview",
            old_name="technical_question",
            new_name="technical_questions",
        ),
    ]
