import random

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from cloudinary.models import CloudinaryField


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a user with an email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    # Loyalty Status
    LOYALTY_TIERS = [
        ('iron', 'Iron'),
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
    ]

    # KYC Fields
    id_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ("passport", "Passport"),
            ("driver_license", "Driver's License"),
            ("national_id", "National ID"),
            ("voter_card", "Voter's Card"),
        ],
        help_text="Select the type of ID provided",
    )
    id_front = CloudinaryField("image", blank=True, null=True, help_text="Front side of ID document")
    id_back = CloudinaryField("image", blank=True, null=True, help_text="Back side of ID document")
    is_verified = models.BooleanField(default=False)
    has_submitted_kyc = models.BooleanField(default=False)
    
    # Personal Info
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    postal_code = models.CharField(max_length=500, blank=True, null=True)

    # Location & Contact Info
    country = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)

    # User Balances
    account_id = models.CharField(max_length=10, blank=True, null=True)
    balance = models.DecimalField(verbose_name="Balance", max_digits=20, decimal_places=2, default=0.00, help_text="This is a monetary value.")
    profit = models.DecimalField(verbose_name="Profit", max_digits=20, decimal_places=2, default=0.00, help_text="This is a monetary value.")
    
    current_loyalty_status = models.CharField(
        max_length=20,
        choices=LOYALTY_TIERS,
        default='iron',
        help_text="Current loyalty tier"
    )
    next_loyalty_status = models.CharField(
        max_length=20,
        choices=LOYALTY_TIERS,
        default='bronze',
        help_text="Next loyalty tier"
    )


    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Email & Password are required by default
    
    class Meta:
        verbose_name_plural = "Users"
        verbose_name = "User"

    def __str__(self):
        return self.email


def generate_unique_account_id():
    while True:
        account_id = str(random.randint(10**9, 10**10 - 1))  # 10-digit number
        if not CustomUser.objects.filter(account_id=account_id).exists():
            return account_id


# Signal: auto-create token for each new user
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

        # Assign unique 10-digit account_id if not already set
        if not instance.account_id:
            instance.account_id = generate_unique_account_id()
            instance.save(update_fields=["account_id"])


class Portfolio(models.Model):
    """Model to track user copy trading portfolios"""
    
    DIRECTION_CHOICES = [
        ('LONG', 'Long'),
        ('SHORT', 'Short'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolios'
    )
    market = models.CharField(max_length=100, help_text="Market/Asset name (e.g., BTC/USD)")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    invested = models.DecimalField(max_digits=20, decimal_places=2, help_text="Amount invested")
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, help_text="Profit/Loss percentage")
    value = models.DecimalField(max_digits=20, decimal_places=2, help_text="Current value")
    opened_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-opened_at']
        verbose_name_plural = "User's Portfolios"
        verbose_name_plural = "User's Portfolio"
        
    def __str__(self):
        return f"{self.user.email} - {self.market} - {self.direction}"


class Trader(models.Model):
    # Basic Info
    name = models.CharField(max_length=150)
    username = models.CharField(
        max_length=100,
        unique=True,
        help_text="Trader username. Example: @SERGE"
    )
    country = models.CharField(max_length=100)
    avatar = CloudinaryField(
        "Trader Image",
        folder="copy_trader_images",
        blank=True,
        null=True,
        help_text="Upload the trader image"
    )
    badge = models.CharField(
        max_length=20,
        choices=[
            ('gold', 'Gold'),
            ('silver', 'Silver'),
            ('bronze', 'Bronze'),
        ],
        default='bronze',
        help_text="Trader badge level"
    )
    
    # Trading Info
    gain = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="This should be the gain he made from the trade e.g. 194.32"
    )
    risk = models.PositiveSmallIntegerField(
        help_text="Risk score should be from 1 to 10."
    )
    capital = models.CharField(
        max_length=50, 
        help_text="Enter the amount in dollars e.g. 2000, 4000"
    )
    copiers = models.PositiveIntegerField(
        help_text="This should range from 1 to 300 or even more."
    )
    avg_trade_time = models.CharField(
        max_length=50, 
        help_text="This should be time basis like '1 week', '3 weeks', '2 months'"
    )
    trades = models.PositiveIntegerField(
        help_text="This should be an integer showing the number of trade this trader has taken."
    )
    
    # Stats fields
    subscribers = models.PositiveIntegerField(
        default=0,
        help_text="Total number of subscribers"
    )
    current_positions = models.PositiveIntegerField(
        default=0,
        help_text="Number of current open positions"
    )
    min_account_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Minimum account balance required to copy this trader"
    )
    expert_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.00,
        help_text="Expert rating out of 5.00"
    )
    
    # Performance stats
    return_ytd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Return Year To Date percentage"
    )
    return_2y = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Return over 2 years percentage"
    )
    avg_score_7d = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Average score over last 7 days"
    )
    profitable_weeks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Percentage of profitable weeks"
    )
    
    # Trading stats
    total_trades_12m = models.PositiveIntegerField(
        default=0,
        help_text="Total trades in past 12 months"
    )
    avg_profit_percent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Average profit percentage per trade"
    )
    avg_loss_percent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Average loss percentage per trade"
    )
    
    # JSON fields for complex data
    performance_data = models.JSONField(
        default=list,
        blank=True,
        help_text="Monthly performance data as list of {month, value}"
    )
    monthly_performance = models.JSONField(
        default=list,
        blank=True,
        help_text="Monthly performance percentages as list of {month, percentage}"
    )
    frequently_traded = models.JSONField(
        default=list,
        blank=True,
        help_text="List of frequently traded assets"
    )
    
    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Is this trader available for copying?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Copy Traders"
        verbose_name = "Trader"
        ordering = ["-gain", "-copiers"]

    def __str__(self):
        return f"{self.name} ({self.country})"


