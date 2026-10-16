from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone

class UserSettings(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="focus_settings")
    daily_screen_goal_minutes=models.PositiveIntegerField(default=180)
    daily_focus_goal_minutes=models.PositiveIntegerField(default=120)

class Challenge(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="challenges")
    start_date=models.DateField(default=timezone.localdate)
    duration_days=models.PositiveSmallIntegerField(default=30)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["-created_at"]
    @property
    def end_date(self): return self.start_date+timedelta(days=self.duration_days-1)
    @property
    def current_day(self): return max(1,min(self.duration_days,(timezone.localdate()-self.start_date).days+1))
    @property
    def days_remaining(self): return max(0,(self.end_date-timezone.localdate()).days)

class DailyUsage(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="daily_usage")
    date=models.DateField()
    total_minutes=models.PositiveIntegerField(default=0)
    source=models.CharField(max_length=24,default="android")
    synced_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["user","date"],name="unique_user_usage_day")]
        ordering=["date"]

class AppUsage(models.Model):
    daily_usage=models.ForeignKey(DailyUsage,on_delete=models.CASCADE,related_name="apps")
    package_name=models.CharField(max_length=255)
    app_name=models.CharField(max_length=120,blank=True)
    minutes=models.PositiveIntegerField(default=0)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["daily_usage","package_name"],name="unique_app_usage_day")]
        ordering=["-minutes"]

class FocusSession(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="focus_sessions")
    date=models.DateField(default=timezone.localdate)
    duration_minutes=models.PositiveIntegerField()
    label=models.CharField(max_length=100,default="Deep work")
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]
