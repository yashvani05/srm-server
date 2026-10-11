from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from accounts.roles import ADMIN, EMPLOYEE
from django.core.management import call_command
from service_requests.models import ServiceRequest, SystemState
from service_requests.overdue import run_overdue_check

BASE = "/api/v1"
VALID = {"title": "Broken monitor", "description": "Screen is dead", "category": "IT", "priority": "HIGH"}


class ApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("migrate", verbosity=0)
        cls.admin = User.objects.create_user("admin@t.com", "Admin", "Passw0rd!", ADMIN)
        cls.emp = User.objects.create_user("emp@t.com", "Emp", "Passw0rd!", EMPLOYEE)
        cls.other = User.objects.create_user("other@t.com", "Other", "Passw0rd!", EMPLOYEE)

    def setUp(self):
        cache.clear()

    def client_for(self, email):
        client = APIClient()
        token = client.post(f"{BASE}/auth/login", {"email": email, "password": "Passw0rd!"}, format="json").json()["data"]["token"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    def make(self, owner=None, hours=0, status="OPEN", **extra):
        when = timezone.now() - timedelta(hours=hours)
        return ServiceRequest.objects.create(
            title=extra.pop("title", "Sample request"), description="d", category="IT", status=status,
            created_by=owner or self.emp, created_at=when, status_changed_at=when, **extra)


class AuthTests(ApiTestCase):
    def test_login_logout_revokes_token(self):
        client = self.client_for("emp@t.com")
        self.assertEqual(client.get(f"{BASE}/auth/me").status_code, 200)
        self.assertEqual(client.post(f"{BASE}/auth/logout").status_code, 200)
        revoked = client.get(f"{BASE}/auth/me")
        self.assertEqual(revoked.status_code, 401)
        self.assertEqual(revoked.json()["message"], "Token has been revoked")

    def test_bad_password_and_missing_token(self):
        r = APIClient().post(f"{BASE}/auth/login", {"email": "emp@t.com", "password": "nope"}, format="json")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(APIClient().get(f"{BASE}/requests").status_code, 401)


class RequestTests(ApiTestCase):
    def test_create_and_validation(self):
        client = self.client_for("emp@t.com")
        self.assertEqual(client.post(f"{BASE}/requests", VALID, format="json").status_code, 201)
        bad = client.post(f"{BASE}/requests", {**VALID, "title": "x"}, format="json")
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(bad.json()["message"], "Validation failed")
        with_status = client.post(f"{BASE}/requests", {**VALID, "status": "RESOLVED"}, format="json")
        self.assertEqual(with_status.status_code, 400)

    def test_employee_sees_only_own_and_others_are_404(self):
        mine, theirs = self.make(self.emp), self.make(self.other)
        client = self.client_for("emp@t.com")
        ids = [i["id"] for i in client.get(f"{BASE}/requests").json()["data"]["items"]]
        self.assertEqual(ids, [str(mine.id)])
        self.assertEqual(client.get(f"{BASE}/requests/{theirs.id}").status_code, 404)

    def test_employee_edit_rules_and_admin_only_actions(self):
        req = self.make(self.emp)
        emp, admin = self.client_for("emp@t.com"), self.client_for("admin@t.com")
        self.assertEqual(emp.patch(f"{BASE}/requests/{req.id}", {"title": "New title"}, format="json").status_code, 200)
        self.assertEqual(emp.patch(f"{BASE}/requests/{req.id}", {}, format="json").status_code, 400)
        self.assertEqual(emp.patch(f"{BASE}/requests/{req.id}/status", {"status": "RESOLVED"}, format="json").status_code, 403)
        self.assertEqual(emp.delete(f"{BASE}/requests/{req.id}").status_code, 403)
        admin.patch(f"{BASE}/requests/{req.id}/status", {"status": "IN_PROGRESS"}, format="json")
        locked = emp.patch(f"{BASE}/requests/{req.id}", {"title": "Again"}, format="json")
        self.assertEqual((locked.status_code, locked.json()["message"]), (403, "Only open requests can be edited"))
        self.assertEqual(admin.delete(f"{BASE}/requests/{req.id}").status_code, 200)

    def test_filters_and_pagination(self):
        for i in range(5):
            self.make(self.emp, title=f"R{i}")
        self.make(self.emp, status="RESOLVED", priority="HIGH")
        admin = self.client_for("admin@t.com")
        page = admin.get(f"{BASE}/requests?limit=2&page=3").json()["data"]
        self.assertEqual((len(page["items"]), page["pagination"]["totalItems"], page["pagination"]["totalPages"]), (2, 6, 3))
        self.assertEqual(admin.get(f"{BASE}/requests?status=resolved").json()["data"]["pagination"]["totalItems"], 1)
        self.assertEqual(admin.get(f"{BASE}/requests?limit=500").status_code, 400)


class OverdueTests(ApiTestCase):
    def test_boundaries_and_idempotence(self):
        old_open = self.make(hours=25)
        old_progress = self.make(hours=30, status="IN_PROGRESS")
        fresh = self.make(hours=23)
        resolved = self.make(hours=100, status="RESOLVED")
        first = run_overdue_check()
        self.assertEqual(first.marked, 2)
        self.assertEqual(run_overdue_check().marked, 0)
        flags = {r.pk: r.overdue for r in ServiceRequest.objects.all()}
        self.assertEqual((flags[old_open.pk], flags[old_progress.pk], flags[fresh.pk], flags[resolved.pk]), (True, True, False, False))
        self.assertTrue(SystemState.objects.filter(key="overdue_check.last_success_at").exists())

    def test_status_change_resets_clock_and_clears_flag(self):
        req = self.make(hours=40)
        run_overdue_check()
        admin = self.client_for("admin@t.com")
        r = admin.patch(f"{BASE}/requests/{req.id}/status", {"status": "IN_PROGRESS"}, format="json").json()["data"]
        self.assertFalse(r["isOverdue"])
        run_overdue_check()
        req.refresh_from_db()
        self.assertFalse(req.overdue)

    def test_stale_flag_is_healed(self):
        req = self.make(hours=50, status="RESOLVED", overdue=True, overdue_at=timezone.now())
        self.assertEqual(run_overdue_check().cleared, 1)
        req.refresh_from_db()
        self.assertFalse(req.overdue)


class DashboardTests(ApiTestCase):
    def test_counts_cache_and_invalidation(self):
        self.make(hours=30)
        self.make(status="RESOLVED")
        run_overdue_check()
        admin = self.client_for("admin@t.com")
        first = admin.get(f"{BASE}/dashboard/summary")
        self.assertEqual(first.headers["X-Cache"], "MISS")
        data = first.json()["data"]
        self.assertEqual((data["totalRequests"], data["openRequests"], data["resolvedRequests"], data["overdueRequests"]), (2, 1, 1, 1))
        self.assertIsNotNone(data["lastOverdueCheckAt"])
        self.assertEqual(admin.get(f"{BASE}/dashboard/summary").headers["X-Cache"], "HIT")
        admin.post(f"{BASE}/requests", VALID, format="json")
        again = admin.get(f"{BASE}/dashboard/summary")
        self.assertEqual((again.headers["X-Cache"], again.json()["data"]["totalRequests"]), ("MISS", 3))
