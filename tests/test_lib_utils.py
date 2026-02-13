"""Tests for lib/utils.py - ImmutableInvertibleMapping."""
import pytest

from istanbul_game.lib.utils import ImmutableInvertibleMapping
from istanbul_game.constants import Location, Tile


class TestImmutableInvertibleMapping:
    """Tests for ImmutableInvertibleMapping class."""

    def test_basic_lookup(self) -> None:
        """Can look up values by key."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b', 3: 'c'})
        assert mapping[1] == 'a'
        assert mapping[2] == 'b'
        assert mapping[3] == 'c'

    def test_inverse_lookup(self) -> None:
        """Can look up keys by value through inverse."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b', 3: 'c'})
        assert mapping.inverse['a'] == 1
        assert mapping.inverse['b'] == 2
        assert mapping.inverse['c'] == 3

    def test_contains(self) -> None:
        """Contains check works for keys."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b'})
        assert 1 in mapping
        assert 2 in mapping
        assert 3 not in mapping

    def test_inverse_contains(self) -> None:
        """Contains check works for inverse."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b'})
        assert 'a' in mapping.inverse
        assert 'b' in mapping.inverse
        assert 'c' not in mapping.inverse

    def test_len(self) -> None:
        """Length returns number of items."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b', 3: 'c'})
        assert len(mapping) == 3

    def test_iter(self) -> None:
        """Can iterate over keys."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b', 3: 'c'})
        keys = list(mapping)
        assert sorted(keys) == [1, 2, 3]

    def test_items(self) -> None:
        """Can get items as key-value pairs."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b'})
        items = list(mapping.items())
        assert (1, 'a') in items
        assert (2, 'b') in items

    def test_keys(self) -> None:
        """Can get keys."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b'})
        keys = list(mapping.keys())
        assert 1 in keys
        assert 2 in keys

    def test_values(self) -> None:
        """Can get values."""
        mapping = ImmutableInvertibleMapping({1: 'a', 2: 'b'})
        values = list(mapping.values())
        assert 'a' in values
        assert 'b' in values

    def test_get_with_default(self) -> None:
        """Get with default returns default for missing keys."""
        mapping = ImmutableInvertibleMapping({1: 'a'})
        assert mapping.get(1) == 'a'
        assert mapping.get(2) is None
        assert mapping.get(2, 'default') == 'default'

    def test_missing_key_raises(self) -> None:
        """Accessing missing key raises KeyError."""
        mapping = ImmutableInvertibleMapping({1: 'a'})
        with pytest.raises(KeyError):
            _ = mapping[999]

    def test_missing_value_in_inverse_raises(self) -> None:
        """Accessing missing value in inverse raises KeyError."""
        mapping = ImmutableInvertibleMapping({1: 'a'})
        with pytest.raises(KeyError):
            _ = mapping.inverse['z']

    def test_immutable_no_setitem(self) -> None:
        """Cannot modify mapping via setitem."""
        mapping = ImmutableInvertibleMapping({1: 'a'})
        with pytest.raises(TypeError):
            mapping[2] = 'b'  # type: ignore[index]

    def test_immutable_no_delitem(self) -> None:
        """Cannot modify mapping via delitem."""
        mapping = ImmutableInvertibleMapping({1: 'a'})
        with pytest.raises(TypeError):
            del mapping[1]  # type: ignore[arg-type]

    def test_inverse_is_also_immutable(self) -> None:
        """Inverse view is also immutable."""
        mapping = ImmutableInvertibleMapping({1: 'a'})
        with pytest.raises(TypeError):
            mapping.inverse['b'] = 2  # type: ignore[index]

    def test_with_location_and_tile(self) -> None:
        """Works with Location and Tile types."""
        mapping = ImmutableInvertibleMapping({
            Location(1): Tile.FOUNTAIN,
            Location(2): Tile.POLICE_STATION,
        })
        assert mapping[Location(1)] == Tile.FOUNTAIN
        assert mapping.inverse[Tile.FOUNTAIN] == Location(1)

    def test_duplicate_values_rejected(self) -> None:
        """Duplicate values in input raise TypeError."""
        # ImmutableInvertibleMapping requires values to be unique for inverse
        with pytest.raises(TypeError, match="not injective"):
            ImmutableInvertibleMapping({1: 'a', 2: 'a'})
