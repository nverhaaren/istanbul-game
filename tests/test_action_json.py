"""Tests for action JSON serialization/deserialization and CSV-JSON conversion."""

import json
import typing
from collections import Counter
from pathlib import Path

import pytest

from istanbul_game.action_json import action_from_json, action_to_json, turn_from_json, turn_to_json
from istanbul_game.actions import (
    ArrestFamilyCardAction,
    BlackMarketAction,
    CaravansaryAction,
    ChooseReward,
    DoubleCardAction,
    EncounterGovernor,
    EncounterSmuggler,
    ExtraMoveCardAction,
    FiveLiraCardAction,
    FountainAction,
    GenericTileAction,
    GreenTileAction,
    MarketAction,
    MosqueAction,
    Move,
    NoMoveCardAction,
    OneGoodCardAction,
    Pay,
    PlayerAction,
    PoliceStationAction,
    RedTileAction,
    ReturnAssistantCardAction,
    SellAnyCardAction,
    SkipTileAction,
    SultansPalaceAction,
    TeaHouseAction,
    YellowTileAction,
    YieldTurn,
)
from istanbul_game.constants import Card, Good, Location, Player
from istanbul_game.load.csv_json import csv_turn_to_json, json_turn_to_csv
from istanbul_game.load.from_csv import setup_from_csv, turns_from_csv
from istanbul_game.load.phases import TurnRow

EXAMPLE_DIR = Path(__file__).resolve().parent.parent / "examples" / "red_wins_3p"


# ---- action_to_json / action_from_json unit tests ----


class TestSimpleActions:
    def test_yield_turn(self) -> None:
        action = YieldTurn()
        result = action_to_json(action)
        assert result == {"type": "YieldTurn"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, YieldTurn)

    def test_pay(self) -> None:
        action = Pay()
        result = action_to_json(action)
        assert result == {"type": "Pay"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, Pay)

    def test_skip_tile_action(self) -> None:
        action = SkipTileAction()
        result = action_to_json(action)
        assert result == {"type": "SkipTileAction"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, SkipTileAction)

    def test_generic_tile_action(self) -> None:
        action = GenericTileAction()
        result = action_to_json(action)
        assert result == {"type": "GenericTileAction"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, GenericTileAction)

    def test_five_lira_card(self) -> None:
        action = FiveLiraCardAction()
        result = action_to_json(action)
        assert result == {"type": "FiveLiraCardAction"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, FiveLiraCardAction)


class TestMoveAction:
    def test_simple_move(self) -> None:
        action = Move(Location(8), skip_assistant=False)
        result = action_to_json(action)
        assert result == {"type": "Move", "location": 8, "skip_assistant": False}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, Move)
        assert roundtripped.tile == Location(8)
        assert roundtripped.skip_assistant is False

    def test_move_skip_assistant(self) -> None:
        action = Move(Location(5), skip_assistant=True)
        result = action_to_json(action)
        assert result["skip_assistant"] is True
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, Move)
        assert roundtripped.skip_assistant is True


class TestChooseReward:
    def test_lira_reward(self) -> None:
        action = ChooseReward(ChooseReward.LIRA)
        result = action_to_json(action)
        assert result == {"type": "ChooseReward", "choice": "Lira"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, ChooseReward)
        assert roundtripped.choice == ChooseReward.LIRA

    def test_card_reward(self) -> None:
        action = ChooseReward(Card.ONE_GOOD)
        result = action_to_json(action)
        assert result == {"type": "ChooseReward", "choice": "OneGood"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, ChooseReward)
        assert roundtripped.choice == Card.ONE_GOOD


