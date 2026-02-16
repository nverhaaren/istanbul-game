"""Bidirectional conversion between CSV turn rows and JSON action format.

CSV -> JSON requires game state context (via PhaseLoader) because the CSV format
is ambiguous without knowing which cards the player holds. The conversion parses
the CSV row into PlayerAction objects and serializes each to JSON.

JSON -> CSV reconstructs a compact CSV TurnRow from a list of JSON action dicts.
This direction does not require game state context since the JSON format is
unambiguous.
"""

import typing

from ..action_json import (
    action_from_json,
    action_to_json,
)
from ..actions import (
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
from ..constants import Card, Good, Roll
from ..serialize import card as serialize_card
from .phases import PhaseLoader, TurnRow

# Reverse good code mapping: Good.RED -> "R", etc.
_GOOD_CODE: dict[Good, str] = {g: g.name[0] for g in Good}


def csv_turn_to_json(phase_loader: PhaseLoader, turn_row: TurnRow) -> list[dict[str, object]]:
    """Convert a CSV turn row to a list of JSON action dicts.

    Requires game state context via PhaseLoader because CSV parsing is
    context-dependent (e.g., determining which card matches "Card").
    Each action is applied to the PhaseLoader's game state as it is parsed,
    keeping the state in sync for subsequent turns.
    """
    result: list[dict[str, object]] = []
    for action in phase_loader.load_turn(turn_row):
        result.append(action_to_json(action))
        phase_loader.gs.take_action(action)
    return result


def _serialize_roll(roll: Roll) -> str:
    return f"{roll[0]}+{roll[1]}"


def _serialize_good_counter(gc: typing.Counter[Good]) -> str:
    """Serialize a good counter to compact CSV format like '2RGY'."""
    parts: list[str] = []
    for good in Good:
        count = gc.get(good, 0)
        if count == 0:
            continue
        if count > 1:
            parts.append(f"{count}{_GOOD_CODE[good]}")
        else:
            parts.append(_GOOD_CODE[good])
    return "".join(parts)


def _serialize_roll_or_red_tile(roll_or_rta: Roll | RedTileAction) -> str:
    if isinstance(roll_or_rta, RedTileAction):
        method_code = "F" if roll_or_rta.method == RedTileAction.TO_FOUR else "R"
        initial = _serialize_roll(roll_or_rta.initial_roll)
        final = _serialize_roll(roll_or_rta.final_roll)
        return f"RedTile {initial} {method_code} {final}"
    return _serialize_roll(roll_or_rta)


def _card_csv_name(card: Card) -> str:
    """Get the CSV-style card name for use in Card- prefixed actions."""
    return serialize_card(card)


def _action_to_csv_move(action: PlayerAction) -> str | None:
    """Convert a phase-1 action to its CSV Move column representation."""
    if isinstance(action, Move):
        suffix = "!" if action.skip_assistant else ""
        return f"{action.tile}{suffix}"
    if isinstance(action, ExtraMoveCardAction):
        suffix = "!" if action.move.skip_assistant else ""
        return f"Card-ExtraMove {action.move.tile}{suffix}"
    if isinstance(action, NoMoveCardAction):
        suffix = "!" if action.skip_assistant else ""
        return f"Card-NoMove{suffix}"
    if isinstance(action, ReturnAssistantCardAction):
        return f"Card-ReturnAssistant {action.from_tile}"
    if isinstance(action, YellowTileAction):
        return f"YellowTile {action.from_tile}"
    if isinstance(action, OneGoodCardAction):
        return f"Card-1Good {_GOOD_CODE[action.good]}"
    if isinstance(action, FiveLiraCardAction):
        return "Card-5Lira"
    if isinstance(action, ArrestFamilyCardAction):
        if action.reward.choice == ChooseReward.LIRA:
            return "Card-ArrestFamily 3"
        return f"Card-ArrestFamily {serialize_card(action.reward.choice)}"
    return None


def _action_to_csv_tile(action: PlayerAction) -> str | None:
    """Convert a phase-3 action to its CSV Action column representation."""
    if isinstance(action, GenericTileAction):
        return ""
    if isinstance(action, SkipTileAction):
        return "!"
    if isinstance(action, MosqueAction):
        return _GOOD_CODE[action.good_color]
    if isinstance(action, MarketAction):
        goods = _serialize_good_counter(action.goods)
        demand = _serialize_good_counter(action.new_demand)
        return f"{goods} {demand}"
    if isinstance(action, BlackMarketAction):
        return f"{_GOOD_CODE[action.good]} {_serialize_roll_or_red_tile(action.roll)}"
    if isinstance(action, TeaHouseAction):
        return f"{action.call} {_serialize_roll_or_red_tile(action.roll)}"
    if isinstance(action, CaravansaryAction):
        parts: list[str] = []
        for g in action.gains:
            if g == CaravansaryAction.DISCARD:
                parts.append("Discard")
            else:
                parts.append(serialize_card(g))
        parts.append(serialize_card(action.cost))
        return " ".join(parts)
    if isinstance(action, SultansPalaceAction):
        return _serialize_good_counter(action.goods)
    if isinstance(action, FountainAction):
        locs = sorted(action.assistant_locations)
        return " ".join(str(loc) for loc in locs)
    if isinstance(action, PoliceStationAction):
        inner = _action_to_csv_tile(action.action)
        assert inner is not None, "Police station inner action must be a tile action"
        return f"{action.location} {inner}".rstrip()
    if isinstance(action, GreenTileAction):
        return f"GreenTile {_GOOD_CODE[action.good]}"
    if isinstance(action, DoubleCardAction):
        card_name = _card_csv_name(action.card)
        if action.card in {Card.DOUBLE_PO, Card.DOUBLE_DEALER}:
            return f"Card-{card_name}"
        # DOUBLE_SULTAN: need sub-action goods
        assert action.card is Card.DOUBLE_SULTAN
        first = typing.cast(SultansPalaceAction, action.actions[0])
        second = typing.cast(SultansPalaceAction, action.actions[1])
        return f"Card-{card_name} {_serialize_good_counter(first.goods)} {_serialize_good_counter(second.goods)}"
    if isinstance(action, SellAnyCardAction):
        inner_market = _action_to_csv_tile(action.action)
        return f"Card-SellAny {inner_market}"
    return None


def _reward_to_csv(action: ChooseReward) -> str:
    """Convert a ChooseReward action to CSV reward notation."""
    if action.choice == ChooseReward.LIRA:
        return "3"
    return serialize_card(action.choice)


def _governor_to_csv(action: EncounterGovernor) -> str:
    """Convert an EncounterGovernor to CSV notation."""
    gain = serialize_card(action.gain)
    cost = "-2" if isinstance(action.cost, Pay) else serialize_card(action.cost)
    return f"{gain} {cost} {_serialize_roll(action.roll)}"


def _smuggler_to_csv(action: EncounterSmuggler) -> str:
    """Convert an EncounterSmuggler to CSV notation."""
    gain = _GOOD_CODE[action.gain]
    cost = "-2" if isinstance(action.cost, Pay) else _GOOD_CODE[action.cost]
    return f"{gain} {cost} {_serialize_roll(action.roll)}"


# Actions that can appear as ancillary actions in any phase column
_ANCILLARY_TYPES = (OneGoodCardAction, FiveLiraCardAction, ArrestFamilyCardAction, YellowTileAction)


def json_turn_to_csv(action_dicts: list[dict[str, object]]) -> TurnRow:
    """Convert a list of JSON action dicts to a CSV TurnRow.

    Groups actions by phase based on type and encodes them back to
    the compact CSV notation.
    """
    actions = [action_from_json(d) for d in action_dicts]
    return actions_to_csv(actions)


def actions_to_csv(actions: list[PlayerAction]) -> TurnRow:
    """Convert a list of PlayerAction objects to a CSV TurnRow.

    Groups actions by phase based on type and encodes them back to
    the compact CSV notation.
    """
    move_parts: list[str] = []
    action_parts: list[str] = []
    reward_parts: list[str] = []
    gov_parts: list[str] = []
    smug_parts: list[str] = []

    # Track which phase we're building
    # Phase transitions: move actions -> (Pay/skip) -> tile action -> rewards/gov/smug -> YieldTurn
    phase = "move"  # "move", "tile", "post"

    for action in actions:
        if isinstance(action, YieldTurn):
            # If we never left move phase and this is a skip-assistant yield, don't add it
            continue

        # Ancillary card/tile actions can appear in any phase column
        if isinstance(action, _ANCILLARY_TYPES):
            csv_repr = _action_to_csv_move(action)
            assert csv_repr is not None
            if phase == "move":
                move_parts.append(csv_repr)
            elif phase == "tile":
                action_parts.append(csv_repr)
            else:
                reward_parts.append(csv_repr)
            continue

        if isinstance(action, Pay):
            phase = "tile"
            # Pay is implicit in CSV (not encoded)
            continue

        # Move-phase actions
        move_csv = _action_to_csv_move(action)
        if move_csv is not None and phase == "move":
            move_parts.append(move_csv)
            # Check if skip_assistant triggers early yield
            if isinstance(action, (Move, ExtraMoveCardAction, NoMoveCardAction)):
                if isinstance(action, (Move, NoMoveCardAction)):
                    sa = action.skip_assistant
                else:
                    sa = action.move.skip_assistant
                if sa:
                    # skip_assistant means the CSV uses ! suffix, and next is YieldTurn
                    # which we skip above
                    pass
            continue

        # Tile-phase actions
        tile_csv = _action_to_csv_tile(action)
        if tile_csv is not None:
            phase = "post"
            action_parts.append(tile_csv)
            continue

        # Post-tile actions
        if isinstance(action, ChooseReward):
            phase = "post"
            reward_parts.append(_reward_to_csv(action))
            continue

        if isinstance(action, EncounterGovernor):
            phase = "post"
            gov_parts.append(_governor_to_csv(action))
            continue

        if isinstance(action, EncounterSmuggler):
            phase = "post"
            smug_parts.append(_smuggler_to_csv(action))
            continue

    move_str = "; ".join(move_parts)
    action_str = "; ".join(action_parts)
    reward_str = "; ".join(reward_parts)
    gov_str = "; ".join(gov_parts)
    smug_str = "; ".join(smug_parts)

    return TurnRow(move_str, action_str, reward_str, gov_str, smug_str)
