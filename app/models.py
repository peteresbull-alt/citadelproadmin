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

    # KYC Fields
    id_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ("passport", "Passport"),
            ("driver_license", "Driver’s License"),
            ("national_id", "National ID"),
            ("voter_card", "Voter’s Card"),
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
    free_margin = models.DecimalField(verbose_name="Free Margin", max_digits=20, decimal_places=2, default=0.00, help_text="This is a monetary value.")
    user_funds = models.DecimalField(verbose_name="User Funds", max_digits=20, decimal_places=2, default=0.00, help_text="This is a monetary value.")
    balance = models.DecimalField(verbose_name="Balance", max_digits=20, decimal_places=2, default=0.00, help_text="This is a monetary value.")
    equity = models.DecimalField(verbose_name="Equity", max_digits=20, decimal_places=2, default=0.00, help_text="This is a monetary value.")
    margin_level = models.DecimalField(
        help_text="The Margin Level is a Percentage value. It should range from 0% to 20%. Do not add the '%' symbol", 
        verbose_name="Margin Level",  max_digits=20, decimal_places=2,
        default=0.00
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




class Trader(models.Model):
    name = models.CharField(max_length=150)
    country = models.CharField(max_length=100)
    avatar =  CloudinaryField(
        "Trader Image",
        folder="copy_trader_images",
        blank=True,
        null=True,
        help_text="Upload copy the trader image"
    )
    gain = models.DecimalField(max_digits=10, decimal_places=2, help_text="This should be the gain he made from the trade e.g. 194.32")  # e.g. 194.32
    risk = models.PositiveSmallIntegerField(help_text="Risk score should be from 1 to 10.")  # assuming 1–10 risk score
    capital = models.CharField(max_length=50, help_text="Enter the amount in dollars e.g. 2000, 4000")  # stored as string because of "$"
    copiers = models.PositiveIntegerField(help_text="This should range from 1 to 300 or even more.")
    avg_trade_time = models.CharField(max_length=50, help_text="This should be time basis like '1 week', '3 weeks', '2 months'")  # e.g. "1 week"
    trades = models.PositiveIntegerField(help_text="This should be an integer showing the number of trade this trader has taken.")

    created_at = models.DateTimeField(auto_now_add=True)  # optional
    updated_at = models.DateTimeField(auto_now=True)      # optional

    def __str__(self):
        return f"{self.name} ({self.country})"
    
    class Meta:
        verbose_name_plural = "Copy Traders"
        verbose_name = "Trader"

class Transaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
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

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} ({self.status})"


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
        "QRCode",
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




