
import math

from brain import format_defense, recommend_defense
from elixir import get_elixir_status, should_save_elixir
from push_analyzer import analyze_push
from threats import recognize_threats


def parse_battlefield_info(raw, enemy_cards):
    """Parse optional entries such as 'Balloon=2@left; Golem=8@right'."""
    known_cards = {card.strip().lower(): card.strip() for card in enemy_cards}
    positions = {}
    if not raw.strip():
        return positions

    for entry in raw.split(";"):
        if not entry.strip():
            continue
        if "=" not in entry:
            raise ValueError(f"Expected Card=seconds@lane, got {entry.strip()!r}.")
        card_name, details = entry.split("=", 1)
        card_key = card_name.strip().lower()
        if card_key not in known_cards:
            raise ValueError(f"{card_name.strip()!r} is not in the enemy list.")

        if "@" in details:
            seconds_text, lane_text = details.rsplit("@", 1)
            lane = lane_text.strip().lower()
            if lane not in ("left", "right", "center"):
                raise ValueError("Lane must be left, right, or center.")
        else:
            seconds_text = details
            lane = None

        seconds = None
        if seconds_text.strip():
            try:
                seconds = float(seconds_text.strip())
            except ValueError as error:
                raise ValueError("Time-to-tower must be a number of seconds.") from error
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError("Time-to-tower must be a finite, non-negative number.")
        if seconds is None and lane is None:
            raise ValueError("Provide a time-to-tower, a lane, or both.")

        positions[card_key] = {
            "seconds_to_tower": seconds,
            "lane": lane,
        }
    return positions


def _read_elixir():
    while True:
        raw = input("Your elixir (0-10): ").strip()
        try:
            elixir = int(raw)
        except ValueError:
            print("Enter a whole number from 0 to 10.")
            continue
        if 0 <= elixir <= 10:
            return elixir
        print("Elixir must be between 0 and 10.")


def simulate_battle():
    print("=== DEFENSIVE GENIUS AI ===")

    enemy_cards = input("Enemy cards (comma separated): ").split(",")
    enemy_cards = [card.strip() for card in enemy_cards if card.strip()]

    elixir = _read_elixir()

    hand = input(
        "Your cards in hand (comma separated; Enter uses your deck): "
    ).split(",")
    hand = [card.strip() for card in hand if card.strip()] or None

    while True:
        raw_battlefield = input(
            "Optional positions (Card=seconds@lane; e.g. Balloon=2@left; "
            "Enter to skip): "
        )
        try:
            battlefield = parse_battlefield_info(raw_battlefield, enemy_cards)
            break
        except ValueError as error:
            print(f"Invalid battlefield information: {error}")

    enemy_threats = analyze_push(enemy_cards)

    print("\nElixir status:", get_elixir_status(elixir))

    if any(threat == "unknown" for _, threat in enemy_threats):
        print("WARNING: Unknown enemy card detected!")

    if any(
        should_save_elixir(elixir, category)
        for card, threat in enemy_threats
        for category in (recognize_threats(card) or [threat])
    ):
        print("AI WARNING: Be careful with your elixir!")

    enemy_state = [
        {
            "card": card,
            **battlefield.get(card.lower(), {}),
        }
        for card in enemy_cards
    ]
    plan = recommend_defense(enemy_state, elixir, hand)
    print("\nAI DECISION:\n" + format_defense(plan))


if __name__ == "__main__":
    simulate_battle()
