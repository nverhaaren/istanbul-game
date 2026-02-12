"""Additional tests for game action handlers."""
import pytest
from collections import Counter

from tests.helpers import create_game, move_player_to_tile

from istanbul_game.game import GameState
from istanbul_game.constants import Player, Location, Tile, Good, Card
from istanbul_game.actions import (
    Move,
    YieldTurn,
    GenericTileAction,
    SkipTileAction,
    ChooseReward,
    MosqueAction,
    MarketAction,
    BlackMarketAction,
    TeaHouseAction,
    SultansPalaceAction,
    PoliceStationAction,
    FountainAction,
    EncounterGovernor,
    EncounterSmuggler,
    CaravansaryAction,
    NoMoveCardAction,
    DoubleCardAction,
)
from istanbul_game.tiles import (
    MosqueTileState,
    MarketTileState,
    SultansPalaceTileState,
    CaravansaryTileState,
    PostOfficeTileState,
    WainwrightTileState,
)


class TestMosqueAction:
    """Tests for mosque tile actions."""

    def test_get_mosque_tile(self) -> None:
        """Can acquire mosque tile by paying goods."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.cart_contents[Good.RED] = 2
        player_state.hand[Card.NO_MOVE] = 1

        # Move to small mosque
        move_player_to_tile(game, Player.RED, Tile.SMALL_MOSQUE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Take mosque action
        game.take_action(MosqueAction(Good.RED))

        # Should have the tile
        assert Good.RED in player_state.tiles
        # Should have paid goods
        assert player_state.cart_contents[Good.RED] == 0

    def test_blue_tile_gives_extra_assistant(self) -> None:
        """Getting blue mosque tile adds an assistant."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.cart_contents[Good.BLUE] = 2
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.GREAT_MOSQUE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_stack = player_state.stack_size
        game.take_action(MosqueAction(Good.BLUE))

        assert player_state.stack_size == initial_stack + 1

    def test_completing_mosque_pair_gives_ruby(self) -> None:
        """Getting both tiles of a pair gives a ruby."""
        game = create_game()
        player_state = game.player_states[Player.RED]

        # Already have yellow tile
        player_state.tiles.add(Good.YELLOW)
        player_state.cart_contents[Good.BLUE] = 2
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.GREAT_MOSQUE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_rubies = player_state.rubies
        game.take_action(MosqueAction(Good.BLUE))

        # Blue + Yellow pair should give a ruby
        assert player_state.rubies == initial_rubies + 1

    def test_red_green_pair_gives_ruby(self) -> None:
        """Getting red + green tiles gives a ruby."""
        game = create_game()
        player_state = game.player_states[Player.RED]

        # Already have red tile
        player_state.tiles.add(Good.RED)
        player_state.cart_contents[Good.GREEN] = 2
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.SMALL_MOSQUE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_rubies = player_state.rubies
        game.take_action(MosqueAction(Good.GREEN))

        # Red + Green pair should give a ruby
        assert player_state.rubies == initial_rubies + 1

    def test_cannot_get_blue_tile_from_small_mosque(self) -> None:
        """Cannot acquire blue tile from small mosque (wrong mosque)."""
        game = create_game()
        player_state = game.player_states[Player.RED]

        player_state.cart_contents[Good.BLUE] = 2
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.SMALL_MOSQUE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Small mosque only has RED and GREEN tiles, not BLUE
        with pytest.raises(KeyError):
            game.take_action(MosqueAction(Good.BLUE))

    def test_cannot_get_red_tile_from_great_mosque(self) -> None:
        """Cannot acquire red tile from great mosque (wrong mosque)."""
        game = create_game()
        player_state = game.player_states[Player.RED]

        player_state.cart_contents[Good.RED] = 2
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.GREAT_MOSQUE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Great mosque only has BLUE and YELLOW tiles, not RED
        with pytest.raises(KeyError):
            game.take_action(MosqueAction(Good.RED))


