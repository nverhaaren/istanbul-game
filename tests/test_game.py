"""Tests for game module."""

from collections import Counter

import pytest

from istanbul_game.actions import (
    ArrestFamilyCardAction,
    ChooseReward,
    DoubleCardAction,
    ExtraMoveCardAction,
    FiveLiraCardAction,
    GenericTileAction,
    Move,
    NoMoveCardAction,
    OneGoodCardAction,
    Pay,
    ReturnAssistantCardAction,
    SkipTileAction,
    SultansPalaceAction,
    YieldTurn,
)
from istanbul_game.constants import Card, Good, Location, Player, Tile
from istanbul_game.game import GameState, taxicab_dist
from istanbul_game.tiles import GemstoneDealerTileState, PostOfficeTileState
from tests.helpers import create_game, move_player_to_tile


class TestTaxicabDistance:
    """Tests for taxicab distance calculation."""

    def test_same_location(self) -> None:
        """Distance to same location is 0."""
        assert taxicab_dist(Location(1), Location(1)) == 0
        assert taxicab_dist(Location(8), Location(8)) == 0

    def test_adjacent_horizontal(self) -> None:
        """Adjacent horizontal locations have distance 1."""
        assert taxicab_dist(Location(1), Location(2)) == 1
        assert taxicab_dist(Location(2), Location(1)) == 1
        assert taxicab_dist(Location(5), Location(6)) == 1

    def test_adjacent_vertical(self) -> None:
        """Adjacent vertical locations have distance 1."""
        assert taxicab_dist(Location(1), Location(5)) == 1
        assert taxicab_dist(Location(5), Location(1)) == 1
        assert taxicab_dist(Location(6), Location(10)) == 1

    def test_diagonal(self) -> None:
        """Diagonal locations have distance 2."""
        assert taxicab_dist(Location(1), Location(6)) == 2
        assert taxicab_dist(Location(6), Location(1)) == 2

    def test_far_apart(self) -> None:
        """Locations far apart have larger distances."""
        # Corners of 4x4 grid
        assert taxicab_dist(Location(1), Location(16)) == 6
        assert taxicab_dist(Location(4), Location(13)) == 6

    def test_same_row(self) -> None:
        """Locations in same row have column difference as distance."""
        # Row 1: 1, 2, 3, 4
        assert taxicab_dist(Location(1), Location(4)) == 3
        # Row 3: 9, 10, 11, 12
        assert taxicab_dist(Location(9), Location(12)) == 3

    def test_same_column(self) -> None:
        """Locations in same column have row difference as distance."""
        # Column 1: 1, 5, 9, 13
        assert taxicab_dist(Location(1), Location(13)) == 3
        # Column 4: 4, 8, 12, 16
        assert taxicab_dist(Location(4), Location(16)) == 3


