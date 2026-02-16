"""Serialize and deserialize PlayerAction objects to/from JSON-compatible dicts.

The JSON action format uses descriptive keys matching the game state serialization
conventions: title-cased goods ("Red", "Blue", "Green", "Yellow"), card names matching
serialize.card() output ("OneGood", "FiveLira", etc.), and integer locations.

Every action is represented as a dict with a ``"type"`` key matching the action class name.

Action Schemas
--------------

Movement and turn control::

    {"type": "Move", "location": 8, "skip_assistant": false}
    {"type": "Pay"}
    {"type": "YieldTurn"}
    {"type": "SkipTileAction"}

Tile actions::

    {"type": "GenericTileAction"}
    {"type": "MosqueAction", "good": "Red"}
    {"type": "MarketAction", "goods": {"Red": 1, "Green": 1},
     "new_demand": {"Blue": 2, "Yellow": 1}}
    {"type": "BlackMarketAction", "good": "Red", "roll": [3, 4]}
    {"type": "TeaHouseAction", "call": 5, "roll": [2, 4]}
    {"type": "CaravansaryAction", "gains": ["OneGood", "discard"], "cost": "FiveLira"}
    {"type": "SultansPalaceAction", "goods": {"Red": 1, "Green": 1, "Yellow": 1}}
    {"type": "FountainAction", "assistant_locations": [3, 7, 12]}
    {"type": "PoliceStationAction", "location": 12,
     "action": {"type": "GenericTileAction"}}

Card-based actions::

    {"type": "ChooseReward", "choice": "Lira"}
    {"type": "ChooseReward", "choice": "OneGood"}
    {"type": "ExtraMoveCardAction", "location": 7, "skip_assistant": false}
    {"type": "NoMoveCardAction", "skip_assistant": false}
    {"type": "OneGoodCardAction", "good": "Red"}
    {"type": "FiveLiraCardAction"}
    {"type": "ReturnAssistantCardAction", "from_tile": 3}
    {"type": "ArrestFamilyCardAction", "reward": {"choice": "Lira"}}
    {"type": "GreenTileAction", "good": "Red"}
    {"type": "YellowTileAction", "from_tile": 3}
    {"type": "RedTileAction", "initial_roll": [2, 3], "final_roll": [4, 3],
     "method": "to_four"}
    {"type": "DoubleCardAction", "card": "2xPostOffice",
     "actions": [{"type": "GenericTileAction"}, {"type": "GenericTileAction"}]}
    {"type": "SellAnyCardAction", "action": {"type": "MarketAction", ...}}

NPC encounters::

    {"type": "EncounterGovernor", "gain": "OneGood", "cost": "pay", "roll": [3, 4]}
    {"type": "EncounterGovernor", "gain": "OneGood", "cost": "FiveLira", "roll": [3, 4]}
    {"type": "EncounterSmuggler", "gain": "Red", "cost": "pay", "roll": [1, 5]}
    {"type": "EncounterSmuggler", "gain": "Blue", "cost": "Green", "roll": [1, 5]}

A turn is represented as a list of action dicts.
"""

import typing
from collections import Counter
from collections.abc import Iterable

