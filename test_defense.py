import unittest
from unittest.mock import patch

from battle import parse_battlefield_info, simulate_battle
from brain import CARD_DATA, DECK, choose_defense, format_defense, recommend_defense
from threats import recognize_threat, recognize_threats
from threat_score import calculate_danger, danger_level


class ThreatRecognitionTests(unittest.TestCase):
    def test_recognizes_multiple_roles_and_win_conditions(self):
        self.assertEqual(
            recognize_threats("Balloon"), ["air", "win_condition"]
        )
        self.assertEqual(recognize_threat("Giant"), "tank")

    def test_push_score_includes_multiple_roles(self):
        score = calculate_danger([("Minion Horde", ["air", "swarm"])])
        self.assertEqual(score, 7)
        self.assertEqual(danger_level(score), "MODERATE")


class DefenseRecommendationTests(unittest.TestCase):
    def test_only_uses_cards_from_configured_deck(self):
        plan = recommend_defense(
            ["Balloon"],
            10,
            ["Hog Rider", "Hero Musketeer"],
        )
        recommended = {action["card"] for action in plan["cards"]}
        self.assertTrue(recommended.issubset(set(DECK)))
        self.assertNotIn("Hog Rider", recommended)
        self.assertIn("Hero Musketeer", recommended)

    def test_golem_night_witch_balloon_gets_a_coordinated_defense(self):
        plan = recommend_defense(["Golem", "Night Witch", "Balloon"], 10)

        cards = {action["card"] for action in plan["cards"]}
        self.assertIn("Evolution Tesla", cards)
        self.assertIn("Hero Musketeer", cards)
        self.assertGreaterEqual(len(cards), 2)
        self.assertLessEqual(plan["total_cost"], 10)
        self.assertEqual(plan["remaining_elixir"], 10 - plan["total_cost"])
        self.assertTrue(all(action["job"] for action in plan["cards"]))
        self.assertTrue(all(action["threats"] for action in plan["cards"]))

    def test_fireball_is_used_for_clustered_support(self):
        push = [
            ("Wizard", "support"),
            ("Witch", "support"),
            ("Musketeer", "support"),
            ("Executioner", "support"),
        ]
        plan = recommend_defense(push, 10)
        self.assertIn("Fireball", {action["card"] for action in plan["cards"]})

    def test_balloon_approaching_tower_is_urgent_and_has_placement_guidance(self):
        plan = recommend_defense(
            [
                {
                    "card": "Balloon",
                    "seconds_to_tower": 2,
                    "lane": "left",
                }
            ],
            8,
        )
        cards = {action["card"] for action in plan["cards"]}
        self.assertIn("Evolution Tesla", cards)
        self.assertIn("Hero Musketeer", cards)
        self.assertTrue(
            all(
                action["timing"] and action["placement"]
                for action in plan["cards"]
            )
        )
        self.assertTrue(any("immediately" in action["timing"] for action in plan["cards"]))

    def test_ground_only_cards_are_not_selected_against_air(self):
        plan = recommend_defense(
            ["Minion Horde"],
            6,
            ["Knight", "Skeletons", "Log"],
        )
        self.assertEqual(plan["cards"], [])
        self.assertIn("No effective defensive card", plan["reason"])
        self.assertEqual(plan["threats"][0]["status"], "likely remains a threat")
        report = format_defense(plan)
        self.assertIn("Minion Horde: likely remains a threat", report)
        self.assertIn("Confidence:", report)

    def test_multiple_lanes_do_not_get_a_false_single_lane_placement(self):
        plan = recommend_defense(
            [
                {"card": "Golem", "lane": "left", "seconds_to_tower": 7},
                {"card": "Balloon", "lane": "right", "seconds_to_tower": 3},
            ],
            10,
        )
        self.assertTrue(
            any(
                action["placement"]
                and "multiple lanes" in action["placement"]
                for action in plan["cards"]
            )
        )

    def test_insufficient_elixir_does_not_exceed_available_amount(self):
        plan = recommend_defense(["Balloon"], 3, ["Hero Musketeer"])
        self.assertEqual(plan["cards"], [])
        self.assertEqual(plan["total_cost"], 0)
        self.assertEqual(plan["remaining_elixir"], 3)
        self.assertIn("affordable", plan["reason"])

    def test_cards_not_in_provided_hand_are_never_recommended(self):
        hand = ["Evolution Tesla"]
        plan = recommend_defense(["Balloon"], 10, hand)
        self.assertTrue(
            {action["card"] for action in plan["cards"]}.issubset(set(hand))
        )
        self.assertNotIn("Hero Musketeer", {action["card"] for action in plan["cards"]})

    def test_reports_threats_that_may_survive(self):
        plan = recommend_defense(["Golem"], 1, ["Skeletons"])
        self.assertEqual(plan["threats"][0]["status"], "likely remains a threat")
        self.assertIn("Golem", plan["cards"][0]["threats"])

    def test_air_and_ground_targeting_data_is_explicit(self):
        for card in ("Knight", "Skeletons", "Log"):
            self.assertNotIn("air", CARD_DATA[card]["targets"])
        for card in ("Evolution Tesla", "Hero Musketeer", "Evolution Ice Spirit", "Fireball"):
            self.assertIn("air", CARD_DATA[card]["targets"])

    def test_confidence_and_limitations_are_reported(self):
        plan = recommend_defense(["Balloon"], 4)
        self.assertEqual(plan["confidence"], "Medium")
        self.assertTrue(any("not measured win probabilities" in item for item in plan["limitations"]))
        self.assertIn("Confidence: Medium", choose_defense(["Balloon"], 4))

    def test_rejects_invalid_elixir(self):
        with self.assertRaises(ValueError):
            recommend_defense(["Balloon"], 11)


class SimulatorRegressionTests(unittest.TestCase):
    def test_parses_optional_time_and_lane_data(self):
        parsed = parse_battlefield_info(
            "Balloon=2@left; Golem=8@right; Night Witch=@right",
            ["Balloon", "Golem", "Night Witch"],
        )
        self.assertEqual(parsed["balloon"]["seconds_to_tower"], 2)
        self.assertEqual(parsed["balloon"]["lane"], "left")
        self.assertIsNone(parsed["night witch"]["seconds_to_tower"])
        self.assertEqual(parsed["night witch"]["lane"], "right")

    def test_rejects_positions_for_non_enemy_cards(self):
        with self.assertRaises(ValueError):
            parse_battlefield_info("Balloon=2@left", ["Golem"])

    def test_existing_text_api_accepts_legacy_threat_tuples(self):
        result = choose_defense([("Wizard", "support")], 4)
        self.assertIn("Recommended defense:", result)
        self.assertIn("4 elixir", result)

    def test_cli_still_runs_and_uses_optional_battlefield_data(self):
        answers = [
            "Balloon",
            "8",
            "Evolution Tesla, Hero Musketeer",
            "Balloon=2@left",
        ]
        with patch("builtins.input", side_effect=answers):
            with patch("builtins.print") as output:
                simulate_battle()

        printed = "\n".join(
            " ".join(str(part) for part in call.args)
            for call in output.call_args_list
        )
        self.assertIn("AI DECISION", printed)
        self.assertIn("2s", printed)
        self.assertIn("left", printed)


if __name__ == "__main__":
    unittest.main()
