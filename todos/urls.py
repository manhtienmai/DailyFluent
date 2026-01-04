from django.urls import path
from . import views

app_name = 'todos'

urlpatterns = [
    path('', views.todo_list, name='todo_list'),
    path('api/', views.todo_list_api, name='todo_list_api'),
    path('create/', views.todo_create, name='todo_create'),
    path('<int:todo_id>/update/', views.todo_update, name='todo_update'),
    path('<int:todo_id>/delete/', views.todo_delete, name='todo_delete'),
    path('<int:todo_id>/toggle/', views.todo_toggle, name='todo_toggle'),
]

