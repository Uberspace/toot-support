import json

from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

import socialhub

from ..tmastodon.models import Toot
from .models import SyncTask
from .models import TicketAction


@csrf_exempt
def webhook(request, task_id):
    task = get_object_or_404(SyncTask, pk=task_id)

    timestamp = request.headers['X-SocialHub-Timestamp']
    signature = request.headers['X-SocialHub-Signature']

    try:
        timestamp = int(timestamp)
    except ValueError:
        raise HttpResponseBadRequest()

    try:
        challenge = socialhub.SocialHub.verify_webhook_signature(
            secret=task.webhook_secret,
            req_timestamp=timestamp,
            req_raw_body=request.body,
            req_signature=signature,
        )
    except socialhub.SocialHubSignatureError:
        return HttpResponseBadRequest()

    data = json.loads(request.body)

    for event in data['events'].get('ticket_action', []):
        if event['type'] not in TicketAction.Kind:
            continue

        # mastodon_uberspace-social_104145826783865959
        _, _, toot_api_id = event['networkItemId'].split('_')
        toot = task.mastodon_credentials.toots.get(api_id=toot_api_id)

        TicketAction.objects.create(
            task=task,
            kind=event['type'],
            action_id=event['actionId'],
            toot=toot,
            payload=json.dumps(event['payload']),
        )

    response = HttpResponse()
    response['X-SocialHub-Challenge'] = challenge
    return response