class TestGameStateInitialization:
    """Tests for GameState initialization."""

    def test_player_count(self, two_player_game: GameState) -> None:
        """Player count is set correctly."""
        assert two_player_game.player_count == 2

    def test_players_tuple(self, two_player_game: GameState) -> None:
        """Players are stored as tuple."""
        assert two_player_game.players == (Player.RED, Player.BLUE)

    def test_current_player_starts_first(self, two_player_game: GameState) -> None:
        """Game starts with first player."""
        assert two_player_game.current_player == Player.RED

    def test_not_completed_initially(self, two_player_game: GameState) -> None:
        """Game is not completed at start."""
        assert two_player_game.completed is False

    def test_two_player_victory_threshold(self, two_player_game: GameState) -> None:
        """Two-player games require 6 rubies."""
        assert two_player_game.victory_threshold == 6

    def test_three_player_victory_threshold(self, three_player_game: GameState) -> None:
        """Three-player games require 5 rubies."""
        assert three_player_game.victory_threshold == 5

    def test_five_player_victory_threshold(self, five_player_game: GameState) -> None:
        """Five-player games require 5 rubies."""
        assert five_player_game.victory_threshold == 5

    def test_players_start_at_fountain(self, two_player_game: GameState) -> None:
        """All players start at fountain."""
        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]
        for player in two_player_game.players:
            assert two_player_game.player_states[player].location == fountain_loc

    def test_family_members_at_police_station(self, two_player_game: GameState) -> None:
        """All family members start at police station."""
        police_tile_state = two_player_game.tile_states[Tile.POLICE_STATION]
        for player in two_player_game.players:
            assert player in police_tile_state.family_members

    def test_initial_lira_varies_by_order(self, three_player_game: GameState) -> None:
        """Players get 2, 3, 4, ... lira based on turn order."""
        assert three_player_game.player_states[Player.RED].lira == 2
        assert three_player_game.player_states[Player.BLUE].lira == 3
        assert three_player_game.player_states[Player.GREEN].lira == 4

    def test_initial_cart_capacity(self, two_player_game: GameState) -> None:
        """Players start with cart capacity of 2."""
        for player in two_player_game.players:
            assert two_player_game.player_states[player].cart_max == 2

    def test_initial_stack_size(self, two_player_game: GameState) -> None:
        """Players start with 4 assistants in stack."""
        for player in two_player_game.players:
            assert two_player_game.player_states[player].stack_size == 4

    def test_initial_rubies(self, two_player_game: GameState) -> None:
        """Players start with 0 rubies."""
        for player in two_player_game.players:
            assert two_player_game.player_states[player].rubies == 0


class TestMovement:
    """Tests for player movement."""

    def test_valid_move_distance_1(self, two_player_game: GameState) -> None:
        """Can move 1 space."""
        # Fountain is at location 7 in standard layout
        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]
        # Find adjacent location
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 1:
                adjacent = Location(i)
                break

        two_player_game.take_action(Move(adjacent, skip_assistant=False))
        assert two_player_game.current_player_location == adjacent

    def test_valid_move_distance_2(self, two_player_game: GameState) -> None:
        """Can move 2 spaces."""
        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 2:
                target = Location(i)
                break

        two_player_game.take_action(Move(target, skip_assistant=False))
        assert two_player_game.current_player_location == target

    def test_invalid_move_distance_0(self, two_player_game: GameState) -> None:
        """Cannot stay in place with regular move."""
        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]
        with pytest.raises(AssertionError, match="Cannot move 0 spaces"):
            two_player_game.take_action(Move(fountain_loc, skip_assistant=False))

    def test_invalid_move_distance_3(self, two_player_game: GameState) -> None:
        """Cannot move 3 spaces with regular move."""
        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 3:
                target = Location(i)
                break

        with pytest.raises(AssertionError, match="Cannot move 3 spaces"):
            two_player_game.take_action(Move(target, skip_assistant=False))

    def test_move_updates_tile_players(self, two_player_game: GameState) -> None:
        """Moving updates players set on tiles."""
        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]
        fountain_tile = two_player_game.location_map[fountain_loc]

        # Find adjacent tile
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 1:
                target = Location(i)
                break

        target_tile = two_player_game.location_map[target]

        assert Player.RED in two_player_game.tile_states[fountain_tile].players
        two_player_game.take_action(Move(target, skip_assistant=False))

        assert Player.RED not in two_player_game.tile_states[fountain_tile].players
        assert Player.RED in two_player_game.tile_states[target_tile].players


