from datetime import timedelta, date
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserSettings,Challenge,DailyUsage,AppUsage,FocusSession
from .serializers import UserSettingsSerializer,ChallengeSerializer,DailyUsageSerializer,FocusSessionSerializer

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request): return Response({"status":"ok","service":"Focus Reset API"})

class Register(APIView):
    permission_classes=[AllowAny]; authentication_classes=[]
    def post(self,request):
        User=get_user_model(); username=str(request.data.get("username","")).strip(); password=str(request.data.get("password",""))
        if len(username)<3 or len(password)<8: return Response({"detail":"Username must be 3+ characters and password 8+ characters."},status=400)
        if User.objects.filter(username=username).exists(): return Response({"detail":"Username already exists."},status=400)
        user=User.objects.create_user(username=username,password=password)
        UserSettings.objects.create(user=user); Challenge.objects.create(user=user)
        token,_=Token.objects.get_or_create(user=user)
        return Response({"token":token.key,"username":user.username},status=201)

class Login(APIView):
    permission_classes=[AllowAny]; authentication_classes=[]
    def post(self,request):
        user=authenticate(request,username=request.data.get("username",""),password=request.data.get("password",""))
        if not user: return Response({"detail":"Invalid username or password."},status=400)
        UserSettings.objects.get_or_create(user=user)
        token,_=Token.objects.get_or_create(user=user)
        return Response({"token":token.key,"username":user.username})

class ChallengeView(APIView):
    def get(self,request):
        obj=Challenge.objects.filter(user=request.user,is_active=True).first()
        if not obj: obj=Challenge.objects.create(user=request.user)
        return Response(ChallengeSerializer(obj).data)
    def post(self,request):
        Challenge.objects.filter(user=request.user,is_active=True).update(is_active=False)
        obj=Challenge.objects.create(user=request.user,start_date=timezone.localdate(),duration_days=30)
        return Response(ChallengeSerializer(obj).data,status=201)

class SettingsView(APIView):
    def get(self,request):
        obj,_=UserSettings.objects.get_or_create(user=request.user)
        return Response(UserSettingsSerializer(obj).data)
    def patch(self,request):
        obj,_=UserSettings.objects.get_or_create(user=request.user)
        ser=UserSettingsSerializer(obj,data=request.data,partial=True); ser.is_valid(raise_exception=True); ser.save()
        return Response(ser.data)

class UsageSync(APIView):
    def get(self,request):
        days=max(1,min(90,int(request.query_params.get("days",30))))
        rows=DailyUsage.objects.filter(user=request.user,date__gte=timezone.localdate()-timedelta(days=days-1)).prefetch_related("apps")
        return Response(DailyUsageSerializer(rows,many=True).data)
    def post(self,request):
        payloads=request.data if isinstance(request.data,list) else [request.data]; saved=[]
        for payload in payloads:
            try:
                day_date=date.fromisoformat(str(payload["date"]))
                total=max(0,int(payload.get("total_minutes",0)))
            except (KeyError,ValueError,TypeError):
                return Response({"detail":"Each record needs a valid YYYY-MM-DD date and integer total_minutes."},status=400)
            day,_=DailyUsage.objects.update_or_create(user=request.user,date=day_date,defaults={"total_minutes":total,"source":"android"})
            seen=set()
            for app in payload.get("apps",[]):
                pkg=str(app.get("package_name","")).strip()[:255]
                if not pkg: continue
                try: mins=max(0,int(app.get("minutes",0)))
                except (TypeError,ValueError): mins=0
                AppUsage.objects.update_or_create(daily_usage=day,package_name=pkg,defaults={"app_name":str(app.get("app_name",""))[:120],"minutes":mins})
                seen.add(pkg)
            day.apps.exclude(package_name__in=seen).delete()
            saved.append(day)
        return Response({"saved":len(saved),"records":DailyUsageSerializer(saved,many=True).data})

class Dashboard(APIView):
    def get(self,request):
        days=max(1,min(30,int(request.query_params.get("days",30))))
        today=timezone.localdate(); start=today-timedelta(days=days-1)
        rows={x.date:x for x in DailyUsage.objects.filter(user=request.user,date__gte=start,date__lte=today).prefetch_related("apps")}
        challenge=Challenge.objects.filter(user=request.user,is_active=True).first()
        if not challenge: challenge=Challenge.objects.create(user=request.user,start_date=today)
        settings_obj,_=UserSettings.objects.get_or_create(user=request.user)
        output=[]
        for i in range(days):
            d=start+timedelta(days=i); row=rows.get(d)
            apps=[{"package_name":a.package_name,"app_name":a.app_name,"minutes":a.minutes} for a in row.apps.all()[:8]] if row else []
            output.append({"date":str(d),"day":(d-challenge.start_date).days+1,"total_minutes":row.total_minutes if row else 0,"apps":apps})
        logged=sum(1 for d in output if challenge.start_date<=date.fromisoformat(d["date"])<=challenge.end_date and d["total_minutes"]>0)
        focus=FocusSession.objects.filter(user=request.user,date__gte=start,date__lte=today)
        focus_total=sum(focus.values_list("duration_minutes",flat=True))
        recorded=[d["total_minutes"] for d in output if d["total_minutes"]>0]
        todayrow=rows.get(today)
        return Response({"challenge":ChallengeSerializer(challenge).data,"settings":UserSettingsSerializer(settings_obj).data,"days":output,
            "summary":{"today_minutes":todayrow.total_minutes if todayrow else 0,"average_minutes":round(sum(recorded)/len(recorded)) if recorded else 0,
            "days_logged":logged,"focus_minutes":focus_total,"goal_met_today":bool(todayrow and todayrow.total_minutes<=settings_obj.daily_screen_goal_minutes)}})

class FocusSessions(APIView):
    def get(self,request): return Response(FocusSessionSerializer(FocusSession.objects.filter(user=request.user)[:100],many=True).data)
    def post(self,request):
        ser=FocusSessionSerializer(data=request.data); ser.is_valid(raise_exception=True); ser.save(user=request.user)
        return Response(ser.data,status=201)
