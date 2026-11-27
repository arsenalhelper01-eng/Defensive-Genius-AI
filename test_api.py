import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from api import AnalyzeRequest
import api
from brain import recommend_defense


client = TestClient(api.app)


class HealthEndpointTests(unittest.TestCase):
    def test_health_returns_ok(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class AnalyzeEndpointTests(unittest.TestCase):
    def test_returns_structured_coordinated_recommendation(self):
        response = client.post(
            "/analyze",
            json={
                "enemy_cards": ["Golem", "Night Witch", "Balloon"],
                "elixir": 10,
                "hand": [
                    "Evolution Tesla",
                    "Hero Musketeer",
                    "Evolution Ice Spirit",
                    "Knight",
                    "Skeletons",
                    "Fireball",
                ],
                "lanes": {"Balloon": "left", "Golem": "left"},
                "times_to_tower": {"Balloon": 2, "Golem": 8},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(len(payload["recommended_cards"]), 2)
        self.assertLessEqual(payload["total_cost"], 10)
        self.assertEqual(
            payload["remaining_elixir"],
            10 - payload["total_cost"],
        )
        self.assertTrue(all(card["job"] for card in payload["recommended_cards"]))
        self.assertIn("Balloon", payload["threats"][-1]["card"])
        self.assertEqual(payload["threats"][-1]["seconds_to_tower"], 2)
        self.assertTrue(payload["confidence"])
        self.assertTrue(payload["limitations"])
        self.assertTrue(payload["explanation"])

    def test_current_hand_is_enforced_by_existing_planner(self):
        response = client.post(
            "/analyze",
            json={
                "enemy_cards": ["Balloon"],
                "elixir": 10,
                "hand": ["Evolution Tesla"],
            },
        )
        self.assertEqual(response.status_code, 200)
        cards = response.json()["recommended_cards"]
        self.assertEqual([card["card"] for card in cards], ["Evolution Tesla"])

    def test_empty_hand_is_not_treated_as_full_deck(self):
        response = client.post(
            "/analyze",
            json={"enemy_cards": ["Balloon"], "elixir": 10, "hand": []},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recommended_cards"], [])

    def test_endpoint_delegates_to_existing_recommendation_system(self):
        expected = recommend_defense(["Balloon"], 4, ["Hero Musketeer"])
        with patch("api.recommend_defense", return_value=expected) as planner:
            response = client.post(
                "/analyze",
                json={
                    "enemy_cards": ["Balloon"],
                    "elixir": 4,
                    "hand": ["Hero Musketeer"],
                },
            )

        self.assertEqual(response.status_code, 200)
        planner.assert_called_once()
        args, _ = planner.call_args
        self.assertEqual(args[1:], (4, ["Hero Musketeer"]))
        self.assertEqual(args[0][0]["card"], "Balloon")

    def test_rejects_elixir_outside_game_range(self):
        response = client.post(
            "/analyze",
            json={"enemy_cards": ["Balloon"], "elixir": 11},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertIn("elixir", response.json()["details"][0]["field"])

    def test_rejects_non_integer_elixir(self):
        response = client.post(
            "/analyze",
            json={"enemy_cards": ["Balloon"], "elixir": 4.5},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("elixir", response.json()["details"][0]["field"])

    def test_rejects_missing_or_blank_enemy_cards(self):
        missing = client.post("/analyze", json={"elixir": 4})
        blank = client.post(
            "/analyze",
            json={"enemy_cards": ["  "], "elixir": 4},
        )
        self.assertEqual(missing.status_code, 422)
        self.assertEqual(blank.status_code, 422)
        self.assertIn("enemy_cards", str(blank.json()["details"]))

    def test_rejects_cards_outside_configured_deck_in_hand(self):
        response = client.post(
            "/analyze",
            json={
                "enemy_cards": ["Balloon"],
                "elixir": 5,
                "hand": ["Mega Knight"],
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("outside the configured deck", str(response.json()["details"]))

    def test_rejects_invalid_lane_and_unrelated_battlefield_keys(self):
        invalid_lane = client.post(
            "/analyze",
            json={
                "enemy_cards": ["Balloon"],
                "elixir": 5,
                "lanes": {"Balloon": "north"},
            },
        )
        unrelated = client.post(
            "/analyze",
            json={
                "enemy_cards": ["Balloon"],
                "elixir": 5,
                "lanes": {"Golem": "left"},
            },
        )
        self.assertEqual(invalid_lane.status_code, 422)
        self.assertEqual(unrelated.status_code, 422)

    def test_rejects_invalid_time_until_tower(self):
        for seconds in (-1, 121):
            with self.subTest(seconds=seconds):
                response = client.post(
                    "/analyze",
                    json={
                        "enemy_cards": ["Balloon"],
                        "elixir": 5,
                        "times_to_tower": {"Balloon": seconds},
                    },
                )
                self.assertEqual(response.status_code, 422)

    def test_rejects_non_finite_time_values(self):
        with self.assertRaises(ValidationError):
            AnalyzeRequest.model_validate(
                {
                    "enemy_cards": ["Balloon"],
                    "elixir": 5,
                    "times_to_tower": {"Balloon": float("inf")},
                }
            )

    def test_rejects_unexpected_request_fields(self):
        response = client.post(
            "/analyze",
            json={
                "enemy_cards": ["Balloon"],
                "elixir": 5,
                "public_deployment": True,
            },
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
