# DEFENSIVE GENIUS - THREAT RECOGNITION V4

# Profiles can include several traits so defenses can account for mixed pushes.
THREAT_PROFILES = {
    "Hog Rider": ("fast", "ground", "win_condition"),
    "Ram Rider": ("fast", "ground", "win_condition"),
    "Battle Ram": ("fast", "ground", "win_condition"),
    "Giant": ("tank", "ground", "win_condition"),
    "Golem": ("tank", "ground", "win_condition"),
    "Royal Giant": ("tank", "ground", "win_condition"),
    "Mega Knight": ("tank", "ground"),
    "P.E.K.K.A": ("tank", "ground"),
    "Lava Hound": ("tank", "air", "win_condition"),
    "Balloon": ("air", "win_condition"),
    "Baby Dragon": ("air", "support"),
    "Electro Dragon": ("air", "support"),
    "Inferno Dragon": ("air", "support"),
    "Skeleton Dragons": ("air", "support"),
    "Minions": ("air", "swarm"),
    "Minion Horde": ("air", "swarm"),
    "Bats": ("air", "swarm"),
    "Mega Minion": ("air", "support"),
    "Flying Machine": ("air", "support"),
    "Skeleton Army": ("swarm", "ground"),
    "Goblin Gang": ("swarm", "ground"),
    "Goblin Barrel": ("swarm", "bait", "win_condition"),
    "Princess": ("bait", "support"),
    "Wizard": ("support", "ground"),
    "Witch": ("support", "ground"),
    "Night Witch": ("support", "ground"),
    "Musketeer": ("support", "ground"),
    "Executioner": ("support", "ground"),
    "Archers": ("support", "ground"),
    "Bomber": ("support", "ground"),
    "Bowler": ("support", "ground"),
    "Dark Prince": ("support", "ground"),
    "Electro Wizard": ("support", "ground"),
    "Phoenix": ("air", "support"),
    "Sparky": ("support", "ground"),
    "Electro Giant": ("tank", "ground", "win_condition"),
    "Elixir Golem": ("tank", "ground", "win_condition"),
    "Giant Skeleton": ("tank", "ground"),
    "Miner": ("ground", "win_condition"),
    "Graveyard": ("swarm", "win_condition"),
    "X-Bow": ("ground", "win_condition"),
    "Mortar": ("ground", "win_condition"),
    "Royal Hogs": ("swarm", "ground", "win_condition"),
    "Goblin Drill": ("swarm", "ground", "win_condition"),
    "Firecracker": ("support", "ground"),
    "Goblin Giant": ("tank", "ground", "win_condition"),
}

# Preserve the original primary labels for callers using the legacy API.
_LEGACY_PRIMARY = {
    "Minion Horde": "swarm",
    "Goblin Barrel": "bait",
    "Princess": "bait",
}

THREATS = {
    card: _LEGACY_PRIMARY.get(card, categories[0])
    for card, categories in THREAT_PROFILES.items()
}


def recognize_threats(enemy_card):
    """Return all known roles for a card, or an empty list when unknown."""
    normalized = enemy_card.strip().lower()
    for card, categories in THREAT_PROFILES.items():
        if card.lower() == normalized:
            return list(categories)
    return []


def recognize_threat(enemy_card):
    """Return a card's primary role, preserving the original API."""
    normalized = enemy_card.strip().lower()
    for card, primary in THREATS.items():
        if card.lower() == normalized:
            return primary
    return "unknown"


if __name__ == "__main__":
    enemy = input("Enemy card: ")
    print("Threat types:", ", ".join(recognize_threats(enemy)) or "unknown")