class TestTileActions:
    def test_mosque_action(self) -> None:
        action = MosqueAction(Good.RED)
        result = action_to_json(action)
        assert result == {"type": "MosqueAction", "good": "Red"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, MosqueAction)
        assert roundtripped.good_color == Good.RED

    def test_market_action(self) -> None:
        action = MarketAction(Counter({Good.RED: 1, Good.GREEN: 1}), Counter({Good.BLUE: 2, Good.YELLOW: 1}))
        result = action_to_json(action)
        assert result["type"] == "MarketAction"
        assert result["goods"] == {"Red": 1, "Green": 1}
        assert result["new_demand"] == {"Blue": 2, "Yellow": 1}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, MarketAction)
        assert roundtripped.goods == Counter({Good.RED: 1, Good.GREEN: 1})
        assert roundtripped.new_demand == Counter({Good.BLUE: 2, Good.YELLOW: 1})

    def test_black_market_action(self) -> None:
        action = BlackMarketAction(Good.GREEN, (3, 4))
        result = action_to_json(action)
        assert result == {"type": "BlackMarketAction", "good": "Green", "roll": [3, 4]}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, BlackMarketAction)
        assert roundtripped.good == Good.GREEN
        assert roundtripped.roll == (3, 4)

    def test_black_market_with_red_tile(self) -> None:
        rta = RedTileAction((2, 3), (4, 3), RedTileAction.TO_FOUR)
        action = BlackMarketAction(Good.RED, rta)
        result = action_to_json(action)
        assert result["type"] == "BlackMarketAction"
        assert isinstance(result["roll"], dict)
        assert result["roll"]["type"] == "RedTileAction"  # type: ignore[index]
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, BlackMarketAction)
        assert isinstance(roundtripped.roll, RedTileAction)
        assert roundtripped.roll.initial_roll == (2, 3)
        assert roundtripped.roll.method == RedTileAction.TO_FOUR

    def test_tea_house_action(self) -> None:
        action = TeaHouseAction(5, (2, 4))
        result = action_to_json(action)
        assert result == {"type": "TeaHouseAction", "call": 5, "roll": [2, 4]}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, TeaHouseAction)
        assert roundtripped.call == 5
        assert roundtripped.roll == (2, 4)

    def test_caravansary_action(self) -> None:
        action = CaravansaryAction((Card.ONE_GOOD, CaravansaryAction.DISCARD), Card.FIVE_LIRA)
        result = action_to_json(action)
        assert result == {
            "type": "CaravansaryAction",
            "gains": ["OneGood", "discard"],
            "cost": "FiveLira",
        }
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, CaravansaryAction)
        assert roundtripped.gains[0] == Card.ONE_GOOD
        assert roundtripped.gains[1] == CaravansaryAction.DISCARD
        assert roundtripped.cost == Card.FIVE_LIRA

    def test_sultans_palace_action(self) -> None:
        action = SultansPalaceAction(Counter({Good.RED: 1, Good.GREEN: 2}))
        result = action_to_json(action)
        assert result == {"type": "SultansPalaceAction", "goods": {"Red": 1, "Green": 2}}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, SultansPalaceAction)
        assert roundtripped.goods == Counter({Good.RED: 1, Good.GREEN: 2})

    def test_fountain_action(self) -> None:
        action = FountainAction([Location(3), Location(7)])
        result = action_to_json(action)
        assert result == {"type": "FountainAction", "assistant_locations": [3, 7]}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, FountainAction)
        assert roundtripped.assistant_locations == frozenset({Location(3), Location(7)})

    def test_police_station_action(self) -> None:
        action = PoliceStationAction(Location(12), GenericTileAction())
        result = action_to_json(action)
        assert result == {
            "type": "PoliceStationAction",
            "location": 12,
            "action": {"type": "GenericTileAction"},
        }
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, PoliceStationAction)
        assert roundtripped.location == Location(12)
        assert isinstance(roundtripped.action, GenericTileAction)


