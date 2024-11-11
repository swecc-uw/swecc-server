import unittest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from questions.models import BehavioralQuestion, QuestionTopic, TechnicalQuestion
from .models import Interview
from .algorithm import CommonAvailabilityStableMatching
import random
import numpy as np

class TestCommonAvailabilityStableMatching(TestCase):
    def setUp(self):
        self.algorithm = CommonAvailabilityStableMatching()

    def test_calculate_common_slots_numpy(self):
        availability1 = np.array([[False] * 48 for _ in range(7)], dtype=bool)
        availability2 = np.array([[False] * 48 for _ in range(7)], dtype=bool)
        self.assertEqual(self.algorithm.calculate_common_slots_numpy(availability1, availability2), 0)

        availability1 = np.array([[True] * 48 for _ in range(7)], dtype=bool)
        availability2 = np.array([[True] * 48 for _ in range(7)], dtype=bool)
        self.assertEqual(self.algorithm.calculate_common_slots_numpy(availability1, availability2), 7 * 48)

        availability1 = np.array([([True] * 24) + ([False] * 24) for _ in range(7)], dtype=bool)
        availability2 = np.array([([True] * 12) + ([False] * 36) for _ in range(7)], dtype=bool)
        self.assertEqual(self.algorithm.calculate_common_slots_numpy(availability1, availability2), 7 * 12)

        availability1 = np.array([[True] * 48 for _ in range(7)], dtype=bool)
        availability2 = np.array([[True] * 48 for _ in range(6)] + [[False] * 48], dtype=bool)
        self.assertEqual(self.algorithm.calculate_common_slots_numpy(availability1, availability2), 6 * 48)

    def test_stable_matching(self):
        preferences = {0: [(1, 0)], 1: [(0, 0)]}
        self.assertEqual(self.algorithm.stable_matching(preferences), [1, 0])

        preferences = {0: []}
        with self.assertRaises(ValueError):
            self.algorithm.stable_matching(preferences)

    def test_large_input(self):
        num_members = 200
        pool_member_ids = list(range(num_members))
        availabilities = {
            i: [[random.choice([True, False]) for __ in range(48)] for _ in range(7)]
            for i in pool_member_ids
        }
        start_time = timezone.now()
        self.algorithm.set_availabilities(availabilities)
        self.algorithm.pair(pool_member_ids)
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds() * 1000
        print(f"Time taken for pairing with {num_members} members: {duration:.2f} ms")

    def test_perfect_matching(self):
        availabilities = {
            0: [[True] * 24 + [False] * 24 for _ in range(7)],
            1: [[False] * 24 + [True] * 24 for _ in range(7)],
            2: [[True] * 24 + [False] * 24 for _ in range(7)],
            3: [[False] * 24 + [True] * 24 for _ in range(7)],
        }
        pool_member_ids = list(availabilities.keys())
        self.algorithm.set_availabilities(availabilities)
        self.assertEqual(self.algorithm.pair(pool_member_ids), [2, 3, 0, 1])

    def test_predictable_cases(self):
        availabilities = {
            0: [[True] * 48 for _ in range(7)],
            1: [[True] * 48 for _ in range(7)],
            2: [[False] * 48 for _ in range(7)],
            3: [[True] * 48 for _ in range(7)],
        }
        pool_member_ids = list(availabilities.keys())
        possible_expected_matchings = [[1, 0, 3, 2], [3, 2, 1, 0], [2, 3, 0, 1]]
        self.algorithm.set_availabilities(availabilities)
        self.assertIn(self.algorithm.pair(pool_member_ids), possible_expected_matchings)

    def test_calculate_preferences(self):
        pool_member_ids = [0, 1, 2]
        availabilities = {
            0: [[True] * 48 for _ in range(7)],
            1: [[True] * 48 for _ in range(7)],
            2: [[False] * 48 for _ in range(7)],
        }
        expected_preferences_rankings = {0: [1, 2], 1: [0, 2], 2: [0, 1]}

        prefs = self.algorithm.calculate_preferences(pool_member_ids, availabilities)

        for member, expected_rankings in expected_preferences_rankings.items():
            calculated_rankings = [other_member for other_member, _ in prefs[member]]
            self.assertEqual(calculated_rankings, expected_rankings)

    def test_large_input_calculate_preferences(self):
        num_members = 100
        pool_member_ids = list(range(num_members))
        availabilities = {
            i: [[random.choice([True, False]) for __ in range(48)] for _ in range(7)]
            for i in pool_member_ids
        }
        start_time = timezone.now()
        self.algorithm.calculate_preferences(pool_member_ids, availabilities)
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds() * 1000
        print(f"Time taken for calculate_preferences with {num_members} members: {duration:.2f} ms")