class TestWarehouseAction:
    """Tests for warehouse tile actions with green tile."""
    WAREHOUSE_COLORS = {
        Tile.FABRIC_WAREHOUSE: Good.RED,
        Tile.SPICE_WAREHOUSE: Good.GREEN,
        Tile.FRUIT_WAREHOUSE: Good.YELLOW,
    }

    @pytest.mark.parametrize("warehouse,good", [
        (Tile.FABRIC_WAREHOUSE, Good.BLUE),  # The colors _should not_ match what the warehouse fills.
        (Tile.SPICE_WAREHOUSE, Good.RED),
        (Tile.FRUIT_WAREHOUSE, Good.GREEN),
    ])
    def test_use_green_tile_at_warehouse(self, warehouse: Tile, good: Good) -> None:
        """Can use green tile at warehouse to get corresponding chosen good, along with the normal warehouse action."""
        from istanbul_game.actions import GreenTileAction

        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.tiles.add(Good.GREEN)
        player_state.hand[Card.NO_MOVE] = 1
        player_state.lira = 10

        move_player_to_tile(game, Player.RED, warehouse)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_good_count = player_state.cart_contents[good]
        initial_lira = player_state.lira

        game.take_action(GreenTileAction(good))

        assert player_state.cart_contents[good] == initial_good_count + 1
        assert player_state.cart_contents[self.WAREHOUSE_COLORS[warehouse]] == player_state.cart_max
        assert player_state.lira == initial_lira - 2  # Costs 2 lira

    def test_cannot_use_green_tile_without_having_it(self) -> None:
        """Cannot use green tile action without the green tile."""
        from istanbul_game.actions import GreenTileAction

        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.FABRIC_WAREHOUSE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        with pytest.raises(AssertionError):
            game.take_action(GreenTileAction(Good.RED))


class TestMarketAction:
    """Tests for market tile actions."""

    def test_sell_goods_at_market(self) -> None:
        """Can sell goods at market for lira."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.cart_contents[Good.RED] = 2
        player_state.cart_contents[Good.GREEN] = 2
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.SMALL_MARKET)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_lira = player_state.lira
        # Sell 2 RED goods - price at small market: 2 + 3 = 5
        new_demand = Counter({Good.BLUE: 2, Good.YELLOW: 2, Good.GREEN: 1})
        game.take_action(MarketAction(
            goods=Counter({Good.RED: 2}),
            new_demand=new_demand
        ))

        assert player_state.lira == initial_lira + 5
        assert player_state.cart_contents[Good.RED] == 0


class TestBlackMarketAction:
    """Tests for black market tile actions."""

    def test_get_good_plus_bonus(self) -> None:
        """Black market gives chosen good plus bonus based on roll."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.BLACK_MARKET)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_red = player_state.cart_contents[Good.RED]
        initial_blue = player_state.cart_contents[Good.BLUE]

        # Roll 7 (3+4) = 1 blue bonus
        game.take_action(BlackMarketAction(Good.RED, roll=(3, 4)))

        assert player_state.cart_contents[Good.RED] == initial_red + 1
        assert player_state.cart_contents[Good.BLUE] == initial_blue + 1

    def test_high_roll_gives_more_blue(self) -> None:
        """Higher rolls give more blue goods."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1
        player_state.cart_max = 5  # Expand cart so we can fit more

        move_player_to_tile(game, Player.RED, Tile.BLACK_MARKET)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_blue = player_state.cart_contents[Good.BLUE]

        # Roll 11 (5+6) = 3 blue bonus
        game.take_action(BlackMarketAction(Good.GREEN, roll=(5, 6)))

        assert player_state.cart_contents[Good.BLUE] == initial_blue + 3


class TestTeaHouseAction:
    """Tests for tea house tile actions."""

    def test_call_met_gets_call_amount(self) -> None:
        """Meeting call amount gives that much lira."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.TEA_HOUSE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_lira = player_state.lira
        # Call 7, roll 8 (3+5) - meets call
        game.take_action(TeaHouseAction(call=7, roll=(3, 5)))

        assert player_state.lira == initial_lira + 7

    def test_call_not_met_gets_2(self) -> None:
        """Not meeting call gives consolation 2 lira."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.TEA_HOUSE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_lira = player_state.lira
        # Call 10, roll 5 (2+3) - fails call
        game.take_action(TeaHouseAction(call=10, roll=(2, 3)))

        assert player_state.lira == initial_lira + 2


class TestSultansPalaceAction:
    """Tests for sultan's palace tile actions."""

    def test_trade_goods_for_ruby(self) -> None:
        """Can trade goods for a ruby."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        # Sultan's palace for 2 players starts at 5 goods required
        # Give player enough goods
        player_state.cart_contents[Good.RED] = 2
        player_state.cart_contents[Good.GREEN] = 2
        player_state.cart_contents[Good.YELLOW] = 2
        player_state.cart_contents[Good.BLUE] = 2
        player_state.cart_max = 5

        move_player_to_tile(game, Player.RED, Tile.SULTANS_PALACE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_rubies = player_state.rubies
        # Pay 5 goods (pattern: Blue, Red, Green, Yellow, any)
        payment = Counter({Good.BLUE: 1, Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2})
        game.take_action(SultansPalaceAction(goods=payment))

        assert player_state.rubies == initial_rubies + 1

    def test_remaining_goods_in_cart(self) -> None:
        """Cart has correct remaining goods after sultan's palace payment."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        # Give player specific amounts of goods
        player_state.cart_contents = Counter({
            Good.RED: 3,
            Good.GREEN: 2,
            Good.YELLOW: 3,
            Good.BLUE: 2,
        })
        player_state.cart_max = 10

        move_player_to_tile(game, Player.RED, Tile.SULTANS_PALACE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Pay 5 goods: 1 Blue, 1 Red, 1 Green, 2 Yellow
        payment = Counter({Good.BLUE: 1, Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2})
        game.take_action(SultansPalaceAction(goods=payment))

        # Verify remaining goods
        assert player_state.cart_contents[Good.RED] == 2  # 3 - 1
        assert player_state.cart_contents[Good.GREEN] == 1  # 2 - 1
        assert player_state.cart_contents[Good.YELLOW] == 1  # 3 - 2
        assert player_state.cart_contents[Good.BLUE] == 1  # 2 - 1


class TestWainwrightAction:
    """Tests for wainwright tile actions."""

    def test_expand_cart(self) -> None:
        """Can pay to expand cart."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.lira = 10
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.WAINWRIGHT)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_cart = player_state.cart_max
        game.take_action(GenericTileAction())

        assert player_state.cart_max == initial_cart + 1
        assert player_state.lira == 10 - 7  # Costs 7 lira

    def test_max_cart_gives_ruby(self) -> None:
        """Reaching max cart capacity gives a ruby."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.lira = 10
        player_state.cart_max = 4  # One expansion away from max
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.WAINWRIGHT)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_rubies = player_state.rubies
        game.take_action(GenericTileAction())

        assert player_state.cart_max == 5
        assert player_state.rubies == initial_rubies + 1