class TestCardActions:
    def test_extra_move_card(self) -> None:
        action = ExtraMoveCardAction(Move(Location(7), skip_assistant=False))
        result = action_to_json(action)
        assert result == {"type": "ExtraMoveCardAction", "location": 7, "skip_assistant": False}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, ExtraMoveCardAction)
        assert roundtripped.move.tile == Location(7)
        assert roundtripped.move.skip_assistant is False

    def test_no_move_card(self) -> None:
        action = NoMoveCardAction(skip_assistant=False)
        result = action_to_json(action)
        assert result == {"type": "NoMoveCardAction", "skip_assistant": False}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, NoMoveCardAction)

    def test_one_good_card(self) -> None:
        action = OneGoodCardAction(Good.BLUE)
        result = action_to_json(action)
        assert result == {"type": "OneGoodCardAction", "good": "Blue"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, OneGoodCardAction)
        assert roundtripped.good == Good.BLUE

    def test_return_assistant_card(self) -> None:
        action = ReturnAssistantCardAction(Location(3))
        result = action_to_json(action)
        assert result == {"type": "ReturnAssistantCardAction", "from_tile": 3}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, ReturnAssistantCardAction)
        assert roundtripped.from_tile == Location(3)

    def test_arrest_family_card_lira(self) -> None:
        action = ArrestFamilyCardAction(ChooseReward(ChooseReward.LIRA))
        result = action_to_json(action)
        assert result == {"type": "ArrestFamilyCardAction", "reward": {"choice": "Lira"}}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, ArrestFamilyCardAction)
        assert roundtripped.reward.choice == ChooseReward.LIRA

    def test_arrest_family_card_card(self) -> None:
        action = ArrestFamilyCardAction(ChooseReward(Card.FIVE_LIRA))
        result = action_to_json(action)
        assert result == {"type": "ArrestFamilyCardAction", "reward": {"choice": "FiveLira"}}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, ArrestFamilyCardAction)
        assert roundtripped.reward.choice == Card.FIVE_LIRA


class TestMosqueTileActions:
    def test_green_tile_action(self) -> None:
        action = GreenTileAction(Good.GREEN)
        result = action_to_json(action)
        assert result == {"type": "GreenTileAction", "good": "Green"}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, GreenTileAction)
        assert roundtripped.good == Good.GREEN

    def test_yellow_tile_action(self) -> None:
        action = YellowTileAction(Location(5))
        result = action_to_json(action)
        assert result == {"type": "YellowTileAction", "from_tile": 5}
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, YellowTileAction)
        assert roundtripped.from_tile == Location(5)

    def test_red_tile_action(self) -> None:
        action = RedTileAction((2, 3), (4, 3), RedTileAction.TO_FOUR)
        result = action_to_json(action)
        assert result == {
            "type": "RedTileAction",
            "initial_roll": [2, 3],
            "final_roll": [4, 3],
            "method": "to_four",
        }
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, RedTileAction)
        assert roundtripped.initial_roll == (2, 3)
        assert roundtripped.final_roll == (4, 3)
        assert roundtripped.method == RedTileAction.TO_FOUR

    def test_red_tile_reroll(self) -> None:
        action = RedTileAction((1, 2), (5, 6), RedTileAction.REROLL)
        result = action_to_json(action)
        assert result["method"] == "reroll"
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, RedTileAction)
        assert roundtripped.method == RedTileAction.REROLL


