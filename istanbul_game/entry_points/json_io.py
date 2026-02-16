"""Entry point that reads game setup and actions as JSON from stdin and outputs game state to stdout.

.. note::

    This module uses ``assert`` for input validation. Do not run with
    Python's ``-O`` flag, which disables assertions.

Input Format
------------

A single JSON object on stdin::

    {
        "setup": {
            "players": ["Red", "Blue", "Green"],
            "governor_location": 1,
            "smuggler_location": 2,
            "small_market_demand": {"Red": 2, "Green": 2, "Yellow": 1},
            "large_market_demand": {"Red": 2, "Green": 1, "Yellow": 1, "Blue": 1},
            "starting_cards": {"Red": "OneGood", "Blue": "OneGood", "Green": "OneGood"},
            "tile_layout": ["GREAT_MOSQUE", "POST_OFFICE", ...]
        },
        "turns": [
            [{"type": "Move", "location": 8, "skip_assistant": false},
             {"type": "GenericTileAction"},
             {"type": "YieldTurn"}],
            ...
        ],
        "trace": false
    }

- ``setup.tile_layout`` is optional and defaults to the standard tile order.
  Tile names use the ``UPPER_SNAKE_CASE`` enum names (matching serialization output),
  e.g., ``"GREAT_MOSQUE"``, ``"POST_OFFICE"``, ``"GEMSTONE_DEALER"``.
- ``trace`` is optional and defaults to ``false``.

Output
------

- If ``trace`` is false: a single JSON game state object (the final state).
- If ``trace`` is true: a JSON object with ``"initial"`` (starting state) and
  ``"turns"`` (list of states after each turn).

See :mod:`istanbul_game.action_json` for the JSON action format and
:mod:`istanbul_game.serialize` for the output schema.
"""

import json
import sys
import typing
from collections import Counter

from .. import serialize
from ..action_json import card_from_name, good_from_name, turn_from_json
from ..constants import DEFAULT_LOCATIONS, Good, Location, Player, Tile
from ..game import GameState
from ..lib.utils import ImmutableInvertibleMapping


def _load_player(name: str) -> Player:
    """Resolve a player name like 'Red' to a Player enum value."""
    for p in Player:
        if p.value == name:
            return p
    raise ValueError(f"Unknown player: {name}")


def _load_good_counter_from_json(data: dict[str, int]) -> typing.Counter[Good]:
    """Convert {"Red": 2, "Green": 1} to a Counter[Good]."""
    return Counter({good_from_name(k): v for k, v in data.items()})


def game_state_from_json_setup(setup: dict[str, object]) -> GameState:
    """Create a GameState from a JSON setup dict.

    Required keys: players, governor_location, smuggler_location,
    small_market_demand, large_market_demand, starting_cards.

    Optional keys: tile_layout (defaults to standard). Tile names use
    ``UPPER_SNAKE_CASE`` enum names matching serialization output
    (e.g., ``"GREAT_MOSQUE"``).
    """
    players = tuple(_load_player(p) for p in typing.cast(list[str], setup["players"]))

    governor_location = Location(typing.cast(int, setup["governor_location"]))
    smuggler_location = Location(typing.cast(int, setup["smuggler_location"]))

    small_demand = _load_good_counter_from_json(typing.cast(dict[str, int], setup["small_market_demand"]))
    large_demand = _load_good_counter_from_json(typing.cast(dict[str, int], setup["large_market_demand"]))

    cards_data = typing.cast(dict[str, str], setup["starting_cards"])
    player_hands = {_load_player(p): card_from_name(c) for p, c in cards_data.items()}

    tile_layout_data = typing.cast(list[str] | None, setup.get("tile_layout"))
    location_map: ImmutableInvertibleMapping[Location, Tile]
    if tile_layout_data is not None:
        tile_by_name = {t.name: t for t in Tile}
        tile_mapping: dict[Location, Tile] = {}
        for idx, name in enumerate(tile_layout_data, 1):
            assert name in tile_by_name, f"Unknown tile name: {name!r}"
            tile_mapping[Location(idx)] = tile_by_name[name]
        location_map = ImmutableInvertibleMapping(tile_mapping)
    else:
        location_map = DEFAULT_LOCATIONS

    return GameState(
        players=players,
        location_map=location_map,
        small_demand=small_demand,
        large_demand=large_demand,
        governor_location=governor_location,
        smuggler_location=smuggler_location,
        player_hands=player_hands,
    )


def main() -> None:
    """Read JSON from stdin, replay game, output state to stdout."""
    input_data = json.load(sys.stdin)

    setup = typing.cast(dict[str, object], input_data["setup"])
    turns_data = typing.cast(list[list[dict[str, object]]], input_data.get("turns", []))
    trace_mode = typing.cast(bool, input_data.get("trace", False))

    gs = game_state_from_json_setup(setup)

    if trace_mode:
        trace_output: dict[str, object] = {"initial": serialize.game_state(gs), "turns": []}
        turns_list = typing.cast(list[dict], trace_output["turns"])
        for turn_data in turns_data:
            actions = turn_from_json(turn_data)
            for action in actions:
                gs.take_action(action)
            turns_list.append(serialize.game_state(gs))
        json.dump(trace_output, sys.stdout, indent=4)
    else:
        for turn_data in turns_data:
            actions = turn_from_json(turn_data)
            for action in actions:
                gs.take_action(action)
        json.dump(serialize.game_state(gs), sys.stdout, indent=4)

    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
