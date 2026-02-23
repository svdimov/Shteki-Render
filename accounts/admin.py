from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from accounts.forms import AppUserCreationForm, AppUserChangeForm, CustomAdminAuthenticationForm
from accounts.models import Profile

UserModel = get_user_model()


admin.site.login_form = CustomAdminAuthenticationForm


@admin.register(UserModel)
class AppUserAdmin(UserAdmin):
    list_display = ("email", "is_active", "is_staff")
    form = AppUserChangeForm
    add_form = AppUserCreationForm
    search_fields = ["email"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    ordering = ("email",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name")
    search_fields = ("user__email", "first_name", "last_name")

