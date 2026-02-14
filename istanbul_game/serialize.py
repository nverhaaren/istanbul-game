import typing

from .constants import ROLL_LOCATIONS, Card, Good, Location, Tile
from .game import GameState
from .player import PlayerState
from .tiles import (
    CaravansaryTileState,
    GemstoneDealerTileState,
    GenericTileState,
    MarketTileState,
    MosqueTileState,
    PostOfficeTileState,
    SultansPalaceTileState,
    TileState,
    WainwrightTileState,
)
from .turn import TurnState

GENERIC_STATE_TILES = frozenset(
    {
        Tile.FABRIC_WAREHOUSE,
        Tile.FRUIT_WAREHOUSE,
        Tile.FOUNTAIN,
        Tile.SPICE_WAREHOUSE,
        Tile.BLACK_MARKET,
        Tile.TEA_HOUSE,
    }
)


def card(c: Card) -> str:
    return {
        Card.ONE_GOOD: "OneGood",
        Card.FIVE_LIRA: "FiveLira",
        Card.EXTRA_MOVE: "ExtraMove",
        Card.NO_MOVE: "NoMove",
        Card.RETURN_ASSISTANT: "ReturnAssistant",
        Card.ARREST_FAMILY: "ArrestFamily",
        Card.SELL_ANY: "SellAny",
        Card.DOUBLE_SULTAN: "2xSultansPalace",
        Card.DOUBLE_PO: "2xPostOffice",
        Card.DOUBLE_DEALER: "2xGemstoneDealer",
    }[c]


def good_counter(gc: typing.Counter[Good]) -> dict:
    return {k.name.title(): v for k, v in gc.items()}


def game_state(gs: GameState) -> dict:
    return {
        "immutable": {
            "players": [p.value for p in gs.players],
            "player_count": gs.player_count,
            "victory_threshold": gs.victory_threshold,
            "tile_layout": [gs.location_map[Location(i)].name for i in range(1, 17)],
        },
        "mutable": {
            "turn_state": turn_state(gs.turn_state),
            "outstanding_reward_choices": gs.outstanding_reward_choices,
            "completed": gs.completed,
            "tile_states": [
                full_tile_state(gs.location_map[Location(i)], gs.tile_states[gs.location_map[Location(i)]], Location(i))
                for i in range(1, 17)
            ],
            "player_states": [player_state(gs.player_states[p]) for p in gs.players],
        },
        "derived": {
            "current_player_idx": gs.current_player_idx,
            "current_player": gs.current_player.value,
            "current_player_state": player_state(gs.current_player_state),
            "current_player_location": gs.current_player_location,
            "current_player_tile": gs.current_player_tile.name,
            "current_player_tile_state": general_tile_state(gs.current_player_tile_state),
            "ranking": {p.value: score[:4] for p, score in gs.ranking().items()},
        },
    }


def player_state(ps: PlayerState) -> dict:
    return {
        "color": ps.color.value.title(),
        "hand": {card(k): v for k, v in ps.hand.items() if v > 0},
        "lira": ps.lira,
        "rubies": ps.rubies,
        "cart_max": ps.cart_max,
        "cart_contents": good_counter(ps.cart_contents),
        "stack_size": ps.stack_size,
        "tiles": [g.name.title() for g in ps.tiles],
        "location": ps.location,
        "assistant_locations": list(ps.assistant_locations),
        "family_location": ps.family_location,
    }


def turn_state(ts: TurnState) -> dict:
    return {
        "players": [p.value for p in ts.players],
        "current_player_idx": ts.current_player_idx,
        "current_player": ts.current_player.value,
        "current_phase": ts.current_phase,
        "yield_required": ts.yield_required,
    }


def full_tile_state(tile: Tile, ts: TileState, loc: Location) -> dict:
    result = {
        "name": tile.value,
        "location": loc,
        "roll_location": ROLL_LOCATIONS.inverse[tile],
        "general": general_tile_state(ts),
    }
    if isinstance(ts, GenericTileState):
        return result
    if isinstance(ts, MarketTileState):
        result["immutable"] = market_immutable_tile_state(ts)
        result["mutable"] = market_mutable_tile_state(ts)
        return result
    result["mutable"] = {
        MosqueTileState: mosque_tile_state,
        PostOfficeTileState: post_office_tile_state,
        CaravansaryTileState: caravansary_tile_state,
        WainwrightTileState: wainwright_tile_state,
        SultansPalaceTileState: sultans_palace_tile_state,
        GemstoneDealerTileState: gemstone_dealer_tile_state,
    }[type(ts)](ts)  # type: ignore[operator]
    return result


def general_tile_state(ts: TileState) -> dict:
    return {
        "governor": ts.governor,
        "smuggler": ts.smuggler,
        "assistants": [p.value.title() for p in ts.assistants],
        "family_members": [p.value.title() for p in ts.family_members],
        "players": [p.value.title() for p in ts.players],
    }


def mosque_tile_state(ts: MosqueTileState) -> dict[str, int]:
    return {k.name.title(): v for k, v in ts.available_tiles.items()}


def post_office_tile_state(ts: PostOfficeTileState) -> dict:
    goods, lira = ts.available()
    return {
        "position": ts.position,
        "available": {
            "goods": [g.name.title() for g in goods],
            "lira": lira,
        },
    }


def caravansary_tile_state(ts: CaravansaryTileState) -> dict:
    return {
        "discard": list(map(card, ts.discard_pile)),
        "awaiting_discard": ts.awaiting_discard,
    }


def wainwright_tile_state(ts: WainwrightTileState) -> dict:
    return {
        "extensions": ts.extensions,
    }


def market_mutable_tile_state(ts: MarketTileState) -> dict:
    return {
        "demand": good_counter(ts.demand) if ts.demand is not None else None,
        "expecting_demand": ts.expecting_demand,
    }


def market_immutable_tile_state(ts: MarketTileState) -> dict:
    return {
        "one_cost": ts.one_cost,
        "cost_map": [sum(range(ts.one_cost, ts.one_cost + i)) for i in range(1, 6)],
    }


def sultans_palace_tile_state(ts: SultansPalaceTileState) -> dict:
    ts_required = ts.required()
    required: dict[Good | None, int] | None = dict(ts_required) if ts_required is not None else None
    if required is not None and None not in required:
        required[None] = 0
    return {
        "required_count": ts.required_count,
        "required": (
            {k.value.title() if k is not None else "Any": v for k, v in required.items()}
            if required is not None
            else None
        ),
    }


def gemstone_dealer_tile_state(ts: GemstoneDealerTileState) -> dict:
    return {
        "cost": ts.cost,
    }
