"""Tests for tile state classes."""

import collections.abc
from collections import Counter

import pytest

from istanbul_game.constants import Card, Good, Player, Tile
from istanbul_game.tiles import (
    CaravansaryTileState,
    GemstoneDealerTileState,
    GenericTileState,
    MarketTileState,
    MosqueTileState,
    PostOfficeTileState,
    SultansPalaceTileState,
    WainwrightTileState,
    initial_tile_state,
)


class TestTileStateBase:
    """Tests for base TileState class."""

    def test_initial_state(self) -> None:
        """TileState initializes with empty sets."""
        state = GenericTileState()
        assert state.governor is False
        assert state.smuggler is False
        assert state.assistants == set()
        assert state.family_members == set()
        assert state.players == set()

    def test_can_add_players(self) -> None:
        """Can add players to tile."""
        state = GenericTileState()
        state.players.add(Player.RED)
        state.players.add(Player.BLUE)
        assert Player.RED in state.players
        assert Player.BLUE in state.players

    def test_can_set_governor(self) -> None:
        """Can place governor on tile."""
        state = GenericTileState()
        state.governor = True
        assert state.governor is True


class TestMosqueTileState:
    """Tests for mosque tile behavior."""

    def test_great_mosque_goods(self) -> None:
        """Great mosque has blue and yellow tiles."""
        state = MosqueTileState({Good.BLUE, Good.YELLOW})
        assert Good.BLUE in state.available_tiles
        assert Good.YELLOW in state.available_tiles
        assert Good.RED not in state.available_tiles

    def test_small_mosque_goods(self) -> None:
        """Small mosque has red and green tiles."""
        state = MosqueTileState({Good.RED, Good.GREEN})
        assert Good.RED in state.available_tiles
        assert Good.GREEN in state.available_tiles
        assert Good.BLUE not in state.available_tiles

    def test_initial_tile_cost(self) -> None:
        """Tiles start at cost 2."""
        state = MosqueTileState({Good.BLUE, Good.YELLOW})
        assert state.available_tiles[Good.BLUE] == 2
        assert state.available_tiles[Good.YELLOW] == 2

    def test_take_action_increases_cost(self) -> None:
        """Taking a tile increases cost for next player."""
        state = MosqueTileState({Good.BLUE, Good.YELLOW})
        state.take_action(Good.BLUE)
        assert state.available_tiles[Good.BLUE] == 3

    def test_take_action_removes_at_max(self) -> None:
        """Tile is removed when cost reaches 5."""
        state = MosqueTileState({Good.BLUE, Good.YELLOW})
        # Cost progression: 2 -> 3 -> 4 -> 5 -> removed
        state.take_action(Good.BLUE)  # 3
        state.take_action(Good.BLUE)  # 4
        state.take_action(Good.BLUE)  # 5
        state.take_action(Good.BLUE)  # removed
        assert Good.BLUE not in state.available_tiles

    def test_cannot_take_unavailable_good(self) -> None:
        """Cannot take action for good not at this mosque."""
        state = MosqueTileState({Good.BLUE, Good.YELLOW})
        with pytest.raises(AssertionError):
            state.take_action(Good.RED)


class TestPostOfficeTileState:
    """Tests for post office cycling behavior."""

    def test_initial_position(self) -> None:
        """Post office starts at position 0."""
        state = PostOfficeTileState()
        assert state.position == 0

    def test_available_at_position_0(self) -> None:
        """At position 0, get first item of each pair."""
        state = PostOfficeTileState()
        goods, lira = state.available()
        # MAIL structure: (RED, GREEN), (2, 1), (BLUE, YELLOW), (2, 1)
        # At position 0: take second from each (GREEN, 1, YELLOW, 1)
        assert Good.GREEN in goods
        assert Good.YELLOW in goods
        assert lira == 2  # 1 + 1

    def test_take_action_advances_position(self) -> None:
        """Taking action advances position."""
        state = PostOfficeTileState()
        state.take_action()
        assert state.position == 1

    def test_position_cycles(self) -> None:
        """Position cycles back to 0 after reaching 4."""
        state = PostOfficeTileState()
        for _ in range(5):
            state.take_action()
        assert state.position == 0

    def test_take_action_returns_goods_and_lira(self) -> None:
        """Take action returns set of goods and lira amount."""
        state = PostOfficeTileState()
        goods, lira = state.take_action()
        assert isinstance(goods, collections.abc.Set)
        assert isinstance(lira, int)
        assert len(goods) == 2
        assert lira >= 0


