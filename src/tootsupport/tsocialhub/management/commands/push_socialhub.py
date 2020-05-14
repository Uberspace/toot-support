from django.core.management.base import BaseCommand

import socialhub

from ...models import SyncTask


def find_root(toot):
    if not toot.in_reply_to:
        return None

    while toot.in_reply_to:
        toot = toot.in_reply_to

    return toot.network_id


def push_toots(task):
    client = task.api_client()

    toots = task.mastodon_credentials.toots.filter(socialhub_id__isnull=True)

    for toot in toots:
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

                raise Exception(
                    f'ticket {toot.network_id} cannot be created, '
                    'because it was synced already but we lost track of it.'
                ) from ex
            else:
                raise

        toot.socialhub_id = socialhub_id
        toot.save(update_fields=['socialhub_id'])


class Command(BaseCommand):
    def handle(self, *args, **options):
        for task in SyncTask.objects.all():
            push_toots(task)
