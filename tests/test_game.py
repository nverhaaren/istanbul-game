"""Tests for game module."""
import pytest
from collections import Counter
from istanbul_game.game import GameState, taxicab_dist
from istanbul_game.constants import Player, Location, Tile, Good, Card
from istanbul_game.lib.utils import ImmutableInvertibleMapping


def test_taxicab_dist() -> None:
    """Test taxicab distance calculation."""
    # Same location
    assert taxicab_dist(Location(1), Location(1)) == 0

    # Adjacent horizontally
    assert taxicab_dist(Location(1), Location(2)) == 1

    # Adjacent vertically
    assert taxicab_dist(Location(1), Location(5)) == 1

    # Diagonal
    assert taxicab_dist(Location(1), Location(6)) == 2


def test_game_state_initialization() -> None:
    """Test that GameState can be initialized with valid parameters."""
    players = (Player.RED, Player.BLUE)
    location_map = ImmutableInvertibleMapping({
        Location(1): Tile.FOUNTAIN,
        Location(2): Tile.POLICE_STATION,
        Location(3): Tile.SMALL_MARKET,
        Location(4): Tile.LARGE_MARKET,
        Location(5): Tile.CARAVANSARY,
        Location(6): Tile.SMALL_MOSQUE,
        Location(7): Tile.GREAT_MOSQUE,
        Location(8): Tile.POST_OFFICE,
        Location(9): Tile.BLACK_MARKET,
        Location(10): Tile.TEA_HOUSE,
        Location(11): Tile.FABRIC_WAREHOUSE,
        Location(12): Tile.SPICE_WAREHOUSE,
        Location(13): Tile.FRUIT_WAREHOUSE,
        Location(14): Tile.WAINWRIGHT,
        Location(15): Tile.GEMSTONE_DEALER,
        Location(16): Tile.SULTANS_PALACE,
    })
    small_demand = Counter({Good.RED: 2, Good.GREEN: 2, Good.YELLOW: 1})
    large_demand = Counter({Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2, Good.BLUE: 1})
    player_hands = {
        Player.RED: Card.ONE_GOOD,
        Player.BLUE: Card.FIVE_LIRA,
    }

    game = GameState(
        players=players,
        location_map=location_map,
        small_demand=small_demand,
        large_demand=large_demand,
        governor_location=Location(3),
        smuggler_location=Location(4),
        player_hands=player_hands,
    )

    assert game.player_count == 2
    assert game.victory_threshold == 6  # 2 players = 6 rubies needed
    assert not game.completed
    assert game.current_player == Player.RED


def test_game_state_two_player_victory_threshold() -> None:
    """Test that 2-player games require 6 rubies to win."""
    players = (Player.RED, Player.BLUE)
    # Each location must map to a unique tile for invertibility
    tiles = list(Tile)
    location_map = ImmutableInvertibleMapping({Location(i): tiles[i-1] for i in range(1, 17)})

    game = GameState(
        players=players,
        location_map=location_map,
        small_demand=Counter({Good.RED: 2, Good.GREEN: 2, Good.YELLOW: 1}),
        large_demand=Counter({Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2, Good.BLUE: 1}),
        governor_location=Location(1),
        smuggler_location=Location(2),
        player_hands={p: Card.ONE_GOOD for p in players},
    )

    assert game.victory_threshold == 6


def test_game_state_multiplayer_victory_threshold() -> None:
    """Test that 3+ player games require 5 rubies to win."""
    players = (Player.RED, Player.BLUE, Player.GREEN)
    # Each location must map to a unique tile for invertibility
    tiles = list(Tile)
    location_map = ImmutableInvertibleMapping({Location(i): tiles[i-1] for i in range(1, 17)})

    game = GameState(
        players=players,
        location_map=location_map,
        small_demand=Counter({Good.RED: 2, Good.GREEN: 2, Good.YELLOW: 1}),
        large_demand=Counter({Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2, Good.BLUE: 1}),
        governor_location=Location(1),
        smuggler_location=Location(2),
        player_hands={p: Card.ONE_GOOD for p in players},
    )

    assert game.victory_threshold == 5
