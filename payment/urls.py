from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('', views.payment_plans, name='plans'),
    path('plans/', views.payment_plans, name='plans'),
    path('create/<slug:plan_slug>/', views.create_payment, name='create'),
    path('<uuid:payment_id>/status/', views.payment_status, name='status'),
    path('<uuid:payment_id>/qr-code/', views.qr_code_image, name='qr_code'),
    path('<uuid:payment_id>/bank-transfer/', views.submit_bank_transfer, name='submit_bank_transfer'),
    path('my-subscription/', views.my_subscription, name='my_subscription'),
]