class TestCaravansaryTileState:
    """Tests for caravansary discard pile behavior."""

    def test_initial_state(self) -> None:
        """Caravansary starts with empty discard pile."""
        state = CaravansaryTileState()
        assert state.discard_pile == []
        assert state.awaiting_discard is False

    def test_discard_onto_adds_card(self) -> None:
        """Cards can be discarded onto pile."""
        state = CaravansaryTileState()
        state.awaiting_discard = True
        state.discard_onto(Card.ONE_GOOD)
        assert Card.ONE_GOOD in state.discard_pile
        assert state.awaiting_discard is False

    def test_take_action_draws_from_top(self) -> None:
        """Take action draws from top of discard pile."""
        state = CaravansaryTileState()
        state.awaiting_discard = True
        state.discard_onto(Card.ONE_GOOD)
        state.awaiting_discard = True
        state.discard_onto(Card.FIVE_LIRA)

        cards = state.take_action(1)
        assert cards == [Card.FIVE_LIRA]  # Top card
        assert state.awaiting_discard is True

    def test_take_action_draws_multiple(self) -> None:
        """Can draw 0, 1, or 2 cards."""
        state = CaravansaryTileState()
        state.awaiting_discard = True
        state.discard_onto(Card.ONE_GOOD)
        state.awaiting_discard = True
        state.discard_onto(Card.FIVE_LIRA)
        state.awaiting_discard = True
        state.discard_onto(Card.EXTRA_MOVE)

        cards = state.take_action(2)
        assert len(cards) == 2
        assert cards == [Card.FIVE_LIRA, Card.EXTRA_MOVE]

    def test_take_zero_cards(self) -> None:
        """Taking 0 cards returns empty list."""
        state = CaravansaryTileState()
        cards = state.take_action(0)
        assert cards == []

    def test_cannot_take_more_than_available(self) -> None:
        """Cannot take more cards than in pile."""
        state = CaravansaryTileState()
        state.awaiting_discard = True
        state.discard_onto(Card.ONE_GOOD)
        with pytest.raises(AssertionError):
            state.take_action(2)


class TestWainwrightTileState:
    """Tests for wainwright cart extension tracking."""

    def test_initial_extensions_by_player_count(self) -> None:
        """Extensions depend on player count."""
        state_2p = WainwrightTileState(6)  # 2 players * 3
        state_5p = WainwrightTileState(15)  # 5 players * 3
        assert state_2p.extensions == 6
        assert state_5p.extensions == 15

    def test_take_action_decrements(self) -> None:
        """Taking action decrements extensions."""
        state = WainwrightTileState(6)
        state.take_action()
        assert state.extensions == 5

    def test_cannot_take_when_empty(self) -> None:
        """Cannot take action when no extensions left."""
        state = WainwrightTileState(1)
        state.take_action()
        with pytest.raises(AssertionError):
            state.take_action()


class TestMarketTileState:
    """Tests for market demand and selling."""

    def test_small_market_one_cost(self) -> None:
        """Small market has one_cost of 2."""
        state = MarketTileState(2)
        assert state.one_cost == 2

    def test_large_market_one_cost(self) -> None:
        """Large market has one_cost of 3."""
        state = MarketTileState(3)
        assert state.one_cost == 3

    def test_initial_expecting_demand(self) -> None:
        """Market starts expecting demand."""
        state = MarketTileState(2)
        assert state.expecting_demand is True

    def test_set_demand(self) -> None:
        """Can set demand with 5 total goods."""
        state = MarketTileState(2)
        demand = Counter({Good.RED: 2, Good.GREEN: 2, Good.YELLOW: 1})
        state.set_demand(demand)
        assert state.demand == demand
        assert state.expecting_demand is False

    def test_set_demand_requires_five_goods(self) -> None:
        """Demand must total exactly 5 goods."""
        state = MarketTileState(2)
        with pytest.raises(AssertionError):
            state.set_demand(Counter({Good.RED: 2}))

    def test_take_action_calculates_payment(self) -> None:
        """Take action returns correct lira for goods sold."""
        state = MarketTileState(2)  # one_cost = 2
        state.set_demand(Counter({Good.RED: 3, Good.GREEN: 2}))

        # Selling 3 goods at small market (one_cost=2): 2+3+4 = 9
        payment = state.take_action(Counter({Good.RED: 3}))
        assert payment == 9  # 2 + 3 + 4

    def test_take_action_resets_expecting_demand(self) -> None:
        """Take action sets expecting_demand back to True."""
        state = MarketTileState(2)
        state.set_demand(Counter({Good.RED: 3, Good.GREEN: 2}))
        state.take_action(Counter({Good.RED: 1}))
        assert state.expecting_demand is True


class TestSultansPalaceTileState:
    """Tests for sultan's palace ruby requirements."""

    def test_initial_required_normal(self) -> None:
        """4+ players start at 4 required goods."""
        state = SultansPalaceTileState(init_advanced=False)
        assert state.required_count == 4

    def test_initial_required_advanced(self) -> None:
        """2-3 players start at 5 required goods."""
        state = SultansPalaceTileState(init_advanced=True)
        assert state.required_count == 5

    def test_required_goods_pattern(self) -> None:
        """Required goods follow BRGY(any) pattern."""
        state = SultansPalaceTileState(init_advanced=False)
        required = state.required()
        assert required is not None
        # 4 goods: Blue, Red, Green, Yellow
        assert required[Good.BLUE] == 1
        assert required[Good.RED] == 1
        assert required[Good.GREEN] == 1
        assert required[Good.YELLOW] == 1
        assert required[None] == 0  # No wildcards at count 4

    def test_required_includes_wildcard(self) -> None:
        """At count 5+, wildcards are needed."""
        state = SultansPalaceTileState(init_advanced=True)  # count=5
        required = state.required()
        assert required is not None
        assert required[None] == 1  # 5th good is wildcard

    def test_take_action_increments_required(self) -> None:
        """Each ruby taken increases requirement."""
        state = SultansPalaceTileState(init_advanced=False)
        payment = Counter({Good.BLUE: 1, Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 1})
        state.take_action(payment)
        assert state.required_count == 5

    def test_no_rubies_after_max(self) -> None:
        """After count exceeds 10, no more rubies available."""
        state = SultansPalaceTileState(init_advanced=False)
        state.required_count = 11
        assert state.required() is None


