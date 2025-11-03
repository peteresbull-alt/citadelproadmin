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
        ('Financial', {
            'fields': (
                'account_id', 'balance', 'profit', 
                'current_loyalty_status', 'next_loyalty_status'
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
admin.site.register(Trader)
# admin.site.register(Asset)
admin.site.register(News)

admin.site.register(TraderPortfolio)

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


