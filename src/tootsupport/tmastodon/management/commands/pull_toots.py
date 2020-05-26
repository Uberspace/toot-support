import logging
from collections import deque

import mastodon
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from ....util import log
from ...models import Credential
from ...models import Toot


def pull_toots(credential):
    logging.info('pulling toots for %s', credential)

    client = credential.api_client()

    if credential.toots.exists():
        since_id = credential.toots \
            .order_by('-api_notification_id').first().api_notification_id
    else:
        since_id = None

    notifications = client.notifications(since_id=since_id, mentions_only=True)
    to_process = deque(notifications)

    logging.info('found %s notifications', len(notifications))

    while len(to_process):
        while len(to_process):
            notification = to_process.popleft()

            if notification.type != 'mention':
                continue

            status = notification.status

            logging.info('importing %s (notification %s): %s',
                         status.id, notification.id, status.url)

            if status.in_reply_to_id and \
                    not Toot.objects.filter(api_id=status.in_reply_to_id).exists():

                logging.info('postponed due to missing parent toot: %s', status.in_reply_to_id)

                try:
                    parent_status = client.status(status.in_reply_to_id)

                    # if the referenced toot does not yet exist in our DB,
                    # process it later and then re-process this one.
                    to_process.append(mastodon.AttribAccessDict({
                        'type': 'mention',
                        'id': None,
                        'status': parent_status,
                    }))
                    to_process.append(notification)
                    continue
                except (mastodon.MastodonNotFoundError, mastodon.MastodonUnauthorizedError):
                    # there is a parent toot somewhere, but we can't load it, ignore it.
                    status.in_reply_to_id = None

            try:
                Toot.create_from_api(credential, status, api_notification_id=notification.id)
            except IntegrityError as ex:
                if 'api_id' in str(ex):
                    logging.info('skipped, due to duplication %s', ex)
                else:
                    raise

        # get the next-newest (previous in ID-order) page
        notifications = client.fetch_previous(notifications)
        logging.info('found %s notifications', len(notifications))
        to_process.extend(notifications)


class Command(BaseCommand):
    def handle(self, *args, **options):
        log.init()

        for credential in Credential.objects.all():
            pull_toots(credential)
