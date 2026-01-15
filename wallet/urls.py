# wallet/urls.py
"""
URL patterns cho wallet API.
"""

from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # GET - Lấy số dư và thông tin ví
    path('balance/', views.WalletBalanceView.as_view(), name='balance'),
    
    # POST - Điểm danh hàng ngày
    path('check-in/', views.CheckInView.as_view(), name='check-in'),
    
    # GET - Lịch sử giao dịch (paginated)
    path('transactions/', views.TransactionHistoryView.as_view(), name='transactions'),
]
