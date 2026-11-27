# DEFENSIVE GENIUS - ELIXIR MANAGER

MAX_ELIXIR = 10

def can_afford(cost, current_elixir):
    return current_elixir >= cost


def remaining_elixir(cost, current_elixir):
    if can_afford(cost, current_elixir):
        return current_elixir - cost

    return current_elixir


def should_save_elixir(current_elixir, enemy_threat):
    if enemy_threat in ["tank", "air"]:
        return current_elixir < 5

    return current_elixir < 3


def get_elixir_status(current_elixir):
    if current_elixir >= 8:
        return "High elixir - prepare a defense!"

    if current_elixir >= 4:
        return "Balanced elixir."

    return "Low elixir - conserve resources."