import logging

from django.core.management.base import BaseCommand

import socialhub

from ....util import log
from ...models import SyncTask


def find_root(toot):
    if not toot.in_reply_to:
        return None

    while toot.in_reply_to:
        toot = toot.in_reply_to

    return toot.network_id


def push_toots(task):
    logging.info('pushing toots for %s', task)

    client = task.api_client()

    toots = task.mastodon_credentials.toots.filter(socialhub_id__isnull=True)

    for toot in toots:
        logging.info('pushing %s', toot)

        try:
            root_id = find_root(toot)
            socialhub_id = client.create_ticket(
                toot.content_stripped,
                toot.network_id,
                toot.url,
                root_id=(root_id if root_id else None),
                interactor=socialhub.TicketInteractor(
                    toot.account.network_id,
                    toot.account.display_name,
                    toot.account.url,
                    toot.account.avatar,
                )
            )
        except socialhub.SocialHubError as ex:
            if ex.code == 'ConflictError':
                toot.socialhub_id = 'unknown-' + toot.network_id
                toot.save()

                logging.info(
                    'ticket %s cannot be created, because it was synced already '
                    'but we lost track of it.', toot.network_id,
                )
            else:
                raise

        toot.socialhub_id = socialhub_id
        toot.save(update_fields=['socialhub_id'])


class Command(BaseCommand):
    def handle(self, *args, **options):
        log.init()

        for task in SyncTask.objects.all():
            push_toots(task)