class TestAssistants:
    """Tests for assistant placement and retrieval."""

    def test_move_places_assistant(self, two_player_game: GameState) -> None:
        """Moving without skip_assistant places an assistant."""
        player_state = two_player_game.current_player_state
        initial_stack = player_state.stack_size

        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 1:
                target = Location(i)
                break

        two_player_game.take_action(Move(target, skip_assistant=False))

        assert player_state.stack_size == initial_stack - 1
        assert target in player_state.assistant_locations

    def test_move_to_assistant_retrieves(self) -> None:
        """Moving to tile with own assistant retrieves it."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player = Player.RED
        target = Location(3)
        target_tile = game.location_map[target]

        # Pre-place assistant at target
        game.tile_states[target_tile].assistants.add(player)
        player_state.assistant_locations.add(target)
        player_state.stack_size -= 1
        initial_stack = player_state.stack_size

        # Move player adjacent to target
        adjacent = Location(4)  # Adjacent to Location(3)
        move_player_to_tile(game, player, game.location_map[adjacent])

        # Move to target tile where assistant is waiting
        game.take_action(Move(target, skip_assistant=False))

        assert player_state.stack_size == initial_stack + 1
        assert target not in player_state.assistant_locations
        assert player not in game.tile_states[target_tile].assistants


class TestPayment:
    """Tests for paying other players."""

    def test_pay_when_alone_skips_phase_2(self, two_player_game: GameState) -> None:
        """Phase 2 is skipped when alone on tile."""
        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 1:
                target = Location(i)
                break

        two_player_game.take_action(Move(target, skip_assistant=False))
        # Should be in phase 3 now (skipped phase 2)
        assert two_player_game.turn_state.current_phase == 3

    def test_pay_when_others_present(self) -> None:
        """Must pay 2 lira per other player on tile."""
        game = create_game()

        fountain_loc = game.location_map.inverse[Tile.FOUNTAIN]
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 1:
                target = Location(i)
                break

        # RED moves to target, takes action, yields
        game.take_action(Move(target, skip_assistant=False))
        game.take_action(SkipTileAction())
        game.take_action(YieldTurn())

        # BLUE moves to same target - now both on tile
        game.take_action(Move(target, skip_assistant=False))

        # Now in phase 2, must pay RED (both are on tile)
        blue_lira_before = game.player_states[Player.BLUE].lira
        red_lira_before = game.player_states[Player.RED].lira

        game.take_action(Pay())

        assert game.player_states[Player.BLUE].lira == blue_lira_before - 2
        assert game.player_states[Player.RED].lira == red_lira_before + 2


class TestCards:
    """Tests for card usage."""

    def test_one_good_card(self, two_player_game: GameState) -> None:
        """One good card adds a good to cart."""
        player_state = two_player_game.current_player_state
        player_state.hand[Card.ONE_GOOD] = 1

        initial_red = player_state.cart_contents[Good.RED]
        two_player_game.take_action(OneGoodCardAction(Good.RED))

        assert player_state.cart_contents[Good.RED] == initial_red + 1
        assert player_state.hand[Card.ONE_GOOD] == 0

    def test_five_lira_card(self, two_player_game: GameState) -> None:
        """Five lira card adds 5 lira."""
        player_state = two_player_game.current_player_state
        player_state.hand[Card.FIVE_LIRA] = 1

        initial_lira = player_state.lira
        two_player_game.take_action(FiveLiraCardAction())

        assert player_state.lira == initial_lira + 5
        assert player_state.hand[Card.FIVE_LIRA] == 0

    def test_no_move_card(self, two_player_game: GameState) -> None:
        """No move card allows staying in place."""
        player_state = two_player_game.current_player_state
        player_state.hand[Card.NO_MOVE] = 1
        initial_location = player_state.location

        two_player_game.take_action(NoMoveCardAction(skip_assistant=False))

        assert player_state.location == initial_location
        assert player_state.hand[Card.NO_MOVE] == 0

    def test_extra_move_card_distance_3(self, two_player_game: GameState) -> None:
        """Extra move card allows moving 3-4 spaces."""
        player_state = two_player_game.current_player_state
        player_state.hand[Card.EXTRA_MOVE] = 1

        fountain_loc = player_state.location
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 3:
                target = Location(i)
                break

        two_player_game.take_action(ExtraMoveCardAction(Move(target, skip_assistant=False)))

        assert player_state.location == target
        assert player_state.hand[Card.EXTRA_MOVE] == 0

    def test_return_assistant_card(self) -> None:
        """Return assistant card retrieves an assistant from the board."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.RETURN_ASSISTANT] = 1

        # Place an assistant on the board
        assistant_loc = Location(3)
        assistant_tile = game.location_map[assistant_loc]
        game.tile_states[assistant_tile].assistants.add(Player.RED)
        player_state.assistant_locations.add(assistant_loc)
        player_state.stack_size = 3

        game.take_action(ReturnAssistantCardAction(assistant_loc))

        assert player_state.stack_size == 4
        assert assistant_loc not in player_state.assistant_locations
        assert player_state.hand[Card.RETURN_ASSISTANT] == 0

    def test_arrest_family_card(self) -> None:
        """Arrest family card returns family member and gives reward."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.ARREST_FAMILY] = 1

        # Move family member away from police station
        family_loc = Location(5)
        family_tile = game.location_map[family_loc]
        police_tile = Tile.POLICE_STATION
        game.tile_states[police_tile].family_members.remove(Player.RED)
        game.tile_states[family_tile].family_members.add(Player.RED)
        player_state.family_location = family_loc

        initial_lira = player_state.lira
        game.take_action(ArrestFamilyCardAction(ChooseReward(ChooseReward.LIRA)))

        # Family should be back at police station
        police_loc = game.location_map.inverse[Tile.POLICE_STATION]
        assert player_state.family_location == police_loc
        assert Player.RED in game.tile_states[police_tile].family_members
        # Should have received 3 lira reward
        assert player_state.lira == initial_lira + 3
        assert player_state.hand[Card.ARREST_FAMILY] == 0

    def test_double_sultan_card(self) -> None:
        """Double sultan card allows two sultan's palace actions."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.DOUBLE_SULTAN] = 1

        # Sultan's palace for 2 players starts at 5 goods required
        # Need enough goods for two purchases (5 + 6 = 11 total goods)
        # Both payments use yellow for the "any" slot, so need 4 total yellow
        player_state.cart_contents[Good.RED] = 3
        player_state.cart_contents[Good.GREEN] = 3
        player_state.cart_contents[Good.YELLOW] = 5
        player_state.cart_contents[Good.BLUE] = 4
        player_state.cart_max = 15

        move_player_to_tile(game, Player.RED, Tile.SULTANS_PALACE)
        game.turn_state.current_phase = 3

        initial_rubies = player_state.rubies

        # First payment: 5 goods (Blue, Red, Green, Yellow, any=Yellow)
        payment1 = Counter({Good.BLUE: 1, Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2})
        # Second payment: 6 goods (Blue, Red, Green, Yellow, any=Yellow, Blue)
        payment2 = Counter({Good.BLUE: 2, Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2})

        game.take_action(
            DoubleCardAction(Card.DOUBLE_SULTAN, (SultansPalaceAction(payment1), SultansPalaceAction(payment2)))
        )

        assert player_state.rubies == initial_rubies + 2
        assert player_state.hand[Card.DOUBLE_SULTAN] == 0

    def test_double_post_office_card(self) -> None:
        """Double post office card allows two post office actions."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.DOUBLE_PO] = 1
        player_state.cart_max = 10  # Ensure enough room for goods

        move_player_to_tile(game, Player.RED, Tile.POST_OFFICE)
        game.turn_state.current_phase = 3

        assert isinstance(po_state := game.tile_states[Tile.POST_OFFICE], PostOfficeTileState)
        initial_position = po_state.position
        initial_lira = player_state.lira

        game.take_action(DoubleCardAction(Card.DOUBLE_PO, (GenericTileAction(), GenericTileAction())))

        # Position should advance by 2 (mod 5)
        expected_position = (initial_position + 2) % 5
        assert po_state.position == expected_position
        # Should have received lira from both actions
        assert player_state.lira > initial_lira
        assert player_state.hand[Card.DOUBLE_PO] == 0

    def test_double_gemstone_dealer_card(self) -> None:
        """Double gemstone dealer card allows two gemstone purchases."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.DOUBLE_DEALER] = 1
        player_state.lira = 50  # Plenty of lira for two purchases

        move_player_to_tile(game, Player.RED, Tile.GEMSTONE_DEALER)
        game.turn_state.current_phase = 3

        assert isinstance(dealer_state := game.tile_states[Tile.GEMSTONE_DEALER], GemstoneDealerTileState)
        initial_cost = dealer_state.cost
        assert initial_cost is not None
        initial_rubies = player_state.rubies
        initial_lira = player_state.lira

        game.take_action(DoubleCardAction(Card.DOUBLE_DEALER, (GenericTileAction(), GenericTileAction())))

        assert player_state.rubies == initial_rubies + 2
        # Cost increases by 1 for each purchase
        expected_cost = initial_cost + (initial_cost + 1)
        assert player_state.lira == initial_lira - expected_cost
        assert player_state.hand[Card.DOUBLE_DEALER] == 0


