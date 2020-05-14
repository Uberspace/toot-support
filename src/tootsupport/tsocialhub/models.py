import json

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string

import socialhub


def generate_webhook_secret():
    return get_random_string(length=32)


class SyncTask(models.Model):
    accesstoken = models.CharField(max_length=1024)
    webhook_secret = models.CharField(max_length=255, default=generate_webhook_secret)
    mastodon_credentials = models.ForeignKey('tmastodon.Credential', on_delete=models.PROTECT)

    def api_client(self):
        return socialhub.SocialHub(self.accesstoken)

    def init(self):
        client = self.api_client()
        client.set_webhook(
            f'https://{settings.SITE_DOMAIN}/webhook/{self.id}',
            self.webhook_secret,
        )
        client.set_ticket_actions([
            socialhub.TicketAction(
                'reply',
                'reply-match',
                'Reply',
            ),
            socialhub.TicketAction(
                'reply',
                'reply-direct',
                'Reply DM',
            ),
        ])


class TicketAction(models.Model):
    class Kind(models.TextChoices):
        REPLY = 'reply'

    task = models.ForeignKey(SyncTask, on_delete=models.CASCADE, related_name='actions')
    kind = models.CharField(max_length=5, choices=Kind.choices)
    action_id = models.CharField(max_length=255)
    toot = models.ForeignKey('tmastodon.Toot', on_delete=models.CASCADE)
    payload = models.TextField()
    handled = models.BooleanField(default=False)

    def payload_json(self):
        return json.loads(self.payload)
