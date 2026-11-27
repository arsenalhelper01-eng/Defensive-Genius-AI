# Defensive Genius AI 🛡️

An intelligent Clash Royale defensive strategy AI.

## Goals
- Analyze enemy threats.
- Evaluate elixir and card rotations.
- Recommend efficient defensive counters.
- Simulate battles against different strategies.

## Technology
- Python
- GitHub

## Project Status
Version 0.1 — Initial development.

## Defensive recommendations
The battle simulator evaluates each enemy troop's roles (including tanks,
support, air, swarms, and win conditions) and evaluates affordable combinations
of defensive cards against the full push.
Recommendations are limited to this deck:

- Evolution Tesla
- Hero Musketeer
- Evolution Ice Spirit
- Hog Rider
- Knight
- Skeletons
- Fireball
- Log

Hog Rider is reserved for counter-pushing, not primary defense. Enter the cards
currently in hand to restrict the recommendation to those cards; leaving the
hand prompt blank evaluates the full deck. Each plan lists the job and cost of
each card, remaining elixir, threats each card contributes against, and threats
that may survive. Matchup coverage is heuristic, not a win probability or
guarantee.

The optional battlefield prompt accepts entries such as
`Balloon=2@left; Golem=8@right` (seconds to tower and lane). Placement and timing
guidance is only offered where that information is relevant; exact tile
coordinates are not inferred.

Run the simulator with `python battle.py`.