class TestGenericTileActions:
    """Tests for generic tile actions (warehouses, gemstone dealer)."""

    def test_warehouse_fills_cart(self, two_player_game: GameState) -> None:
        """Warehouse fills cart with corresponding good."""
        fabric_loc = two_player_game.location_map.inverse[Tile.FABRIC_WAREHOUSE]

        # Need to get to fabric warehouse - use no_move if adjacent
        player_state = two_player_game.current_player_state
        player_state.hand[Card.NO_MOVE] = 1

        # Manually move player for test setup
        two_player_game.tile_states[Tile.FOUNTAIN].players.remove(Player.RED)
        player_state.location = fabric_loc
        two_player_game.tile_states[Tile.FABRIC_WAREHOUSE].players.add(Player.RED)

        # Use no-move to stay and trigger warehouse action
        two_player_game.take_action(NoMoveCardAction(skip_assistant=False))
        two_player_game.take_action(GenericTileAction())

        assert player_state.cart_contents[Good.RED] == player_state.cart_max

    def test_spice_warehouse_fills_cart(self) -> None:
        """Spice warehouse fills cart with green goods."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.SPICE_WAREHOUSE)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(GenericTileAction())

        assert player_state.cart_contents[Good.GREEN] == player_state.cart_max

    def test_fruit_warehouse_fills_cart(self) -> None:
        """Fruit warehouse fills cart with yellow goods."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.FRUIT_WAREHOUSE)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(GenericTileAction())

        assert player_state.cart_contents[Good.YELLOW] == player_state.cart_max

    def test_gemstone_dealer(self) -> None:
        """Gemstone dealer sells ruby for lira."""
        game = create_game()
        player_state = game.player_states[Player.RED]
        player_state.lira = 20  # Enough to buy

        dealer_loc = game.location_map.inverse[Tile.GEMSTONE_DEALER]

        # Move player to dealer
        game.tile_states[Tile.FOUNTAIN].players.remove(Player.RED)
        player_state.location = dealer_loc
        game.tile_states[Tile.GEMSTONE_DEALER].players.add(Player.RED)

        player_state.hand[Card.NO_MOVE] = 1
        game.take_action(NoMoveCardAction(skip_assistant=False))

        assert isinstance(
            dealer_state := game.tile_states[Tile.GEMSTONE_DEALER],
            GemstoneDealerTileState,
        )
        cost = dealer_state.cost
        assert cost is not None

        initial_rubies = player_state.rubies
        initial_lira = player_state.lira

        game.take_action(GenericTileAction())

        assert player_state.rubies == initial_rubies + 1
        assert player_state.lira == initial_lira - cost


