import unittest
import random
import time
import numpy as np
from typing import Dict, List
from .algorithm import CommonAvailabilityStableMatching

class TestCommonAvailabilityStableMatching(unittest.TestCase):
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
        preferences = {0: [(1, 2), (2, 1)], 1: [(2, 1), (0, 2)], 2: [(0, 1), (1, 2)]}
        self.assertEqual(self.algorithm.stable_matching(preferences), [2, 0, 1])

        preferences = {0: [(1, 0)], 1: [(0, 0)]}
        self.assertEqual(self.algorithm.stable_matching(preferences), [1, 0])

        preferences = {0: []}
        with self.assertRaises(ValueError):
            self.algorithm.stable_matching(preferences)

    def test_large_input(self):
        num_members = 2000
        pool_member_ids = list(range(num_members))
        availabilities = {
            i: [[random.choice([True, False]) for __ in range(48)] for _ in range(7)]
            for i in pool_member_ids
        }
        start_time = time.perf_counter_ns()
        self.algorithm.set_availabilities(availabilities)
        self.algorithm.pair(pool_member_ids)
        end_time = time.perf_counter_ns()
        print(f"Time taken for pairing with {num_members} members: {(end_time - start_time)/1e6} ms")

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
        start_time = time.perf_counter_ns()
        self.algorithm.calculate_preferences(pool_member_ids, availabilities)
        end_time = time.perf_counter_ns()
        print(f"Time taken for calculate_preferences with {num_members} members: {(end_time - start_time)/1e6} ms")

if __name__ == "__main__":
    unittest.main()