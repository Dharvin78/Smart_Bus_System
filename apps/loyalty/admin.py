from django.contrib import admin

from .models import LoyaltyReward


@admin.register(LoyaltyReward)
class LoyaltyRewardAdmin(admin.ModelAdmin):
    list_display = (
        "name", "points_required", "discount_percentage", "max_discount", "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
