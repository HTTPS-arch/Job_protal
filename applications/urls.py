from django.urls import path
from . import views

urlpatterns = [
    path(
        'apply/<slug:slug>/',
        views.apply_for_job,
        name='apply_for_job'
    ),
]