class TestNPCEncounters:
    def test_governor_pay(self) -> None:
        action = EncounterGovernor(Card.ONE_GOOD, Pay(), (3, 4))
        result = action_to_json(action)
        assert result == {
            "type": "EncounterGovernor",
            "gain": "OneGood",
            "cost": "pay",
            "roll": [3, 4],
        }
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, EncounterGovernor)
        assert roundtripped.gain == Card.ONE_GOOD
        assert isinstance(roundtripped.cost, Pay)
        assert roundtripped.roll == (3, 4)

    def test_governor_card_cost(self) -> None:
        action = EncounterGovernor(Card.FIVE_LIRA, Card.ONE_GOOD, (1, 2))
        result = action_to_json(action)
        assert result["cost"] == "OneGood"
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, EncounterGovernor)
        assert roundtripped.cost == Card.ONE_GOOD

    def test_smuggler_pay(self) -> None:
        action = EncounterSmuggler(Good.BLUE, Pay(), (1, 5))
        result = action_to_json(action)
        assert result == {
            "type": "EncounterSmuggler",
            "gain": "Blue",
            "cost": "pay",
            "roll": [1, 5],
        }
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, EncounterSmuggler)
        assert roundtripped.gain == Good.BLUE
        assert isinstance(roundtripped.cost, Pay)

    def test_smuggler_good_cost(self) -> None:
        action = EncounterSmuggler(Good.RED, Good.GREEN, (2, 3))
        result = action_to_json(action)
        assert result["cost"] == "Green"
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, EncounterSmuggler)
        assert roundtripped.cost == Good.GREEN


class TestCompoundActions:
    def test_double_card_po(self) -> None:
        action = DoubleCardAction(Card.DOUBLE_PO, (GenericTileAction(), GenericTileAction()))
        result = action_to_json(action)
        assert result == {
            "type": "DoubleCardAction",
            "card": "2xPostOffice",
            "actions": [{"type": "GenericTileAction"}, {"type": "GenericTileAction"}],
        }
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, DoubleCardAction)
        assert roundtripped.card == Card.DOUBLE_PO
        assert len(roundtripped.actions) == 2

    def test_double_card_sultan(self) -> None:
        action = DoubleCardAction(
            Card.DOUBLE_SULTAN,
            (
                SultansPalaceAction(Counter({Good.RED: 1, Good.GREEN: 1})),
                SultansPalaceAction(Counter({Good.RED: 1, Good.BLUE: 1, Good.YELLOW: 1})),
            ),
        )
        result = action_to_json(action)
        assert result["card"] == "2xSultansPalace"
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, DoubleCardAction)
        assert roundtripped.card == Card.DOUBLE_SULTAN
        first = typing.cast(SultansPalaceAction, roundtripped.actions[0])
        assert first.goods == Counter({Good.RED: 1, Good.GREEN: 1})

    def test_sell_any_card(self) -> None:
        market = MarketAction(Counter({Good.RED: 2}), Counter({Good.GREEN: 1, Good.YELLOW: 1}))
        action = SellAnyCardAction(market)
        result = action_to_json(action)
        assert result["type"] == "SellAnyCardAction"
        roundtripped = action_from_json(result)
        assert isinstance(roundtripped, SellAnyCardAction)
        assert isinstance(roundtripped.action, MarketAction)
        assert roundtripped.action.goods == Counter({Good.RED: 2})


class TestTurnSerialization:
    def test_simple_turn(self) -> None:
        actions: list[PlayerAction] = [
            Move(Location(8), skip_assistant=False),
            GenericTileAction(),
            YieldTurn(),
        ]
        result = turn_to_json(actions)
        assert len(result) == 3
        assert result[0]["type"] == "Move"
        assert result[1]["type"] == "GenericTileAction"
        assert result[2]["type"] == "YieldTurn"
        roundtripped = turn_from_json(result)
        assert len(roundtripped) == 3
        assert isinstance(roundtripped[0], Move)
        assert isinstance(roundtripped[1], GenericTileAction)
        assert isinstance(roundtripped[2], YieldTurn)

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown action type"):
            action_from_json({"type": "NonexistentAction"})

    def test_unknown_action_class_raises(self) -> None:
        class FakeAction(PlayerAction):
            pass

        with pytest.raises(ValueError, match="Unknown action type"):
            action_to_json(FakeAction())


# ---- CSV <-> JSON round-trip tests ----


