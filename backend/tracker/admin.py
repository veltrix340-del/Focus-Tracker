from django.contrib import admin
from .models import UserSettings,Challenge,DailyUsage,AppUsage,FocusSession
admin.site.register(UserSettings)
admin.site.register(Challenge)
class AppUsageInline(admin.TabularInline):
    model=AppUsage
    extra=0
@admin.register(DailyUsage)
class DailyUsageAdmin(admin.ModelAdmin):
    list_display=("user","date","total_minutes","source","synced_at")
    list_filter=("date","source")
    inlines=[AppUsageInline]
admin.site.register(FocusSession)
