from urllib.parse import urlparse

from django.core.management.base import BaseCommand

import socialhub

from ...models import SyncTask


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'account',
            choices=SyncTask.objects.values_list('mastodon_credentials__server', flat=True),
        )

    def handle(self, account, *args, **options):
        task = SyncTask.objects.get(mastodon_credentials__server=account)
        task.init()