class TraderPortfolio(models.Model):
    DIRECTION_CHOICES = [
        ('LONG', 'Long'),
        ('SHORT', 'Short'),
    ]
    
    trader = models.ForeignKey(
        Trader,
        on_delete=models.CASCADE,
        related_name='portfolios',
        help_text="The trader this portfolio belongs to"
    )
    market = models.CharField(
        max_length=100,
        help_text="Market/Asset name. Example: AAPL, EURUSD, BTC"
    )
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        help_text="Trade direction: Long or Short"
    )
    invested = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount invested in this position"
    )
    profit_loss = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Profit/Loss percentage"
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Current value of the position"
    )
    opened_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this position was opened"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this position still open?"
    )
    
    class Meta:
        verbose_name = "Trader Portfolio Position"
        verbose_name_plural = "Trader Portfolio Positions"
        ordering = ["-opened_at"]
    
    def __str__(self):
        return f"{self.trader.name} - {self.market} ({self.direction})"


class Transaction(models.Model):

    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    TRANSACTION_TYPES = [
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(verbose_name="Total Amount", max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default="pending")
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=100)
    unit = models.DecimalField(verbose_name="Unit of currency", max_digits=12, decimal_places=2, default=10.00)

    receipt = CloudinaryField(
        "receipt",
        folder="receipt",
        blank=True,
        null=True,
        help_text="Here's the receipt for the transaction."
    )

    

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"TXN-{random.randint(100000, 999999)}-{self.user.id}"
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Transactions"
        verbose_name = "Transaction"

class Ticket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    subject = models.CharField(max_length=200, blank=True, null=False)
    category = models.CharField(max_length=200, blank=True, null=False)
    description = models.TextField(blank=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class PaymentMethod(models.Model):
    WALLET_CHOICES = [
        ("ETH", "Ethereum"),
        ("BTC", "Bitcoin"),
        ("SOL", "Solana"),
        ("USDT_ERC20", "USDT (ERC20)"),  # ADDED
        ("USDT_TRC20", "USDT (TRC20)"),  # ADDED
        ("BANK", "Bank Transfer"),
        ("CASHAPP", "Cash App"),
        ("PAYPAL", "PayPal"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods")
    method_type = models.CharField(max_length=20, choices=WALLET_CHOICES)

    # Generic fields to store values depending on type
    address = models.CharField(max_length=255, blank=True, null=True)  # for ETH, BTC, SOL
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    cashapp_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_email = models.EmailField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.method_type}"


class AdminWallet(models.Model):
    CURRENCY_CHOICES = [
        ("BTC", "Bitcoin (BTC)"),
        ("ETH", "Ethereum (ETH)"),
        ("SOL", "Solana (SOL)"),
        ("USDT ERC20", "USDT (ERC20)"),
        ("USDT TRC20", "USDT (TRC20)"),
        ("BNB", "Binance Coin (BNB)"),
        ("TRX", "Tron (TRX)"),
        ("USDC", "USDC (BASE)"),
    ]

    currency = models.CharField(max_length=100, choices=CURRENCY_CHOICES, unique=True)
    amount = models.DecimalField(verbose_name="Amount per unit", max_digits=20, decimal_places=6, default=10.00)
    wallet_address = models.CharField(max_length=255)
    qr_code = CloudinaryField(
        "QRCode",
        folder="wallet_qrcodes",
        blank=True,
        null=True,
        help_text="Optional QR code image for scanning"
    )

    is_active = models.BooleanField(default=True, help_text="Enable/disable this payment option")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin Wallet"
        verbose_name_plural = "Admin Wallets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_currency_display()} - {self.wallet_address[:10]}..."


class Asset(models.Model):
    CATEGORY_CHOICES = [
        ("Forex", "Forex"),
        ("Crypto", "Crypto"),
        ("Commodities", "Commodities"),
        ("Stocks", "Stocks"),
    ]

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Choose the asset category. Example: Forex, Crypto, Commodities, Stocks"
    )
    symbol = models.CharField(
        max_length=20,
        unique=True,
        help_text="Enter the trading symbol. Example: EURUSD, BTCUSD, XAUUSD"
    )
    
    flag = CloudinaryField(
        "Asset Flag",
        folder="asset_flags",
        blank=True,
        null=True,
        help_text="Upload the asset flag/logo image. Example: eurousd_nobg.png"
    )
    change = models.FloatField(
        help_text="Enter the percentage change in price. Example: 0.02 for +0.02%"
    )
    bid = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Enter the bid price (buy). Example: 1.18031"
    )
    ask = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Enter the ask price (sell). Example: 1.18051"
    )
    low = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Enter the lowest price for the period. Example: 1.17626"
    )
    high = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Enter the highest price for the period. Example: 1.18199"
    )
    time = models.TimeField(
        help_text="Enter the timestamp of the price update. Example: 10:47:52"
    )

    def __str__(self):
        return f"{self.symbol} ({self.category})"


