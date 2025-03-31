from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

# to run tests, exec into docker container and run:
# `python server/manage.py test interview`


@dataclass
class MatchingResult:
    pairs: List[int]
    common_slots: NDArray[np.int_]
    preference_scores: Dict[int, List[Tuple[int, int]]]


class PairingAlgorithm(ABC):
    """'abstract' class for implementing pairing algorithms"""

    @abstractmethod
    def pair(self, pool_member_ids: List[int]) -> MatchingResult:
        """
        Pair members from the given pool.

        args: pool_member_ids: List of member IDs to be paired

        returns: MatchingResult containing pairs

        raises: NotImplementedError: If not implemented by child class
        """
        raise NotImplementedError


class CommonAvailabilityStableMatching(PairingAlgorithm):
    """
    stable matching impl based on common availability slots.
    """

    def __init__(self):
        self._availabilities: Optional[Dict[int, NDArray[np.bool_]]] = None

    def set_availabilities(self, availabilities: Dict[int, List[List[bool]]]) -> None:
        """
        set availabilities for all members.

        args:
            availabilities: Dictionary mapping member IDs to their availabilities

        raises:
            ValueError: If availabilities dict isn't provided or is empty
        """
        if not availabilities:
            raise ValueError("Availabilities dictionary cannot be empty")

        self._availabilities = {
            member_id: np.array(schedule, dtype=bool)
            for member_id, schedule in availabilities.items()
        }

    def calculate_common_slots_numpy(
        self, availability1: np.ndarray, availability2: np.ndarray
    ) -> int:
        """
        calculate common slots between two availabilities.
        """
        return np.sum(np.logical_and(availability1, availability2))

    def _validate_input(
        self, pool_member_ids: List[int], require_even: bool = True
    ) -> None:
        """
        validate input parameters for the pairing algorithm.

        args:
            pool_member_ids: List of member IDs to validate
            require_even: Whether to require an even number of members

        raises:
            ValueError: If input parameters are invalid
        """
        if not pool_member_ids:
            raise ValueError("Pool member IDs list cannot be empty")
        if require_even and len(pool_member_ids) % 2 != 0:
            raise ValueError("Number of members must be even")
        if len(pool_member_ids) < 2:
            raise ValueError("At least two members are required for matching")
        if len(set(pool_member_ids)) != len(pool_member_ids):
            raise ValueError("Duplicate member IDs are not allowed")

    def pair(self, pool_member_ids: List[int]) -> MatchingResult:
        """
        pair members based on common availability slots. Number of members must be even.
        """
        self._validate_input(pool_member_ids)

        if not self._availabilities:
            raise ValueError("Availabilities must be set before pairing")

        if not all(mid in self._availabilities for mid in pool_member_ids):
            raise ValueError("All pool members must have availabilities")

        common_slots = self._calculate_common_slots_matrix(pool_member_ids)
        preferences = self._calculate_preferences(pool_member_ids, common_slots)
        pairs = self._stable_matching(preferences)

        return MatchingResult(
            pairs=pairs, common_slots=common_slots, preference_scores=preferences
        )

    def _calculate_common_slots_matrix(
        self, pool_member_ids: List[int]
    ) -> NDArray[np.int_]:
        num_members = len(pool_member_ids)
        common_slots = np.zeros((num_members, num_members), dtype=np.int_)

        for i in range(num_members):
            availability1 = self._availabilities[pool_member_ids[i]]

            for j in range(i + 1, num_members):
                availability2 = self._availabilities[pool_member_ids[j]]
                common_count = self.calculate_common_slots_numpy(
                    availability1, availability2
                )
                common_slots[i, j] = common_count
                common_slots[j, i] = common_count

        return common_slots

    def calculate_preferences(
        self, pool_member_ids: List[int], availabilities: Dict[int, List[List[bool]]]
    ) -> Dict[int, List[Tuple[int, int]]]:
        """
        calculate preference lists for all members based on common availability.
        """
        self.set_availabilities(availabilities)
        self._validate_input(pool_member_ids, require_even=False)

        common_slots = self._calculate_common_slots_matrix(pool_member_ids)
        return self._calculate_preferences(pool_member_ids, common_slots)

    def _calculate_preferences(
        self, pool_member_ids: List[int], common_slots: NDArray[np.int_]
    ) -> Dict[int, List[Tuple[int, int]]]:
        num_members = len(pool_member_ids)
        preferences: Dict[int, List[Tuple[int, int]]] = {}

        for i in range(num_members):
            prefs = [(j, common_slots[i, j]) for j in range(num_members) if i != j]
            preferences[i] = sorted(prefs, key=lambda x: (x[1], -x[0]), reverse=True)

        return preferences

    def _stable_matching(
        self, preferences: Dict[int, List[Tuple[int, int]]]
    ) -> List[int]:
        """
        Gale-Shapley algorithm for stable matching.
        """
        n = len(preferences)

        free_members = deque(range(n))
        paired = [-1] * n

        preference_indices = {
            i: {partner: idx for idx, (partner, _) in enumerate(prefs)}
            for i, prefs in preferences.items()
        }

        while free_members:
            member = free_members.popleft()
            if not preferences[member]:
                free_members.append(member)
                continue

            for partner, _ in preferences[member]:
                if paired[partner] == -1:
                    paired[partner] = member
                    break
                else:
                    current_partner = paired[partner]
                    if preference_indices[partner].get(
                        member, float("inf")
                    ) < preference_indices[partner].get(current_partner, float("inf")):
                        paired[partner] = member
                        free_members.append(current_partner)
                        break
            else:
                free_members.append(member)

        return paired
