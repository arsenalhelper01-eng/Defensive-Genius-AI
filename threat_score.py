
# DEFENSIVE GENIUS - THREAT SCORING

THREAT_POINTS = {
    "tank": 5,
    "air": 4,
    "support": 3,
    "swarm": 3,
    "fast": 3,
    "ground": 1,
    "bait": 2,
    "win_condition": 4,
    "unknown": 1
}


def calculate_danger(threats):
    score = 0

    for _, threat in threats:
        categories = threat if isinstance(threat, (list, tuple, set)) else [threat]
        category_score = sum(
            THREAT_POINTS.get(category, 1) for category in set(categories)
        )
        score += category_score or 1

    if len(threats) >= 3:
        score += 3

    if any(
        "tank" in (threat if isinstance(threat, (list, tuple, set)) else [threat])
        for _, threat in threats
    ):
        if any(
            "support" in (threat if isinstance(threat, (list, tuple, set)) else [threat])
            for _, threat in threats
        ):
            score += 5

    return score


def danger_level(score):
    if score >= 15:
        return "EXTREME"
    elif score >= 10:
        return "HIGH"
    elif score >= 5:
        return "MODERATE"

    return "LOW"
