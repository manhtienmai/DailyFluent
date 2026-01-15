# wallet/views.py
"""
API Views cho wallet app.
Sử dụng Django Rest Framework.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .services import CoinService
from .serializers import (
    WalletBalanceSerializer,
    CheckInResultSerializer,
    CoinTransactionSerializer,
)
from .exceptions import (
    AlreadyCheckedInError,
    WalletLockedError,
    InsufficientCoinsError,
)


class WalletBalanceView(APIView):
    """
    GET /api/wallet/balance/
    
    Trả về thông tin ví của user:
    - Số dư coin
    - Streak điểm danh
    - Trạng thái đã điểm danh hôm nay chưa
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        wallet_info = CoinService.get_wallet_info(request.user)
        serializer = WalletBalanceSerializer(wallet_info)
        return Response(serializer.data)


class CheckInView(APIView):
    """
    POST /api/wallet/check-in/
    
    Thực hiện điểm danh hàng ngày.
    
    Success Response (200):
    {
        "success": true,
        "coins_earned": 10,
        "bonus_earned": 0,
        "total_earned": 10,
        "new_streak": 5,
        "new_balance": 150,
        "message": "Điểm danh thành công!"
    }
    
    Error Response (400):
    {
        "success": false,
        "error": "already_checked_in",
        "message": "Bạn đã điểm danh hôm nay rồi!"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            result = CoinService.daily_checkin(request.user)
            
            # Thêm message thân thiện
            if result['bonus_earned'] > 0:
                result['message'] = (
                    f"🎉 Tuyệt vời! Bạn đã điểm danh {result['new_streak']} ngày liên tục "
                    f"và nhận được thưởng {result['bonus_earned']} coin!"
                )
            else:
                result['message'] = f"✅ Điểm danh thành công! Chuỗi {result['new_streak']} ngày."
            
            serializer = CheckInResultSerializer(result)
            return Response(serializer.data)
            
        except AlreadyCheckedInError as e:
            return Response({
                'success': False,
                'error': 'already_checked_in',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except WalletLockedError as e:
            return Response({
                'success': False,
                'error': 'wallet_locked',
                'message': str(e),
            }, status=status.HTTP_403_FORBIDDEN)


class TransactionPagination(PageNumberPagination):
    """Pagination cho transaction list."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TransactionHistoryView(APIView):
    """
    GET /api/wallet/transactions/
    
    Lấy lịch sử giao dịch (phân trang).
    
    Query params:
    - page: Trang số (default: 1)
    - page_size: Số items mỗi trang (default: 20, max: 100)
    - type: Filter theo loại giao dịch (optional)
    
    Response:
    {
        "count": 50,
        "next": "/api/wallet/transactions/?page=2",
        "previous": null,
        "results": [...]
    }
    """
    permission_classes = [IsAuthenticated]
    pagination_class = TransactionPagination
    
    def get(self, request):
        from .models import CoinTransaction
        
        # Get queryset
        queryset = CoinTransaction.objects.filter(user=request.user)
        
        # Filter by type if provided
        tx_type = request.query_params.get('type')
        if tx_type:
            queryset = queryset.filter(transaction_type=tx_type)
        
        # Order by newest first
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = CoinTransactionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = CoinTransactionSerializer(queryset, many=True)
        return Response(serializer.data)
