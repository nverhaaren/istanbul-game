"""Shared test fixtures for Istanbul game tests."""
import pytest
from collections import Counter
from typing import Dict

from istanbul_game.game import GameState
from istanbul_game.constants import Player, Location, Tile, Good, Card
from istanbul_game.lib.utils import ImmutableInvertibleMapping


def create_standard_location_map() -> ImmutableInvertibleMapping[Location, Tile]:
    """Create a standard 4x4 board layout with tiles in enum order."""
    tiles = list(Tile)
    return ImmutableInvertibleMapping({Location(i): tiles[i - 1] for i in range(1, 17)})


def create_game(
    players: tuple[Player, ...] = (Player.RED, Player.BLUE),
    location_map: ImmutableInvertibleMapping[Location, Tile] | None = None,
    small_demand: Counter[Good] | None = None,
    large_demand: Counter[Good] | None = None,
    governor_location: Location = Location(1),
    smuggler_location: Location = Location(2),
    player_hands: Dict[Player, Card] | None = None,
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


@pytest.fixture
def two_player_game() -> GameState:
    """A minimal two-player game setup."""
    return create_game(players=(Player.RED, Player.BLUE))


@pytest.fixture
def three_player_game() -> GameState:
    """A three-player game setup."""
    return create_game(players=(Player.RED, Player.BLUE, Player.GREEN))


@pytest.fixture
def five_player_game() -> GameState:
    """A five-player game setup."""
    return create_game(
        players=(Player.RED, Player.BLUE, Player.GREEN, Player.YELLOW, Player.WHITE)
    )


@pytest.fixture
def standard_location_map() -> ImmutableInvertibleMapping[Location, Tile]:
    """Standard 4x4 board layout."""
    return create_standard_location_map()
