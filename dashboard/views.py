# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal

from app.models import (
    CustomUser, Transaction, Stock, AdminWallet,
    Portfolio, Notification, UserStockPosition, Trader, UserCopyTraderHistory
)
from .forms import (
    AddTradeForm, AddEarningsForm, ApproveDepositForm,
    ApproveWithdrawalForm, ApproveKYCForm, AddCopyTradeForm,
    AddTraderForm, EditTraderForm, EditDepositForm,
)
from .decorators import admin_required


def admin_login(request):
    """Admin login view"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'Welcome back, {user.email}!')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
    
    return render(request, 'dashboard/login.html')


@admin_required
def admin_logout(request):
    """Admin logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('dashboard:login')


@admin_required
def dashboard(request):
    """Main dashboard view"""
    # Get statistics
    total_users = CustomUser.objects.filter(is_active=True).count()
    verified_users = CustomUser.objects.filter(is_verified=True).count()
    pending_kyc = CustomUser.objects.filter(
        has_submitted_kyc=True,
        is_verified=False
    ).count()
    
    # Transaction statistics
    pending_deposits = Transaction.objects.filter(
        transaction_type='deposit',
        status='pending'
    ).count()
    
    pending_withdrawals = Transaction.objects.filter(
        transaction_type='withdrawal',
        status='pending'
    ).count()
    
    # Financial statistics
    total_deposits = Transaction.objects.filter(
        transaction_type='deposit',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_withdrawals = Transaction.objects.filter(
        transaction_type='withdrawal',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Recent activity
    recent_transactions = Transaction.objects.select_related('user').order_by('-created_at')[:10]
    recent_users = CustomUser.objects.filter(is_active=True).order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'verified_users': verified_users,
        'pending_kyc': pending_kyc,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'recent_transactions': recent_transactions,
        'recent_users': recent_users,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@admin_required
def users_list(request):
    """List all users with search and filter"""
    search_query = request.GET.get('search', '')
    filter_status = request.GET.get('status', '')
    
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Search
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(account_id__icontains=search_query)
        )
    
    # Filter
    if filter_status == 'verified':
        users = users.filter(is_verified=True)
    elif filter_status == 'unverified':
        users = users.filter(is_verified=False)
    elif filter_status == 'kyc_pending':
        users = users.filter(has_submitted_kyc=True, is_verified=False)
    
    # Pagination - 20 users per page
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    
    context = {
        'users': users_page,
        'page_obj': users_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'search_query': search_query,
        'filter_status': filter_status,
    }
    
    return render(request, 'dashboard/users.html', context)


@admin_required
def user_detail(request, user_id):
    """View and edit user details"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            user.is_verified = True
            user.save()
            messages.success(request, f'User {user.email} has been verified')
        
        elif action == 'unverify':
            user.is_verified = False
            user.save()
            messages.success(request, f'User {user.email} has been unverified')
        
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'User {user.email} has been activated')
        
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f'User {user.email} has been deactivated')
        
        elif action == 'update_balance':
            new_balance = request.POST.get('balance')
            if new_balance:
                user.balance = Decimal(new_balance)
                user.save()
                messages.success(request, f'Balance updated to ${user.balance}')
        
        return redirect('dashboard:user_detail', user_id=user.id)
    
    # Get user's transactions
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:20]
    
    # Get user's portfolios
    portfolios = Portfolio.objects.filter(user=user, is_active=True)
    
    context = {
        'view_user': user,
        'transactions': transactions,
        'portfolios': portfolios,
    }
    
    return render(request, 'dashboard/user_detail.html', context)


@admin_required
def kyc_requests(request):
    """List all KYC requests"""
    status_filter = request.GET.get('status', 'pending')
    
    if status_filter == 'pending':
        users = CustomUser.objects.filter(
            has_submitted_kyc=True,
            is_verified=False
        ).order_by('-date_joined')
    elif status_filter == 'approved':
        users = CustomUser.objects.filter(
            has_submitted_kyc=True,
            is_verified=True
        ).order_by('-date_joined')
    else:  # all
        users = CustomUser.objects.filter(
            has_submitted_kyc=True
        ).order_by('-date_joined')
    
    # Pagination - 15 KYC requests per page
    paginator = Paginator(users, 15)
    page = request.GET.get('page')
    
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    
    context = {
        'kyc_requests': users_page,
        'page_obj': users_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/kyc_requests.html', context)


@admin_required
def kyc_detail(request, user_id):
    """View KYC details and approve/reject"""
    user = get_object_or_404(CustomUser, id=user_id, has_submitted_kyc=True)
    
    if request.method == 'POST':
        form = ApproveKYCForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            admin_notes = form.cleaned_data['admin_notes']
            
            if action == 'approve':
                user.is_verified = True
                user.save()
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    type='system',
                    title='KYC Approved',
                    message='Your KYC verification has been approved!',
                    full_details='Your account is now fully verified. You can access all features.'
                )
                
                messages.success(request, f'KYC approved for {user.email}')
            else:  # reject
                user.is_verified = False
                user.has_submitted_kyc = False
                user.save()
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    type='alert',
                    title='KYC Rejected',
                    message='Your KYC verification was not approved',
                    full_details=admin_notes or 'Please review your documents and submit again.'
                )
                
                messages.warning(request, f'KYC rejected for {user.email}')
            
            return redirect('dashboard:kyc_requests')
    else:
        form = ApproveKYCForm()
    
    context = {
        'view_user': user,
        'form': form,
    }
    
    return render(request, 'dashboard/kyc_detail.html', context)


@admin_required
def deposits(request):
    """List all deposit requests"""
    status_filter = request.GET.get('status', 'pending')
    
    deposits = Transaction.objects.filter(
        transaction_type='deposit'
    ).select_related('user').order_by('-created_at')
    
    if status_filter and status_filter != 'all':
        deposits = deposits.filter(status=status_filter)
    
    # Pagination - 20 deposits per page
    paginator = Paginator(deposits, 20)
    page = request.GET.get('page')
    
    try:
        deposits_page = paginator.page(page)
    except PageNotAnInteger:
        deposits_page = paginator.page(1)
    except EmptyPage:
        deposits_page = paginator.page(paginator.num_pages)
    
    context = {
        'deposits': deposits_page,
        'page_obj': deposits_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/deposits.html', context)


@admin_required
def deposit_detail(request, transaction_id):
    """View deposit detail and approve/reject"""
    deposit = get_object_or_404(
        Transaction,
        id=transaction_id,
        transaction_type='deposit'
    )
    
    if request.method == 'POST':
        form = ApproveDepositForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            admin_notes = form.cleaned_data['admin_notes']
            
            deposit.status = status
            deposit.save()
            
            if status == 'completed':
                # Credit user balance
                deposit.user.balance += deposit.amount
                deposit.user.save()
                
                # Create notification
                Notification.objects.create(
                    user=deposit.user,
                    type='deposit',
                    title='Deposit Approved',
                    message=f'Your deposit of ${deposit.amount} has been approved',
                    full_details=f'Amount: ${deposit.amount}\nReference: {deposit.reference}'
                )
                
                messages.success(request, f'Deposit approved and ${deposit.amount} credited to {deposit.user.email}')
            else:  # failed
                # Create notification
                Notification.objects.create(
                    user=deposit.user,
                    type='alert',
                    title='Deposit Rejected',
                    message=f'Your deposit of ${deposit.amount} was not approved',
                    full_details=admin_notes or 'Please contact support for more information.'
                )
                
                messages.warning(request, f'Deposit rejected for {deposit.user.email}')
            
            return redirect('dashboard:deposits')
    else:
        form = ApproveDepositForm()
    
    context = {
        'deposit': deposit,
        'form': form,
    }
    
    return render(request, 'dashboard/deposit_detail.html', context)



@admin_required
def edit_deposit(request, transaction_id):
    """Edit deposit details"""
    deposit = get_object_or_404(
        Transaction,
        id=transaction_id,
        transaction_type='deposit'
    )
    
    if request.method == 'POST':
        form = EditDepositForm(request.POST, request.FILES)
        if form.is_valid():
            old_amount = deposit.amount
            old_status = deposit.status
            
            # Update deposit fields
            deposit.amount = form.cleaned_data['amount']
            deposit.currency = form.cleaned_data['currency']
            deposit.unit = form.cleaned_data['unit']
            deposit.status = form.cleaned_data['status']
            deposit.description = form.cleaned_data['description']
            deposit.reference = form.cleaned_data['reference']
            
            # Update receipt if new one uploaded
            if form.cleaned_data.get('receipt'):
                deposit.receipt = form.cleaned_data['receipt']
            
            deposit.save()
            
            # Handle balance adjustments if status changed
            if old_status != deposit.status:
                if old_status == 'completed' and deposit.status != 'completed':
                    # Was completed, now not completed - deduct from balance
                    deposit.user.balance -= old_amount
                    deposit.user.save()
                    messages.warning(request, f'${old_amount} deducted from {deposit.user.email} balance due to status change')
                
                elif old_status != 'completed' and deposit.status == 'completed':
                    # Wasn't completed, now completed - add to balance
                    deposit.user.balance += deposit.amount
                    deposit.user.save()
                    messages.success(request, f'${deposit.amount} credited to {deposit.user.email} balance')
            
            # Handle amount changes for completed deposits
            elif deposit.status == 'completed' and old_amount != deposit.amount:
                # Adjust balance by difference
                difference = deposit.amount - old_amount
                deposit.user.balance += difference
                deposit.user.save()
                
                if difference > 0:
                    messages.success(request, f'Additional ${difference} credited to {deposit.user.email} balance')
                else:
                    messages.warning(request, f'${abs(difference)} deducted from {deposit.user.email} balance')
            
            # Create notification
            Notification.objects.create(
                user=deposit.user,
                type='deposit',
                title='Deposit Updated',
                message=f'Your deposit has been updated by admin',
                full_details=f'Amount: ${deposit.amount}\nCurrency: {deposit.currency}\nStatus: {deposit.status}\nReference: {deposit.reference}'
            )
            
            messages.success(request, 'Deposit updated successfully!')
            return redirect('dashboard:deposit_detail', transaction_id=deposit.id)
    else:
        # Pre-fill form with existing data
        initial_data = {
            'amount': deposit.amount,
            'currency': deposit.currency,
            'unit': deposit.unit,
            'status': deposit.status,
            'description': deposit.description or '',
            'reference': deposit.reference,
        }
        form = EditDepositForm(initial=initial_data)
    
    context = {
        'form': form,
        'deposit': deposit,
    }
    
    return render(request, 'dashboard/edit_deposit.html', context)



@admin_required
def withdrawals(request):
    """List all withdrawal requests"""
    status_filter = request.GET.get('status', 'pending')
    
    withdrawals = Transaction.objects.filter(
        transaction_type='withdrawal'
    ).select_related('user').order_by('-created_at')
    
    if status_filter and status_filter != 'all':
        withdrawals = withdrawals.filter(status=status_filter)
    
    # Pagination - 20 withdrawals per page
    paginator = Paginator(withdrawals, 20)
    page = request.GET.get('page')
    
    try:
        withdrawals_page = paginator.page(page)
    except PageNotAnInteger:
        withdrawals_page = paginator.page(1)
    except EmptyPage:
        withdrawals_page = paginator.page(paginator.num_pages)
    
    context = {
        'withdrawals': withdrawals_page,
        'page_obj': withdrawals_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/withdrawals.html', context)


@admin_required
def withdrawal_detail(request, transaction_id):
    """View withdrawal detail and approve/reject"""
    withdrawal = get_object_or_404(
        Transaction,
        id=transaction_id,
        transaction_type='withdrawal'
    )
    
    if request.method == 'POST':
        form = ApproveWithdrawalForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            admin_notes = form.cleaned_data['admin_notes']
            
            withdrawal.status = status
            withdrawal.save()
            
            if status == 'completed':
                # Create notification
                Notification.objects.create(
                    user=withdrawal.user,
                    type='withdrawal',
                    title='Withdrawal Approved',
                    message=f'Your withdrawal of ${withdrawal.amount} has been processed',
                    full_details=f'Amount: ${withdrawal.amount}\nReference: {withdrawal.reference}'
                )
                
                messages.success(request, f'Withdrawal approved for {withdrawal.user.email}')
            else:  # failed
                # Refund the amount back to user balance
                withdrawal.user.balance += withdrawal.amount
                withdrawal.user.save()
                
                # Create notification
                Notification.objects.create(
                    user=withdrawal.user,
                    type='alert',
                    title='Withdrawal Rejected',
                    message=f'Your withdrawal of ${withdrawal.amount} was not processed',
                    full_details=admin_notes or 'Amount has been refunded to your balance.'
                )
                
                messages.warning(request, f'Withdrawal rejected and amount refunded to {withdrawal.user.email}')
            
            return redirect('dashboard:withdrawals')
    else:
        form = ApproveWithdrawalForm()
    
    context = {
        'withdrawal': withdrawal,
        'form': form,
    }
    
    return render(request, 'dashboard/withdrawal_detail.html', context)


@admin_required
def transactions(request):
    """List all transactions with filters"""
    transaction_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    transactions = Transaction.objects.select_related('user').order_by('-created_at')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if status:
        transactions = transactions.filter(status=status)
    
    if search:
        transactions = transactions.filter(
            Q(user__email__icontains=search) |
            Q(reference__icontains=search)
        )
    
    # Pagination - 25 transactions per page
    paginator = Paginator(transactions, 25)
    page = request.GET.get('page')
    
    try:
        transactions_page = paginator.page(page)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)
    
    context = {
        'transactions': transactions_page,
        'page_obj': transactions_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'transaction_type': transaction_type,
        'status': status,
        'search': search,
    }
    
    return render(request, 'dashboard/transactions.html', context)


@admin_required
def add_trade(request):
    """Add trade for a user"""
    if request.method == 'POST':
        form = AddTradeForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['user_email']
            entry = form.cleaned_data['entry']
            asset_type = form.cleaned_data['asset_type']
            asset = form.cleaned_data['asset']
            direction = form.cleaned_data['direction']
            profit = form.cleaned_data['profit'] or Decimal('0.00')
            duration = form.cleaned_data['duration']
            rate = form.cleaned_data['rate'] or Decimal('0.00')
            
            # Create portfolio entry
            Portfolio.objects.create(
                user=user_email,
                market=f"{asset} ({asset_type})",
                direction=direction.upper(),
                invested=entry,
                profit_loss=profit,
                value=entry + profit,
                is_active=True
            )
            
            messages.success(request, f'Trade added successfully for {user_email.email}')
            return redirect('dashboard:add_trade')
    else:
        form = AddTradeForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboard/add_trade.html', context)


@admin_required
def add_earnings(request):
    """Add earnings to user balance"""
    if request.method == 'POST':
        form = AddEarningsForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['user_email']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description'] or 'Admin added earnings'
            
            # Add to user balance
            user_email.balance += amount
            user_email.save()
            
            # Create transaction record
            from django.utils.crypto import get_random_string
            reference = f"EARN-{get_random_string(12).upper()}"
            
            Transaction.objects.create(
                user=user_email,
                transaction_type='deposit',
                amount=amount,
                status='completed',
                reference=reference,
                description=description
            )
            
            # Create notification
            Notification.objects.create(
                user=user_email,
                type='system',
                title='Earnings Added',
                message=f'${amount} has been added to your account',
                full_details=description
            )
            
            messages.success(request, f'${amount} added to {user_email.email}')
            return redirect('dashboard:add_earnings')
    else:
        form = AddEarningsForm()
    
    # Get recent earnings
    recent_earnings = Transaction.objects.filter(
        transaction_type='deposit',
        status='completed',
        description__icontains='admin'
    ).select_related('user').order_by('-created_at')[:10]
    
    context = {
        'form': form,
        'recent_earnings': recent_earnings,
    }
    
    return render(request, 'dashboard/add_earnings.html', context)


@admin_required
def get_assets_by_type(request):
    """API endpoint to get assets filtered by type"""
    asset_type = request.GET.get('type', '')
    
    if asset_type == 'stock':
        assets = Stock.objects.filter(is_active=True).values('symbol', 'name')
        asset_list = [{'value': s['symbol'], 'label': f"{s['symbol']} - {s['name']}"} for s in assets]
    elif asset_type == 'crypto':
        # Common crypto assets
        asset_list = [
            {'value': 'BTC', 'label': 'Bitcoin (BTC)'},
            {'value': 'ETH', 'label': 'Ethereum (ETH)'},
            {'value': 'BNB', 'label': 'Binance Coin (BNB)'},
            {'value': 'SOL', 'label': 'Solana (SOL)'},
            {'value': 'XRP', 'label': 'Ripple (XRP)'},
            {'value': 'ADA', 'label': 'Cardano (ADA)'},
            {'value': 'DOGE', 'label': 'Dogecoin (DOGE)'},
            {'value': 'MATIC', 'label': 'Polygon (MATIC)'},
        ]
    elif asset_type == 'forex':
        # Common forex pairs
        asset_list = [
            {'value': 'EURUSD', 'label': 'EUR/USD'},
            {'value': 'GBPUSD', 'label': 'GBP/USD'},
            {'value': 'USDJPY', 'label': 'USD/JPY'},
            {'value': 'USDCAD', 'label': 'USD/CAD'},
            {'value': 'AUDUSD', 'label': 'AUD/USD'},
            {'value': 'NZDUSD', 'label': 'NZD/USD'},
        ]
    else:
        asset_list = []
    
    return JsonResponse({'assets': asset_list})


@admin_required
def copy_trades_list(request):
    """List all copy trade history with filters"""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    copy_trades = UserCopyTraderHistory.objects.select_related('user', 'trader').order_by('-opened_at')
    
    if status_filter:
        copy_trades = copy_trades.filter(status=status_filter)
    
    if search:
        copy_trades = copy_trades.filter(
            Q(user__email__icontains=search) |
            Q(trader__name__icontains=search) |
            Q(market__icontains=search) |
            Q(reference__icontains=search)
        )
    
    # Pagination - 20 copy trades per page
    paginator = Paginator(copy_trades, 20)
    page = request.GET.get('page')
    
    try:
        copy_trades_page = paginator.page(page)
    except PageNotAnInteger:
        copy_trades_page = paginator.page(1)
    except EmptyPage:
        copy_trades_page = paginator.page(paginator.num_pages)
    
    context = {
        'copy_trades': copy_trades_page,
        'page_obj': copy_trades_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'dashboard/copy_trades_list.html', context)


@admin_required
def add_copy_trade(request):
    """Add new copy trade"""
    if request.method == 'POST':
        form = AddCopyTradeForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            trader = form.cleaned_data['trader']
            market = form.cleaned_data['market']
            direction = form.cleaned_data['direction']
            leverage = form.cleaned_data['leverage']
            duration = form.cleaned_data['duration']
            amount = form.cleaned_data['amount']
            entry_price = form.cleaned_data['entry_price']
            exit_price = form.cleaned_data.get('exit_price')
            profit_loss = form.cleaned_data['profit_loss']
            status = form.cleaned_data['status']
            closed_at = form.cleaned_data.get('closed_at')
            notes = form.cleaned_data.get('notes', '')
            
            # Create copy trade
            copy_trade = UserCopyTraderHistory.objects.create(
                user=user,
                trader=trader,
                market=market,
                direction=direction,
                leverage=leverage,
                duration=duration,
                amount=amount,
                entry_price=entry_price,
                exit_price=exit_price,
                profit_loss=profit_loss,
                status=status,
                closed_at=closed_at,
                notes=notes
            )
            
            # Update user profit AND balance with profit/loss
            if profit_loss:
                # Update profit field (cumulative profit tracking)
                user.profit = (user.profit or Decimal('0.00')) + profit_loss
                
                # Update balance (add profit or subtract loss)
                user.balance = (user.balance or Decimal('0.00')) + profit_loss
                
                user.save(update_fields=['profit', 'balance'])
            
            # Create detailed notification
            if profit_loss >= 0:
                notif_title = 'Copy Trade Profit! 🎉'
                notif_message = f'Your copy trade on {market} has generated ${profit_loss} profit!'
            else:
                notif_title = 'Copy Trade Closed'
                notif_message = f'Your copy trade on {market} closed with ${abs(profit_loss)} loss'
            
            Notification.objects.create(
                user=user,
                type='trade',
                title=notif_title,
                message=notif_message,
                full_details=f'''
Trader: {trader.name}
Market: {market}
Direction: {direction.upper()}
Amount: ${amount}
Leverage: {leverage}
Entry Price: ${entry_price}
Exit Price: ${exit_price if exit_price else "N/A"}
Profit/Loss: ${profit_loss}
Status: {status.capitalize()}

Your new balance: ${user.balance}
                '''.strip()
            )
            
            messages.success(request, f'Copy trade added successfully for {user.email}')
            return redirect('dashboard:copy_trades_list')
    else:
        form = AddCopyTradeForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboard/add_copy_trade.html', context)


@admin_required
def copy_trade_detail(request, trade_id):
    """View copy trade details"""
    copy_trade = get_object_or_404(
        UserCopyTraderHistory.objects.select_related('user', 'trader'),
        id=trade_id
    )
    
    context = {
        'copy_trade': copy_trade,
    }
    
    return render(request, 'dashboard/copy_trade_detail.html', context)


@admin_required
def traders_list(request):
    """List all professional traders with pagination"""
    search = request.GET.get('search', '')
    badge_filter = request.GET.get('badge', '')
    active_filter = request.GET.get('active', '')
    
    traders = Trader.objects.all().order_by('-gain', '-copiers')
    
    if search:
        traders = traders.filter(
            Q(name__icontains=search) |
            Q(username__icontains=search) |
            Q(country__icontains=search)
        )
    
    if badge_filter:
        traders = traders.filter(badge=badge_filter)
    
    if active_filter:
        is_active = active_filter == 'active'
        traders = traders.filter(is_active=is_active)
    
    # Pagination - 20 traders per page
    paginator = Paginator(traders, 20)
    page = request.GET.get('page')
    
    try:
        traders_page = paginator.page(page)
    except PageNotAnInteger:
        traders_page = paginator.page(1)
    except EmptyPage:
        traders_page = paginator.page(paginator.num_pages)
    
    context = {
        'traders': traders_page,
        'page_obj': traders_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'search': search,
        'badge_filter': badge_filter,
        'active_filter': active_filter,
    }
    
    return render(request, 'dashboard/traders_list.html', context)


@admin_required
def add_trader(request):
    """Add new professional trader"""
    if request.method == 'POST':
        form = AddTraderForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle capital - use dropdown or custom
            capital_dropdown = form.cleaned_data.get('capital_dropdown', '')
            capital_custom = form.cleaned_data.get('capital', '')
            if capital_custom:
                capital = capital_custom
            elif capital_dropdown:
                capital = capital_dropdown
            else:
                capital = '0'
            
            # Handle gain - use dropdown or custom
            gain_dropdown = form.cleaned_data.get('gain_dropdown', '')
            gain_custom = form.cleaned_data.get('gain')
            if gain_custom:
                gain = gain_custom
            elif gain_dropdown:
                gain = Decimal(gain_dropdown)
            else:
                gain = Decimal('0.00')
            
            # Handle avg profit - use dropdown or custom
            avg_profit_dropdown = form.cleaned_data.get('avg_profit_dropdown', '')
            avg_profit_custom = form.cleaned_data.get('avg_profit_percent')
            if avg_profit_custom:
                avg_profit_percent = avg_profit_custom
            elif avg_profit_dropdown:
                avg_profit_percent = Decimal(avg_profit_dropdown)
            else:
                avg_profit_percent = Decimal('0.00')
            
            # Handle avg loss - use dropdown or custom
            avg_loss_dropdown = form.cleaned_data.get('avg_loss_dropdown', '')
            avg_loss_custom = form.cleaned_data.get('avg_loss_percent')
            if avg_loss_custom:
                avg_loss_percent = avg_loss_custom
            elif avg_loss_dropdown:
                avg_loss_percent = Decimal(avg_loss_dropdown)
            else:
                avg_loss_percent = Decimal('0.00')
            
            # Handle total wins - use dropdown or custom
            wins_dropdown = form.cleaned_data.get('total_wins_dropdown', '')
            wins_custom = form.cleaned_data.get('total_wins')
            if wins_custom:
                total_wins = wins_custom
            elif wins_dropdown:
                total_wins = int(wins_dropdown)
            else:
                total_wins = 0
            
            # Handle total losses - use dropdown or custom
            losses_dropdown = form.cleaned_data.get('total_losses_dropdown', '')
            losses_custom = form.cleaned_data.get('total_losses')
            if losses_custom:
                total_losses = losses_custom
            elif losses_dropdown:
                total_losses = int(losses_dropdown)
            else:
                total_losses = 0
            
            # Handle copiers - use exact or range
            copiers_exact = form.cleaned_data.get('copiers')
            copiers_range = form.cleaned_data.get('copiers_range', '')
            if copiers_exact:
                copiers = copiers_exact
            elif copiers_range:
                if copiers_range == '1-10':
                    copiers = 5
                elif copiers_range == '11-20':
                    copiers = 15
                elif copiers_range == '21-30':
                    copiers = 25
                elif copiers_range == '31-50':
                    copiers = 40
                elif copiers_range == '51-100':
                    copiers = 75
                elif copiers_range == '101-200':
                    copiers = 150
                elif copiers_range == '201-300':
                    copiers = 250
                elif copiers_range == '300+':
                    copiers = 350
                else:
                    copiers = 0
            else:
                copiers = 0
            
            # Handle trades - use exact or range
            trades_exact = form.cleaned_data.get('trades')
            trades_range = form.cleaned_data.get('trades_range', '')
            if trades_exact:
                trades = trades_exact
            elif trades_range:
                if trades_range == '1-50':
                    trades = 25
                elif trades_range == '51-100':
                    trades = 75
                elif trades_range == '101-200':
                    trades = 150
                elif trades_range == '201-300':
                    trades = 250
                elif trades_range == '301-500':
                    trades = 400
                elif trades_range == '500+':
                    trades = 600
                else:
                    trades = 0
            else:
                trades = 0
            
            # Handle subscribers - use exact or range
            subscribers_exact = form.cleaned_data.get('subscribers')
            subscribers_range = form.cleaned_data.get('subscribers_range', '')
            if subscribers_exact:
                subscribers = subscribers_exact
            elif subscribers_range:
                if subscribers_range == '0':
                    subscribers = 0
                elif subscribers_range == '1-10':
                    subscribers = 5
                elif subscribers_range == '11-25':
                    subscribers = 18
                elif subscribers_range == '26-50':
                    subscribers = 38
                elif subscribers_range == '51-100':
                    subscribers = 75
                elif subscribers_range == '101-200':
                    subscribers = 150
                elif subscribers_range == '200+':
                    subscribers = 250
                else:
                    subscribers = 0
            else:
                subscribers = 0
            
            # Handle current positions - use exact or range
            positions_exact = form.cleaned_data.get('current_positions')
            positions_range = form.cleaned_data.get('current_positions_range', '')
            if positions_exact:
                current_positions = positions_exact
            elif positions_range:
                if positions_range == '0':
                    current_positions = 0
                elif positions_range == '1-5':
                    current_positions = 3
                elif positions_range == '6-10':
                    current_positions = 8
                elif positions_range == '11-20':
                    current_positions = 15
                elif positions_range == '20+':
                    current_positions = 25
                else:
                    current_positions = 0
            else:
                current_positions = 0
            
            # Handle expert rating
            expert_rating_value = form.cleaned_data.get('expert_rating')
            if expert_rating_value:
                expert_rating = Decimal(expert_rating_value)
            else:
                expert_rating = Decimal('5.00')
            
            # Create trader with form data
            trader = Trader.objects.create(
                name=form.cleaned_data['name'],
                username=form.cleaned_data['username'],
                avatar=form.cleaned_data.get('avatar'),
                country_flag=form.cleaned_data.get('country_flag'),
                country=form.cleaned_data['country'],
                badge=form.cleaned_data['badge'],
                capital=capital,
                gain=gain,
                risk=int(form.cleaned_data['risk']),
                copiers=copiers,
                trades=trades,
                avg_trade_time=form.cleaned_data['avg_trade_time'],
                avg_profit_percent=avg_profit_percent,
                avg_loss_percent=avg_loss_percent,
                total_wins=total_wins,
                total_losses=total_losses,
                subscribers=subscribers,
                current_positions=current_positions,
                expert_rating=expert_rating,
                return_ytd=form.cleaned_data.get('return_ytd', Decimal('0.00')),
                avg_score_7d=form.cleaned_data.get('avg_score_7d', Decimal('0.00')),
                profitable_weeks=form.cleaned_data.get('profitable_weeks', Decimal('0.00')),
                min_account_threshold=form.cleaned_data.get('min_account_threshold', Decimal('0.00')),
                is_active=form.cleaned_data.get('is_active', True),
                total_trades_12m=trades,
            )
            
            messages.success(request, f'Trader "{trader.name}" added successfully!')
            return redirect('dashboard:traders_list')
    else:
        form = AddTraderForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboard/add_trader.html', context)


@admin_required
def trader_detail(request, trader_id):
    """View trader details"""
    trader = get_object_or_404(Trader, id=trader_id)
    
    # Get copy trades associated with this trader
    copy_trades = UserCopyTraderHistory.objects.filter(
        trader=trader
    ).select_related('user').order_by('-opened_at')[:10]
    
    context = {
        'trader': trader,
        'copy_trades': copy_trades,
    }
    
    return render(request, 'dashboard/trader_detail.html', context)


@admin_required
def edit_trader(request, trader_id):
    """Edit existing trader"""
    trader = get_object_or_404(Trader, id=trader_id)
    
    if request.method == 'POST':
        form = EditTraderForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle copiers - use exact or range (same logic as add_trader)
            copiers_exact = form.cleaned_data.get('copiers')
            copiers_range = form.cleaned_data.get('copiers_range', '')
            if copiers_exact:
                copiers = copiers_exact
            elif copiers_range:
                if copiers_range == '1-10':
                    copiers = 5
                elif copiers_range == '11-20':
                    copiers = 15
                elif copiers_range == '21-30':
                    copiers = 25
                elif copiers_range == '31-50':
                    copiers = 40
                elif copiers_range == '51-100':
                    copiers = 75
                elif copiers_range == '101-200':
                    copiers = 150
                elif copiers_range == '201-300':
                    copiers = 250
                elif copiers_range == '300+':
                    copiers = 350
                else:
                    copiers = trader.copiers  # Keep existing
            else:
                copiers = trader.copiers  # Keep existing
            
            # Handle trades - use exact or range
            trades_exact = form.cleaned_data.get('trades')
            trades_range = form.cleaned_data.get('trades_range', '')
            if trades_exact:
                trades = trades_exact
            elif trades_range:
                if trades_range == '1-50':
                    trades = 25
                elif trades_range == '51-100':
                    trades = 75
                elif trades_range == '101-200':
                    trades = 150
                elif trades_range == '201-300':
                    trades = 250
                elif trades_range == '301-500':
                    trades = 400
                elif trades_range == '500+':
                    trades = 600
                else:
                    trades = trader.trades  # Keep existing
            else:
                trades = trader.trades  # Keep existing
            
            # Handle subscribers
            subscribers_exact = form.cleaned_data.get('subscribers')
            subscribers_range = form.cleaned_data.get('subscribers_range', '')
            if subscribers_exact:
                subscribers = subscribers_exact
            elif subscribers_range:
                if subscribers_range == '0':
                    subscribers = 0
                elif subscribers_range == '1-10':
                    subscribers = 5
                elif subscribers_range == '11-25':
                    subscribers = 18
                elif subscribers_range == '26-50':
                    subscribers = 38
                elif subscribers_range == '51-100':
                    subscribers = 75
                elif subscribers_range == '101-200':
                    subscribers = 150
                elif subscribers_range == '200+':
                    subscribers = 250
                else:
                    subscribers = trader.subscribers  # Keep existing
            else:
                subscribers = trader.subscribers  # Keep existing
            
            # Handle current positions
            positions_exact = form.cleaned_data.get('current_positions')
            positions_range = form.cleaned_data.get('current_positions_range', '')
            if positions_exact:
                current_positions = positions_exact
            elif positions_range:
                if positions_range == '0':
                    current_positions = 0
                elif positions_range == '1-5':
                    current_positions = 3
                elif positions_range == '6-10':
                    current_positions = 8
                elif positions_range == '11-20':
                    current_positions = 15
                elif positions_range == '20+':
                    current_positions = 25
                else:
                    current_positions = trader.current_positions  # Keep existing
            else:
                current_positions = trader.current_positions  # Keep existing
            
            # Handle expert rating
            expert_rating_value = form.cleaned_data.get('expert_rating')
            if expert_rating_value:
                expert_rating = Decimal(expert_rating_value)
            else:
                expert_rating = trader.expert_rating  # Keep existing
            
            # Handle capital - use dropdown or custom
            capital_dropdown = form.cleaned_data.get('capital_dropdown', '')
            capital_custom = form.cleaned_data.get('capital', '')
            if capital_custom:
                capital = capital_custom
            elif capital_dropdown:
                capital = capital_dropdown
            else:
                capital = trader.capital
            
            # Handle gain - use dropdown or custom
            gain_dropdown = form.cleaned_data.get('gain_dropdown', '')
            gain_custom = form.cleaned_data.get('gain')
            if gain_custom:
                gain = gain_custom
            elif gain_dropdown:
                gain = Decimal(gain_dropdown)
            else:
                gain = trader.gain
            
            # Handle avg profit - use dropdown or custom
            avg_profit_dropdown = form.cleaned_data.get('avg_profit_dropdown', '')
            avg_profit_custom = form.cleaned_data.get('avg_profit_percent')
            if avg_profit_custom:
                avg_profit_percent = avg_profit_custom
            elif avg_profit_dropdown:
                avg_profit_percent = Decimal(avg_profit_dropdown)
            else:
                avg_profit_percent = trader.avg_profit_percent
            
            # Handle avg loss - use dropdown or custom
            avg_loss_dropdown = form.cleaned_data.get('avg_loss_dropdown', '')
            avg_loss_custom = form.cleaned_data.get('avg_loss_percent')
            if avg_loss_custom:
                avg_loss_percent = avg_loss_custom
            elif avg_loss_dropdown:
                avg_loss_percent = Decimal(avg_loss_dropdown)
            else:
                avg_loss_percent = trader.avg_loss_percent
            
            # Handle total wins - use dropdown or custom
            wins_dropdown = form.cleaned_data.get('total_wins_dropdown', '')
            wins_custom = form.cleaned_data.get('total_wins')
            if wins_custom:
                total_wins = wins_custom
            elif wins_dropdown:
                total_wins = int(wins_dropdown)
            else:
                total_wins = trader.total_wins
            
            # Handle total losses - use dropdown or custom
            losses_dropdown = form.cleaned_data.get('total_losses_dropdown', '')
            losses_custom = form.cleaned_data.get('total_losses')
            if losses_custom:
                total_losses = losses_custom
            elif losses_dropdown:
                total_losses = int(losses_dropdown)
            else:
                total_losses = trader.total_losses
            
            # Update trader
            trader.name = form.cleaned_data['name']
            trader.username = form.cleaned_data['username']
            
            # Update avatar if new one uploaded
            if form.cleaned_data.get('avatar'):
                trader.avatar = form.cleaned_data['avatar']
            
            # Update country_flag if new one uploaded
            if form.cleaned_data.get('country_flag'):
                trader.country_flag = form.cleaned_data['country_flag']
            
            trader.country = form.cleaned_data['country']
            trader.badge = form.cleaned_data['badge']
            trader.capital = capital
            trader.gain = gain
            trader.risk = int(form.cleaned_data['risk'])
            trader.copiers = copiers
            trader.trades = trades
            trader.avg_trade_time = form.cleaned_data['avg_trade_time']
            trader.avg_profit_percent = avg_profit_percent
            trader.avg_loss_percent = avg_loss_percent
            trader.total_wins = total_wins
            trader.total_losses = total_losses
            trader.subscribers = subscribers
            trader.current_positions = current_positions
            trader.expert_rating = expert_rating
            trader.return_ytd = form.cleaned_data.get('return_ytd', Decimal('0.00'))
            trader.avg_score_7d = form.cleaned_data.get('avg_score_7d', Decimal('0.00'))
            trader.profitable_weeks = form.cleaned_data.get('profitable_weeks', Decimal('0.00'))
            trader.min_account_threshold = form.cleaned_data.get('min_account_threshold', Decimal('0.00'))
            trader.is_active = form.cleaned_data.get('is_active', True)
            trader.total_trades_12m = trades
            
            trader.save()
            
            messages.success(request, f'Trader "{trader.name}" updated successfully!')
            return redirect('dashboard:trader_detail', trader_id=trader.id)
    else:
        # Pre-fill form with existing data
        initial_data = {
            'name': trader.name,
            'username': trader.username,
            'country': trader.country,
            'badge': trader.badge,
            # Capital fields
            'capital': trader.capital,
            # Gain fields
            'gain': trader.gain,
            'risk': str(trader.risk),
            'avg_trade_time': trader.avg_trade_time,
            # Copiers fields
            'copiers': trader.copiers,
            # Trades fields
            'trades': trader.trades,
            # Avg profit fields
            'avg_profit_percent': trader.avg_profit_percent,
            # Avg loss fields
            'avg_loss_percent': trader.avg_loss_percent,
            # Total wins fields
            'total_wins': trader.total_wins,
            # Total losses fields
            'total_losses': trader.total_losses,
            # Subscribers fields
            'subscribers': trader.subscribers,
            # Positions fields
            'current_positions': trader.current_positions,
            # Expert rating
            'expert_rating': str(float(trader.expert_rating)),
            'return_ytd': trader.return_ytd,
            'avg_score_7d': trader.avg_score_7d,
            'profitable_weeks': trader.profitable_weeks,
            'min_account_threshold': trader.min_account_threshold,
            'is_active': trader.is_active,
        }
        form = EditTraderForm(initial=initial_data)
    
    context = {
        'form': form,
        'trader': trader,
    }
    
    return render(request, 'dashboard/edit_trader.html', context)



@admin_required
def investors_list(request):
    """
    List all users who have ever made a deposit
    Shows unique users with their total deposits and amounts
    """
    search_query = request.GET.get('search', '')
    
    # Get all users who have made at least one deposit
    investor_ids = Transaction.objects.filter(
        transaction_type='deposit'
    ).values_list('user_id', flat=True).distinct()
    
    investors = CustomUser.objects.filter(
        id__in=investor_ids
    ).order_by('-date_joined')
    
    # Search functionality
    if search_query:
        investors = investors.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(account_id__icontains=search_query)
        )
    
    # Annotate with deposit statistics
    investors_data = []
    for investor in investors:
        deposits = Transaction.objects.filter(
            user=investor,
            transaction_type='deposit'
        )
        
        total_deposits = deposits.count()
        completed_deposits = deposits.filter(status='completed').count()
        pending_deposits = deposits.filter(status='pending').count()
        
        total_amount = deposits.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        investors_data.append({
            'user': investor,
            'total_deposits': total_deposits,
            'completed_deposits': completed_deposits,
            'pending_deposits': pending_deposits,
            'total_amount': total_amount,
        })
    
    # Pagination - 20 investors per page
    paginator = Paginator(investors_data, 20)
    page = request.GET.get('page')
    
    try:
        investors_page = paginator.page(page)
    except PageNotAnInteger:
        investors_page = paginator.page(1)
    except EmptyPage:
        investors_page = paginator.page(paginator.num_pages)
    
    context = {
        'investors': investors_page,
        'page_obj': investors_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'search_query': search_query,
        'total_investors': len(investors_data),
    }
    
    return render(request, 'dashboard/investors_list.html', context)


@admin_required
def investor_detail(request, user_id):
    """
    Show detailed view of a specific investor
    Lists all their deposit transactions
    """
    investor = get_object_or_404(CustomUser, id=user_id)
    
    # Get all deposits for this user
    deposits = Transaction.objects.filter(
        user=investor,
        transaction_type='deposit'
    ).order_by('-created_at')
    
    # Calculate statistics
    total_deposits = deposits.count()
    completed_deposits = deposits.filter(status='completed')
    pending_deposits = deposits.filter(status='pending')
    failed_deposits = deposits.filter(status='failed')
    
    total_completed_amount = completed_deposits.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_pending_amount = pending_deposits.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Pagination - 15 deposits per page
    paginator = Paginator(deposits, 15)
    page = request.GET.get('page')
    
    try:
        deposits_page = paginator.page(page)
    except PageNotAnInteger:
        deposits_page = paginator.page(1)
    except EmptyPage:
        deposits_page = paginator.page(paginator.num_pages)
    
    context = {
        'investor': investor,
        'deposits': deposits_page,
        'page_obj': deposits_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'total_deposits': total_deposits,
        'completed_count': completed_deposits.count(),
        'pending_count': pending_deposits.count(),
        'failed_count': failed_deposits.count(),
        'total_completed_amount': total_completed_amount,
        'total_pending_amount': total_pending_amount,
    }
    
    return render(request, 'dashboard/investor_detail.html', context)






