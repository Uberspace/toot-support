from django.core.management.base import BaseCommand

from ...models import SyncTask


class Command(BaseCommand):
    def handle(self, *args, **options):
        for task in SyncTask.objects.all():
            task.init()
