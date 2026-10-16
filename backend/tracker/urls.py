from django.urls import path
from .views import Register,Login,ChallengeView,SettingsView,UsageSync,Dashboard,FocusSessions
urlpatterns=[
 path("auth/register/",Register.as_view()),path("auth/token/",Login.as_view()),
 path("challenge/",ChallengeView.as_view()),path("challenge/start/",ChallengeView.as_view()),
 path("settings/",SettingsView.as_view()),path("usage/sync/",UsageSync.as_view()),
 path("dashboard/",Dashboard.as_view()),path("focus-sessions/",FocusSessions.as_view()),
]
