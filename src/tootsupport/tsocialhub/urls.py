from django.urls import path

from . import views

urlpatterns = [
    path('webhook/<int:task_id>', views.webhook),
]