class TestCSVToJSON:
    """Test converting CSV turn rows to JSON via PhaseLoader."""

    def test_simple_move_turn(self) -> None:
        """A simple move to location 8 (Spice Warehouse) with generic action."""
        with open(EXAMPLE_DIR / "setup.csv") as setup:
            phase_loader = setup_from_csv(setup)

        turn_row = TurnRow("8", "", "", "", "")
        json_actions = csv_turn_to_json(phase_loader, turn_row)

        # Should have Move + GenericTileAction + YieldTurn
        types = [a["type"] for a in json_actions]
        assert types[0] == "Move"
        assert json_actions[0]["location"] == 8
        assert "GenericTileAction" in types
        assert types[-1] == "YieldTurn"

    def test_move_with_smuggler(self) -> None:
        """First turn for Blue: move to 2 with smuggler encounter."""
        with open(EXAMPLE_DIR / "setup.csv") as setup:
            phase_loader = setup_from_csv(setup)

        # Play Red's first turn to advance to Blue
        turn1 = TurnRow("8", "", "", "", "")
        for action in phase_loader.load_turn(turn1):
            phase_loader.gs.take_action(action)

        # Blue's first turn: move to 2 with smuggler
        turn2 = TurnRow("2", "", "", "", "R G 3+4")
        json_actions = csv_turn_to_json(phase_loader, turn2)

        types = [a["type"] for a in json_actions]
        assert "EncounterSmuggler" in types
        smug = next(a for a in json_actions if a["type"] == "EncounterSmuggler")
        assert smug["gain"] == "Red"
        assert smug["cost"] == "Green"
        assert smug["roll"] == [3, 4]


class TestJSONToCSV:
    """Test converting JSON action lists back to CSV TurnRow."""

    def test_simple_move(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 8, "skip_assistant": False},
            {"type": "GenericTileAction"},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.move == "8"
        assert row.action == ""
        assert row.rewards == ""
        assert row.gov == ""
        assert row.smug == ""

    def test_move_with_mosque_action(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 4, "skip_assistant": False},
            {"type": "MosqueAction", "good": "Red"},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.move == "4"
        assert row.action == "R"

    def test_skip_assistant(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 1, "skip_assistant": True},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.move == "1!"

    def test_smuggler_encounter(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 2, "skip_assistant": False},
            {"type": "GenericTileAction"},
            {"type": "EncounterSmuggler", "gain": "Red", "cost": "Green", "roll": [3, 4]},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.move == "2"
        assert row.smug == "R G 3+4"

    def test_governor_encounter(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 1, "skip_assistant": False},
            {"type": "GenericTileAction"},
            {"type": "EncounterGovernor", "gain": "OneGood", "cost": "pay", "roll": [3, 4]},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.gov == "OneGood -2 3+4"

    def test_market_action(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 11, "skip_assistant": False},
            {"type": "MarketAction", "goods": {"Red": 1, "Green": 1}, "new_demand": {"Blue": 2, "Yellow": 1}},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.action == "RG 2BY"

    def test_black_market(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 9, "skip_assistant": False},
            {"type": "BlackMarketAction", "good": "Green", "roll": [3, 4]},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.action == "G 3+4"

    def test_tea_house(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 12, "skip_assistant": False},
            {"type": "TeaHouseAction", "call": 5, "roll": [2, 4]},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.action == "5 2+4"

    def test_reward_lira(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 6, "skip_assistant": False},
            {"type": "GenericTileAction"},
            {"type": "ChooseReward", "choice": "Lira"},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert row.rewards == "3"

    def test_reward_card(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 6, "skip_assistant": False},
            {"type": "GenericTileAction"},
            {"type": "ChooseReward", "choice": "OneGood"},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert "Card-1Good" in row.rewards or "OneGood" in row.rewards

    def test_police_station(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 6, "skip_assistant": False},
            {"type": "PoliceStationAction", "location": 12, "action": {"type": "GenericTileAction"}},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert "12" in row.action

    def test_caravansary(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 10, "skip_assistant": False},
            {"type": "CaravansaryAction", "gains": ["OneGood", "discard"], "cost": "FiveLira"},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert "OneGood" in row.action
        assert "Discard" in row.action
        assert "FiveLira" in row.action

    def test_green_tile_at_warehouse(self) -> None:
        actions: list[dict[str, object]] = [
            {"type": "Move", "location": 3, "skip_assistant": False},
            {"type": "GreenTileAction", "good": "Red"},
            {"type": "YieldTurn"},
        ]
        row = json_turn_to_csv(actions)
        assert "GreenTile" in row.action
        assert "R" in row.action


