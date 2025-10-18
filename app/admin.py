from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, 
    Transaction, 
    PaymentMethod, 
    AdminWallet, 
    Trader, 
    Asset,
)

from django.forms import TextInput, Textarea
from django import forms

class UserAdminConfig(UserAdmin):
    model = CustomUser
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_staff", "is_active", "is_superuser")
    ordering = ("-date_joined",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "account_id")}),
        ("Location", {"fields": ("country", "region", "city", "phone", "dob", "address", "postal_code", "currency")}),
        ("KYC", {"fields": ("id_type", "is_verified", "has_submitted_kyc", "id_front", "id_back")}),
        ("Monetary Values", {"fields": ("user_funds", "free_margin", "balance", "equity", "margin_level")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_active")}
        ),
    )

admin.site.register(CustomUser, UserAdminConfig)
admin.site.register(Transaction)
admin.site.register(PaymentMethod)
admin.site.register(AdminWallet)
admin.site.register(Trader)
admin.site.register(Asset)






