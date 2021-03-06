import html
from urllib.parse import urlparse

from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _


class Credential(models.Model):
    name = models.CharField(_('Name'), max_length=64)
    server = models.URLField()
    client_key = models.CharField(
        _('App Client Key/ID'),
        max_length=64,
        help_text='public identifier from the mastodon development settings',
    )
    client_secret = models.CharField(_('App Client Secret'), max_length=64)
    access_token = models.CharField(_('Account Access Token'), max_length=64)
    url_template = models.CharField(
        _('Template to construct URLs to toots'),
        help_text=_('use any {toot_dict_field}: https://mastodonpy.readthedocs.io/en/stable/#toot-dicts'),
        max_length=64,
        null=True, blank=True,
    )

    def api_client(self):
        from mastodon import Mastodon

        return Mastodon(
            api_base_url=self.server,
            client_id=self.client_key,
            client_secret=self.client_secret,
            access_token=self.access_token,
        )

    @property
    def friendly_hostname(self):
        hostname = urlparse(self.server).netloc
        hostname = hostname.replace('.', '-')
        return hostname

    def __str__(self):
        return f'<Credentials {self.name}>'


class Account(models.Model):
    credentials = models.ForeignKey(
        Credential,
        on_delete=models.CASCADE, related_name='accounts',
    )
    api_id = models.BigIntegerField(db_index=True)
    acct = models.CharField(max_length=1024)
    display_name = models.CharField(max_length=1024)
    url = models.URLField()
    avatar = models.URLField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['api_id', 'credentials'], name='unique-account-api-id-per-server')
        ]

    def __str__(self):
        return f'<Account {self.acct}>'

    @property
    def network_id(self):
        return f'mastodon_account_{self.credentials.friendly_hostname}_{self.api_id}'

    @classmethod
    def get_or_create_from_api(cls, account, credentials):
        return Account.objects.get_or_create(
            api_id=account.id,
            credentials__server=credentials.server,
            defaults={
                'acct': account.acct,
                'display_name': account.display_name,
                'url': account.url,
                'avatar': account.avatar,
                'credentials': credentials,
            }
        )[0]


class Toot(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = 'public', _('public')
        UNLISTED = 'unlisted', _('unlisted')
        PRIVATE = 'private', _('private')
        DIRECT = 'direct', _('direct')

    credentials = models.ForeignKey(
        Credential,
        on_delete=models.CASCADE, related_name='toots',
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE, related_name='toots',
    )
    in_reply_to = models.ForeignKey('Toot', on_delete=models.CASCADE, null=True)
    api_id = models.BigIntegerField(db_index=True)
    api_notification_id = models.BigIntegerField(null=True, unique=True, db_index=True)
    url = models.URLField()
    created_at = models.DateTimeField()
    content = models.TextField()
    visibility = models.CharField(max_length=8, choices=Visibility.choices)
    socialhub_id = models.CharField(max_length=128, null=True, unique=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['api_id', 'credentials'], name='unique-toot-api-id-per-server')
        ]

    @property
    def content_stripped(self):
        return html.unescape(strip_tags(self.content))

    @classmethod
    def create_from_api(cls, credentials, status, **kwargs):
        account = Account.get_or_create_from_api(status.account, credentials)
        in_reply_to = None

        if status.in_reply_to_id:
            toots = cls.objects.filter(api_id=status.in_reply_to_id)

            try:
                in_reply_to = toots.get(credentials=credentials)
            except cls.DoesNotExist as ex:
                try:
                    in_reply_to = toots.filter(credentials__server=credentials.server)[0]
                except IndexError:
                    raise Exception('parent toot cannot be found') from ex

        url_template = credentials.url_template or '{url}'
        url = url_template.format(**status)

        return cls.objects.create(
            credentials=credentials,
            account=account,
            in_reply_to=in_reply_to,
            api_id=status.id,
            url=url,
            created_at=status.created_at,
            content=status.content,
            visibility=status.visibility,
            **kwargs,
        )

    @property
    def network_id(self):
        return self.get_network_id(self.credentials, self.api_id)

    @classmethod
    def get_network_id(cls, credentials, api_id):
        return f'mastodon_{credentials.friendly_hostname}_{api_id}'

    def __str__(self):
        return f'<Toot {self.content_stripped}>'
