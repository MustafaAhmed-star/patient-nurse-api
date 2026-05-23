from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import JoinRequest, NurseProfile, PatientProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "role", "is_blocked", "is_staff", "is_active", "date_joined"]
    list_filter = ["role", "is_blocked", "is_staff", "is_active"]
    search_fields = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Permissions"), {"fields": ("role", "is_blocked", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "password1", "password2"),
            },
        ),
    )


@admin.register(NurseProfile)
class NurseProfileAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "user", "gender", "is_approved", "created_at"]
    list_filter = ["gender", "is_approved", "created_at"]
    search_fields = ["full_name", "phone", "user__email"]
    readonly_fields = ["approved_at", "rejected_at", "created_at", "updated_at"]


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "user", "accepted_terms", "created_at"]
    list_filter = ["accepted_terms", "created_at"]
    search_fields = ["full_name", "phone", "user__email"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ["nurse", "status", "reviewed_by", "reviewed_at", "created_at"]
    list_filter = ["status", "created_at", "reviewed_at"]
    search_fields = ["nurse__email", "nurse__nurse_profile__full_name"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
