import logging

from django.core.management.base import BaseCommand

from ....util import log
from ...models import SyncTask


class Command(BaseCommand):
    def handle(self, *args, **options):
        log.init()

        for task in SyncTask.objects.all():
            logging.info('init %s', task)
            task.init()
