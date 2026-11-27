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

## Private API
The FastAPI service wraps the existing recommendation engine. It binds to
localhost by default; do not bind it to a public interface or forward its port
to the internet.

Install the Python dependencies and start the local server:

```bash
python -m pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Check `GET http://127.0.0.1:8000/health` or send a request to
`POST http://127.0.0.1:8000/analyze`:

```json
{
  "enemy_cards": ["Golem", "Night Witch", "Balloon"],
  "elixir": 10,
  "hand": ["Evolution Tesla", "Hero Musketeer", "Skeletons"],
  "lanes": {"Balloon": "left", "Golem": "left"},
  "times_to_tower": {"Balloon": 2, "Golem": 8}
}
```

`hand`, `lanes`, and `times_to_tower` are optional. If `hand` is omitted, the
planner uses its configured deck; an explicitly empty hand means no cards are
available. Lane values are `left`, `right`, or `center`; time-to-tower values
must be between 0 and 120 seconds. Input validation errors return HTTP 422
with field-level details. The response includes recommended cards and jobs,
total and remaining elixir, threat outcomes, confidence, limitations, and an
explanation.

Run API and existing CLI regression tests with:

```bash
python -m unittest -v
```

This local-only setup is intended for development. It is not an authenticated
or encrypted service and should not be exposed to a network; a future private
iPhone connection will need an explicit secure local-network design.