from .actions import (
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
from .constants import Card, Good, Location, Roll
from .serialize import card as serialize_card

# Reverse mapping from serialized card name to Card enum
_CARD_FROM_NAME: dict[str, Card] = {serialize_card(c): c for c in Card}

# Mapping from Good enum to title-cased name (e.g., Good.RED -> "Red")
_GOOD_NAMES: dict[Good, str] = {g: g.name.title() for g in Good}

# Reverse mapping from title-cased name to Good enum
_GOOD_FROM_NAME: dict[str, Good] = {v: k for k, v in _GOOD_NAMES.items()}


def card_from_name(name: str) -> Card:
    """Resolve a serialized card name (e.g., ``"OneGood"``) to a Card enum value."""
    result = _CARD_FROM_NAME.get(name)
    if result is None:
        raise ValueError(f"Unknown card name: {name!r}")
    return result


def good_from_name(name: str) -> Good:
    """Resolve a title-cased good name (e.g., ``"Red"``) to a Good enum value."""
    result = _GOOD_FROM_NAME.get(name)
    if result is None:
        raise ValueError(f"Unknown good name: {name!r}")
    return result


# RedTileAction method serialization
_METHOD_TO_JSON: dict[str, str] = {
    RedTileAction.TO_FOUR: "to_four",
    RedTileAction.REROLL: "reroll",
}
_METHOD_FROM_JSON: dict[str, str] = {v: k for k, v in _METHOD_TO_JSON.items()}


def _roll_to_json(roll: Roll) -> list[int]:
    return list(roll)


def _roll_from_json(data: list[int]) -> Roll:
    assert len(data) == 2, f"Roll must have exactly 2 elements, got {len(data)}"
    return typing.cast(Roll, (data[0], data[1]))


def _good_counter_to_json(gc: typing.Counter[Good]) -> dict[str, int]:
    return {_GOOD_NAMES[k]: v for k, v in gc.items() if v > 0}


def _good_counter_from_json(data: dict[str, int]) -> typing.Counter[Good]:
    return Counter({_GOOD_FROM_NAME[k]: v for k, v in data.items()})


def _roll_or_red_tile_to_json(roll: Roll | RedTileAction) -> list[int] | dict[str, object]:
    if isinstance(roll, RedTileAction):
        return _red_tile_action_to_json_inner(roll)
    return _roll_to_json(roll)


def _roll_or_red_tile_from_json(data: list[int] | dict[str, object]) -> Roll | RedTileAction:
    if isinstance(data, dict):
        return _red_tile_action_from_json_inner(data)
    return _roll_from_json(data)


def _red_tile_action_to_json_inner(action: RedTileAction) -> dict[str, object]:
    return {
        "type": "RedTileAction",
        "initial_roll": _roll_to_json(action.initial_roll),
        "final_roll": _roll_to_json(action.final_roll),
        "method": _METHOD_TO_JSON[action.method],
    }


def _red_tile_action_from_json_inner(data: dict[str, object]) -> RedTileAction:
    return RedTileAction(
        initial_roll=_roll_from_json(typing.cast(list[int], data["initial_roll"])),
        final_roll=_roll_from_json(typing.cast(list[int], data["final_roll"])),
        method=typing.cast(RedTileAction._Method, _METHOD_FROM_JSON[typing.cast(str, data["method"])]),
    )


def action_to_json(action: PlayerAction) -> dict[str, object]:
    """Serialize a PlayerAction to a JSON-compatible dict."""
    if isinstance(action, YieldTurn):
        return {"type": "YieldTurn"}

    if isinstance(action, Move):
        return {"type": "Move", "location": int(action.tile), "skip_assistant": action.skip_assistant}

    if isinstance(action, Pay):
        return {"type": "Pay"}

    if isinstance(action, ChooseReward):
        choice: str
        if action.choice == ChooseReward.LIRA:
            choice = "Lira"
        else:
            choice = serialize_card(action.choice)
        return {"type": "ChooseReward", "choice": choice}

    if isinstance(action, EncounterGovernor):
        cost: str
        if isinstance(action.cost, Pay):
            cost = "pay"
        else:
            cost = serialize_card(action.cost)
        return {
            "type": "EncounterGovernor",
            "gain": serialize_card(action.gain),
            "cost": cost,
            "roll": _roll_to_json(action.roll),
        }

    if isinstance(action, EncounterSmuggler):
        smug_cost: str
        if isinstance(action.cost, Pay):
            smug_cost = "pay"
        else:
            smug_cost = _GOOD_NAMES[action.cost]
        return {
            "type": "EncounterSmuggler",
            "gain": _GOOD_NAMES[action.gain],
            "cost": smug_cost,
            "roll": _roll_to_json(action.roll),
        }

    if isinstance(action, SkipTileAction):
        return {"type": "SkipTileAction"}

    if isinstance(action, GenericTileAction):
        return {"type": "GenericTileAction"}

    if isinstance(action, MosqueAction):
        return {"type": "MosqueAction", "good": _GOOD_NAMES[action.good_color]}

    if isinstance(action, MarketAction):
        return {
            "type": "MarketAction",
            "goods": _good_counter_to_json(action.goods),
            "new_demand": _good_counter_to_json(action.new_demand),
        }

    if isinstance(action, BlackMarketAction):
        return {
            "type": "BlackMarketAction",
            "good": _GOOD_NAMES[action.good],
            "roll": _roll_or_red_tile_to_json(action.roll),
        }

    if isinstance(action, TeaHouseAction):
        return {
            "type": "TeaHouseAction",
            "call": action.call,
            "roll": _roll_or_red_tile_to_json(action.roll),
        }

    if isinstance(action, CaravansaryAction):
        gains_json: list[str] = []
        for g in action.gains:
            if g == CaravansaryAction.DISCARD:
                gains_json.append("discard")
            else:
                gains_json.append(serialize_card(g))
        return {
            "type": "CaravansaryAction",
            "gains": gains_json,
            "cost": serialize_card(action.cost),
        }

    if isinstance(action, SultansPalaceAction):
        return {"type": "SultansPalaceAction", "goods": _good_counter_to_json(action.goods)}

    if isinstance(action, FountainAction):
        return {"type": "FountainAction", "assistant_locations": sorted(int(loc) for loc in action.assistant_locations)}

    if isinstance(action, PoliceStationAction):
        return {
            "type": "PoliceStationAction",
            "location": int(action.location),
            "action": action_to_json(action.action),
        }

    if isinstance(action, DoubleCardAction):
        return {
            "type": "DoubleCardAction",
            "card": serialize_card(action.card),
            "actions": [action_to_json(a) for a in action.actions],
        }

    if isinstance(action, SellAnyCardAction):
        return {
            "type": "SellAnyCardAction",
            "action": action_to_json(action.action),
        }

    if isinstance(action, GreenTileAction):
        return {"type": "GreenTileAction", "good": _GOOD_NAMES[action.good]}

    if isinstance(action, RedTileAction):
        return _red_tile_action_to_json_inner(action)

    if isinstance(action, YellowTileAction):
        return {"type": "YellowTileAction", "from_tile": int(action.from_tile)}

    if isinstance(action, ExtraMoveCardAction):
        return {
            "type": "ExtraMoveCardAction",
            "location": int(action.move.tile),
            "skip_assistant": action.move.skip_assistant,
        }

    if isinstance(action, NoMoveCardAction):
        return {"type": "NoMoveCardAction", "skip_assistant": action.skip_assistant}

    if isinstance(action, OneGoodCardAction):
        return {"type": "OneGoodCardAction", "good": _GOOD_NAMES[action.good]}

    if isinstance(action, FiveLiraCardAction):
        return {"type": "FiveLiraCardAction"}

    if isinstance(action, ReturnAssistantCardAction):
        return {"type": "ReturnAssistantCardAction", "from_tile": int(action.from_tile)}

    if isinstance(action, ArrestFamilyCardAction):
        reward_choice: str
        if action.reward.choice == ChooseReward.LIRA:
            reward_choice = "Lira"
        else:
            reward_choice = serialize_card(action.reward.choice)
        return {"type": "ArrestFamilyCardAction", "reward": {"choice": reward_choice}}

    raise ValueError(f"Unknown action type: {type(action).__name__}")


def action_from_json(data: dict[str, object]) -> PlayerAction:
    """Deserialize a JSON-compatible dict to a PlayerAction."""
    action_type = data["type"]

    if action_type == "YieldTurn":
        return YieldTurn()

    if action_type == "Move":
        return Move(
            tile=Location(typing.cast(int, data["location"])),
            skip_assistant=typing.cast(bool, data["skip_assistant"]),
        )

    if action_type == "Pay":
        return Pay()

    if action_type == "ChooseReward":
        choice_str = typing.cast(str, data["choice"])
        if choice_str == "Lira":
            return ChooseReward(ChooseReward.LIRA)
        return ChooseReward(_CARD_FROM_NAME[choice_str])

    if action_type == "EncounterGovernor":
        cost_str = typing.cast(str, data["cost"])
        gov_cost: Card | Pay
        if cost_str == "pay":
            gov_cost = Pay()
        else:
            gov_cost = _CARD_FROM_NAME[cost_str]
        return EncounterGovernor(
            gain=_CARD_FROM_NAME[typing.cast(str, data["gain"])],
            cost=gov_cost,
            roll=_roll_from_json(typing.cast(list[int], data["roll"])),
        )

    if action_type == "EncounterSmuggler":
        cost_str = typing.cast(str, data["cost"])
        smug_cost: Good | Pay
        if cost_str == "pay":
            smug_cost = Pay()
        else:
            smug_cost = _GOOD_FROM_NAME[cost_str]
        return EncounterSmuggler(
            gain=_GOOD_FROM_NAME[typing.cast(str, data["gain"])],
            cost=smug_cost,
            roll=_roll_from_json(typing.cast(list[int], data["roll"])),
        )

    if action_type == "SkipTileAction":
        return SkipTileAction()

    if action_type == "GenericTileAction":
        return GenericTileAction()

    if action_type == "MosqueAction":
        return MosqueAction(good_color=_GOOD_FROM_NAME[typing.cast(str, data["good"])])

    if action_type == "MarketAction":
        return MarketAction(
            goods=_good_counter_from_json(typing.cast(dict[str, int], data["goods"])),
            new_demand=_good_counter_from_json(typing.cast(dict[str, int], data["new_demand"])),
        )

    if action_type == "BlackMarketAction":
        return BlackMarketAction(
            good=typing.cast(BlackMarketAction._Choices, _GOOD_FROM_NAME[typing.cast(str, data["good"])]),
            roll=_roll_or_red_tile_from_json(typing.cast(list[int] | dict[str, object], data["roll"])),
        )

    if action_type == "TeaHouseAction":
        return TeaHouseAction(
            call=typing.cast(int, data["call"]),
            roll=_roll_or_red_tile_from_json(typing.cast(list[int] | dict[str, object], data["roll"])),
        )

    if action_type == "CaravansaryAction":
        gains_data = typing.cast(list[str], data["gains"])
        gains: list[Card | str] = []
        for g in gains_data:
            if g == "discard":
                gains.append(CaravansaryAction.DISCARD)
            else:
                gains.append(_CARD_FROM_NAME[g])
        return CaravansaryAction(
            gains=typing.cast(tuple[CaravansaryAction._Gain, CaravansaryAction._Gain], tuple(gains)),
            cost=_CARD_FROM_NAME[typing.cast(str, data["cost"])],
        )

    if action_type == "SultansPalaceAction":
        return SultansPalaceAction(goods=_good_counter_from_json(typing.cast(dict[str, int], data["goods"])))

    if action_type == "FountainAction":
        locations = typing.cast(list[int], data["assistant_locations"])
        return FountainAction(assistant_locations=[Location(loc) for loc in locations])

    if action_type == "PoliceStationAction":
        inner_action = action_from_json(typing.cast(dict[str, object], data["action"]))
        return PoliceStationAction(
            location=Location(typing.cast(int, data["location"])),
            action=inner_action,  # type: ignore[arg-type]
        )

    if action_type == "DoubleCardAction":
        card = _CARD_FROM_NAME[typing.cast(str, data["card"])]
        actions_data = typing.cast(list[dict[str, object]], data["actions"])
        assert len(actions_data) == 2, "DoubleCardAction requires exactly 2 actions"
        inner_actions = tuple(action_from_json(a) for a in actions_data)
        return DoubleCardAction(
            card=card,
            actions=typing.cast(tuple[typing.Any, typing.Any], inner_actions),
        )

    if action_type == "SellAnyCardAction":
        inner = action_from_json(typing.cast(dict[str, object], data["action"]))
        assert isinstance(inner, MarketAction), "SellAnyCardAction requires a MarketAction"
        return SellAnyCardAction(action=inner)

    if action_type == "GreenTileAction":
        return GreenTileAction(good=_GOOD_FROM_NAME[typing.cast(str, data["good"])])

    if action_type == "RedTileAction":
        return _red_tile_action_from_json_inner(data)

    if action_type == "YellowTileAction":
        return YellowTileAction(from_tile=Location(typing.cast(int, data["from_tile"])))

    if action_type == "ExtraMoveCardAction":
        return ExtraMoveCardAction(
            move=Move(
                tile=Location(typing.cast(int, data["location"])),
                skip_assistant=typing.cast(bool, data["skip_assistant"]),
            )
        )

    if action_type == "NoMoveCardAction":
        return NoMoveCardAction(skip_assistant=typing.cast(bool, data["skip_assistant"]))

    if action_type == "OneGoodCardAction":
        return OneGoodCardAction(good=_GOOD_FROM_NAME[typing.cast(str, data["good"])])

    if action_type == "FiveLiraCardAction":
        return FiveLiraCardAction()

    if action_type == "ReturnAssistantCardAction":
        return ReturnAssistantCardAction(from_tile=Location(typing.cast(int, data["from_tile"])))

    if action_type == "ArrestFamilyCardAction":
        reward_data = typing.cast(dict[str, str], data["reward"])
        choice_str = reward_data["choice"]
        if choice_str == "Lira":
            reward = ChooseReward(ChooseReward.LIRA)
        else:
            reward = ChooseReward(_CARD_FROM_NAME[choice_str])
        return ArrestFamilyCardAction(reward=reward)

    raise ValueError(f"Unknown action type: {action_type}")


def turn_to_json(actions: Iterable[PlayerAction]) -> list[dict[str, object]]:
    """Serialize a sequence of actions (one turn) to a list of JSON dicts."""
    return [action_to_json(a) for a in actions]


def turn_from_json(data: list[dict[str, object]]) -> list[PlayerAction]:
    """Deserialize a list of JSON dicts to a list of PlayerAction objects."""
    return [action_from_json(d) for d in data]
