from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Client, CustomerProfile, Feedback


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    extra = 0
    autocomplete_fields = ["client"]


User = get_user_model()
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [CustomerProfileInline]
    list_select_related = ("customer_profile",)

    def get_list_display(self, request):
        base = list(super().get_list_display(request))
        if "client" not in base:
            base.append("client")
        return tuple(base)

    @admin.display(ordering="customer_profile__client__name")
    def client(self, obj):
        profile = getattr(obj, "customer_profile", None)
        return profile.client if profile else "-"


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "public_token", "google_review_url", "created_at", "public_url")
    search_fields = ("name", "public_token")
    readonly_fields = ("created_at", "public_token")

    @admin.display(description="Public URL")
    def public_url(self, obj: Client):
        return obj.get_public_url()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        profile = getattr(request.user, "customer_profile", None)
        if not profile:
            return qs.none()
        return qs.filter(pk=profile.client_id)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("created_at", "client", "rating", "comment")
    list_filter = ("client", "rating", "created_at")
    search_fields = ("comment", "client__name", "client__public_token")
    readonly_fields = ("created_at", "metadata")
    autocomplete_fields = ["client"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        profile = getattr(request.user, "customer_profile", None)
        if not profile:
            return qs.none()
        return qs.filter(client_id=profile.client_id)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_change_permission(request, obj=obj)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "client")
    search_fields = ("user__username", "user__email", "client__name", "client__public_token")
    autocomplete_fields = ("user", "client")

