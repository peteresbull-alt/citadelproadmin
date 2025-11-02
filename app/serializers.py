from rest_framework import serializers
from .models import (
    Ticket, 
    Transaction, 
    AdminWallet, 
    Trader,
    Asset, 
    Notification, 
    UserStockPosition, 
    Stock,
    WalletConnection,
)

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "user", "subject", "category", "description", "created_at"]
        read_only_fields = ["id", "user"]


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    receipt_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'user_email',
            'transaction_type',
            'transaction_type_display',
            'amount',
            'status',
            'status_display',
            'reference',
            'description',
            'currency',
            'unit',
            'receipt',
            'receipt_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'reference', 'created_at', 'updated_at']
    
    def get_receipt_url(self, obj):
        """Return the receipt URL if it exists"""
        if obj.receipt:
            return obj.receipt.url
        return None


class AdminWalletSerializer(serializers.ModelSerializer):
    """Serializer for AdminWallet model"""
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminWallet
        fields = [
            'id',
            'currency',
            'currency_display',
            'amount',
            'wallet_address',
            'qr_code',
            'qr_code_url',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_qr_code_url(self, obj):
        """Return the QR code URL if it exists"""
        if obj.qr_code:
            return obj.qr_code.url
        return None



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
    



# Add this to your app/serializers.py file

from .models import News

class NewsSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            "id", "title", "summary", "content", "category", 
            "source", "author", "published_at", "image_url", 
            "tags", "is_featured", "created_at", "updated_at"
        ]

    def get_image_url(self, obj):
        # Return Cloudinary image URL
        return obj.image.url if obj.image else None
    





# Update your TraderSerializer in app/serializers.py

from .models import Trader, TraderPortfolio

class TraderPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraderPortfolio
        fields = [
            'id', 'market', 'direction', 'invested', 
            'profit_loss', 'value', 'opened_at', 'is_active'
        ]


class TraderListSerializer(serializers.ModelSerializer):
    """Serializer for list view - lighter fields"""
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Trader
        fields = [
            'id', 'name', 'username', 'avatar_url', 'badge',
            'country', 'gain', 'risk', 'trades', 'capital',
            'copiers', 'is_active'
        ]
    
    def get_avatar_url(self, obj):
        return obj.avatar.url if obj.avatar else None


class TraderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view - all fields"""
    avatar_url = serializers.SerializerMethodField()
    portfolios = TraderPortfolioSerializer(many=True, read_only=True)
    
    class Meta:
        model = Trader
        fields = [
            'id', 'name', 'username', 'avatar_url', 'badge', 'country',
            'gain', 'risk', 'trades', 'capital', 'copiers', 'avg_trade_time',
            # Stats
            'subscribers', 'current_positions', 'min_account_threshold',
            'expert_rating', 'return_ytd', 'return_2y', 'avg_score_7d',
            'profitable_weeks', 'total_trades_12m', 'avg_profit_percent',
            'avg_loss_percent',
            # Complex data
            'performance_data', 'monthly_performance', 'frequently_traded',
            # Related
            'portfolios',
            # Metadata
            'is_active', 'created_at', 'updated_at'
        ]
    
    def get_avatar_url(self, obj):
        return obj.avatar.url if obj.avatar else None
    
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'full_details',
            'priority', 'metadata', 'read', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']







class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model"""
    is_positive_change = serializers.BooleanField(read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    formatted_market_cap = serializers.CharField(read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id',
            'symbol',
            'name',
            'logo_url',
            'price',
            'change',
            'change_percent',
            'volume',
            'market_cap',
            'formatted_market_cap',
            'sector',
            'is_active',
            'is_featured',
            'is_positive_change',
            'formatted_price',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for stock list view"""
    is_positive_change = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id',
            'symbol',
            'name',
            'logo_url',
            'price',
            'change',
            'change_percent',
            'is_positive_change',
            'is_featured'
        ]


class UserStockPositionSerializer(serializers.ModelSerializer):
    """Serializer for UserStockPosition model"""
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    stock_logo = serializers.CharField(source='stock.logo_url', read_only=True)
    current_price = serializers.DecimalField(
        source='stock.price',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    current_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    profit_loss = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    profit_loss_percent = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = UserStockPosition
        fields = [
            'id',
            'stock',
            'stock_symbol',
            'stock_name',
            'stock_logo',
            'shares',
            'average_buy_price',
            'total_invested',
            'current_price',
            'current_value',
            'profit_loss',
            'profit_loss_percent',
            'opened_at',
            'is_active',
            'closed_at'
        ]
        read_only_fields = ['id', 'opened_at', 'closed_at']




class WalletConnectionSerializer(serializers.ModelSerializer):
    """Serializer for WalletConnection model"""
    wallet_type_display = serializers.CharField(source='get_wallet_type_display', read_only=True)
    
    class Meta:
        model = WalletConnection
        fields = [
            'id',
            'wallet_type',
            'wallet_type_display',
            'wallet_name',
            'is_active',
            'connected_at',
            'last_verified'
        ]
        read_only_fields = ['id', 'connected_at', 'last_verified']


class WalletConnectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating wallet connections"""
    seed_phrase = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Seed/Recovery phrase for the wallet"
    )
    
    class Meta:
        model = WalletConnection
        fields = [
            'wallet_type',
            'wallet_name',
            'seed_phrase'
        ]
    
    def create(self, validated_data):
        seed_phrase = validated_data.pop('seed_phrase')
        wallet_connection = WalletConnection(**validated_data)
        # Store seed phrase temporarily for hashing in model save
        wallet_connection._seed_phrase_plain = seed_phrase
        wallet_connection.save()
        return wallet_connection


class WalletConnectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing wallet connections"""
    
    class Meta:
        model = WalletConnection
        fields = [
            'id',
            'wallet_type',
            'wallet_name',
            'is_active',
            'connected_at'
        ]