class TestPostOfficeAction:
    """Tests for post office tile actions."""

    def test_get_goods_and_lira(self) -> None:
        """Post office gives goods and lira."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.POST_OFFICE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_lira = player_state.lira

        # Get what's available at position 0
        assert isinstance(
            po_state := game.tile_states[Tile.POST_OFFICE],
            PostOfficeTileState
        )
        expected_goods, expected_lira = po_state.available()

        game.take_action(GenericTileAction())

        assert player_state.lira == initial_lira + expected_lira
        for good in expected_goods:
            assert player_state.cart_contents[good] >= 1


class TestCaravansaryAction:
    """Tests for caravansary tile actions."""

    def test_draw_from_discard(self) -> None:
        """Can draw cards from discard pile."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.FIVE_LIRA] = 2  # Have extra to discard

        # Set up discard pile with cards we'll draw
        assert isinstance(
            cara_state := game.tile_states[Tile.CARAVANSARY],
            CaravansaryTileState
        )
        cara_state.discard_pile = [Card.EXTRA_MOVE, Card.RETURN_ASSISTANT]
        cara_state.awaiting_discard = False

        # Move player directly to caravansary (skip using a card)
        move_player_to_tile(game, Player.RED, Tile.CARAVANSARY)
        # Set up game state to be in phase 3
        game.turn_state.current_phase = 3

        initial_five_lira = player_state.hand[Card.FIVE_LIRA]

        # Draw 2 from discard, discard FIVE_LIRA
        game.take_action(CaravansaryAction(
            gains=(CaravansaryAction.DISCARD, CaravansaryAction.DISCARD),
            cost=Card.FIVE_LIRA
        ))

        # Should have gained the top 2 cards from discard
        assert player_state.hand[Card.EXTRA_MOVE] >= 1
        assert player_state.hand[Card.RETURN_ASSISTANT] >= 1
        assert player_state.hand[Card.FIVE_LIRA] == initial_five_lira - 1