class TestGemstoneDealerTileState:
    """Tests for gemstone dealer price progression."""

    def test_initial_cost_varies_by_players(self) -> None:
        """Initial cost depends on player count."""
        # These would come from initial_tile_state, but we test the class directly
        state_2p = GemstoneDealerTileState(15)
        state_3p = GemstoneDealerTileState(14)
        state_4p = GemstoneDealerTileState(12)
        assert state_2p.cost == 15
        assert state_3p.cost == 14
        assert state_4p.cost == 12

    def test_take_action_increases_cost(self) -> None:
        """Each ruby increases cost by 1."""
        state = GemstoneDealerTileState(12)
        state.take_action()
        assert state.cost == 13

    def test_sold_out_at_25(self) -> None:
        """After cost reaches 24 and action taken, no more rubies."""
        state = GemstoneDealerTileState(24)
        state.take_action()
        assert state.cost is None

    def test_cannot_buy_when_sold_out(self) -> None:
        """Cannot take action when cost is None."""
        state = GemstoneDealerTileState(24)
        state.take_action()
        with pytest.raises(AssertionError):
            state.take_action()


class TestInitialTileState:
    """Tests for initial_tile_state factory function."""

    def test_generic_tiles_return_generic_state(self) -> None:
        """Warehouses and simple tiles return GenericTileState."""
        for tile in [
            Tile.FABRIC_WAREHOUSE,
            Tile.FRUIT_WAREHOUSE,
            Tile.SPICE_WAREHOUSE,
            Tile.FOUNTAIN,
            Tile.BLACK_MARKET,
            Tile.TEA_HOUSE,
            Tile.POLICE_STATION,
        ]:
            state = initial_tile_state(tile, 2)
            assert isinstance(state, GenericTileState)

    def test_mosque_states(self) -> None:
        """Mosques return MosqueTileState with correct goods."""
        great = initial_tile_state(Tile.GREAT_MOSQUE, 2)
        small = initial_tile_state(Tile.SMALL_MOSQUE, 2)
        assert isinstance(great, MosqueTileState)
        assert isinstance(small, MosqueTileState)
        assert Good.BLUE in great.available_tiles
        assert Good.RED in small.available_tiles

    def test_market_states(self) -> None:
        """Markets return MarketTileState with correct one_cost."""
        small = initial_tile_state(Tile.SMALL_MARKET, 2)
        large = initial_tile_state(Tile.LARGE_MARKET, 2)
        assert isinstance(small, MarketTileState)
        assert isinstance(large, MarketTileState)
        assert small.one_cost == 2
        assert large.one_cost == 3

    def test_wainwright_by_player_count(self) -> None:
        """Wainwright extensions scale with players."""
        state_2 = initial_tile_state(Tile.WAINWRIGHT, 2)
        state_5 = initial_tile_state(Tile.WAINWRIGHT, 5)
        assert isinstance(state_2, WainwrightTileState)
        assert isinstance(state_5, WainwrightTileState)
        assert state_2.extensions == 6
        assert state_5.extensions == 15

    def test_gemstone_dealer_by_player_count(self) -> None:
        """Gemstone dealer cost varies by player count."""
        state_2 = initial_tile_state(Tile.GEMSTONE_DEALER, 2)
        state_3 = initial_tile_state(Tile.GEMSTONE_DEALER, 3)
        state_4 = initial_tile_state(Tile.GEMSTONE_DEALER, 4)
        assert isinstance(state_2, GemstoneDealerTileState)
        assert state_2.cost == 15
        assert isinstance(state_3, GemstoneDealerTileState)
        assert state_3.cost == 14
        assert isinstance(state_4, GemstoneDealerTileState)
        assert state_4.cost == 12

    def test_sultans_palace_by_player_count(self) -> None:
        """Sultan's palace init varies by player count."""
        state_2 = initial_tile_state(Tile.SULTANS_PALACE, 2)
        state_3 = initial_tile_state(Tile.SULTANS_PALACE, 3)
        state_4 = initial_tile_state(Tile.SULTANS_PALACE, 4)
        assert isinstance(state_2, SultansPalaceTileState)
        assert isinstance(state_4, SultansPalaceTileState)
        # 2-3 players: init_advanced=True (starts at 5)
        assert state_2.required_count == 5
        assert state_3.required_count == 5
        # 4+ players: init_advanced=False (starts at 4)
        assert state_4.required_count == 4
