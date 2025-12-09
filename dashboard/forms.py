# dashboard/forms.py
from django import forms
from app.models import CustomUser, Stock, Transaction, AdminWallet, Trader, UserCopyTraderHistory
from decimal import Decimal

class AddTradeForm(forms.Form):
    """Form for adding trades with extensive dropdowns"""
    
    # User selection
    user_email = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        }),
        to_field_name='email'
    )
    
    # Entry amount
    entry = forms.DecimalField(
        label="Entry Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '5255'
        })
    )
    
    # Asset type
    ASSET_TYPE_CHOICES = [
        ('', 'Select Type'),
        ('stock', 'Stock'),
        ('crypto', 'Crypto'),
        ('forex', 'Forex'),
    ]
    
    asset_type = forms.ChoiceField(
        choices=ASSET_TYPE_CHOICES,
        label="Type",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Asset (populated dynamically based on type)
    asset = forms.CharField(
        label="Asset",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Select type first'
        })
    )
    
    # Direction
    DIRECTION_CHOICES = [
        ('', 'Select Direction'),
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('futures', 'Futures'),
    ]
    
    direction = forms.ChoiceField(
        choices=DIRECTION_CHOICES,
        label="Direction",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Profit/Loss
    profit = forms.DecimalField(
        label="Profit/Loss",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '0.00'
        })
    )
    
    # Duration
    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 minutes'),
        ('5 minutes', '5 minutes'),
        ('30 minutes', '30 minutes'),
        ('1 hour', '1 hour'),
        ('8 hours', '8 hours'),
        ('10 hours', '10 hours'),
        ('20 hours', '20 hours'),
        ('1 day', '1 day'),
        ('2 days', '2 days'),
        ('3 days', '3 days'),
        ('4 days', '4 days'),
        ('5 days', '5 days'),
        ('6 days', '6 days'),
        ('1 week', '1 week'),
        ('2 weeks', '2 weeks'),
    ]
    
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Duration",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Rate (optional)
    rate = forms.DecimalField(
        label="Rate (Optional)",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '251'
        })
    )


class AddEarningsForm(forms.Form):
    """Quick form for adding earnings to users"""
    
    user_email = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
        to_field_name='email'
    )
    
    amount = forms.DecimalField(
        label="Earnings Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': '100.00'
        })
    )
    
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Bonus, Referral, Trade Profit, etc.'
        })
    )


class ApproveDepositForm(forms.Form):
    """Form for approving deposits"""
    
    STATUS_CHOICES = [
        ('completed', 'Approve'),
        ('failed', 'Reject'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Internal notes about this transaction...'
        })
    )


class ApproveWithdrawalForm(forms.Form):
    """Form for approving withdrawals"""
    
    STATUS_CHOICES = [
        ('completed', 'Approve'),
        ('failed', 'Reject'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Internal notes about this withdrawal...'
        })
    )


