from django.urls import path

from .views import( 
    validate_token,
    register_user, 
    login_user, 
    change_password, 
    ticket_list_create,
    transactions_view, 
    get_user_profile,
    upload_kyc,
    withdrawal_view,
    transaction_history,
    payment_methods,
    get_deposit_options,
    create_deposit,
    trader_list_create,
    trader_detail,
    asset_list,
    grouped_assets,
    
)

urlpatterns = [
     path("api/validate-token/", validate_token, name="validate-token"),
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
    path("profile/", get_user_profile, name="get_user_profile"),
    path("tickets/", ticket_list_create, name="tickets_view"),
    path("transactions/", transactions_view, name="transactions_view"),

     path("change-password/", change_password, name="change-password"),
     path("withdrawal/", withdrawal_view, name="withdrawal"),

     path("kyc/upload/", upload_kyc, name="upload_kyc"),
     path("transactions/", transaction_history, name="transaction-history"),
     path("payments/", payment_methods, name="payments"),
     
     path("admin-wallets/", get_deposit_options, name="get_deposit_options"),

     path("deposits/", create_deposit, name="create-deposit"),

     path("traders/", trader_list_create, name="trader-list-create"),
    path("traders/<int:pk>/", trader_detail, name="trader-detail"),

    path("assets/", asset_list, name="asset-list"),
    path("assets/grouped/", grouped_assets, name="grouped-assets"),
     

]

