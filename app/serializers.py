# tickets/serializers.py
from rest_framework import serializers
from .models import Ticket, Transaction, AdminWallet, Trader, Asset

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "user", "subject", "category", "description", "created_at"]
        read_only_fields = ["id", "user"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "transaction_type", "asset_type", "amount", "status", "created_at"]



class AdminWalletSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = AdminWallet
        fields = ["id", "currency", "amount", "wallet_address", "qr_code_url", "is_active"]

    def get_qr_code_url(self, obj):
        return obj.qr_code.url if obj.qr_code else None



class TraderSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(use_url=True)
    class Meta:
        model = Trader
        fields = [
            "id", "name", "country", "avatar", "gain", "risk",
            "capital", "copiers", "avg_trade_time", "trades",
        ]

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url  # Full Cloudinary URL
        return None


class AssetSerializer(serializers.ModelSerializer):
    flag = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ["id", "category", "symbol", "flag", "change", "bid", "ask", "low", "high", "time"]

    def get_flag(self, obj):
        # return Cloudinary image URL
        return obj.flag.url if obj.flag else None