"""Shared test utilities for Istanbul game tests."""

from collections import Counter

from istanbul_game.constants import Card, Good, Location, Player, Tile
from istanbul_game.game import GameState
from istanbul_game.lib.utils import ImmutableInvertibleMapping

_DEFAULT_GOVERNOR_LOCATION = Location(1)
_DEFAULT_SMUGGLER_LOCATION = Location(2)


def create_standard_location_map() -> ImmutableInvertibleMapping[Location, Tile]:
    """Create a standard 4x4 board layout with tiles in enum order."""
    tiles = list(Tile)
    return ImmutableInvertibleMapping({Location(i): tiles[i - 1] for i in range(1, 17)})


def create_game(
    players: tuple[Player, ...] = (Player.RED, Player.BLUE),
    location_map: ImmutableInvertibleMapping[Location, Tile] | None = None,
    small_demand: Counter[Good] | None = None,
    large_demand: Counter[Good] | None = None,
    governor_location: Location = _DEFAULT_GOVERNOR_LOCATION,
    smuggler_location: Location = _DEFAULT_SMUGGLER_LOCATION,
    player_hands: dict[Player, Card] | None = None,
) -> GameState:
    """Create a GameState with sensible defaults for testing."""
    if location_map is None:
        location_map = create_standard_location_map()
    if small_demand is None:
        small_demand = Counter({Good.RED: 2, Good.GREEN: 2, Good.YELLOW: 1})
    if large_demand is None:
        large_demand = Counter({Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2, Good.BLUE: 1})
    if player_hands is None:
        player_hands = {p: Card.ONE_GOOD for p in players}

    return GameState(
        players=players,
        location_map=location_map,
        small_demand=small_demand,
        large_demand=large_demand,
        governor_location=governor_location,
        smuggler_location=smuggler_location,
        player_hands=player_hands,
    )


def move_player_to_tile(game: GameState, player: Player, tile: Tile) -> None:
    """Helper to directly move a player to a tile for testing."""
    player_state = game.player_states[player]
    old_tile = game.location_map[player_state.location]
    new_loc = game.location_map.inverse[tile]

    game.tile_states[old_tile].players.remove(player)
    player_state.location = new_loc
    game.tile_states[tile].players.add(player)
