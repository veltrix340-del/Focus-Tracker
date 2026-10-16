from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.utils import timezone
from .models import DailyUsage
class ApiTests(TestCase):
 def setUp(self):
  self.user=User.objects.create_user(username="tester",password="test-password-123")
  self.token=Token.objects.create(user=self.user); self.client=APIClient()
  self.client.credentials(HTTP_AUTHORIZATION="Token "+self.token.key)
 def test_health(self): self.assertEqual(self.client.get("/api/health/").status_code,200)
 def test_sync(self):
  r=self.client.post("/api/usage/sync/",{"date":str(timezone.localdate()),"total_minutes":90,"apps":[{"package_name":"com.example","app_name":"Example","minutes":40}]},format="json")
  self.assertEqual(r.status_code,200); self.assertEqual(DailyUsage.objects.get(user=self.user).total_minutes,90)
