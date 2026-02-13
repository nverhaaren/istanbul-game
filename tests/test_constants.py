"""Tests for constants module."""

from istanbul_game.constants import ROLL_LOCATIONS, Card, Good, Location, Player, Tile


def test_card_enum_exists() -> None:
    """Test that Card enum has expected values."""
    assert Card.ONE_GOOD is not None
    assert Card.FIVE_LIRA is not None


def test_good_enum_exists() -> None:
    """Test that Good enum has expected values."""
    assert Good.RED is not None
    assert Good.GREEN is not None
    assert Good.YELLOW is not None
    assert Good.BLUE is not None


def test_player_enum_exists() -> None:
    """Test that Player enum has expected colors."""
    assert Player.RED is not None
    assert Player.BLUE is not None


def test_tile_enum_exists() -> None:
    """Test that Tile enum has expected tiles."""
    assert Tile.FOUNTAIN is not None
    assert Tile.POLICE_STATION is not None
    assert Tile.SMALL_MARKET is not None


def test_roll_locations_mapping() -> None:
    """Test that ROLL_LOCATIONS contains expected mappings."""
    assert len(ROLL_LOCATIONS) > 0
    # ROLL_LOCATIONS is an ImmutableInvertibleMapping
    assert Location(7) in ROLL_LOCATIONS  # Sum of 7 from dice roll