class TestVictoryConditions:
    """Tests for game completion."""

    def test_game_completes_at_threshold(self) -> None:
        """Game completes when player reaches ruby threshold."""
        game = create_game()

        # Give RED enough rubies
        game.player_states[Player.RED].rubies = 6

        # Complete a turn cycle - both start at fountain
        fountain_loc = game.location_map.inverse[Tile.FOUNTAIN]
        target: Location | None = None
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 1:
                target = Location(i)
                break
        assert target is not None

        # RED's turn - move to adjacent tile (alone -> skips phase 2)
        game.take_action(Move(target, skip_assistant=False))
        # Now in phase 3, skip tile action
        game.take_action(SkipTileAction())
        game.take_action(YieldTurn())

        # BLUE's turn - move to different adjacent tile
        blue_loc = game.player_states[Player.BLUE].location
        target2: Location | None = None
        for i in range(1, 17):
            loc = Location(i)
            if taxicab_dist(blue_loc, loc) == 1 and loc != target:
                target2 = loc
                break
        assert target2 is not None
        game.take_action(Move(target2, skip_assistant=False))
        game.take_action(SkipTileAction())
        game.take_action(YieldTurn())

        assert game.completed is True

    def test_game_not_complete_before_last_player(self) -> None:
        """Game doesn't complete until last player's turn ends."""
        game = create_game()

        # Give RED enough rubies
        game.player_states[Player.RED].rubies = 6

        # RED's turn only
        fountain_loc = game.location_map.inverse[Tile.FOUNTAIN]
        target: Location | None = None
        for i in range(1, 17):
            if taxicab_dist(fountain_loc, Location(i)) == 1:
                target = Location(i)
                break
        assert target is not None

        game.take_action(Move(target, skip_assistant=False))
        game.take_action(SkipTileAction())
        game.take_action(YieldTurn())

        # After RED yields, game should not be complete yet
        assert game.completed is False
        assert game.current_player == Player.BLUE

    def test_ranking_by_rubies(self) -> None:
        """Ranking is primarily by rubies."""
        game = create_game()
        game.player_states[Player.RED].rubies = 3
        game.player_states[Player.BLUE].rubies = 5

        ranking = game.ranking()
        players_ranked = list(ranking.keys())

        assert players_ranked[0] == Player.BLUE
        assert players_ranked[1] == Player.RED

    def test_ranking_tiebreaker_lira(self) -> None:
        """Lira breaks ties when rubies are equal."""
        game = create_game()
        game.player_states[Player.RED].rubies = 3
        game.player_states[Player.BLUE].rubies = 3
        game.player_states[Player.RED].lira = 10
        game.player_states[Player.BLUE].lira = 15

        ranking = game.ranking()
        players_ranked = list(ranking.keys())

        assert players_ranked[0] == Player.BLUE
        assert players_ranked[1] == Player.RED

    def test_ranking_tiebreaker_cart_contents(self) -> None:
        """Cart contents breaks ties when rubies and lira are equal."""
        game = create_game()
        game.player_states[Player.RED].rubies = 3
        game.player_states[Player.BLUE].rubies = 3
        game.player_states[Player.RED].lira = 10
        game.player_states[Player.BLUE].lira = 10
        game.player_states[Player.RED].cart_contents = Counter({Good.RED: 1})
        game.player_states[Player.BLUE].cart_contents = Counter({Good.RED: 2})

        ranking = game.ranking()
        players_ranked = list(ranking.keys())

        assert players_ranked[0] == Player.BLUE
        assert players_ranked[1] == Player.RED

    def test_ranking_tiebreaker_cart_mixed_colors(self) -> None:
        """Cart contents with mixed colors are counted correctly for tiebreaking."""
        game = create_game()
        game.player_states[Player.RED].rubies = 3
        game.player_states[Player.BLUE].rubies = 3
        game.player_states[Player.RED].lira = 10
        game.player_states[Player.BLUE].lira = 10
        # RED has 3 total goods (1 red + 2 blue)
        game.player_states[Player.RED].cart_contents = Counter({Good.RED: 1, Good.BLUE: 2})
        # BLUE has 4 total goods (1 of each color)
        game.player_states[Player.BLUE].cart_contents = Counter(
            {Good.RED: 1, Good.BLUE: 1, Good.GREEN: 1, Good.YELLOW: 1}
        )

        ranking = game.ranking()
        players_ranked = list(ranking.keys())

        # BLUE should win with 4 goods vs RED's 3 goods
        assert players_ranked[0] == Player.BLUE
        assert players_ranked[1] == Player.RED

    def test_ranking_tiebreaker_hand_size(self) -> None:
        """Hand size breaks ties when rubies, lira, and cart are equal."""
        game = create_game()
        game.player_states[Player.RED].rubies = 3
        game.player_states[Player.BLUE].rubies = 3
        game.player_states[Player.RED].lira = 10
        game.player_states[Player.BLUE].lira = 10
        game.player_states[Player.RED].cart_contents = Counter({Good.RED: 1})
        game.player_states[Player.BLUE].cart_contents = Counter({Good.RED: 1})
        game.player_states[Player.RED].hand = Counter({Card.ONE_GOOD: 1})
        game.player_states[Player.BLUE].hand = Counter({Card.ONE_GOOD: 2})

        ranking = game.ranking()
        players_ranked = list(ranking.keys())

        assert players_ranked[0] == Player.BLUE
        assert players_ranked[1] == Player.RED

    def test_ranking_full_tie_multiple_winners(self) -> None:
        """Players tied on all criteria share the same rank (multiple winners)."""
        game = create_game()
        game.player_states[Player.RED].rubies = 5
        game.player_states[Player.BLUE].rubies = 5
        game.player_states[Player.RED].lira = 10
        game.player_states[Player.BLUE].lira = 10
        game.player_states[Player.RED].cart_contents = Counter({Good.RED: 1})
        game.player_states[Player.BLUE].cart_contents = Counter({Good.RED: 1})
        game.player_states[Player.RED].hand = Counter({Card.ONE_GOOD: 1})
        game.player_states[Player.BLUE].hand = Counter({Card.ONE_GOOD: 1})

        ranking = game.ranking()
        scores = list(ranking.values())

        # Both players should have identical scores — they are co-winners
        assert scores[0] == scores[1]


