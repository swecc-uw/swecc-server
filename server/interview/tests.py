import random

import numpy as np
from django.test import TestCase
from django.utils import timezone
from interview.algorithm import CommonAvailabilityStableMatching


class TestCommonAvailabilityStableMatching(TestCase):
    def setUp(self):
        self.algorithm = CommonAvailabilityStableMatching()

    def test_calculate_common_slots_numpy(self):
        availability1 = np.array([[False] * 48 for _ in range(7)], dtype=bool)
        availability2 = np.array([[False] * 48 for _ in range(7)], dtype=bool)
        self.assertEqual(
            self.algorithm.calculate_common_slots_numpy(availability1, availability2), 0
        )

        availability1 = np.array([[True] * 48 for _ in range(7)], dtype=bool)
        availability2 = np.array([[True] * 48 for _ in range(7)], dtype=bool)
        self.assertEqual(
            self.algorithm.calculate_common_slots_numpy(availability1, availability2),
            7 * 48,
        )

        availability1 = np.array(
            [([True] * 24) + ([False] * 24) for _ in range(7)], dtype=bool
        )
        availability2 = np.array(
            [([True] * 12) + ([False] * 36) for _ in range(7)], dtype=bool
        )
        self.assertEqual(
            self.algorithm.calculate_common_slots_numpy(availability1, availability2),
            7 * 12,
        )

        availability1 = np.array([[True] * 48 for _ in range(7)], dtype=bool)
        availability2 = np.array(
            [[True] * 48 for _ in range(6)] + [[False] * 48], dtype=bool
        )
        self.assertEqual(
            self.algorithm.calculate_common_slots_numpy(availability1, availability2),
            6 * 48,
        )

    def test_stable_matching_two_members(self):
        availabilities = {
            0: [[True] * 48 for _ in range(7)],
            1: [[True] * 48 for _ in range(7)],
        }
        self.algorithm.set_availabilities(availabilities)
        result = self.algorithm.pair([0, 1])
        self.assertEqual(result.pairs, [1, 0])

        with self.assertRaises(ValueError):
            self.algorithm.pair([0])

    def test_large_input(self):
        num_members = 200
        pool_member_ids = list(range(num_members))
        availabilities = {
            i: [[random.choice([True, False]) for __ in range(48)] for _ in range(7)]
            for i in pool_member_ids
        }
        start_time = timezone.now()
        self.algorithm.set_availabilities(availabilities)
        result = self.algorithm.pair(pool_member_ids)
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds() * 1000
        print(f"Time taken for pairing with {num_members} members: {duration:.2f} ms")

        self.assertEqual(len(result.pairs), num_members)

    def test_perfect_matching(self):
        availabilities = {
            0: [[True] * 24 + [False] * 24 for _ in range(7)],
            1: [[False] * 24 + [True] * 24 for _ in range(7)],
            2: [[True] * 24 + [False] * 24 for _ in range(7)],
            3: [[False] * 24 + [True] * 24 for _ in range(7)],
        }
        pool_member_ids = list(availabilities.keys())
        self.algorithm.set_availabilities(availabilities)
        result = self.algorithm.pair(pool_member_ids)
        self.assertEqual(result.pairs, [2, 3, 0, 1])

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
        result = self.algorithm.pair(pool_member_ids)
        self.assertIn(result.pairs, possible_expected_matchings)

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

    def _pair_large_input_calculate_preferences(self, num_members=200):
        pool_member_ids = list(range(num_members))
        availabilities = {
            i: [[random.choice([True, False]) for __ in range(48)] for _ in range(7)]
            for i in pool_member_ids
        }
        start_time = timezone.now()
        prefs = self.algorithm.calculate_preferences(pool_member_ids, availabilities)
        pairs = self.algorithm.pair(pool_member_ids)
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds() * 1000
        print(f"Time taken for pairing {num_members} members: {duration:.2f} ms")
        self.assertEqual(len(prefs), num_members)
        self.assertEqual(len(pairs.pairs), num_members)

    def test_trend_in_clock_time(self):

        for num_members in [10, 20, 50, 100, 200, 500, 1000, 2000]:
            self._pair_large_input_calculate_preferences(num_members)
