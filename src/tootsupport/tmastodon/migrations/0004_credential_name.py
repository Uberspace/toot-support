# Generated by Django 3.0.6 on 2020-05-25 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tmastodon', '0003_credential_url_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='credential',
            name='name',
            field=models.CharField(default='unnamed account', max_length=64, verbose_name='Name'),
            preserve_default=False,
        ),
    ]