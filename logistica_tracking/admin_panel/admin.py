from django.contrib import admin

from .models import PriorityList


@admin.register(PriorityList)
class PriorityListAdmin(admin.ModelAdmin):
    list_display = ("driver", "added_by", "created_at")
