"""Tests for game module."""
import pytest
from collections import Counter

from istanbul_game.game import GameState, taxicab_dist
from istanbul_game.constants import Player, Location, Tile, Good, Card
from istanbul_game.actions import (
    Move,
    Pay,
    YieldTurn,
    GenericTileAction,
    SkipTileAction,
    ChooseReward,
    OneGoodCardAction,
    FiveLiraCardAction,
    NoMoveCardAction,
    ExtraMoveCardAction,
    MosqueAction,
    MarketAction,
    BlackMarketAction,
    TeaHouseAction,
    FountainAction,
    EncounterGovernor,
    EncounterSmuggler,
)
from istanbul_game.tiles import MarketTileState, GemstoneDealerTileState
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

        # Manually set up: place an assistant at a location
        fountain_loc = game.location_map.inverse[Tile.FOUNTAIN]
        target = Location(3)  # Pick a specific location

        # Pre-place assistant at target
        target_tile = game.location_map[target]
        game.tile_states[target_tile].assistants.add(player)
        player_state.assistant_locations.add(target)
        player_state.stack_size -= 1
        initial_stack = player_state.stack_size

        # Now move player to target (from fountain)
        # First, use no-move card to stay at fountain (which is adjacent to many tiles)
        # Actually, let's just manually move for this test
        game.tile_states[Tile.FOUNTAIN].players.remove(player)
        adjacent_to_target: Location | None = None
        for i in range(1, 17):
            loc = Location(i)
            if taxicab_dist(target, loc) == 1:
                adjacent_to_target = loc
                break
        assert adjacent_to_target is not None
        player_state.location = adjacent_to_target
        game.tile_states[game.location_map[adjacent_to_target]].players.add(player)

        # Now make a legal move to target
        game.take_action(Move(target, skip_assistant=False))

        # Should have picked up assistant (stack increased, location removed)
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

        two_player_game.take_action(
            ExtraMoveCardAction(Move(target, skip_assistant=False))
        )

        assert player_state.location == target
        assert player_state.hand[Card.EXTRA_MOVE] == 0


class TestTileActions:
    """Tests for tile-specific actions."""

    def test_warehouse_fills_cart(self, two_player_game: GameState) -> None:
        """Warehouse fills cart with corresponding good."""
        fabric_loc = two_player_game.location_map.inverse[Tile.FABRIC_WAREHOUSE]
        fountain_loc = two_player_game.location_map.inverse[Tile.FOUNTAIN]

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
