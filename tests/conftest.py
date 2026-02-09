"""Shared test fixtures for Istanbul game tests."""
import pytest

from istanbul_game.game import GameState
from istanbul_game.constants import Player, Location, Tile
from istanbul_game.lib.utils import ImmutableInvertibleMapping

from tests.helpers import create_game, create_standard_location_map


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
