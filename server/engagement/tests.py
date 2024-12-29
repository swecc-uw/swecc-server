from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
import pytz

from engagement.models import AttendanceSession

class AttendanceSessionTests(TestCase):
    def setUp(self):
        self.future_time = timezone.now() + timedelta(hours=1)
        self.past_time = timezone.now() - timedelta(hours=1)
        
    def test_expires_converts_to_utc(self):
        # Create session with non-UTC timezone
        est = pytz.timezone('US/Eastern')
        est_time = self.future_time.astimezone(est)
        
        session = AttendanceSession.objects.create(
            key="TEST123",
            title="Test Session",
            expires=est_time
        )
        
        # Verify timezone is UTC
        self.assertEqual(session.expires.tzinfo, timezone.utc)
        # Verify time value is equivalent
        self.assertEqual(session.expires, est_time.astimezone(timezone.utc))

    def test_unique_key_constraint_active_sessions(self):
        # Create first session
        AttendanceSession.objects.create(
            key="TEST123",
            title="Test Session 1",
            expires=self.future_time
        )
        
        # Attempt to create second session with same key
        with self.assertRaises(ValidationError):
            AttendanceSession.objects.create(
                key="TEST123",
                title="Test Session 2",
                expires=self.future_time
            )

    def test_allow_duplicate_key_for_expired_session(self):
        # Create expired session
        AttendanceSession.objects.create(
            key="TEST123",
            title="Test Session 1",
            expires=self.past_time
        )
        
        # Should be able to create new session with same key
        try:
            AttendanceSession.objects.create(
                key="TEST123",
                title="Test Session 2",
                expires=self.future_time
            )
        except ValidationError:
            self.fail("Should allow duplicate key for expired session")