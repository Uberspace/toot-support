from collections import deque

from django.core.management.base import BaseCommand
from django.db import IntegrityError
import mastodon
from ...models import Credential
from ...models import Toot


def pull_toots(credential):
    client = credential.api_client()

    if credential.toots.exists():
        since_id = credential.toots \
            .order_by('-api_notification_id').first().api_notification_id
    else:
        since_id = None

    notifications = client.notifications(since_id=since_id, mentions_only=True)
    to_process = deque(notifications)

    while len(to_process):
        while len(to_process):
            notification = to_process.popleft()

            if notification.type != 'mention':
                continue

            status = notification.status

            if status.in_reply_to_id and \
                    not Toot.objects.filter(api_id=status.in_reply_to_id).exists():
                # if the referenced toot does not yet exist in our DB,
                # process it later and then re-process this one.
                to_process.append(mastodon.AttribAccessDict({
                    'type': 'mention',
                    'id': None,
                    'status': client.status(status.in_reply_to_id),
                }))
                to_process.append(notification)
                continue

            try:
                Toot.create_from_api(credential, status, api_notification_id=notification.id)
            except IntegrityError as ex:
                pass  # we already know that one

        # get the next-newest (previous in ID-order) page
        notifications = client.fetch_previous(notifications)
        to_process.extend(notifications)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'account',
            choices=Credential.objects.values_list('server', flat=True),
        )

    def handle(self, account, *args, **options):
        credential = Credential.objects.get(server=account)
        pull_toots(credential)