class TestSpecialNPCs:
    """Tests for governor and smuggler encounters."""

    def test_governor_location(self, two_player_game: GameState) -> None:
        """Governor is placed at specified location."""
        gov_loc = Location(1)
        game = create_game(governor_location=gov_loc)
        tile = game.location_map[gov_loc]
        assert game.tile_states[tile].governor is True

    def test_smuggler_location(self, two_player_game: GameState) -> None:
        """Smuggler is placed at specified location."""
        smug_loc = Location(2)
        game = create_game(smuggler_location=smug_loc)
        tile = game.location_map[smug_loc]
        assert game.tile_states[tile].smuggler is True


class TestCurrentPlayerProperties:
    """Tests for current player convenience properties."""

    def test_current_player_idx(self, two_player_game: GameState) -> None:
        """current_player_idx matches turn state."""
        assert two_player_game.current_player_idx == 0

    def test_current_player_state(self, two_player_game: GameState) -> None:
        """current_player_state returns correct PlayerState."""
        state = two_player_game.current_player_state
        assert state.color == Player.RED

    def test_current_player_location(self, two_player_game: GameState) -> None:
        """current_player_location returns correct location."""
        loc = two_player_game.current_player_location
        assert loc == two_player_game.location_map.inverse[Tile.FOUNTAIN]

    def test_current_player_tile(self, two_player_game: GameState) -> None:
        """current_player_tile returns correct tile."""
        tile = two_player_game.current_player_tile
        assert tile == Tile.FOUNTAIN
