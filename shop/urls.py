# shop/urls.py
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.shop_list, name='list'),
    path('buy/<int:frame_id>/', views.buy_frame, name='buy_frame'),
    path('equip/<int:frame_id>/', views.equip_frame, name='equip_frame'),
    path('unequip/', views.unequip_frame, name='unequip_frame'),
]
