from django.contrib import admin
from accounts.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "phone_number",
        "points",
        "updated_at",
    )
    list_filter = ("role",)
    search_fields = (
        "user__username",
        "user__email",
        "phone_number",
    )
    list_select_related = ("user",)