class News(models.Model):
    CATEGORY_CHOICES = [
        ("Stocks", "Stocks"),
        ("Technology", "Technology"),
        ("Economy", "Economy"),
        ("Cryptocurrency", "Cryptocurrency"),
        ("Commodities", "Commodities"),
        ("Forex", "Forex"),
    ]

    title = models.CharField(
        max_length=255,
        help_text="Enter the news article title. Example: Tesla Stock Surges After Record Q4 Deliveries"
    )
    summary = models.TextField(
        help_text="Brief summary of the article (1-2 sentences)"
    )
    content = models.TextField(
        help_text="Full article content"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        help_text="Select the news category"
    )
    source = models.CharField(
        max_length=100,
        help_text="News source name. Example: Financial Times, Bloomberg"
    )
    author = models.CharField(
        max_length=100,
        help_text="Author name. Example: Sarah Johnson"
    )
    published_at = models.DateTimeField(
        help_text="Publication date and time"
    )
    image = CloudinaryField(
        "News Image",
        folder="news_images",
        blank=True,
        null=True,
        help_text="Upload news article image or company logo"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Enter tags as a list. Example: ['Tesla', 'Electric Vehicles', 'Earnings']"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Mark as featured article"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"
        ordering = ["-published_at"]

    def __str__(self):
        return f"{self.title} - {self.category}"
    


class Notification(models.Model):
    TYPE_CHOICES = [
        ('trade', 'Trade'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('alert', 'Alert'),
        ('system', 'System'),
        ('news', 'News'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="The user this notification belongs to"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type of notification"
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Short notification message"
    )
    full_details = models.TextField(
        help_text="Full notification details/description"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Notification priority level"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata like amount, stock, status"
    )
    read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the notification was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'read']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.type} - {self.title}"
    


# ADD THIS TO YOUR EXISTING models.py FILE AT THE END

class Stock(models.Model):
    """Model for stock data"""
    
    # Popular stock symbols that work with TradingView
    SYMBOL_CHOICES = [
        # Tech Giants
        ("AAPL", "Apple Inc. (AAPL)"),
        ("MSFT", "Microsoft Corporation (MSFT)"),
        ("GOOGL", "Alphabet Inc. (GOOGL)"),
        ("GOOG", "Alphabet Inc. Class C (GOOG)"),
        ("AMZN", "Amazon.com Inc. (AMZN)"),
        ("META", "Meta Platforms Inc. (META)"),
        ("TSLA", "Tesla Inc. (TSLA)"),
        ("NVDA", "NVIDIA Corporation (NVDA)"),
        ("AMD", "Advanced Micro Devices (AMD)"),
        ("INTC", "Intel Corporation (INTC)"),
        
        # Streaming & Entertainment
        ("NFLX", "Netflix Inc. (NFLX)"),
        ("DIS", "Walt Disney Company (DIS)"),
        ("SPOT", "Spotify Technology (SPOT)"),
        ("ROKU", "Roku Inc. (ROKU)"),
        
        # Financial & Fintech
        ("V", "Visa Inc. (V)"),
        ("MA", "Mastercard Inc. (MA)"),
        ("PYPL", "PayPal Holdings (PYPL)"),
        ("SQ", "Block Inc. (SQ)"),
        ("COIN", "Coinbase Global (COIN)"),
        ("SOFI", "SoFi Technologies (SOFI)"),
        ("AFRM", "Affirm Holdings (AFRM)"),
        
        # Crypto Mining & Blockchain
        ("MARA", "Marathon Digital Holdings (MARA)"),
        ("RIOT", "Riot Platforms Inc. (RIOT)"),
        ("CLSK", "CleanSpark Inc. (CLSK)"),
        ("MSTR", "MicroStrategy Inc. (MSTR)"),
        
        # E-commerce & Travel
        ("SHOP", "Shopify Inc. (SHOP)"),
        ("ABNB", "Airbnb Inc. (ABNB)"),
        ("UBER", "Uber Technologies (UBER)"),
        ("DASH", "DoorDash Inc. (DASH)"),
        
        # Semiconductors
        ("AVGO", "Broadcom Inc. (AVGO)"),
        ("QCOM", "QUALCOMM Inc. (QCOM)"),
        ("MU", "Micron Technology (MU)"),
        ("ASML", "ASML Holding (ASML)"),
        
        # Software & Cloud
        ("CRM", "Salesforce Inc. (CRM)"),
        ("ORCL", "Oracle Corporation (ORCL)"),
        ("ADBE", "Adobe Inc. (ADBE)"),
        ("NOW", "ServiceNow Inc. (NOW)"),
        ("SNOW", "Snowflake Inc. (SNOW)"),
        ("CRWD", "CrowdStrike Holdings (CRWD)"),
        ("ZS", "Zscaler Inc. (ZS)"),
        
        # Energy & Clean Energy
        ("ENPH", "Enphase Energy (ENPH)"),
        ("SEDG", "SolarEdge Technologies (SEDG)"),
        ("RUN", "Sunrun Inc. (RUN)"),
        
        # Other Tech
        ("SNAP", "Snap Inc. (SNAP)"),
        ("PINS", "Pinterest Inc. (PINS)"),
        ("TWLO", "Twilio Inc. (TWLO)"),
        ("BMR", "Beamr Imaging Ltd. (BMR)"),
        ("ZM", "Zoom Video Communications (ZM)"),
        ("DOCU", "DocuSign Inc. (DOCU)"),
    ]
    
    symbol = models.CharField(
        max_length=10,
        choices=SYMBOL_CHOICES,
        unique=True,
        help_text="Select stock symbol from the dropdown"
    )
    name = models.CharField(
        max_length=200,
        help_text="Full company name. Example: Apple Inc."
    )
    logo_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Company logo URL. Example: https://logo.clearbit.com/apple.com"
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Current stock price. Example: 225.91"
    )
    change = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price change amount. Example: 12.15 (can be negative)"
    )
    change_percent = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Price change percentage. Example: 5.68 (can be negative)"
    )
    volume = models.BigIntegerField(
        default=0,
        help_text="Trading volume"
    )
    market_cap = models.BigIntegerField(
        default=0,
        help_text="Market capitalization in dollars"
    )
    sector = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Company sector. Example: Technology, Finance, Healthcare"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this stock actively traded/displayed?"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured stock on homepage?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        ordering = ["-is_featured", "symbol"]
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['is_active', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
    @property
    def is_positive_change(self):
        """Check if price change is positive"""
        return self.change > 0
    
    @property
    def formatted_price(self):
        """Return formatted price string"""
        return f"${self.price:,.2f}"
    
    @property
    def formatted_market_cap(self):
        """Return formatted market cap"""
        if self.market_cap >= 1_000_000_000_000:
            return f"${self.market_cap / 1_000_000_000_000:.2f}T"
        elif self.market_cap >= 1_000_000_000:
            return f"${self.market_cap / 1_000_000_000:.2f}B"
        elif self.market_cap >= 1_000_000:
            return f"${self.market_cap / 1_000_000:.2f}M"
        return f"${self.market_cap:,}"


class UserStockPosition(models.Model):
    """Model to track user's stock positions"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stock_positions',
        help_text="User who owns this position"
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='positions',
        help_text="Stock in this position"
    )
    shares = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Number of shares owned"
    )
    average_buy_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Average purchase price per share"
    )
    total_invested = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total amount invested"
    )
    opened_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When position was opened"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this position still open?"
    )
    closed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When position was closed"
    )
    
    class Meta:
        verbose_name = "User Stock Position"
        verbose_name_plural = "User Stock Positions"
        ordering = ["-opened_at"]
        unique_together = ['user', 'stock', 'is_active']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['stock', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.stock.symbol} ({self.shares} shares)"
    
    @property
    def current_value(self):
        """Calculate current value of position"""
        return float(self.shares) * float(self.stock.price)
    
    @property
    def profit_loss(self):
        """Calculate profit/loss"""
        return self.current_value - float(self.total_invested)
    
    @property
    def profit_loss_percent(self):
        """Calculate profit/loss percentage"""
        if float(self.total_invested) == 0:
            return 0
        return (self.profit_loss / float(self.total_invested)) * 100