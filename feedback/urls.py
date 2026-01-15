from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('', views.feedback_list, name='list'),
    path('create/', views.feedback_create, name='create'),
    path('<int:pk>/', views.feedback_detail, name='detail'),
    path('<int:pk>/vote/', views.feedback_vote, name='vote'),
    path('<int:pk>/comment/', views.feedback_add_comment, name='add_comment'),
]
