# Generated by Django 4.2.16 on 2024-10-22 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0003_technicalquestion_title'),
        ('interview', '0003_interview_committed_time_interview_proposed_by_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interview',
            name='technical_question',
        ),
        migrations.AddField(
            model_name='interview',
            name='technical_question',
            field=models.ManyToManyField(to='questions.technicalquestion'),
        ),
    ]