class TestFountainAction:
    """Tests for fountain tile actions."""

    def test_return_all_assistants(self) -> None:
        """Fountain returns all assistants."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        # Place some assistants on the board
        loc1, loc2 = Location(3), Location(5)
        tile1, tile2 = game.location_map[loc1], game.location_map[loc2]
        player_state.assistant_locations = {loc1, loc2}
        player_state.stack_size = 2
        game.tile_states[tile1].assistants.add(Player.RED)
        game.tile_states[tile2].assistants.add(Player.RED)

        # Move to fountain (already there, use no-move)
        move_player_to_tile(game, Player.RED, Tile.FOUNTAIN)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        game.take_action(GenericTileAction())

        # All assistants should be back
        assert player_state.stack_size == 4
        assert len(player_state.assistant_locations) == 0

    def test_family_member_at_fountain_returns_assistants(self) -> None:
        """Family member sent to fountain returns player's assistants."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        # Place some assistants on the board
        loc1, loc2 = Location(3), Location(5)
        tile1, tile2 = game.location_map[loc1], game.location_map[loc2]
        player_state.assistant_locations = {loc1, loc2}
        player_state.stack_size = 2
        game.tile_states[tile1].assistants.add(Player.RED)
        game.tile_states[tile2].assistants.add(Player.RED)

        # Move to police station (player already has family member there)
        move_player_to_tile(game, Player.RED, Tile.POLICE_STATION)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Send family member to fountain
        fountain_loc = game.location_map.inverse[Tile.FOUNTAIN]
        game.take_action(PoliceStationAction(
            location=fountain_loc,
            action=GenericTileAction()
        ))

        # All assistants should be back
        assert player_state.stack_size == 4
        assert len(player_state.assistant_locations) == 0


