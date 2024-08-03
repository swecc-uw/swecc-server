import numpy as np

def calculate_common_slots(availability1, availability2):
    availability1 = np.array(availability1, dtype=bool)
    availability2 = np.array(availability2, dtype=bool)

    common_slots = np.sum(np.logical_and(availability1, availability2))
    return common_slots

def calculate_common_slots_numpy(availability1, availability2):
    return np.sum(np.logical_and(availability1, availability2))

def stable_matching(preferences):
    n = len(preferences)

    if n < 2:
        raise ValueError("At least two members are required for matching")

    free_members = list(range(n))
    paired = [-1] * n

    preference_indices = {}
    for i, prefs in preferences.items():
        preference_indices[i] = {partner: idx for idx, (partner, _) in enumerate(prefs)}

    while free_members:
        member = free_members.pop(0)
        member_prefs = preferences[member]

        for partner, _ in member_prefs:
            # partner is free
            if paired[partner] == -1:
                paired[partner] = member
                break
            else:
                current_partner = paired[partner]
                # check if current member better than current partner
                if preference_indices[partner].get(member, float('inf')) < preference_indices[partner].get(current_partner, float('inf')):
                    paired[partner] = member
                    free_members.append(current_partner)
                    break
        else:
            free_members.append(member)

    return paired

def calculate_preferences(pool_member_ids, availabilities):
    num_members = len(pool_member_ids)
    preferences = {i: [] for i in range(num_members)}

    # convert to numpy arrays
    availability_arrays = {
        member_id: np.array(availabilities[member_id], dtype=bool)
        for member_id in pool_member_ids
    }

    # pre-compute common slots
    common_slots_matrix = np.zeros((num_members, num_members), dtype=int)
    for i in range(num_members):
        for j in range(i+1, num_members):
            common_slots = calculate_common_slots_numpy(
                availability_arrays[pool_member_ids[i]],
                availability_arrays[pool_member_ids[j]]
            )
            common_slots_matrix[i, j] = common_slots
            common_slots_matrix[j, i] = common_slots

    for i in range(num_members):
        for j in range(num_members):
            if i != j:
                preferences[i].append((j, common_slots_matrix[i, j]))

        # sort dec by number of common slots
        preferences[i] = sorted(preferences[i], key=lambda x: x[1], reverse=True)

    return preferences