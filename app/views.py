from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.decorators import (
    api_view, 
    permission_classes, 
    authentication_classes,
)
from collections import defaultdict
from django.utils import timezone
from .serializers import AdminWalletSerializer
from decimal import Decimal, InvalidOperation
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils.crypto import get_random_string

from django.db.models import Sum, Q

from .serializers import (
    TicketSerializer, 
    TransactionSerializer, 
    AdminWalletSerializer,
    AssetSerializer,
    NewsSerializer,
    NotificationSerializer,
    AdminWalletSerializer, 
    TransactionSerializer,
    TraderListSerializer, 
    TraderDetailSerializer, 
    TraderPortfolioSerializer,
    StockSerializer,
    StockListSerializer,
    UserStockPositionSerializer,
)
from .models import (
    Ticket, 
    Trader, 
    Transaction, 
    PaymentMethod, 
    AdminWallet,
    Asset,
    News,
    Notification,
    AdminWallet, 
    Transaction,
    Trader, 
    TraderPortfolio,
    Stock, 
    UserStockPosition,
)



User = get_user_model()



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """
    Get all dashboard data for the authenticated user
    """
    user = request.user
    
    # Get all transactions
    from .models import Transaction
    transactions = user.transactions.all()
    
    # Calculate total deposits (completed only)
    total_deposits = transactions.filter(
        transaction_type='deposit',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate total withdrawals (completed only)
    total_withdrawals = transactions.filter(
        transaction_type='withdrawal',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get active portfolios
    from .models import Portfolio
    portfolios = user.portfolios.filter(is_active=True).values(
        'id', 'market', 'direction', 'invested', 'profit_loss', 
        'value', 'opened_at', 'is_active'
    )
    
    # Build response data
    data = {
        'email': user.email,
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'account_id': user.account_id or 'N/A',
        'currency': user.currency or 'USD',
        'balance': float(user.balance),
        'profit': float(user.profit),
        'current_loyalty_status': user.current_loyalty_status,
        'next_loyalty_status': user.next_loyalty_status,
        'has_submitted_kyc': user.has_submitted_kyc,
        'is_verified': user.is_verified,
        'date_joined': user.date_joined.isoformat(),
        'total_deposits': float(total_deposits),
        'total_withdrawals': float(total_withdrawals),
        'portfolios': list(portfolios)
    }
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_transactions(request):
    """
    Get all transactions for the authenticated user
    """
    user = request.user
    transaction_type = request.query_params.get('type', None)
    
    from .models import Transaction
    transactions = user.transactions.all()
    
    # Filter by type if provided
    if transaction_type and transaction_type in ['deposit', 'withdrawal']:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    data = transactions.values(
        'id', 'transaction_type', 'amount', 'status', 
        'reference', 'description', 'created_at', 'updated_at'
    )
    
    return Response(list(data), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_portfolios(request):
    """
    Get all portfolios for the authenticated user
    """
    user = request.user
    active_only = request.query_params.get('active_only', 'true').lower() == 'true'
    
    from .models import Portfolio
    portfolios = user.portfolios.all()
    
    if active_only:
        portfolios = portfolios.filter(is_active=True)
    
    data = portfolios.values(
        'id', 'market', 'direction', 'invested', 'profit_loss', 
        'value', 'opened_at', 'is_active'
    )
    
    return Response(list(data), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """
    Get user statistics summary
    """
    user = request.user
    
    from .models import Transaction, Portfolio
    
    # Transaction stats
    completed_deposits = user.transactions.filter(
        transaction_type='deposit',
        status='completed'
    ).count()
    
    completed_withdrawals = user.transactions.filter(
        transaction_type='withdrawal',
        status='completed'
    ).count()
    
    # Portfolio stats
    active_portfolios = user.portfolios.filter(is_active=True).count()
    total_invested = user.portfolios.filter(is_active=True).aggregate(
        total=Sum('invested')
    )['total'] or 0
    
    data = {
        'total_deposits_count': completed_deposits,
        'total_withdrawals_count': completed_withdrawals,
        'active_portfolios_count': active_portfolios,
        'total_invested': float(total_invested),
        'balance': float(user.balance),
        'profit': float(user.profit),
    }
    
    return Response(data, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([AllowAny])
def validate_token(request):
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Token "):
        return Response({"detail": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

    token_key = auth_header.split(" ")[1]

    try:
        token = Token.objects.get(key=token_key)
        user = token.user
        return Response({"valid": True, "user": user.email}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({"valid": False}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    """
    Functional view to register a new user with Django password validation
    """
    email = request.data.get("email")
    password = request.data.get("password")
    first_name = request.data.get("first_name", "")
    last_name = request.data.get("last_name", "")
    country = request.data.get("country", "")
    region = request.data.get("region", "")
    city = request.data.get("city", "")
    phone = request.data.get("phone", "")
    currency = request.data.get("currency", "")

    print("User data: ", request.data)

    if not email or not password:
        return Response(
            {"error": "Email and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "User with this email already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Run Django’s password validators
    try:
        validate_password(password)
    except DjangoValidationError as e:
        return Response(
            {"error": e.messages},  # returns a list of validation messages
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create user if password is valid
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        country=country,
        region=region,
        city=city,
        phone=phone,
        currency=currency
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "token": token.key,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    """
    Functional view to login a user
    """
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    


    user = authenticate(request, email=email, password=password)

    if user is None:
        return Response(
            {"error": "Invalid email or password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "token": token.key,
        },
        status=status.HTTP_200_OK,
    )


# Tickets
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def ticket_list_create(request):
    if request.method == "GET":
        # Only show tickets belonging to logged-in user
        tickets = Ticket.objects.filter(user=request.user).order_by("-pk")
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        serializer = TicketSerializer(data=request.data)
        if serializer.is_valid():
            # auto-assign logged-in user
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_user_profile(request):
    user = request.user

    if request.method == "POST":
        data = request.data

        # update only the fields that are provided
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.dob = data.get("dob", user.dob)
        user.address = data.get("address", user.address)
        user.postal_code = data.get("postal_code", user.postal_code)
        user.country = data.get("country", user.country)
        user.city = data.get("city", user.city)
        user.region = data.get("region", user.region)

        user.save()

        return Response(
            {"message": "Profile updated successfully"},
            status=status.HTTP_200_OK,
        )
    elif request.method == "GET":
        """
        Retrieve the profile of the logged-in user
        """
        user = request.user

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,

                    "balance": user.balance,

                    "account_id": user.account_id,
                    "dob": user.dob,
                    "address": user.address,
                    "postal_code": user.postal_code,
                    "country": user.country,
                    "city": user.city,
                    "region": user.region,
                    "is_verified": user.is_verified,
                    "has_submitted_kyc": user.has_submitted_kyc,
                }
            },
            status=status.HTTP_200_OK,
        )
    else:
        return Response({"error": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# @api_view(["GET", "POST"])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
# def transactions_view(request):
#     if request.method == "POST":
#         transaction_type = request.data.get("transaction_type")
#         amount = request.data.get("amount")
#         description = request.data.get("description", "")

#         if not transaction_type or not amount:
#             return Response(
#                 {"error": "transaction_type and amount are required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         if transaction_type not in ["deposit", "withdrawal"]:
#             return Response(
#                 {"error": "Invalid transaction type"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         try:
#             amount = float(amount)
#         except ValueError:
#             return Response(
#                 {"error": "Amount must be a number"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Generate a unique reference
#         reference = get_random_string(12)

#         transaction = Transaction.objects.create(
#             user=request.user,
#             transaction_type=transaction_type,
#             amount=amount,
#             description=description,
#             reference=reference,
#             status="pending",  # default
#         )

#         return Response(
#             {
#                 "message": "Transaction created successfully",
#                 "transaction": {
#                     "id": transaction.id,
#                     "transaction_type": transaction.transaction_type,
#                     "amount": str(transaction.amount),
#                     "status": transaction.status,
#                     "reference": transaction.reference,
#                     "description": transaction.description,
#                     "created_at": transaction.created_at,
#                 },
#             },
#             status=status.HTTP_201_CREATED,
#         )

#     # GET request → return all transactions for logged-in user
#     transactions = Transaction.objects.filter(user=request.user).values(
#         "id", "transaction_type", "amount", "status", "reference", "description", "created_at"
#     ).order_by("-id")

#     return Response(
#         {"transactions": list(transactions)},  # [] if none exist
#         status=status.HTTP_200_OK,
#     )



# Change Password
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Allows authenticated users to change their password.
    Expects: old_password, new_password, confirm_password
    """
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    # Validate inputs
    if not old_password or not new_password or not confirm_password:
        return Response(
            {"error": "All fields are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.check_password(old_password):
        return Response(
            {"error": "Old password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if new_password != confirm_password:
        return Response(
            {"error": "New password and confirm password do not match"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Run Django’s password validators
    try:
        validate_password(new_password)
    except DjangoValidationError as e:
        return Response(
            {"error": e.messages},  # returns a list of validation messages
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 8:
        return Response(
            {"error": "New password must be at least 8 characters long"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Save new password
    user.set_password(new_password)
    user.save()

    return Response(
        {"success": "Password changed successfully"},
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser]) # Handles file uploads
def upload_kyc(request):
    user = request.user

    # Get text field
    id_type = request.data.get("id_type")

    # Validate required fields
    if not id_type:
        return Response({"error": "ID type is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Handle file uploads
    id_front = request.FILES.get("id_front")
    id_back = request.FILES.get("id_back")

    if not id_front or not id_back:
        return Response({"error": "Both front and back ID images are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Save to user model
    user.id_type = id_type
    user.id_front = id_front
    user.id_back = id_back
    user.has_submitted_kyc = True
    user.save()

    return Response({
        "success": "KYC details uploaded successfully",
        "data": {
            "id_type": user.id_type,
            "id_front": str(user.id_front.url) if user.id_front else None,
            "id_back": str(user.id_back.url) if user.id_back else None,
        }
    }, status=status.HTTP_200_OK)





@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def withdrawal_view(request):
    """
    Handle user withdrawals.
    Expects: asset (balance, equity, user_funds, free_margin), amount
    """
    user = request.user
    asset = request.data.get("asset")
    amount = request.data.get("amount")

    valid_assets = ["balance", "equity", "user_funds", "free_margin"]

    if not asset or not amount:
        return Response(
            {"error": "Asset and amount are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if asset not in valid_assets:
        return Response(
            {"error": "Invalid asset type"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        amount = Decimal(amount)   # ✅ Use Decimal
    except (InvalidOperation, TypeError):
        return Response(
            {"error": "Amount must be a valid number"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if amount <= 0:
        return Response(
            {"error": "Amount must be greater than zero"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    available_balance = getattr(user, asset, Decimal("0.00"))

    if amount > available_balance:
        return Response(
            {"error": f"Insufficient {asset.replace('_', ' ')} balance"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create a unique reference
    reference = get_random_string(12)

    # Create withdrawal transaction (status pending by default)
    transaction = Transaction.objects.create(
        user=user,
        transaction_type="withdrawal",
        amount=amount,
        description=f"Withdrawal from {asset.replace('_', ' ')}",
        reference=reference,
        status="pending",
    )

    # ✅ If you want to immediately deduct from user balance:
    setattr(user, asset, available_balance - amount)
    user.save()

    return Response(
        {
            "message": "Withdrawal request submitted successfully",
            "transaction": {
                "id": transaction.id,
                "asset": asset,
                "amount": str(transaction.amount),  # ensure JSON serializable
                "status": transaction.status,
                "reference": transaction.reference,
                "created_at": transaction.created_at,
            },
        },
        status=status.HTTP_201_CREATED,
    )






@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def transaction_history(request):
    """
    Return all transactions belonging to the logged-in user.
    """
    user = request.user
    transactions = Transaction.objects.filter(user=user).order_by("-created_at")
    serializer = TransactionSerializer(transactions, many=True)

    return Response({"transactions": serializer.data}, status=status.HTTP_200_OK)




@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def payment_methods(request):
    if request.method == "POST":
        try:
            data = request.data
            method_type = data.get("method_type")

            if method_type not in dict(PaymentMethod.WALLET_CHOICES):
                return Response(
                    {"error": "Invalid payment method type"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update if exists, otherwise create
            payment, created = PaymentMethod.objects.update_or_create(
                user=request.user,
                method_type=method_type,
                defaults={
                    "address": data.get("address", ""),
                    "bank_name": data.get("bank_name", ""),
                    "bank_account_number": data.get("bank_account_number", ""),
                    "cashapp_id": data.get("cashapp_id", ""),
                    "paypal_email": data.get("paypal_email", ""),
                }
            )

            return Response({
                "message": "Payment method saved successfully" if created else "Payment method updated successfully",
                "id": payment.id,
                "method_type": payment.method_type,
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == "GET":
        try:
            payments = PaymentMethod.objects.filter(user=request.user)
            data = [
                {
                    "id": p.id,
                    "method_type": p.method_type,
                    "address": p.address,
                    "bank_name": p.bank_name,
                    "bank_account_number": p.bank_account_number,
                    "cashapp_id": p.cashapp_id,
                    "paypal_email": p.paypal_email,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                }
                for p in payments
            ]

            return Response({"payments": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




@api_view(["GET"])
@permission_classes([AllowAny])  # Anyone can view deposit options
def get_deposit_options(request):
    wallets = AdminWallet.objects.filter(is_active=True)
    serializer = AdminWalletSerializer(wallets, many=True)
    return Response( serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_deposit(request):
    """
    Handle deposit creation.
    Expects: currency, unit, amount, receipt (file)
    """
    user = request.user

    currency = request.data.get("currency")
    unit = request.data.get("unit")
    amount = request.data.get("amount")
    receipt = request.FILES.get("receipt")

    if not all([currency, unit, amount, receipt]):
        return Response(
            {"detail": "currency, unit, amount, and receipt are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        unit = Decimal(unit)
        amount = Decimal(amount)
    except Exception:
        return Response(
            {"detail": "unit and amount must be valid numbers."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Generate a unique reference
    reference = get_random_string(12)

    transaction = Transaction.objects.create(
        user=user,
        transaction_type="deposit",
        currency=currency,
        unit=unit,
        amount=amount,
        receipt=receipt,
        reference=reference,
        description=f"Deposit of {unit} {currency} (≈ {amount})",
        status="pending",
        created_at=timezone.now(),
    )

    return Response(
        {
            "id": transaction.id,
            "currency": transaction.currency,
            "unit": str(transaction.unit),
            "amount": str(transaction.amount),
            "status": transaction.status,
            "reference": transaction.reference,
            "receipt_url": str(transaction.receipt.url) if transaction.receipt else None,
        },
        status=status.HTTP_201_CREATED,
    )







from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Trader
from .serializers import TraderSerializer


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def trader_list_create(request):
    """
    GET: List all traders
    POST: Create a new trader
    """
    if request.method == "GET":
        traders = Trader.objects.all().order_by("-created_at")
        serializer = TraderSerializer(traders, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "POST":
        serializer = TraderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
def trader_detail(request, pk):
    """
    GET: Retrieve a single trader by ID
    PUT/PATCH: Update trader
    DELETE: Delete trader
    """
    try:
        trader = Trader.objects.get(pk=pk)
    except Trader.DoesNotExist:
        return Response({"error": "Trader not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = TraderSerializer(trader)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method in ["PUT", "PATCH"]:
        serializer = TraderSerializer(trader, data=request.data, partial=(request.method == "PATCH"))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        trader.delete()
        return Response({"message": "Trader deleted successfully"}, status=status.HTTP_204_NO_CONTENT)




@api_view(["GET"])
def asset_list(request):
    """
    Return a flat list of all assets.
    Example: GET /assets/
    """
    category = request.GET.get("category")
    if category:
        assets = Asset.objects.filter(category=category)
    else:
        assets = Asset.objects.all()
    
    serializer = AssetSerializer(assets, many=True)
    return Response(serializer.data)



@api_view(["GET"])
def grouped_assets(request):
    """
    Return assets grouped by category.
    Example: GET /assets/grouped/
    """
    assets = Asset.objects.all()
    serializer = AssetSerializer(assets, many=True)
    
    grouped = defaultdict(list)
    for asset in serializer.data:
        grouped[asset["category"]].append(asset)
    
    return Response(grouped)


# STARTER



# Add these views to your app/views.py file

@api_view(["GET"])
@permission_classes([AllowAny])
def news_list(request):
    """
    GET: List all news articles with optional filtering
    Query params:
    - category: Filter by category (optional)
    - search: Search in title and summary (optional)
    """
    news_queryset = News.objects.all()

    # Filter by category
    category = request.GET.get("category")
    if category and category != "All":
        news_queryset = news_queryset.filter(category=category)

    # Search functionality
    search = request.GET.get("search")
    if search:
        from django.db.models import Q
        news_queryset = news_queryset.filter(
            Q(title__icontains=search) | 
            Q(summary__icontains=search) |
            Q(content__icontains=search)
        )

    serializer = NewsSerializer(news_queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def news_detail(request, pk):
    """
    GET: Retrieve a single news article by ID
    """
    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response(
            {"error": "News article not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = NewsSerializer(news)
    return Response(serializer.data, status=status.HTTP_200_OK)


# REPLACE your existing trader views in app/views.py with these:

@api_view(["GET"])
@permission_classes([AllowAny])
def trader_list(request):
    """
    GET: List all traders with optional filtering
    Query params:
    - search: Search in name and username
    - badge: Filter by badge (gold, silver, bronze)
    - min_gain: Filter by minimum gain percentage
    - max_risk: Filter by maximum risk level
    """
    traders = Trader.objects.filter(is_active=True)

    # Search functionality
    search = request.GET.get("search")
    if search:
        from django.db.models import Q
        traders = traders.filter(
            Q(name__icontains=search) | 
            Q(username__icontains=search)
        )

    # Filter by badge
    badge = request.GET.get("badge")
    if badge:
        traders = traders.filter(badge=badge)
    
    # Filter by minimum gain
    min_gain = request.GET.get("min_gain")
    if min_gain:
        try:
            traders = traders.filter(gain__gte=float(min_gain))
        except ValueError:
            pass
    
    # Filter by maximum risk
    max_risk = request.GET.get("max_risk")
    if max_risk:
        try:
            traders = traders.filter(risk__lte=int(max_risk))
        except ValueError:
            pass

    serializer = TraderListSerializer(traders, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def trader_detail(request, pk):
    """
    GET: Retrieve a single trader by ID with full details
    """
    try:
        trader = Trader.objects.get(pk=pk, is_active=True)
    except Trader.DoesNotExist:
        return Response(
            {"error": "Trader not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = TraderDetailSerializer(trader)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def trader_portfolios(request, trader_id):
    """
    GET: Get all active portfolio positions for a specific trader
    """
    try:
        trader = Trader.objects.get(pk=trader_id, is_active=True)
    except Trader.DoesNotExist:
        return Response(
            {"error": "Trader not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    portfolios = TraderPortfolio.objects.filter(trader=trader, is_active=True)
    serializer = TraderPortfolioSerializer(portfolios, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """
    GET: List all notifications for the authenticated user
    Query params:
    - type: Filter by notification type (trade, deposit, withdrawal, alert, system, news)
    - read: Filter by read status (true/false)
    - priority: Filter by priority (low, medium, high)
    """
    notifications = Notification.objects.filter(user=request.user)
    
    # Filter by type
    notification_type = request.GET.get("type")
    if notification_type:
        notifications = notifications.filter(type=notification_type)
    
    # Filter by read status
    read_status = request.GET.get("read")
    if read_status:
        is_read = read_status.lower() == "true"
        notifications = notifications.filter(read=is_read)
    
    # Filter by priority
    priority = request.GET.get("priority")
    if priority:
        notifications = notifications.filter(priority=priority)
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_detail(request, pk):
    """
    GET: Retrieve a single notification by ID
    """
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = NotificationSerializer(notification)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """
    PATCH: Mark a notification as read
    """
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    notification.read = True
    notification.save()
    
    serializer = NotificationSerializer(notification)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """
    POST: Mark all notifications as read for the authenticated user
    """
    updated_count = Notification.objects.filter(
        user=request.user, 
        read=False
    ).update(read=True)
    
    return Response(
        {
            "message": f"Marked {updated_count} notifications as read",
            "count": updated_count
        }, 
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_notification_count(request):
    """
    GET: Get count of unread notifications for the authenticated user
    """
    count = Notification.objects.filter(user=request.user, read=False).count()
    
    return Response(
        {"unread_count": count}, 
        status=status.HTTP_200_OK
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk):
    """
    DELETE: Delete a notification
    """
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    notification.delete()
    return Response(
        {"message": "Notification deleted successfully"}, 
        status=status.HTTP_200_OK
    )

# UPDATED SETTINGS VIEWS - Replace the previous versions in your views.py

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_user_settings(request):
    """
    GET: Retrieve complete user settings including profile, security, and payment info
    """
    user = request.user
    
    # Get payment methods
    payment_methods_qs = PaymentMethod.objects.filter(user=user)
    
    # Organize payment methods by type
    btc_method = payment_methods_qs.filter(method_type="BTC").first()
    eth_method = payment_methods_qs.filter(method_type="ETH").first()
    # Check for both USDT types
    usdt_method = payment_methods_qs.filter(method_type__in=["USDT_ERC20", "USDT_TRC20"]).first()
    
    return Response({
        "profile": {
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "email": user.email,
            "phone": user.phone or "",
            "country": user.country or "",
            "region": user.region or "",
            "city": user.city or "",
            "account_id": user.account_id or "",
            "is_verified": user.is_verified,
            "account_status": "Verified" if user.is_verified else "Unverified",
        },
        "payment_methods": {
            "btc": {
                "address": btc_method.address if btc_method else "",
                "has_method": bool(btc_method),
            },
            "eth": {
                "address": eth_method.address if eth_method else "",
                "network": "ERC20",
                "has_method": bool(eth_method),
            },
            "usdt": {
                "address": usdt_method.address if usdt_method else "",
                "network": "TRC20" if usdt_method and usdt_method.method_type == "USDT_TRC20" else "ERC20",
                "method_type": usdt_method.method_type if usdt_method else "USDT_TRC20",
                "has_method": bool(usdt_method),
            },
        }
    }, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_profile(request):
    """
    PATCH: Update user profile information (name, phone, country)
    Expects: first_name, last_name, phone, country (all optional)
    """
    user = request.user
    
    # Get data from request
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")
    phone = request.data.get("phone")
    country = request.data.get("country")
    
    # Update only provided fields
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if phone is not None:
        user.phone = phone
    if country is not None:
        user.country = country
    
    user.save()
    
    return Response({
        "message": "Profile updated successfully",
        "profile": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "country": user.country,
        }
    }, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_payment_method(request):
    """
    PATCH: Update or create a payment method
    Expects: method_type (BTC, ETH, SOL, USDT_ERC20, USDT_TRC20), address
    """
    user = request.user
    
    method_type = request.data.get("method_type")
    address = request.data.get("address")
    
    # Validate inputs
    if not method_type or not address:
        return Response(
            {"error": "method_type and address are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate method_type - must match model choices
    valid_crypto_methods = ["BTC", "ETH", "SOL", "USDT_ERC20", "USDT_TRC20"]
    if method_type not in valid_crypto_methods:
        return Response(
            {"error": f"Invalid method_type. Must be one of: {', '.join(valid_crypto_methods)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate address is not empty
    if not address.strip():
        return Response(
            {"error": "Address cannot be empty"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # For USDT, delete the other USDT type if it exists (can only have one USDT address)
    if method_type in ["USDT_ERC20", "USDT_TRC20"]:
        other_usdt = "USDT_TRC20" if method_type == "USDT_ERC20" else "USDT_ERC20"
        PaymentMethod.objects.filter(user=user, method_type=other_usdt).delete()
    
    # Update or create payment method
    payment_method, created = PaymentMethod.objects.update_or_create(
        user=user,
        method_type=method_type,
        defaults={"address": address}
    )
    
    return Response({
        "message": f"{method_type.replace('_', ' ')} address {'added' if created else 'updated'} successfully",
        "payment_method": {
            "method_type": payment_method.method_type,
            "address": payment_method.address,
            "created": created,
        }
    }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def change_user_password(request):
    """
    POST: Change user password
    Expects: old_password, new_password, confirm_password
    """
    user = request.user
    
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")
    
    # Validate inputs
    if not old_password or not new_password or not confirm_password:
        return Response(
            {"error": "All fields are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check old password
    if not user.check_password(old_password):
        return Response(
            {"error": "Current password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check new passwords match
    if new_password != confirm_password:
        return Response(
            {"error": "New password and confirm password do not match"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate new password
    try:
        validate_password(new_password, user)
    except DjangoValidationError as e:
        return Response(
            {"error": e.messages},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update password
    user.set_password(new_password)
    user.save()
    
    return Response(
        {"message": "Password changed successfully"},
        status=status.HTTP_200_OK
    )




# ADD THESE UPDATED VIEWS TO YOUR app/views.py

@api_view(["GET"])
@permission_classes([AllowAny])
def get_active_deposit_options(request):
    """
    GET: Retrieve all active admin wallets for deposit options
    Returns: List of active wallets with currency, amount (rate), wallet_address, and qr_code
    """
    try:
        wallets = AdminWallet.objects.filter(is_active=True).order_by('currency')
        serializer = AdminWalletSerializer(wallets, many=True)
        return Response({
            "success": True,
            "wallets": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_deposit_transaction(request):
    """
    POST: Create a new deposit transaction
    Expects:
    - currency: The cryptocurrency type (e.g., "BTC", "ETH")
    - dollar_amount: The dollar amount user wants to deposit
    - currency_unit: The calculated amount of cryptocurrency units
    - receipt: Image file of payment receipt
    
    Returns: Created transaction details
    """
    user = request.user

    # Extract data from request
    currency = request.data.get("currency")
    dollar_amount = request.data.get("dollar_amount")
    currency_unit = request.data.get("currency_unit")
    receipt = request.FILES.get("receipt")

    # Validation
    if not all([currency, dollar_amount, currency_unit, receipt]):
        return Response(
            {
                "success": False,
                "error": "currency, dollar_amount, currency_unit, and receipt are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate wallet exists and is active
    try:
        wallet = AdminWallet.objects.get(currency=currency, is_active=True)
    except AdminWallet.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": f"No active wallet found for {currency}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Convert to Decimal for precision
    try:
        dollar_amount = Decimal(str(dollar_amount))
        currency_unit = Decimal(str(currency_unit))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "success": False,
                "error": "Invalid amount values provided"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate amounts are positive
    if dollar_amount <= 0 or currency_unit <= 0:
        return Response(
            {
                "success": False,
                "error": "Amounts must be greater than zero"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Generate unique reference
    reference = f"DEP-{get_random_string(12).upper()}"

    # Create transaction
    try:
        transaction = Transaction.objects.create(
            user=user,
            transaction_type="deposit",
            currency=currency,
            unit=currency_unit,
            amount=dollar_amount,
            receipt=receipt,
            reference=reference,
            description=f"Deposit of {currency_unit} {currency} (≈ ${dollar_amount})",
            status="pending",
            created_at=timezone.now(),
        )

        return Response(
            {
                "success": True,
                "message": "Deposit request submitted successfully",
                "transaction": {
                    "id": transaction.id,
                    "reference": transaction.reference,
                    "currency": transaction.currency,
                    "unit": str(transaction.unit),
                    "amount": str(transaction.amount),
                    "status": transaction.status,
                    "receipt_url": transaction.receipt.url if transaction.receipt else None,
                    "created_at": transaction.created_at.isoformat(),
                }
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response(
            {
                "success": False,
                "error": f"Failed to create transaction: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_deposit_history(request):
    """
    GET: Retrieve deposit transaction history for authenticated user
    Query params:
    - limit: Number of transactions to return (default: 10)
    """
    user = request.user
    limit = request.GET.get("limit", 10)
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    try:
        transactions = Transaction.objects.filter(
            user=user,
            transaction_type="deposit"
        ).order_by("-created_at")[:limit]
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            "success": True,
            "transactions": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_user_profile_for_withdrawal(request):
    """
    GET: Retrieve authenticated user's profile with balance and other info
    Returns: User profile data including balance
    """
    user = request.user
    
    return Response({
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
            "account_id": user.account_id,
            "balance": str(user.balance),
            "formatted_balance": f"${user.balance:,.2f}",
            "country": user.country or "",
            "phone": user.phone or "",
            "is_verified": user.is_verified,
            "has_submitted_kyc": user.has_submitted_kyc,
        }
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_withdrawal_methods(request):
    """
    GET: Retrieve all available withdrawal methods for the user
    Returns: List of payment methods the user has set up with their addresses
    """
    user = request.user
    
    try:
        payment_methods = PaymentMethod.objects.filter(user=user)
        
        # Format the response
        methods = []
        for pm in payment_methods:
            # Only include crypto methods with addresses
            if pm.method_type in ["BTC", "ETH", "SOL", "USDT_ERC20", "USDT_TRC20", "BNB", "TRX", "XRP", "LTC", "BUSD"] and pm.address:
                # Simplify the display name
                display_name = pm.method_type.replace("_ERC20", "").replace("_TRC20", "")
                
                method_data = {
                    "id": pm.id,
                    "method_type": pm.method_type,
                    "display_name": display_name,
                    "address": pm.address,
                }
                methods.append(method_data)
        
        return Response({
            "success": True,
            "methods": methods,
            "count": len(methods)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def create_withdrawal_request(request):
    """
    POST: Create a new withdrawal request
    Expects:
    - method_type: The withdrawal method (BTC, ETH, USDT_ERC20, etc.)
    - amount: The amount to withdraw (in USD)
    - withdrawal_address: The address to send funds to
    
    Returns: Created transaction details
    """
    user = request.user
    
    # Extract data from request
    method_type = request.data.get("method_type")
    amount = request.data.get("amount")
    withdrawal_address = request.data.get("withdrawal_address")
    
    # Validation
    if not all([method_type, amount, withdrawal_address]):
        return Response(
            {
                "success": False,
                "error": "method_type, amount, and withdrawal_address are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Validate payment method exists for user
    try:
        payment_method = PaymentMethod.objects.get(
            user=user,
            method_type=method_type
        )
    except PaymentMethod.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": f"No payment method found for {method_type}. Please add this method in settings first."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Convert to Decimal for precision
    try:
        amount = Decimal(str(amount))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "success": False,
                "error": "Invalid amount value provided"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Validate amount is positive
    if amount <= 0:
        return Response(
            {
                "success": False,
                "error": "Amount must be greater than zero"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Check if user has sufficient balance
    if amount > user.balance:
        return Response(
            {
                "success": False,
                "error": f"Insufficient balance. Your balance is ${user.balance:,.2f}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Verify withdrawal address matches the one on file (security check)
    if payment_method.address != withdrawal_address:
        return Response(
            {
                "success": False,
                "error": "Withdrawal address does not match your saved address. Please update your payment method in settings first."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Check if user is verified (optional security check)
    if not user.is_verified and amount > 1000:  # Example: require verification for amounts over $1000
        return Response(
            {
                "success": False,
                "error": "Account verification required for withdrawals over $1,000. Please complete KYC verification."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Generate unique reference
    reference = f"WTH-{get_random_string(12).upper()}"
    
    # Create transaction
    try:
        transaction = Transaction.objects.create(
            user=user,
            transaction_type="withdrawal",
            currency=method_type.replace("_ERC20", "").replace("_TRC20", ""),  # Simplify currency name
            unit=amount,  # For withdrawals, unit can be same as amount
            amount=amount,
            reference=reference,
            description=f"Withdrawal of ${amount} via {method_type} to {withdrawal_address[:20]}...",
            status="pending",
            created_at=timezone.now(),
        )
        
        # Deduct from user balance immediately (pending admin approval)
        # NOTE: In production, you might want to hold this in a separate field until admin approval
        user.balance -= amount
        user.save()
        
        return Response(
            {
                "success": True,
                "message": "Withdrawal request submitted successfully and is pending approval",
                "transaction": {
                    "id": transaction.id,
                    "reference": transaction.reference,
                    "method": method_type,
                    "currency": transaction.currency,
                    "amount": str(transaction.amount),
                    "status": transaction.status,
                    "withdrawal_address": withdrawal_address,
                    "created_at": transaction.created_at.isoformat(),
                    "new_balance": str(user.balance),
                    "formatted_new_balance": f"${user.balance:,.2f}",
                }
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response(
            {
                "success": False,
                "error": f"Failed to create withdrawal: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_withdrawal_history(request):
    """
    GET: Retrieve withdrawal transaction history for authenticated user
    Query params:
    - limit: Number of transactions to return (default: 10)
    """
    user = request.user
    limit = request.GET.get("limit", 10)
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    try:
        transactions = Transaction.objects.filter(
            user=user,
            transaction_type="withdrawal"
        ).order_by("-created_at")[:limit]
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            "success": True,
            "transactions": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# ADD THIS NEW VIEW TO YOUR views.py FILE (after get_withdrawal_history function)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_transaction_history(request):
    """
    GET: Retrieve all transaction history (deposits + withdrawals) for authenticated user
    Query params:
    - limit: Number of transactions to return (default: 10)
    - type: Filter by transaction type (deposit/withdrawal) - optional
    """
    user = request.user
    limit = request.GET.get("limit", 10)
    transaction_type = request.GET.get("type", None)
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    try:
        # Get all transactions for user
        transactions = Transaction.objects.filter(user=user)
        
        # Filter by type if provided
        if transaction_type and transaction_type in ['deposit', 'withdrawal']:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Order by most recent and limit
        transactions = transactions.order_by("-created_at")[:limit]
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            "success": True,
            "transactions": serializer.data,
            "count": len(serializer.data)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Stocks
@api_view(["GET"])
@permission_classes([AllowAny])
def stock_list(request):
    """
    GET: List all active stocks with optional filtering
    Query params:
    - search: Search in symbol and name
    - sector: Filter by sector
    - featured: Show only featured stocks (true/false)
    - limit: Limit number of results
    """
    stocks = Stock.objects.filter(is_active=True)
    
    # Search functionality
    search = request.GET.get("search")
    if search:
        from django.db.models import Q
        stocks = stocks.filter(
            Q(symbol__icontains=search) | 
            Q(name__icontains=search)
        )
    
    # Filter by sector
    sector = request.GET.get("sector")
    if sector:
        stocks = stocks.filter(sector=sector)
    
    # Filter by featured
    featured = request.GET.get("featured")
    if featured and featured.lower() == "true":
        stocks = stocks.filter(is_featured=True)
    
    # Limit results
    limit = request.GET.get("limit")
    if limit:
        try:
            stocks = stocks[:int(limit)]
        except ValueError:
            pass
    
    serializer = StockListSerializer(stocks, many=True)
    
    return Response({
        "success": True,
        "count": len(serializer.data),
        "stocks": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def stock_detail(request, symbol):
    """
    GET: Retrieve a single stock by symbol
    """
    try:
        stock = Stock.objects.get(symbol=symbol.upper(), is_active=True)
    except Stock.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Stock not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = StockSerializer(stock)
    
    # If user is authenticated, include their position in this stock
    user_position = None
    if request.user.is_authenticated:
        try:
            position = UserStockPosition.objects.get(
                user=request.user,
                stock=stock,
                is_active=True
            )
            user_position = UserStockPositionSerializer(position).data
        except UserStockPosition.DoesNotExist:
            pass
    
    return Response({
        "success": True,
        "stock": serializer.data,
        "user_position": user_position
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def stock_sectors(request):
    """
    GET: Get list of unique sectors
    """
    sectors = Stock.objects.filter(
        is_active=True,
        sector__isnull=False
    ).values_list('sector', flat=True).distinct().order_by('sector')
    
    return Response({
        "success": True,
        "sectors": list(sectors)
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def user_stock_positions(request):
    """
    GET: Get all stock positions for authenticated user
    Query params:
    - active_only: Show only active positions (default: true)
    """
    active_only = request.GET.get("active_only", "true").lower() == "true"
    
    positions = UserStockPosition.objects.filter(user=request.user)
    
    if active_only:
        positions = positions.filter(is_active=True)
    
    serializer = UserStockPositionSerializer(positions, many=True)
    
    # Calculate totals
    total_invested = sum(
        float(p.total_invested) for p in positions if p.is_active
    )
    total_current_value = sum(
        p.current_value for p in positions if p.is_active
    )
    total_profit_loss = total_current_value - total_invested
    total_profit_loss_percent = (
        (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
    )
    
    return Response({
        "success": True,
        "positions": serializer.data,
        "summary": {
            "total_invested": f"{total_invested:.2f}",
            "total_current_value": f"{total_current_value:.2f}",
            "total_profit_loss": f"{total_profit_loss:.2f}",
            "total_profit_loss_percent": f"{total_profit_loss_percent:.2f}"
        }
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def buy_stock(request):
    """
    POST: Buy stock shares
    Expects: symbol, shares, order_type
    """
    user = request.user
    symbol = request.data.get("symbol")
    shares_str = request.data.get("shares")
    order_type = request.data.get("order_type", "Market Buy")
    
    # Validation
    if not symbol or not shares_str:
        return Response(
            {
                "success": False,
                "error": "Symbol and shares are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        shares = Decimal(str(shares_str))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "success": False,
                "error": "Invalid shares value"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if shares <= 0:
        return Response(
            {
                "success": False,
                "error": "Shares must be greater than zero"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get stock
    try:
        stock = Stock.objects.get(symbol=symbol.upper(), is_active=True)
    except Stock.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Stock not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculate cost
    total_cost = shares * stock.price
    
    # Check balance
    if user.balance < total_cost:
        return Response(
            {
                "success": False,
                "error": f"Insufficient balance. Required: ${total_cost:.2f}, Available: ${user.balance:.2f}"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create position
    position, created = UserStockPosition.objects.get_or_create(
        user=user,
        stock=stock,
        is_active=True,
        defaults={
            'shares': shares,
            'average_buy_price': stock.price,
            'total_invested': total_cost
        }
    )
    
    if not created:
        # Update existing position
        old_total = position.total_invested
        old_shares = position.shares
        new_total = old_total + total_cost
        new_shares = old_shares + shares
        position.average_buy_price = new_total / new_shares
        position.shares = new_shares
        position.total_invested = new_total
        position.save()
    
    # Deduct from balance
    user.balance -= total_cost
    user.save()
    
    # Create transaction record
    reference = f"BUY-{get_random_string(12).upper()}"
    Transaction.objects.create(
        user=user,
        transaction_type="withdrawal",  # Buying is a withdrawal from balance
        amount=total_cost,
        reference=reference,
        description=f"Bought {shares} shares of {stock.symbol} @ ${stock.price}",
        status="completed"
    )
    
    return Response({
        "success": True,
        "message": f"Successfully bought {shares} shares of {stock.symbol}",
        "position": UserStockPositionSerializer(position).data,
        "new_balance": str(user.balance)
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def sell_stock(request):
    """
    POST: Sell stock shares
    Expects: symbol, shares
    """
    user = request.user
    symbol = request.data.get("symbol")
    shares_str = request.data.get("shares")
    
    # Validation
    if not symbol or not shares_str:
        return Response(
            {
                "success": False,
                "error": "Symbol and shares are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        shares = Decimal(str(shares_str))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "success": False,
                "error": "Invalid shares value"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if shares <= 0:
        return Response(
            {
                "success": False,
                "error": "Shares must be greater than zero"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get stock
    try:
        stock = Stock.objects.get(symbol=symbol.upper(), is_active=True)
    except Stock.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Stock not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get user's position
    try:
        position = UserStockPosition.objects.get(
            user=user,
            stock=stock,
            is_active=True
        )
    except UserStockPosition.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "You don't own any shares of this stock"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user has enough shares
    if position.shares < shares:
        return Response(
            {
                "success": False,
                "error": f"Insufficient shares. You own {position.shares} shares"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate sale value
    sale_value = shares * stock.price
    
    # Update position
    if position.shares == shares:
        # Selling all shares - close position
        position.is_active = False
        position.closed_at = timezone.now()
        position.save()
    else:
        # Partial sale
        remaining_shares = position.shares - shares
        proportion = remaining_shares / position.shares
        position.shares = remaining_shares
        position.total_invested = position.total_invested * proportion
        position.save()
    
    # Add to balance
    user.balance += sale_value
    user.save()
    
    # Calculate profit/loss
    cost_basis = (float(position.average_buy_price) * float(shares))
    profit_loss = float(sale_value) - cost_basis
    
    # Create transaction record
    reference = f"SELL-{get_random_string(12).upper()}"
    Transaction.objects.create(
        user=user,
        transaction_type="deposit",  # Selling is a deposit to balance
        amount=sale_value,
        reference=reference,
        description=f"Sold {shares} shares of {stock.symbol} @ ${stock.price} (P/L: ${profit_loss:.2f})",
        status="completed"
    )
    
    return Response({
        "success": True,
        "message": f"Successfully sold {shares} shares of {stock.symbol}",
        "sale_value": str(sale_value),
        "profit_loss": f"{profit_loss:.2f}",
        "new_balance": str(user.balance)
    }, status=status.HTTP_200_OK)






















































































































