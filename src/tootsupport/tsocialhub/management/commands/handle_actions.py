from django.core.management.base import BaseCommand

from ....tmastodon.models import Toot
from ...models import SyncTask


def handle_action(action):
    client_mastodon = action.task.mastodon_credentials.api_client()
    client_socialhub = action.task.api_client()

    if action.action_id == 'reply-match':
        visibility = action.toot.visibility
    elif action.action_id == 'reply-direct':
        visibility = Toot.Visibility.DIRECT
    else:
        raise Exception(f'unkown action: {action.action_id}')

    new_status = client_mastodon.status_reply(
        client_mastodon.status(action.toot.api_id),
        action.payload_json()['text'],
        visibility=visibility,
    )
    new_network_id = Toot.get_network_id(action.toot.credentials, new_status['id'])
    socialhub_id = client_socialhub.followup_success(
        action.toot.socialhub_id, action.payload_json(
        )['followupId'], new_network_id, new_status['url'],
    )
    Toot.create_from_api(action.task.mastodon_credentials, new_status, socialhub_id=socialhub_id)


def handle_actions(task):
    actions = task.actions.filter(handled=False)

    for action in actions:
        client_socialhub = action.task.api_client()

        try:
            handle_action(action)
        except Exception as ex:
            client_socialhub.followup_reset(
                action.toot.socialhub_id, action.payload_json()['followupId'], action.action_id,
                str(ex)
            )

        action.handled = True
        action.save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        for task in SyncTask.objects.all():
            handle_actions(task)
