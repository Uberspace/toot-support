# Generated by Django 3.0.6 on 2020-05-26 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tmastodon', '0004_credential_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='api_id',
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='toot',
            name='api_id',
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AddConstraint(
            model_name='account',
            constraint=models.UniqueConstraint(fields=('api_id', 'credentials'), name='account API id per server'),
        ),
        migrations.AddConstraint(
            model_name='toot',
            constraint=models.UniqueConstraint(fields=('api_id', 'credentials'), name='toot API id per server'),
        ),
    ]