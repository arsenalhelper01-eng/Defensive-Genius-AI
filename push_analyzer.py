
# DEFENSIVE GENIUS - PUSH ANALYZER

from threats import recognize_threat, recognize_threats
from threat_score import calculate_danger, danger_level


def analyze_push(enemy_cards):
    threats = []

    for card in enemy_cards:
        threat = recognize_threat(card)
        threats.append((card, threat))

    print("\n=== ENEMY PUSH ANALYSIS ===")

    for card, threat in threats:
        categories = recognize_threats(card)
        print(f"{card}: {', '.join(categories) if categories else threat}")

    score_threats = [
        (card, recognize_threats(card) or [threat])
        for card, threat in threats
    ]
    score = calculate_danger(score_threats)

    print("\nDANGER SCORE:", score)
    print("DANGER LEVEL:", danger_level(score))

    if any("tank" in recognize_threats(card) for card, _ in threats):
        print("WARNING: Heavy push detected!")

    if any("support" in recognize_threats(card) for card, _ in threats):
        print("Support troops detected!")

    if any("air" in recognize_threats(card) for card, _ in threats):
        print("Air threat detected!")

    if any("swarm" in recognize_threats(card) for card, _ in threats):
        print("Swarm threat detected!")

    if any("win_condition" in recognize_threats(card) for card, _ in threats):
        print("Enemy win condition detected!")

    return threats


if __name__ == "__main__":
    cards = input("Enemy cards (comma separated): ").split(",")
    cards = [card.strip() for card in cards]
    analyze_push(cards)
