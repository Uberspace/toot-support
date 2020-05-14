import django.contrib.admin as admin

from .models import Account
from .models import Credential
from .models import Toot

admin.site.register(Credential)
admin.site.register(Account)
admin.site.register(Toot)
