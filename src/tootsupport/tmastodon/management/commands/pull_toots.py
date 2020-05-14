from collections import deque

import mastodon
from django.core.management.base import BaseCommand
from django.db import IntegrityError

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
            except IntegrityError:
                pass  # we already know that one

        # get the next-newest (previous in ID-order) page
        notifications = client.fetch_previous(notifications)
        to_process.extend(notifications)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for credential in Credential.objects.all():
            pull_toots(credential)
