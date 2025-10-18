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
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .serializers import (
    TicketSerializer, 
    TransactionSerializer, 
    AdminWalletSerializer,
    AssetSerializer,

)
from .models import (
    Ticket, 
    Trader, 
    Transaction, 
    PaymentMethod, 
    AdminWallet,
    Asset,
)
from django.utils.crypto import get_random_string


User = get_user_model()





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

                    "free_margin": user.free_margin,
                    "user_funds": user.user_funds,
                    "balance": user.balance,
                    "equity": user.equity,
                    "margin_level": user.margin_level,

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


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def transactions_view(request):
    if request.method == "POST":
        transaction_type = request.data.get("transaction_type")
        amount = request.data.get("amount")
        description = request.data.get("description", "")

        if not transaction_type or not amount:
            return Response(
                {"error": "transaction_type and amount are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if transaction_type not in ["deposit", "withdrawal"]:
            return Response(
                {"error": "Invalid transaction type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = float(amount)
        except ValueError:
            return Response(
                {"error": "Amount must be a number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate a unique reference
        reference = get_random_string(12)

        transaction = Transaction.objects.create(
            user=request.user,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            reference=reference,
            status="pending",  # default
        )

        return Response(
            {
                "message": "Transaction created successfully",
                "transaction": {
                    "id": transaction.id,
                    "transaction_type": transaction.transaction_type,
                    "amount": str(transaction.amount),
                    "status": transaction.status,
                    "reference": transaction.reference,
                    "description": transaction.description,
                    "created_at": transaction.created_at,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    # GET request → return all transactions for logged-in user
    transactions = Transaction.objects.filter(user=request.user).values(
        "id", "transaction_type", "amount", "status", "reference", "description", "created_at"
    ).order_by("-id")

    return Response(
        {"transactions": list(transactions)},  # [] if none exist
        status=status.HTTP_200_OK,
    )



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



