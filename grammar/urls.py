from django.urls import path
from . import views

app_name = "grammar"

urlpatterns = [
    path("", views.grammar_list, name="list"),
    path("<slug:slug>/", views.grammar_detail, name="detail"),
]

