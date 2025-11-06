from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, 
    Transaction, 
    PaymentMethod, 
    AdminWallet, 
    Trader, 
    # Asset,
    TraderPortfolio,
    Notification,
    Portfolio,
    News,
    Stock, 
    UserStockPosition,

    WalletConnection,
    
)



@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model"""
    
    list_display = (
        'email', 'first_name', 'last_name', 'account_id', 
        'balance', 'profit', 'current_loyalty_status', 
        'is_verified', 'is_active', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_verified', 
        'has_submitted_kyc', 'current_loyalty_status', 
        'date_joined'
    )
    search_fields = ('email', 'first_name', 'last_name', 'account_id')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'dob', 
                'phone', 'address', 'postal_code'
            )
        }),
        ('Location', {
            'fields': ('country', 'region', 'city', 'currency')
        }),
        ('KYC Information', {
            'fields': (
                'id_type', 'id_front', 'id_back', 
                'has_submitted_kyc', 'is_verified'
            )
        }),
        ('Referral Information', {
            'fields': (
                'referral_code', 'referred_by', 'referral_bonus_earned',
            )
        }),
        ('Financial', {
            'fields': (
                'account_id', 'balance', 'profit', 
                'current_loyalty_status', 'next_loyalty_status',
                'next_amount_to_upgrade',
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 
                'groups', 'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2', 
                'first_name', 'last_name', 'is_active', 'is_staff'
            ),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'account_id')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model"""
    
    list_display = (
        'reference', 'user', 'transaction_type', 
        'amount', 'status', 'created_at'
    )
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('reference', 'user__email', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('reference', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'user', 'transaction_type', 'amount', 
                'status', 'reference', 'description'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Allow admins to create transactions"""
        return True

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """Admin configuration for Portfolio model"""
    
    list_display = (
        'user', 'market', 'direction', 'invested', 
        'profit_loss', 'value', 'is_active', 'opened_at'
    )
    list_filter = ('direction', 'is_active', 'opened_at')
    search_fields = ('user__email', 'market')
    ordering = ('-opened_at',)
    readonly_fields = ('opened_at',)
    
    fieldsets = (
        ('Portfolio Details', {
            'fields': (
                'user', 'market', 'direction', 'invested', 
                'profit_loss', 'value', 'is_active'
            )
        }),
        ('Timestamp', {
            'fields': ('opened_at',)
        }),
    )



# admin.site.register(Transaction)
admin.site.register(PaymentMethod)
admin.site.register(AdminWallet)

# admin.site.register(Asset)
admin.site.register(News)



# Register Notification model
admin.site.register(Notification)

# Connect WALLET
admin.site.register(WalletConnection)



# Stocks


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = [
        'symbol',
        'name',
        'price',
        'change',
        'change_percent',
        'sector',
        'is_active',
        'is_featured',
        'updated_at'
    ]
    list_filter = ['is_active', 'is_featured', 'sector', 'created_at']
    search_fields = ['symbol', 'name', 'sector']
    list_editable = ['is_active', 'is_featured', 'price']
    readonly_fields = ['created_at', 'updated_at', 'formatted_price', 'formatted_market_cap']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('symbol', 'name', 'logo_url', 'sector')
        }),
        ('Price Data', {
            'fields': ('price', 'change', 'change_percent', 'formatted_price')
        }),
        ('Market Data', {
            'fields': ('volume', 'market_cap', 'formatted_market_cap')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()
    
    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']
    
    @admin.action(description='Mark selected stocks as active')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} stocks marked as active')
    
    @admin.action(description='Mark selected stocks as inactive')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} stocks marked as inactive')
    
    @admin.action(description='Mark selected stocks as featured')
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} stocks marked as featured')
    
    @admin.action(description='Remove featured status from selected stocks')
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f'{queryset.count()} stocks unfeatured')


@admin.register(UserStockPosition)
class UserStockPositionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'stock',
        'shares',
        'average_buy_price',
        'total_invested',
        'current_value_display',
        'profit_loss_display',
        'use_admin_profit',
        'is_active',
        'opened_at'
    ]
    list_filter = ['is_active', 'use_admin_profit', 'opened_at', 'closed_at']
    search_fields = ['user__email', 'stock__symbol', 'stock__name']
    list_editable = ['use_admin_profit']
    readonly_fields = [
        'opened_at',
        'closed_at',
        'current_value_display',
        'calculated_profit_loss_display',
        'calculated_profit_loss_percent_display'
    ]
    
    fieldsets = (
        ('Position Information', {
            'fields': ('user', 'stock', 'shares', 'is_active')
        }),
        ('Investment Details', {
            'fields': (
                'average_buy_price',
                'total_invested',
                'current_value_display',
            )
        }),
        ('Calculated Profit/Loss (Read-Only)', {
            'fields': (
                'calculated_profit_loss_display',
                'calculated_profit_loss_percent_display',
            ),
            'description': 'These are automatically calculated values for reference'
        }),
        ('Admin Custom Profit/Loss', {
            'fields': (
                'use_admin_profit',
                'admin_profit_loss',
                'admin_profit_loss_percent',
            ),
            'description': 'Enable "Use admin profit" and set custom profit/loss values here'
        }),
        ('Timestamps', {
            'fields': ('opened_at', 'closed_at'),
        }),
    )
    
    def current_value_display(self, obj):
        """Display current value"""
        return f"${obj.current_value:,.2f}"
    current_value_display.short_description = 'Current Value'
    
    def calculated_profit_loss_display(self, obj):
        """Show calculated profit/loss for reference"""
        calculated_pl = float(obj.current_value) - float(obj.total_invested)
        color = "green" if calculated_pl >= 0 else "red"
        formatted_value = "${:,.2f}".format(calculated_pl)
        return format_html('<span style="color: {};">{}</span>', color, formatted_value)
    calculated_profit_loss_display.short_description = 'Calculated P/L'
    
    def calculated_profit_loss_percent_display(self, obj):
        """Show calculated profit/loss percent for reference"""
        calculated_pl = float(obj.current_value) - float(obj.total_invested)
        if float(obj.total_invested) > 0:
            calculated_plp = (calculated_pl / float(obj.total_invested)) * 100
        else:
            calculated_plp = 0
        color = "green" if calculated_plp >= 0 else "red"
        formatted_value = "{:.2f}%".format(calculated_plp)
        return format_html('<span style="color: {};">{}</span>', color, formatted_value)
    calculated_profit_loss_percent_display.short_description = 'Calculated P/L %'
    
    @admin.display(description="Displayed Profit/Loss")
    def profit_loss_display(self, obj):
        """Display profit/loss - shows admin value if enabled, otherwise calculated"""
        # Use the property which handles the logic
        pl_value = float(obj.profit_loss)
        color = "green" if pl_value >= 0 else "red"
        formatted_value = "${:,.2f}".format(pl_value)
        
        # Add indicator if using admin value
        indicator = " 🔧" if obj.use_admin_profit else ""
        
        return format_html(
            '<span style="color: {};">{}{}</span>', 
            color, 
            formatted_value,
            indicator
        )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'stock')
    
    actions = ['close_positions', 'enable_admin_profit', 'disable_admin_profit']
    
    @admin.action(description='Close selected positions')
    def close_positions(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(is_active=True).update(
            is_active=False,
            closed_at=timezone.now()
        )
        self.message_user(request, f'{count} positions closed')
    
    @admin.action(description='Enable admin profit control')
    def enable_admin_profit(self, request, queryset):
        count = queryset.update(use_admin_profit=True)
        self.message_user(request, f'Admin profit control enabled for {count} positions')
    
    @admin.action(description='Disable admin profit control (use calculated)')
    def disable_admin_profit(self, request, queryset):
        count = queryset.update(use_admin_profit=False)
        self.message_user(request, f'Admin profit control disabled for {count} positions (using calculated values)')




# app/admin.py - Add this to your existing admin.py

from django.contrib import admin
from .models import Signal, UserSignalPurchase


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'signal_type', 
        'price', 
        'signal_strength',
        'action',
        'risk_level',
        'status',
        'is_featured',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'signal_type',
        'status',
        'risk_level',
        'is_featured',
        'is_active',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'market_analysis',
        'technical_indicators'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'signal_type',
                'price',
                'signal_strength',
                'is_featured',
                'is_active',
            )
        }),
        ('Trading Details', {
            'fields': (
                'action',
                'entry_point',
                'target_price',
                'stop_loss',
                'timeframe',
                'risk_level',
            )
        }),
        ('Analysis', {
            'fields': (
                'market_analysis',
                'technical_indicators',
                'fundamental_analysis',
            ),
            'classes': ('wide',)
        }),
        ('Status & Expiry', {
            'fields': (
                'status',
                'expires_at',
            )
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at']
    
    actions = ['mark_as_featured', 'mark_as_not_featured', 'mark_as_expired']
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} signal(s) marked as featured.')
    mark_as_featured.short_description = "Mark selected signals as featured"
    
    def mark_as_not_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} signal(s) removed from featured.')
    mark_as_not_featured.short_description = "Remove from featured"
    
    def mark_as_expired(self, request, queryset):
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} signal(s) marked as expired.')
    mark_as_expired.short_description = "Mark selected signals as expired"


@admin.register(UserSignalPurchase)
class UserSignalPurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'signal',
        'amount_paid',
        'purchase_reference',
        'purchased_at'
    ]
    
    list_filter = [
        'purchased_at',
        'signal__signal_type'
    ]
    
    search_fields = [
        'user__email',
        'signal__name',
        'purchase_reference'
    ]
    
    readonly_fields = [
        'user',
        'signal',
        'amount_paid',
        'purchase_reference',
        'signal_data',
        'purchased_at',
        'accessed_at'
    ]
    
    date_hierarchy = 'purchased_at'
    
    ordering = ['-purchased_at']
    
    def has_add_permission(self, request):
        # Prevent manual adding of purchases through admin
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of purchase records
        return False


# Add this to your admin.py file, replacing the basic registrations

from django.contrib import admin
from django.utils.html import format_html
from .models import Trader, TraderPortfolio

@admin.register(Trader)
class TraderAdmin(admin.ModelAdmin):
    """Admin configuration for Trader model"""
    
    list_display = [
        'name',
        'username',
        'country',
        'badge',
        'gain',
        'risk',
        'copiers',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'badge',
        'is_active',
        'country',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'username',
        'country'
    ]
    
    list_editable = [
        'is_active',
        'badge'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'avatar_preview',
        'flag_preview'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'username',
                'country',
                'badge',
                'is_active'
            )
        }),
        ('Images', {
            'fields': (
                'avatar',
                'avatar_preview',
                'country_flag',
                'flag_preview'
            )
        }),
        ('Trading Statistics', {
            'fields': (
                'gain',
                'risk',
                'capital',
                'copiers',
                'avg_trade_time',
                'trades'
            )
        }),
        ('Subscriber & Position Stats', {
            'fields': (
                'subscribers',
                'current_positions',
                'min_account_threshold',
                'expert_rating'
            )
        }),
        ('Performance Statistics', {
            'fields': (
                'return_ytd',
                'return_2y',
                'avg_score_7d',
                'profitable_weeks'
            )
        }),
        ('Trading Details', {
            'fields': (
                'total_trades_12m',
                'avg_profit_percent',
                'avg_loss_percent'
            )
        }),
        ('JSON Data', {
            'fields': (
                'performance_data',
                'monthly_performance',
                'frequently_traded'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-gain', '-copiers']
    
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def avatar_preview(self, obj):
        """Display avatar image preview"""
        if obj.avatar:
            try:
                return format_html(
                    '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 50%;" />',
                    obj.avatar.url
                )
            except:
                return "No image available"
        return "No avatar"
    avatar_preview.short_description = 'Avatar Preview'
    
    def flag_preview(self, obj):
        """Display country flag preview"""
        if obj.country_flag:
            try:
                return format_html(
                    '<img src="{}" style="max-height: 50px; max-width: 80px;" />',
                    obj.country_flag.url
                )
            except:
                return "No flag available"
        return "No flag"
    flag_preview.short_description = 'Flag Preview'
    
    @admin.action(description='Mark selected traders as active')
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} trader(s) marked as active.')
    
    @admin.action(description='Mark selected traders as inactive')
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} trader(s) marked as inactive.')


@admin.register(TraderPortfolio)
class TraderPortfolioAdmin(admin.ModelAdmin):
    """Admin configuration for TraderPortfolio model"""
    
    list_display = [
        'trader',
        'market',
        'direction',
        'invested',
        'profit_loss_display',
        'value',
        'is_active',
        'opened_at'
    ]
    
    list_filter = [
        'direction',
        'is_active',
        'opened_at',
        'trader__name'
    ]
    
    search_fields = [
        'trader__name',
        'trader__username',
        'market'
    ]
    
    list_editable = [
        'is_active'
    ]
    
    readonly_fields = [
        'opened_at'
    ]
    
    fieldsets = (
        ('Position Details', {
            'fields': (
                'trader',
                'market',
                'direction',
                'is_active'
            )
        }),
        ('Financial Data', {
            'fields': (
                'invested',
                'profit_loss',
                'value'
            )
        }),
        ('Timestamp', {
            'fields': (
                'opened_at',
            )
        })
    )
    
    ordering = ['-opened_at']
    
    date_hierarchy = 'opened_at'
    
    actions = ['close_positions', 'open_positions']
    
    def profit_loss_display(self, obj):
        """Display profit/loss with color coding"""
        color = "green" if obj.profit_loss >= 0 else "red"
        # Format the number FIRST into a string
        formatted_value = "{:.2f}%".format(float(obj.profit_loss))
        # Then pass the formatted string to format_html
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            formatted_value
        )
    profit_loss_display.short_description = 'Profit/Loss %'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('trader')
    
    @admin.action(description='Close selected positions')
    def close_positions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} position(s) closed.')
    
    @admin.action(description='Open selected positions')
    def open_positions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} position(s) opened.')


# IMPORTANT: Remove these lines from your admin.py:









































