# Generated by Django 4.2.4 on 2024-01-24 18:42

import chat_with_your_data_api.user_settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_with_your_data_api', '0014_room_alter_user_settings_contextentry_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='anonymizeentitie',
            name='anonymized',
            field=models.CharField(default=' ', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='anonymizeentitie',
            name='deanonymized',
            field=models.CharField(default=' ', max_length=255, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='anonymizeentitie',
            name='entityType',
            field=models.CharField(default=' ', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='settings',
            field=models.JSONField(default=chat_with_your_data_api.user_settings.UserSettings.to_dict),
        ),
    ]
