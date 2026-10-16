from rest_framework import serializers
from .models import UserSettings,Challenge,DailyUsage,AppUsage,FocusSession
class AppUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model=AppUsage
        fields=["package_name","app_name","minutes"]
class DailyUsageSerializer(serializers.ModelSerializer):
    apps=AppUsageSerializer(many=True,read_only=True)
    class Meta:
        model=DailyUsage
        fields=["date","total_minutes","source","synced_at","apps"]
class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserSettings
        fields=["daily_screen_goal_minutes","daily_focus_goal_minutes"]
class ChallengeSerializer(serializers.ModelSerializer):
    end_date=serializers.DateField(read_only=True)
    current_day=serializers.IntegerField(read_only=True)
    days_remaining=serializers.IntegerField(read_only=True)
    progress_percent=serializers.SerializerMethodField()
    class Meta:
        model=Challenge
        fields=["id","start_date","duration_days","end_date","current_day","days_remaining","is_active","progress_percent","created_at"]
        read_only_fields=fields
    def get_progress_percent(self,obj): return min(100,round(obj.current_day/obj.duration_days*100))
class FocusSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model=FocusSession
        fields=["id","date","duration_minutes","label","created_at"]
        read_only_fields=["id","created_at"]