# ignore these for now
User = get_user_model()
@unittest.skip("Skipping Interview tests")
class InterviewLifecycleTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.interviewer = User.objects.create_user(username='interviewer', password='password')
        self.interviewee = User.objects.create_user(username='interviewee', password='password')
        self.technical_questions = TechnicalQuestion.objects.create(
            created_by=self.interviewer,
            prompt='Prompt',
            solution='Solution',
            topic=QuestionTopic.objects.create(name='Topic')
        )
        self.behavioral_question = BehavioralQuestion.objects.create(
            created_by=self.interviewer,
            prompt='Prompt',
            solution='Solution'
        )
        self.interview = Interview.objects.create(
            interviewer=self.interviewer,
            interviewee=self.interviewee,
            date_effective=timezone.now()
        )
        self.interview.behavioral_questions.add(self.behavioral_question)
        self.interview.technical_questions = self.technical_questions

    def test_propose_view(self):
        self.client.force_authenticate(user=self.interviewer)
        url = reverse('interview-propose', kwargs={'interview_id': self.interview.interview_id})
        proposed_time = timezone.now() + timezone.timedelta(days=1)
        data = {'time': proposed_time.isoformat()}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.interview.refresh_from_db()
        self.assertEqual(self.interview.proposed_time, proposed_time)
        self.assertEqual(self.interview.proposed_by, self.interviewer)
        self.assertEqual(self.interview.status, 'pending')

    def test_commit_view(self):
        self.client.force_authenticate(user=self.interviewee)
        url = reverse('interview-commit', kwargs={'interview_id': self.interview.interview_id})
        proposed_time = timezone.now() + timezone.timedelta(days=1)
        self.interview.proposed_time = proposed_time
        self.interview.proposed_by = self.interviewer
        self.interview.save()

        data = {'time': proposed_time.isoformat()}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.interview.refresh_from_db()
        self.assertEqual(self.interview.committed_time, proposed_time)
        self.assertEqual(self.interview.status, 'active')
        self.assertIsNone(self.interview.proposed_time)
        self.assertIsNone(self.interview.proposed_by)

    def test_complete_view(self):
        self.client.force_authenticate(user=self.interviewee)
        url = reverse('interview-complete', kwargs={'interview_id': self.interview.interview_id})
        self.interview.status = 'inactive_unconfirmed'
        self.interview.save()

        completion_time = timezone.now()
        data = {'time': completion_time.isoformat()}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.interview.refresh_from_db()
        self.assertEqual(self.interview.status, 'inactive_completed')
        self.assertEqual(self.interview.date_completed, completion_time)

    def test_complete_view_without_time(self):
        self.client.force_authenticate(user=self.interviewee)
        url = reverse('interview-complete', kwargs={'interview_id': self.interview.interview_id})
        self.interview.status = 'inactive_unconfirmed'
        self.interview.save()

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.interview.refresh_from_db()
        self.assertEqual(self.interview.status, 'inactive_incomplete')
        self.assertIsNotNone(self.interview.date_completed)

    def test_propose_view_invalid_status(self):
        self.client.force_authenticate(user=self.interviewer)
        url = reverse('interview-propose', kwargs={'interview_id': self.interview.interview_id})
        self.interview.status = 'inactive_completed'
        self.interview.save()

        data = {'time': timezone.now().isoformat()}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_commit_view_invalid_user(self):
        self.client.force_authenticate(user=self.interviewer)
        url = reverse('interview-commit', kwargs={'interview_id': self.interview.interview_id})
        self.interview.proposed_time = timezone.now()
        self.interview.proposed_by = self.interviewer
        self.interview.save()

        data = {'time': self.interview.proposed_time.isoformat()}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_view_invalid_status(self):
        self.client.force_authenticate(user=self.interviewee)
        url = reverse('interview-complete', kwargs={'interview_id': self.interview.interview_id})
        self.interview.status = 'active'
        self.interview.save()

        data = {'time': timezone.now().isoformat()}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)