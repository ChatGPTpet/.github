# Generated by Django 4.2.4 on 2024-02-10 14:35

import chat_with_your_data_api.user_settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_with_your_data_api', '0022_alter_user_settings_roomdocuments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='roomID',
        ),
        migrations.AlterField(
            model_name='user',
            name='settings',
            field=models.JSONField(default=chat_with_your_data_api.user_settings.UserSettings.to_dict),
        ),
    ]