class TestCSVJSONRoundTrip:
    """Test that CSV -> JSON -> CSV -> JSON round trips produce consistent results.

    We replay the entire red_wins_3p example game through JSON, and verify
    the final game state matches the expected output.
    """

    def test_full_game_via_json(self) -> None:
        """Convert each CSV turn to JSON, deserialize back to actions, and replay."""
        from istanbul_game import serialize

        # First pass: convert CSV rows to JSON turns
        with open(EXAMPLE_DIR / "setup.csv") as setup:
            phase_loader = setup_from_csv(setup)
        with open(EXAMPLE_DIR / "moves.csv") as moves:
            csv_turns = list(turns_from_csv(moves))

        json_turns: list[list[dict[str, object]]] = []
        for turn_row in csv_turns:
            json_actions = csv_turn_to_json(phase_loader, turn_row)
            json_turns.append(json_actions)

        # Second pass: replay from JSON
        with open(EXAMPLE_DIR / "setup.csv") as setup:
            phase_loader2 = setup_from_csv(setup)
        gs = phase_loader2.gs

        for json_turn in json_turns:
            actions = turn_from_json(json_turn)
            for action in actions:
                gs.take_action(action)

        assert gs.completed
        assert gs.player_states[Player.RED].rubies == 5

        # Verify final state matches expected
        actual = serialize.game_state(gs)
        with open(EXAMPLE_DIR / "expected_output.json") as f:
            expected = json.load(f)

        assert _normalize(actual) == _normalize(expected)

    def test_csv_json_csv_roundtrip(self) -> None:
        """CSV -> JSON -> CSV -> JSON should produce identical JSON both times."""
        with open(EXAMPLE_DIR / "setup.csv") as setup:
            phase_loader = setup_from_csv(setup)
        with open(EXAMPLE_DIR / "moves.csv") as moves:
            csv_turns = list(turns_from_csv(moves))

        all_json_turns_1: list[list[dict[str, object]]] = []
        for turn_row in csv_turns:
            json_actions = csv_turn_to_json(phase_loader, turn_row)
            all_json_turns_1.append(json_actions)

        # Now convert each JSON turn back to CSV, then back to JSON
        # For the second conversion, we need a fresh game state
        with open(EXAMPLE_DIR / "setup.csv") as setup:
            phase_loader2 = setup_from_csv(setup)

        all_json_turns_2: list[list[dict[str, object]]] = []
        for json_turn in all_json_turns_1:
            # JSON -> CSV
            csv_row = json_turn_to_csv(json_turn)
            # CSV -> JSON (needs game state context)
            json_actions2 = csv_turn_to_json(phase_loader2, csv_row)
            all_json_turns_2.append(json_actions2)

        assert len(all_json_turns_1) == len(all_json_turns_2)
        for i, (t1, t2) in enumerate(zip(all_json_turns_1, all_json_turns_2, strict=True)):
            assert t1 == t2, f"Turn {i} mismatch:\n  original: {t1}\n  roundtrip: {t2}"


def _normalize(obj: object) -> object:
    """Normalize JSON-like objects for comparison, sorting list elements where possible."""
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        normalized = [_normalize(x) for x in obj]
        if all(isinstance(x, (str, int, float, bool)) for x in normalized):
            return sorted(normalized, key=str)
        return normalized
    return obj
