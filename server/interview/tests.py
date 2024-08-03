import unittest
import random
import time
from algorithm import calculate_common_slots, stable_matching, calculate_preferences


class TestCalculateCommonSlots(unittest.TestCase):
    def test_no_common_slots(self):
        availability1 = [[False] * 48 for _ in range(7)]
        availability2 = [[False] * 48 for _ in range(7)]
        self.assertEqual(calculate_common_slots(availability1, availability2), 0)

    def test_all_common_slots(self):
        availability1 = [[True] * 48 for _ in range(7)]
        availability2 = [[True] * 48 for _ in range(7)]
        self.assertEqual(calculate_common_slots(availability1, availability2), 7 * 48)

    def test_some_common_slots(self):
        availability1 = [([True] * 24) + ([False] * 24) for _ in range(7)]
        availability2 = [([True] * 12) + ([False] * 36) for _ in range(7)]
        self.assertEqual(calculate_common_slots(availability1, availability2), 7 * 12)

    def test_different_days(self):
        availability1 = [[True] * 48 for _ in range(7)]
        availability2 = [[True] * 48 for _ in range(6)] + [[False] * 48]
        self.assertEqual(calculate_common_slots(availability1, availability2), 6 * 48)


class TestStableMatching(unittest.TestCase):
    def test_basic_matching(self):
        preferences = {0: [(1, 2), (2, 1)], 1: [(2, 1), (0, 2)], 2: [(0, 1), (1, 2)]}
        self.assertEqual(stable_matching(preferences), [2, 0, 1])

    def test_no_common_preferences(self):
        preferences = {0: [(1, 0)], 1: [(0, 0)]}
        self.assertEqual(stable_matching(preferences), [1, 0])

    def test_one_member(self):
        preferences = {0: []}
        with self.assertRaises(ValueError):
            stable_matching(preferences)

    def test_large_input(self):
        num_members = 300

        pool_member_ids = list(range(num_members))
        availabilities = {
            i: [[random.choice([True, False]) for __ in range(48)] for _ in range(7)]
            for i in pool_member_ids
        }
        start_time = time.perf_counter_ns()

        preferences = calculate_preferences(pool_member_ids, availabilities)

        stable_matching(preferences)
        end_time = time.perf_counter_ns()
        print(start_time, end_time)
        print(
            f"Time taken for stable_matching with {num_members} members: {(end_time - start_time)/1e6} ms"
        )

    def test_perfect_matching(self):
        availabilities = {
            0: [[True] * 24 + [False] * 24 for _ in range(7)],
            1: [[False] * 24 + [True] * 24 for _ in range(7)],
            2: [[True] * 24 + [False] * 24 for _ in range(7)],
            3: [[False] * 24 + [True] * 24 for _ in range(7)],
        }
        pool_member_ids = list(availabilities.keys())
        preferences = calculate_preferences(pool_member_ids, availabilities)
        self.assertEqual(stable_matching(preferences), [2, 3, 0, 1])

    def test_predictable_cases(self):
        availabilities = {
            0: [[True] * 48 for _ in range(7)],
            1: [[True] * 48 for _ in range(7)],
            2: [[False] * 48 for _ in range(7)],
            3: [[True] * 48 for _ in range(7)],
        }
        pool_member_ids = list(availabilities.keys())
        preferences = calculate_preferences(pool_member_ids, availabilities)
        # Expecting members with more availability to be matched first
        possible_expected_matchings = [[1, 0, 3, 2], [3, 2, 1, 0], [2, 3, 0, 1]]
        self.assertIn(stable_matching(preferences), possible_expected_matchings)


class TestCalculatePreferences(unittest.TestCase):
    def test_preferences_calculation(self):
        pool_member_ids = [0, 1, 2]
        availabilities = {
            0: [[True] * 48 for _ in range(7)],
            1: [[True] * 48 for _ in range(7)],
            2: [[False] * 48 for _ in range(7)],
        }
        expected_preferences_rankings = {0: [1, 2], 1: [0, 2], 2: [0, 1]}

        fail = False
        prefs = calculate_preferences(pool_member_ids, availabilities)

        for member, expected_rankings in expected_preferences_rankings.items():
            for i, (other_member, _) in enumerate(prefs[member]):
                if other_member != expected_rankings[i]:
                    fail = True
                    break
            if fail:
                break

        self.assertFalse(fail)

    def test_large_input(self):
        num_members = 100
        pool_member_ids = list(range(num_members))
        availabilities = {
            i: [[random.choice([True, False]) for __ in range(48)] for _ in range(7)]
            for i in pool_member_ids
        }
        start_time = time.perf_counter_ns()
        calculate_preferences(pool_member_ids, availabilities)
        end_time = time.perf_counter_ns()
        print(
            f"Time taken for calculate_preferences with {num_members} members: {(end_time - start_time)/1e6} ms"
        )


if __name__ == "__main__":
    unittest.main()