class TestGovernorEncounter:
    """Tests for governor encounters."""

    def test_pay_lira_for_card(self) -> None:
        """Can pay 2 lira to get card from governor."""
        game = create_game(governor_location=Location(3))
        player_state = game.player_states[Player.RED]
        player_state.lira = 10
        player_state.hand[Card.NO_MOVE] = 1

        # Move to tile with governor
        tile = game.location_map[Location(3)]
        move_player_to_tile(game, Player.RED, tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(SkipTileAction())

        initial_lira = player_state.lira
        initial_cards = player_state.hand[Card.FIVE_LIRA]

        # Encounter governor, pay 2 lira for FIVE_LIRA card
        from istanbul_game.actions import Pay
        game.take_action(EncounterGovernor(
            gain=Card.FIVE_LIRA,
            cost=Pay(),
            roll=(3, 4)
        ))

        assert player_state.lira == initial_lira - 2
        assert player_state.hand[Card.FIVE_LIRA] == initial_cards + 1

    def test_trade_card_for_card(self) -> None:
        """Can trade a card to get a different card from governor."""
        game = create_game(governor_location=Location(3))
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1
        player_state.hand[Card.ONE_GOOD] = 2  # Have card to trade

        # Move to tile with governor
        tile = game.location_map[Location(3)]
        move_player_to_tile(game, Player.RED, tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(SkipTileAction())

        initial_one_good = player_state.hand[Card.ONE_GOOD]
        initial_extra_move = player_state.hand[Card.EXTRA_MOVE]
        initial_lira = player_state.lira

        # Encounter governor, trade ONE_GOOD for EXTRA_MOVE card
        game.take_action(EncounterGovernor(
            gain=Card.EXTRA_MOVE,
            cost=Card.ONE_GOOD,
            roll=(3, 4)
        ))

        # Should have traded one card for another
        assert player_state.hand[Card.ONE_GOOD] == initial_one_good - 1
        assert player_state.hand[Card.EXTRA_MOVE] == initial_extra_move + 1
        # Lira should be unchanged
        assert player_state.lira == initial_lira


class TestSmugglerEncounter:
    """Tests for smuggler encounters."""

    def test_pay_lira_for_good(self) -> None:
        """Can pay 2 lira to get good from smuggler."""
        game = create_game(smuggler_location=Location(3))
        player_state = game.player_states[Player.RED]
        player_state.lira = 10
        player_state.hand[Card.NO_MOVE] = 1

        # Move to tile with smuggler
        tile = game.location_map[Location(3)]
        move_player_to_tile(game, Player.RED, tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(SkipTileAction())

        initial_lira = player_state.lira
        initial_red = player_state.cart_contents[Good.RED]

        # Encounter smuggler, pay 2 lira for RED good
        from istanbul_game.actions import Pay
        game.take_action(EncounterSmuggler(
            gain=Good.RED,
            cost=Pay(),
            roll=(3, 4)
        ))

        assert player_state.lira == initial_lira - 2
        assert player_state.cart_contents[Good.RED] == initial_red + 1

    def test_trade_good_for_good(self) -> None:
        """Can trade a good for a different good."""
        game = create_game(smuggler_location=Location(3))
        player_state = game.player_states[Player.RED]
        player_state.cart_contents[Good.GREEN] = 2
        player_state.hand[Card.NO_MOVE] = 1

        tile = game.location_map[Location(3)]
        move_player_to_tile(game, Player.RED, tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(SkipTileAction())

        initial_red = player_state.cart_contents[Good.RED]
        initial_green = player_state.cart_contents[Good.GREEN]

        # Trade GREEN for RED
        game.take_action(EncounterSmuggler(
            gain=Good.RED,
            cost=Good.GREEN,
            roll=(3, 4)
        ))

        assert player_state.cart_contents[Good.RED] == initial_red + 1
        assert player_state.cart_contents[Good.GREEN] == initial_green - 1


class TestPoliceStationAction:
    """Tests for police station actions."""

    def test_send_family_member(self) -> None:
        """Can send family member to another tile."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        # Already at police station with family member
        move_player_to_tile(game, Player.RED, Tile.POLICE_STATION)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Send family member to fabric warehouse
        target_loc = game.location_map.inverse[Tile.FABRIC_WAREHOUSE]
        game.take_action(PoliceStationAction(
            location=target_loc,
            action=GenericTileAction()
        ))

        # Family member should be at warehouse
        assert player_state.family_location == target_loc
        assert Player.RED in game.tile_states[Tile.FABRIC_WAREHOUSE].family_members
        # Player should still be at police station
        assert player_state.location == game.location_map.inverse[Tile.POLICE_STATION]

    def test_family_member_with_double_card(self) -> None:
        """Family member can use double card action."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1
        player_state.hand[Card.DOUBLE_PO] = 1
        player_state.cart_max = 10

        move_player_to_tile(game, Player.RED, Tile.POLICE_STATION)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_lira = player_state.lira

        # Send family member to post office with double card
        po_loc = game.location_map.inverse[Tile.POST_OFFICE]
        game.take_action(PoliceStationAction(
            location=po_loc,
            action=DoubleCardAction(
                Card.DOUBLE_PO,
                (GenericTileAction(), GenericTileAction())
            )
        ))

        # Should have received lira from two post office actions
        assert player_state.lira > initial_lira
        assert player_state.hand[Card.DOUBLE_PO] == 0

    def test_family_member_sultan_palace(self) -> None:
        """Family member can perform sultan's palace action."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        # Give player enough goods for sultan's palace
        player_state.cart_contents = Counter({
            Good.RED: 2,
            Good.GREEN: 2,
            Good.YELLOW: 2,
            Good.BLUE: 2,
        })
        player_state.cart_max = 8

        move_player_to_tile(game, Player.RED, Tile.POLICE_STATION)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        initial_rubies = player_state.rubies
        sultan_loc = game.location_map.inverse[Tile.SULTANS_PALACE]

        # Send family member to sultan's palace
        payment = Counter({Good.BLUE: 1, Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2})
        game.take_action(PoliceStationAction(
            location=sultan_loc,
            action=SultansPalaceAction(goods=payment)
        ))

        assert player_state.rubies == initial_rubies + 1
