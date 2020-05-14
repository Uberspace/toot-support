# Generated by Django 3.0.6 on 2020-05-14 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tmastodon', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='api_id',
            field=models.BigIntegerField(db_index=True, unique=True),
        ),
        migrations.AlterField(
            model_name='toot',
            name='api_id',
            field=models.BigIntegerField(db_index=True, unique=True),
        ),
        migrations.AlterField(
            model_name='toot',
            name='api_notification_id',
            field=models.BigIntegerField(db_index=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='toot',
            name='socialhub_id',
            field=models.CharField(db_index=True, max_length=128, null=True, unique=True),
        ),
    ]