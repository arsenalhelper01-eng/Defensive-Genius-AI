# DEFENSIVE GENIUS - DEFENSE PLANNER

from itertools import combinations

from threats import recognize_threats


DECK = (
    "Evolution Tesla",
    "Hero Musketeer",
    "Evolution Ice Spirit",
    "Hog Rider",
    "Knight",
    "Skeletons",
    "Fireball",
    "Log",
)

# Effectiveness values are heuristic matchup weights, not win probabilities.
CARD_DATA = {
    "Evolution Tesla": {
        "cost": 4,
        "targets": frozenset({"air", "ground"}),
        "effectiveness": {
            "tank": 0.78,
            "ground": 0.42,
            "fast": 0.45,
            "air": 0.62,
            "win_condition": 0.68,
            "support": 0.16,
            "swarm": 0.18,
        },
        "job": "Pull and damage threats with a defensive building.",
    },
    "Hero Musketeer": {
        "cost": 4,
        "targets": frozenset({"air", "ground"}),
        "effectiveness": {
            "tank": 0.20,
            "ground": 0.35,
            "fast": 0.18,
            "air": 0.86,
            "win_condition": 0.50,
            "support": 0.62,
            "swarm": 0.12,
        },
        "job": "Provide sustained ranged damage, especially against air.",
    },
    "Evolution Ice Spirit": {
        "cost": 1,
        "targets": frozenset({"air", "ground"}),
        "effectiveness": {
            "tank": 0.08,
            "ground": 0.14,
            "fast": 0.30,
            "air": 0.25,
            "win_condition": 0.10,
            "support": 0.18,
            "swarm": 0.32,
            "bait": 0.12,
        },
        "job": "Briefly freeze or interrupt a threat to buy time; not a solo stopper.",
    },
    "Knight": {
        "cost": 3,
        "targets": frozenset({"ground"}),
        "effectiveness": {
            "tank": 0.32,
            "ground": 0.38,
            "fast": 0.25,
            "win_condition": 0.18,
            "support": 0.48,
            "swarm": 0.10,
        },
        "job": "Absorb damage and contest a ground troop.",
    },
    "Skeletons": {
        "cost": 1,
        "targets": frozenset({"ground"}),
        "effectiveness": {
            "tank": 0.28,
            "ground": 0.20,
            "fast": 0.12,
            "win_condition": 0.10,
            "support": 0.05,
        },
        "job": "Distract a ground threat briefly; fragile and timing-dependent.",
    },
    "Fireball": {
        "cost": 4,
        "targets": frozenset({"air", "ground"}),
        "effectiveness": {
            "tank": 0.08,
            "ground": 0.18,
            "fast": 0.12,
            "air": 0.22,
            "win_condition": 0.20,
            "support": 0.72,
            "swarm": 0.30,
            "bait": 0.20,
        },
        "job": "Damage clustered troops; a hit is not a guaranteed kill.",
    },
    "Log": {
        "cost": 2,
        "targets": frozenset({"ground"}),
        "effectiveness": {
            "ground": 0.15,
            "fast": 0.10,
            "win_condition": 0.10,
            "support": 0.12,
            "swarm": 0.65,
            "bait": 0.70,
        },
        "job": "Clear or knock back ground swarms; it cannot hit air troops.",
    },
}

CARD_ALIASES = {
    "tesla": "Evolution Tesla",
    "evolution tesla": "Evolution Tesla",
    "ice spirit": "Evolution Ice Spirit",
    "evolution ice spirit": "Evolution Ice Spirit",
    "musketeer": "Hero Musketeer",
    "hero musketeer": "Hero Musketeer",
}

def _normalize_card(card):
    normalized = str(card).strip()
    return CARD_ALIASES.get(normalized.lower(), normalized)


def _normalize_enemy(enemy):
    """Accept card names, legacy (card, role) pairs, or state dictionaries."""
    profiles = []
    for item in enemy:
        supplied_categories = None
        seconds_to_tower = None
        lane = None
        if isinstance(item, str):
            card = item.strip()
        elif isinstance(item, dict):
            card = str(item.get("card", "")).strip()
            supplied_categories = item.get("categories")
            seconds_to_tower = item.get("seconds_to_tower")
            lane = item.get("lane")
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            card = str(item[0]).strip()
            supplied_categories = item[1]
            if len(item) >= 3 and isinstance(item[2], dict):
                seconds_to_tower = item[2].get("seconds_to_tower")
                lane = item[2].get("lane")
        else:
            card = str(item).strip()

        categories = recognize_threats(card)
        if not categories and supplied_categories:
            categories = (
                [supplied_categories]
                if isinstance(supplied_categories, str)
                else list(supplied_categories)
            )
        try:
            if seconds_to_tower is not None:
                seconds_to_tower = float(seconds_to_tower)
                if seconds_to_tower < 0:
                    seconds_to_tower = None
        except (TypeError, ValueError):
            seconds_to_tower = None
        profiles.append(
            {
                "card": card or "Unknown",
                "categories": categories,
                "seconds_to_tower": seconds_to_tower,
                "lane": str(lane).strip().lower() if lane else None,
            }
        )
    return profiles


