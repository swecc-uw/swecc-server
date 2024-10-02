from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, List, Tuple

class PairingAlgorithm(ABC):
    @abstractmethod
    def pair(self, pool_member_ids: List[int]) -> List[int]:
        pass

class CommonAvailabilityStableMatching(PairingAlgorithm):
    def set_availabilities(self, availabilities: Dict[int, List[List[bool]]]):
        self.availabilities = availabilities

    def pair(self, pool_member_ids: List[int]) -> List[int]:
        availabilities = self.availabilities
        preferences = self.calculate_preferences(pool_member_ids, availabilities)
        return self.stable_matching(preferences)

    def calculate_common_slots_numpy(self, availability1: np.ndarray, availability2: np.ndarray) -> int:
        return np.sum(np.logical_and(availability1, availability2))

    def stable_matching(self, preferences: Dict[int, List[Tuple[int, int]]]) -> List[int]:
        n = len(preferences)
        if n < 2:
            raise ValueError("At least two members are required for matching")

        free_members = list(range(n))
        paired = [-1] * n
        preference_indices = {}
        for i, prefs in preferences.items():
            preference_indices[i] = {partner: idx for idx, (partner, _) in enumerate(prefs)}

        while len(free_members) > 1:
            member = free_members.pop(0)
            member_prefs = preferences[member]
            for partner, _ in member_prefs:
                if paired[partner] == -1:
                    paired[partner] = member
                    break
                else:
                    current_partner = paired[partner]
                    if preference_indices[partner].get(member, float('inf')) < preference_indices[partner].get(current_partner, float('inf')):
                        paired[partner] = member
                        free_members.append(current_partner)
                        break
            else:
                free_members.append(member)

        return paired

    def calculate_preferences(self, pool_member_ids: List[int], availabilities: Dict[int, List[List[bool]]]) -> Dict[int, List[Tuple[int, int]]]:
        num_members = len(pool_member_ids)
        preferences = {i: [] for i in range(num_members)}

        availability_arrays = {
            member_id: np.array(availabilities[member_id], dtype=bool)
            for member_id in pool_member_ids
        }

        common_slots_matrix = np.zeros((num_members, num_members), dtype=int)
        for i in range(num_members):
            for j in range(i+1, num_members):
                common_slots = self.calculate_common_slots_numpy(
                    availability_arrays[pool_member_ids[i]],
                    availability_arrays[pool_member_ids[j]]
                )
                common_slots_matrix[i, j] = common_slots
                common_slots_matrix[j, i] = common_slots

        for i in range(num_members):
            for j in range(num_members):
                if i != j:
                    preferences[i].append((j, common_slots_matrix[i, j]))
            preferences[i] = sorted(preferences[i], key=lambda x: x[1], reverse=True)

        return preferences