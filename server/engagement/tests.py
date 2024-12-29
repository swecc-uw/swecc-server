from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta, datetime
from .models import AttendanceSession
from members.models import User
from unittest.mock import patch


class AuthenticatedTestCase(TestCase):
    """Base test case that automatically mocks authentication"""
    def setUp(self):
        super().setUp()
        self.api_patcher = patch('members.permissions.IsApiKey.has_permission')
        self.admin_patcher = patch('custom_auth.permissions.IsAdmin.has_permission')
        
        # Start the patchers
        self.mock_api_perm = self.api_patcher.start()
        self.mock_admin_perm = self.admin_patcher.start()
        
        # Set return values
        self.mock_api_perm.return_value = True
        self.mock_admin_perm.return_value = True

    def tearDown(self):
        super().tearDown()
        # Stop the patchers
        self.api_patcher.stop()
        self.admin_patcher.stop()

    def assertResponse(self, response, expected_status):
        """Helper method to assert response status with detailed error message"""
        try:
            self.assertEqual(
                response.status_code, 
                expected_status,
                f"Expected status {expected_status}, got {response.status_code}. Response data: {response.data}"
            )
        except AttributeError:
            self.assertEqual(
                response.status_code, 
                expected_status,
                f"Expected status {expected_status}, got {response.status_code}. Response content: {response.content}"
            )

class AttendanceAPITests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        # Create test user
        self.user = User.objects.create(
            discord_id="123456789",
            discord_username="test_user"
        )
        # Create test session
        self.session = AttendanceSession.objects.create(
            title="Test Session",
            key="test-key",
            expires=(timezone.now() + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        )
        self.expired_session = AttendanceSession.objects.create(
            title="Expired Session",
            key="expired-key",
            expires=(timezone.now() - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        )

    def test_create_session(self):
        response = self.client.post('/engagement/attendance/session', {
            'title': 'New Session',
            'key': 'new-key',
            'expires': (timezone.now() + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        })
        self.assertResponse(response, 201)
        self.assertTrue(
            AttendanceSession.objects.filter(title='New Session').exists(),
            "Session was not created in database"
        )
    
    def test_create_duplicate_active_session(self):
        response = self.client.post('/engagement/attendance/session', {
            'title': 'New Session',
            'key': 'test-key',
            'expires': (timezone.now() + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        })
        self.assertResponse(response, 400)
    
    def test_create_duplicate_expired_session(self):
        response = self.client.post('/engagement/attendance/session', {
            'title': 'New Session',
            'key': 'expired-key',
            'expires': (timezone.now() - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        })
        self.assertResponse(response, 201)

    def test_get_all_sessions(self):
        response = self.client.get('/engagement/attendance/')
        self.assertResponse(response, 200)
        self.assertEqual(
            len(response.data), 
            2,
            f"Expected 2 sessions, got {len(response.data)}. Data: {response.data}"
        )

    def test_get_member_sessions(self):
        self.session.attendees.add(self.user)
        response = self.client.get(f'/engagement/attendance/member/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_session_attendees(self):
        self.session.attendees.add(self.user)
        response = self.client.get(f'/engagement/attendance/session/{self.session.session_id}/')
        self.assertResponse(response, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.user.id)

    def test_attend_session(self):
        response = self.client.post('/engagement/attendance/attend', {
            'session_key': 'test-key',
            'discord_id': '123456789'
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.session.attendees.filter(id=self.user.id).exists())

    def test_attend_expired_session(self):
        response = self.client.post('/engagement/attendance/attend', {
            'session_key': 'expired-key',
            'discord_id': '123456789'
        })
        self.assertResponse(response, 400)
        self.assertEqual(
            response.data['error'],
            'Session has expired',
            f"Unexpected error message: {response.data}"
        )

    def test_attend_nonexistent_session(self):
        response = self.client.post('/engagement/attendance/attend', {
            'session_key': 'nonexistent-key',
            'discord_id': '123456789'
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'Session not found')

    def test_attend_nonexistent_member(self):
        response = self.client.post('/engagement/attendance/attend', {
            'session_key': 'test-key',
            'discord_id': '999999999'
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'Member not found')
