# wallet/serializers.py
"""
DRF Serializers cho wallet app.
"""

from rest_framework import serializers
from .models import UserWallet, CoinTransaction


class WalletBalanceSerializer(serializers.Serializer):
    """
    Serializer cho response balance API.
    """
    coins = serializers.IntegerField()
    checkin_streak = serializers.IntegerField()
    last_checkin_date = serializers.DateField(allow_null=True)
    checked_in_today = serializers.BooleanField()
    is_locked = serializers.BooleanField()


class CheckInResultSerializer(serializers.Serializer):
    """
    Serializer cho response check-in API.
    """
    success = serializers.BooleanField()
    coins_earned = serializers.IntegerField()
    bonus_earned = serializers.IntegerField()
    total_earned = serializers.IntegerField()
    new_streak = serializers.IntegerField()
    new_balance = serializers.IntegerField()
    message = serializers.CharField(required=False)


class CoinTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer cho lịch sử giao dịch.
    """
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    
    class Meta:
        model = CoinTransaction
        fields = [
            'id',
            'amount',
            'balance_after',
            'transaction_type',
            'transaction_type_display',
            'description',
            'reference_id',
            'created_at',
        ]
        read_only_fields = fields  # Tất cả đều readonly


class TransactionListSerializer(serializers.Serializer):
    """
    Serializer cho paginated transaction list response.
    """
    count = serializers.IntegerField()
    results = CoinTransactionSerializer(many=True)