class ApproveKYCForm(forms.Form):
    """Form for approving KYC submissions"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve KYC'),
        ('reject', 'Reject KYC'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Reason for rejection or any notes...'
        })
    )


class AddCopyTradeForm(forms.Form):
    """Form for adding copy trade history with dropdowns"""
    
    # User selection
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'id': 'id_user'
        }),
        empty_label="Select User"
    )
    
    # Trader selection
    trader = forms.ModelChoiceField(
        queryset=Trader.objects.filter(is_active=True).order_by('name'),
        label="Select Trader",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'id': 'id_trader'
        }),
        empty_label="Select Trader"
    )
    
    # Market selection
    MARKET_CHOICES = [
        ('', 'Select Market'),
        ('BTC/USD', 'Bitcoin / US Dollar'),
        ('ETH/USD', 'Ethereum / US Dollar'),
        ('EUR/USD', 'Euro / US Dollar'),
        ('GBP/USD', 'British Pound / US Dollar'),
        ('USD/JPY', 'US Dollar / Japanese Yen'),
        ('AUD/USD', 'Australian Dollar / US Dollar'),
        ('USD/CAD', 'US Dollar / Canadian Dollar'),
        ('NZD/USD', 'New Zealand Dollar / US Dollar'),
        ('XAU/USD', 'Gold / US Dollar'),
        ('XAG/USD', 'Silver / US Dollar'),
        ('AAPL', 'Apple Inc.'),
        ('GOOGL', 'Google (Alphabet)'),
        ('TSLA', 'Tesla Inc.'),
        ('MSFT', 'Microsoft'),
        ('AMZN', 'Amazon'),
    ]
    
    market = forms.ChoiceField(
        choices=MARKET_CHOICES,
        label="Market / Asset",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Direction
    direction = forms.ChoiceField(
        choices=[('', 'Select Direction')] + list(UserCopyTraderHistory.DIRECTION_CHOICES),
        label="Trade Direction",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Leverage
    LEVERAGE_CHOICES = [
        ('', 'Select Leverage'),
        ('1x', '1x'),
        ('2x', '2x'),
        ('5x', '5x'),
        ('10x', '10x'),
        ('20x', '20x'),
        ('25x', '25x'),
        ('50x', '50x'),
        ('75x', '75x'),
        ('100x', '100x'),
        ('125x', '125x'),
        ('150x', '150x'),
    ]
    
    leverage = forms.ChoiceField(
        choices=LEVERAGE_CHOICES,
        label="Leverage",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Duration
    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 Minutes'),
        ('5 minutes', '5 Minutes'),
        ('10 minutes', '10 Minutes'),
        ('15 minutes', '15 Minutes'),
        ('30 minutes', '30 Minutes'),
        ('1 hour', '1 Hour'),
        ('2 hours', '2 Hours'),
        ('4 hours', '4 Hours'),
        ('12 hours', '12 Hours'),
        ('1 day', '1 Day'),
        ('2 days', '2 Days'),
        ('1 week', '1 Week'),
        ('2 weeks', '2 Weeks'),
        ('1 month', '1 Month'),
    ]
    
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Trade Duration",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Amount
    amount = forms.DecimalField(
        label="Investment Amount",
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '1000.00',
            'step': '0.00000001'
        })
    )
    
    # Entry Price
    entry_price = forms.DecimalField(
        label="Entry Price",
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '50000.00',
            'step': '0.00000001'
        })
    )
    
    # Exit Price (Optional)
    exit_price = forms.DecimalField(
        label="Exit Price (Optional)",
        max_digits=20,
        decimal_places=8,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '51000.00',
            'step': '0.00000001'
        })
    )
    
    # Profit/Loss
    profit_loss = forms.DecimalField(
        label="Profit / Loss",
        max_digits=20,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '250.00 (positive for profit, negative for loss)',
            'step': '0.01'
        })
    )
    
    # Status
    status = forms.ChoiceField(
        choices=[('', 'Select Status')] + list(UserCopyTraderHistory.STATUS_CHOICES),
        label="Trade Status",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Closed At (Optional)
    closed_at = forms.DateTimeField(
        label="Close Date & Time (Optional)",
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'datetime-local',
            'placeholder': 'Leave blank if trade is still open'
        })
    )
    
    # Notes
    notes = forms.CharField(
        label="Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Additional notes about this trade...'
        })
    )


class AddTraderForm(forms.Form):
    """Form for adding professional traders with dropdowns"""
    
    # Basic Info (Required)
    name = forms.CharField(
        label="Trader Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Kristijan'
        })
    )
    
    username = forms.CharField(
        label="Username",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '@kristijan'
        }),
        help_text="Must be unique"
    )
    
    avatar = forms.ImageField(
        label="Trader Avatar (Profile Picture)",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'accept': 'image/*'
        }),
        help_text="Upload trader profile picture (JPG, PNG, WEBP, etc.)"
    )
    
    country_flag = forms.ImageField(
        label="Country Flag Image",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'accept': 'image/*'
        }),
        help_text="Upload country flag image (optional)"
    )
    
    COUNTRY_CHOICES = [
        ('', 'Select Country'),
        ('United States', 'United States'),
        ('United Kingdom', 'United Kingdom'),
        ('Germany', 'Germany'),
        ('France', 'France'),
        ('Canada', 'Canada'),
        ('Australia', 'Australia'),
        ('Singapore', 'Singapore'),
        ('Hong Kong', 'Hong Kong'),
        ('Japan', 'Japan'),
        ('South Korea', 'South Korea'),
        ('India', 'India'),
        ('Brazil', 'Brazil'),
        ('Mexico', 'Mexico'),
        ('Netherlands', 'Netherlands'),
        ('Switzerland', 'Switzerland'),
        ('Sweden', 'Sweden'),
        ('Norway', 'Norway'),
        ('Denmark', 'Denmark'),
        ('Spain', 'Spain'),
        ('Italy', 'Italy'),
        ('Other', 'Other'),
    ]
    
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        label="Country",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    # Badge Level
    badge = forms.ChoiceField(
        choices=[
            ('', 'Select Badge'),
            ('bronze', 'Bronze'),
            ('silver', 'Silver'),
            ('gold', 'Gold'),
        ],
        label="Badge Level",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    # Trading Stats (Required)
    CAPITAL_CHOICES = [
        ('', 'Select Starting Capital'),
        ('1000', '$1,000'),
        ('5000', '$5,000'),
        ('10000', '$10,000'),
        ('25000', '$25,000'),
        ('50000', '$50,000'),
        ('75000', '$75,000'),
        ('100000', '$100,000'),
        ('250000', '$250,000'),
        ('500000', '$500,000'),
        ('1000000', '$1,000,000'),
    ]
    
    capital_dropdown = forms.ChoiceField(
        choices=CAPITAL_CHOICES,
        label="Starting Capital (Dropdown)",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    capital = forms.CharField(
        label="OR Enter Custom Amount",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '50000'
        }),
        help_text="Leave blank to use dropdown"
    )
    
    GAIN_CHOICES = [
        ('', 'Select Total Gain %'),
        ('50', '50% - Beginner'),
        ('100', '100% - Good'),
        ('500', '500% - Very Good'),
        ('1000', '1,000% - Excellent'),
        ('5000', '5,000% - Outstanding'),
        ('10000', '10,000% - Expert'),
        ('50000', '50,000% - Master'),
        ('100000', '100,000% - Legend'),
        ('126799', '126,799% - Elite'),
    ]
    
    gain_dropdown = forms.ChoiceField(
        choices=GAIN_CHOICES,
        label="Total Gain % (Dropdown)",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    gain = forms.DecimalField(
        label="OR Enter Exact Gain %",
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '126799.00',
            'step': '0.01'
        }),
        help_text="Leave blank to use dropdown"
    )
    
    RISK_CHOICES = [(i, str(i)) for i in range(1, 11)]
    risk = forms.ChoiceField(
        choices=[('', 'Select Risk Level')] + RISK_CHOICES,
        label="Risk Level (1-10)",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    COPIERS_CHOICES = [
        ('', 'Select Number of Copiers'),
        ('1-10', '1-10 Copiers'),
        ('11-20', '11-20 Copiers'),
        ('21-30', '21-30 Copiers'),
        ('31-50', '31-50 Copiers'),
        ('51-100', '51-100 Copiers'),
        ('101-200', '101-200 Copiers'),
        ('201-300', '201-300 Copiers'),
        ('300+', '300+ Copiers'),
    ]
    
    copiers_range = forms.ChoiceField(
        choices=COPIERS_CHOICES,
        label="Number of Copiers",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    copiers = forms.IntegerField(
        label="Exact Number (Optional)",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '40',
            'min': '0'
        }),
        help_text="Leave blank to use range"
    )
    
    TRADES_CHOICES = [
        ('', 'Select Total Trades'),
        ('1-50', '1-50 Trades'),
        ('51-100', '51-100 Trades'),
        ('101-200', '101-200 Trades'),
        ('201-300', '201-300 Trades'),
        ('301-500', '301-500 Trades'),
        ('500+', '500+ Trades'),
    ]
    
    trades_range = forms.ChoiceField(
        choices=TRADES_CHOICES,
        label="Total Trades (12 months)",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    trades = forms.IntegerField(
        label="Exact Number (Optional)",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '251',
            'min': '0'
        }),
        help_text="Leave blank to use range"
    )
    
    AVG_TRADE_TIME_CHOICES = [
        ('', 'Select Average Trade Time'),
        ('1 day', '1 Day'),
        ('3 days', '3 Days'),
        ('1 week', '1 Week'),
        ('2 weeks', '2 Weeks'),
        ('3 weeks', '3 Weeks'),
        ('1 month', '1 Month'),
        ('2 months', '2 Months'),
        ('3 months', '3 Months'),
        ('6 months', '6 Months'),
    ]
    
    avg_trade_time = forms.ChoiceField(
        choices=AVG_TRADE_TIME_CHOICES,
        label="Average Trade Time",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    AVG_PROFIT_CHOICES = [
        ('', 'Select Avg Profit %'),
        ('10', '10%'),
        ('20', '20%'),
        ('30', '30%'),
        ('40', '40%'),
        ('50', '50%'),
        ('60', '60%'),
        ('70', '70%'),
        ('80', '80%'),
        ('86', '86%'),
        ('90', '90%'),
        ('95', '95%'),
    ]
    
    avg_profit_dropdown = forms.ChoiceField(
        choices=AVG_PROFIT_CHOICES,
        label="Average Profit % (Dropdown)",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    avg_profit_percent = forms.DecimalField(
        label="OR Enter Exact %",
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '86.00',
            'step': '0.01'
        }),
        help_text="Leave blank to use dropdown"
    )
    
    AVG_LOSS_CHOICES = [
        ('', 'Select Avg Loss %'),
        ('5', '5%'),
        ('8', '8%'),
        ('10', '10%'),
        ('12', '12%'),
        ('15', '15%'),
        ('20', '20%'),
        ('25', '25%'),
        ('30', '30%'),
    ]
    
    avg_loss_dropdown = forms.ChoiceField(
        choices=AVG_LOSS_CHOICES,
        label="Average Loss % (Dropdown)",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    avg_loss_percent = forms.DecimalField(
        label="OR Enter Exact %",
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '8.00',
            'step': '0.01'
        }),
        help_text="Leave blank to use dropdown"
    )
    
    WINS_CHOICES = [
        ('', 'Select Total Wins'),
        ('50', '50 Wins'),
        ('100', '100 Wins'),
        ('250', '250 Wins'),
        ('500', '500 Wins'),
        ('1000', '1,000 Wins'),
        ('1166', '1,166 Wins'),
        ('1500', '1,500 Wins'),
        ('2000', '2,000 Wins'),
    ]
    
    total_wins_dropdown = forms.ChoiceField(
        choices=WINS_CHOICES,
        label="Total Wins (Dropdown)",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    total_wins = forms.IntegerField(
        label="OR Enter Exact Number",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '1166',
            'min': '0'
        }),
        help_text="Leave blank to use dropdown"
    )
    
    LOSSES_CHOICES = [
        ('', 'Select Total Losses'),
        ('10', '10 Losses'),
        ('50', '50 Losses'),
        ('100', '100 Losses'),
        ('160', '160 Losses'),
        ('200', '200 Losses'),
        ('300', '300 Losses'),
        ('500', '500 Losses'),
    ]
    
    total_losses_dropdown = forms.ChoiceField(
        choices=LOSSES_CHOICES,
        label="Total Losses (Dropdown)",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    total_losses = forms.IntegerField(
        label="OR Enter Exact Number",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '160',
            'min': '0'
        }),
        help_text="Leave blank to use dropdown"
    )
    
    # Optional Stats
    SUBSCRIBERS_CHOICES = [
        ('', 'Select Subscribers Range'),
        ('0', '0 Subscribers'),
        ('1-10', '1-10 Subscribers'),
        ('11-25', '11-25 Subscribers'),
        ('26-50', '26-50 Subscribers'),
        ('51-100', '51-100 Subscribers'),
        ('101-200', '101-200 Subscribers'),
        ('200+', '200+ Subscribers'),
    ]
    
    subscribers_range = forms.ChoiceField(
        choices=SUBSCRIBERS_CHOICES,
        label="Total Subscribers",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    subscribers = forms.IntegerField(
        label="Exact Number (Optional)",
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '49',
            'min': '0'
        }),
        help_text="Leave blank to use range"
    )
    
    POSITIONS_CHOICES = [
        ('', 'Select Current Positions'),
        ('0', 'No Open Positions'),
        ('1-5', '1-5 Positions'),
        ('6-10', '6-10 Positions'),
        ('11-20', '11-20 Positions'),
        ('20+', '20+ Positions'),
    ]
    
    current_positions_range = forms.ChoiceField(
        choices=POSITIONS_CHOICES,
        label="Current Open Positions",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    current_positions = forms.IntegerField(
        label="Exact Number (Optional)",
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '3',
            'min': '0'
        }),
        help_text="Leave blank to use range"
    )
    
    EXPERT_RATING_CHOICES = [
        ('', 'Select Rating'),
        ('5.00', '5.00 - Excellent'),
        ('4.90', '4.90 - Outstanding'),
        ('4.80', '4.80 - Very Good'),
        ('4.70', '4.70 - Very Good'),
        ('4.60', '4.60 - Good'),
        ('4.50', '4.50 - Good'),
        ('4.00', '4.00 - Above Average'),
        ('3.50', '3.50 - Average'),
        ('3.00', '3.00 - Below Average'),
    ]
    
    expert_rating = forms.ChoiceField(
        choices=EXPERT_RATING_CHOICES,
        label="Expert Rating (out of 5.00)",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    return_ytd = forms.DecimalField(
        label="Return YTD % (Optional)",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '2187.00',
            'step': '0.01'
        })
    )
    
    avg_score_7d = forms.DecimalField(
        label="Average Score (Last 7 Days)",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '9.30',
            'step': '0.01'
        })
    )
    
    profitable_weeks = forms.DecimalField(
        label="Profitable Weeks % (Optional)",
        max_digits=5,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '92.00',
            'step': '0.01'
        })
    )
    
    min_account_threshold = forms.DecimalField(
        label="Minimum Account Balance Required (Optional)",
        max_digits=12,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '50000.00',
            'step': '0.01'
        })
    )
    
    is_active = forms.BooleanField(
        label="Active (Available for Copying)",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500',
        })
    )


class EditTraderForm(AddTraderForm):
    """Form for editing existing traders - inherits all fields from AddTraderForm"""
    pass