def _card_effectiveness(card, enemy):
    categories = enemy["categories"]
    target_type = "air" if "air" in categories else "ground"
    if target_type not in CARD_DATA[card]["targets"]:
        return 0.0
    return max(
        (CARD_DATA[card]["effectiveness"].get(category, 0) for category in categories),
        default=0.0,
    )


def _threat_weight(enemy):
    categories = enemy["categories"]
    weight = 1.0
    if "tank" in categories:
        weight += 0.35
    if "win_condition" in categories:
        weight += 0.25
    if "air" in categories:
        weight += 0.20
    if "support" in categories:
        weight += 0.10
    if "swarm" in categories:
        weight += 0.10
    if enemy["card"].lower() == "balloon":
        weight = max(weight, 1.8)

    seconds = enemy["seconds_to_tower"]
    if seconds is not None:
        if seconds <= 3:
            weight *= 2.5
        elif seconds <= 6:
            weight *= 1.8
        elif seconds <= 10:
            weight *= 1.25
    return weight


def _threat_outcomes(profiles, cards):
    outcomes = []
    for enemy in profiles:
        effects = {
            card: _card_effectiveness(card, enemy)
            for card in cards
        }
        remaining_fraction = 1.0
        for effect in effects.values():
            remaining_fraction *= 1.0 - effect
        coverage = 1.0 - remaining_fraction
        if coverage >= 0.75:
            status = "strongly contested; may still survive"
        elif coverage >= 0.30:
            status = "partially contested; may survive"
        else:
            status = "likely remains a threat"
        outcomes.append(
            {
                "card": enemy["card"],
                "coverage": coverage,
                "status": status,
                "seconds_to_tower": enemy["seconds_to_tower"],
                "lane": enemy["lane"],
                "contributed_by": [
                    card for card, effect in effects.items() if effect >= 0.18
                ],
            }
        )
    return outcomes


def _plan_score(profiles, cards):
    outcomes = _threat_outcomes(profiles, cards)
    threat_value = sum(
        _threat_weight(enemy) * outcome["coverage"]
        for enemy, outcome in zip(profiles, outcomes)
    )
    cost = sum(CARD_DATA[card]["cost"] for card in cards)
    # A modest cost penalty breaks ties in favor of efficient, smaller defenses.
    return threat_value - (0.065 * cost) - (0.03 * len(cards))


def _card_job(card, profiles):
    matches = [
        enemy["card"]
        for enemy in profiles
        if _card_effectiveness(card, enemy) >= 0.18
    ]
    job = CARD_DATA[card]["job"]
    if not matches:
        return job
    return f"{job} Contributes against: {', '.join(matches)}."


def _placement_and_timing(card, profiles):
    relevant = [
        enemy for enemy in profiles
        if _card_effectiveness(card, enemy) >= 0.18
    ]
    if not relevant:
        return None, None

    known_lanes = sorted({enemy["lane"] for enemy in relevant if enemy["lane"]})
    known_times = [
        enemy["seconds_to_tower"]
        for enemy in relevant
        if enemy["seconds_to_tower"] is not None
    ]

    placement = None
    if len(known_lanes) > 1:
        placement = (
            "Threats span multiple lanes; one placement cannot be chosen "
            "reliably from this information."
        )
    elif known_lanes:
        if card == "Evolution Tesla":
            placement = (
                f"Place centrally to pull threats from the {known_lanes[0]} lane; "
                "the exact tile depends on the troop path."
            )
        elif card in ("Hero Musketeer", "Knight"):
            placement = (
                f"Deploy on the threatened {known_lanes[0]} side, behind the tower "
                "or at a safe intercept point."
            )
        elif card == "Evolution Ice Spirit":
            placement = (
                f"Deploy into the {known_lanes[0]}-lane engagement to buy a brief "
                "freeze window."
            )
        elif card == "Skeletons":
            placement = (
                f"Place at a ground-threat intercept on the {known_lanes[0]} lane; "
                "avoid placing too early."
            )
        elif card == "Fireball":
            placement = (
                f"Aim to catch clustered troops on the {known_lanes[0]} lane; "
                "only use if they are within spell radius."
            )
        elif card == "Log":
            placement = (
                f"Roll along the {known_lanes[0]}-lane path after ground troops "
                "line up."
            )

    timing = None
    if known_times:
        earliest = min(known_times)
        if earliest <= 3:
            timing = (
                f"Deploy immediately; estimated tower contact is in {earliest:g}s. "
                "The estimate excludes deployment and travel time."
            )
        elif earliest <= 7:
            timing = (
                f"Prepare now and deploy before contact (estimated {earliest:g}s); "
                "avoid spending the card too early."
            )
        else:
            timing = (
                f"Threat is estimated {earliest:g}s from tower contact; wait for a "
                "better commitment if safe."
            )
    elif known_lanes:
        timing = "Exact timing unavailable because time-to-tower was not supplied."

    if not placement and known_times:
        placement = "Exact placement unavailable because no lane was supplied."
    return placement, timing


