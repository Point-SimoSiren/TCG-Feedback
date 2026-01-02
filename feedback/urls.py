from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("f/<str:token>/", views.public_feedback, name="public-feedback"),
    path("f/<str:token>/thanks/", views.public_thanks, name="public-thanks"),
]

