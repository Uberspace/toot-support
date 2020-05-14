import django.contrib.admin as admin

from .models import SyncTask
from .models import TicketAction

admin.site.register(SyncTask)
admin.site.register(TicketAction)