def recommend_defense(enemy, elixir, hand=None):
    """Return a coordinated, affordable defense plan with explicit limitations."""
    if not isinstance(elixir, (int, float)) or not 0 <= elixir <= 10:
        raise ValueError("Elixir must be between 0 and 10.")

    profiles = _normalize_enemy(enemy)
    source_cards = DECK if hand is None else hand
    candidates = []
    for raw_card in source_cards:
        card = _normalize_card(raw_card)
        if card in CARD_DATA and card not in candidates:
            candidates.append(card)
    # Hog Rider remains reserved for counter-pushing, not primary defense.
    candidates = [card for card in candidates if card != "Hog Rider"]
    affordable = [
        card for card in candidates
        if CARD_DATA[card]["cost"] <= elixir
    ]

    plan_cards = []
    if affordable and profiles:
        best_score = 0.0
        for size in range(1, len(affordable) + 1):
            for card_set in combinations(affordable, size):
                score = _plan_score(profiles, card_set)
                if score > best_score:
                    best_score = score
                    plan_cards = list(card_set)

    outcomes = _threat_outcomes(profiles, plan_cards)
    total_cost = sum(CARD_DATA[card]["cost"] for card in plan_cards)
    card_actions = []
    for card in plan_cards:
        placement, timing = _placement_and_timing(card, profiles)
        card_actions.append(
            {
                "card": card,
                "cost": CARD_DATA[card]["cost"],
                "job": _card_job(card, profiles),
                "threats": [
                    enemy["card"]
                    for enemy in profiles
                    if _card_effectiveness(card, enemy) >= 0.18
                ],
                "placement": placement,
                "timing": timing,
            }
        )

    unknown_threats = [enemy for enemy in profiles if not enemy["categories"]]
    limitations = [
        "Effectiveness values are heuristic estimates, not measured win probabilities.",
        "The plan cannot guarantee a defense; troop levels, health, exact positions, and player timing are unknown.",
    ]
    if not profiles:
        limitations.append("No enemy troops were supplied.")
    if unknown_threats:
        limitations.append(
            "Unknown troops cannot be scored reliably: "
            + ", ".join(enemy["card"] for enemy in unknown_threats)
            + "."
        )
    if not any(enemy["lane"] or enemy["seconds_to_tower"] is not None for enemy in profiles):
        limitations.append("No lane or time-to-tower data was supplied.")

    confidence = "Low" if unknown_threats or not profiles else "Medium"
    reason = None
    if not candidates:
        reason = "No defensive cards are available in the selected hand."
        if hand is not None and any(_normalize_card(card) == "Hog Rider" for card in hand):
            reason += " Hog Rider is reserved for counter-pushing."
    elif not affordable:
        reason = "No defensive card in the selected cards is affordable."
    elif not plan_cards:
        reason = "No effective defensive card is available for the supplied threats."

    return {
        "cards": card_actions,
        "total_cost": total_cost,
        "remaining_elixir": elixir - total_cost,
        "threats": outcomes,
        "confidence": confidence,
        "limitations": limitations,
        "reason": reason,
    }


def format_defense(plan):
    lines = []
    if not plan["cards"]:
        lines.append(plan["reason"] or "No defensive recommendation is available.")
    else:
        lines.append(
            "Recommended defense: "
            + " + ".join(action["card"] for action in plan["cards"])
            + f" ({plan['total_cost']} elixir; "
            + f"{plan['remaining_elixir']} remaining)."
        )
        lines.append("Card jobs:")
        for action in plan["cards"]:
            lines.append(
                f"- {action['card']} ({action['cost']} elixir): {action['job']}"
            )
            if action["placement"]:
                lines.append(f"  Placement: {action['placement']}")
            if action["timing"]:
                lines.append(f"  Timing: {action['timing']}")

    if plan["threats"]:
        lines.append("Threat outlook:")
        for outcome in plan["threats"]:
            coverage = round(outcome["coverage"] * 100)
            contributors = (
                f" (contributions from {', '.join(outcome['contributed_by'])})"
                if outcome["contributed_by"]
                else ""
            )
            lines.append(
                f"- {outcome['card']}: {outcome['status']} "
                f"(heuristic coverage {coverage}%){contributors}."
            )
    lines.append(f"Confidence: {plan['confidence']} (heuristic, not a guarantee).")
    lines.append("Limitations: " + " ".join(plan["limitations"]))
    return "\n".join(lines)


def choose_defense(enemy, elixir, hand=None):
    """Preserve the original text-returning API, now backed by multi-card plans."""
    return format_defense(recommend_defense(enemy, elixir, hand))
