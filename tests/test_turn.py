"""Tests for turn state management."""
import pytest
from collections import Counter

from istanbul_game.turn import TurnState, phase_allowed_cards, ALL_PHASE_CARDS
from istanbul_game.actions import (
    YieldTurn,
    Move,
    Pay,
    PlaceTileAction,
    GenericTileAction,
    SkipTileAction,
    ChooseReward,
    EncounterGovernor,
    EncounterSmuggler,
    ExtraMoveCardAction,
    NoMoveCardAction,
    ReturnAssistantCardAction,
    DoubleCardAction,
    SellAnyCardAction,
    MarketAction,
    OneGoodCardAction,
    FiveLiraCardAction,
    ArrestFamilyCardAction,
    YellowTileAction,
)
from istanbul_game.constants import Player, Location, Card, Good


class TestTurnStateInitialization:
    """Tests for TurnState initialization."""

    def test_starts_with_first_player(self) -> None:
        """Turn starts with first player in sequence."""
        players = (Player.RED, Player.BLUE, Player.GREEN)
        state = TurnState(players)
        assert state.current_player == Player.RED
        assert state.current_player_idx == 0

    def test_starts_in_phase_1(self) -> None:
        """Turn starts in phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        assert state.current_phase == 1

    def test_yield_not_required_initially(self) -> None:
        """Yield is not required at start."""
        state = TurnState((Player.RED, Player.BLUE))
        assert state.yield_required is False


class TestTurnStateValidAction:
    """Tests for action validation by phase."""

    def test_move_valid_in_phase_1(self) -> None:
        """Move is valid in phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        move = Move(Location(5), skip_assistant=False)
        assert state.valid_action(move) is True

    def test_move_invalid_in_phase_2(self) -> None:
        """Move is invalid in phase 2."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 2
        move = Move(Location(5), skip_assistant=False)
        assert state.valid_action(move) is False

    def test_pay_valid_in_phase_2(self) -> None:
        """Pay is valid in phase 2."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 2
        assert state.valid_action(Pay()) is True

    def test_pay_invalid_in_phase_1(self) -> None:
        """Pay is invalid in phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        assert state.valid_action(Pay()) is False

    def test_tile_action_valid_in_phase_3(self) -> None:
        """Tile actions are valid in phase 3."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 3
        assert state.valid_action(GenericTileAction()) is True
        assert state.valid_action(SkipTileAction()) is True

    def test_tile_action_invalid_in_phase_1(self) -> None:
        """Tile actions are invalid in phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        assert state.valid_action(GenericTileAction()) is False

    def test_choose_reward_valid_in_phase_4(self) -> None:
        """Choose reward is valid in phase 4."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 4
        reward = ChooseReward(ChooseReward.LIRA)
        assert state.valid_action(reward) is True

    def test_yield_valid_in_phase_2_and_4(self) -> None:
        """Yield is valid in phases 2 and 4."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 2
        assert state.valid_action(YieldTurn()) is True
        state.current_phase = 4
        assert state.valid_action(YieldTurn()) is True

    def test_yield_invalid_in_phase_1(self) -> None:
        """Yield is invalid in phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        assert state.valid_action(YieldTurn()) is False

    def test_yield_invalid_in_phase_3(self) -> None:
        """Yield is invalid in phase 3."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 3
        assert state.valid_action(YieldTurn()) is False

    def test_extra_move_valid_in_phase_1(self) -> None:
        """Extra move card is valid in phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        action = ExtraMoveCardAction(Move(Location(5), skip_assistant=False))
        assert state.valid_action(action) is True

    def test_no_move_valid_in_phase_1(self) -> None:
        """No move card is valid in phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        action = NoMoveCardAction(skip_assistant=False)
        assert state.valid_action(action) is True

    def test_return_assistant_valid_in_phase_1(self) -> None:
        """Return assistant card is valid in phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        action = ReturnAssistantCardAction(Location(5))
        assert state.valid_action(action) is True

    def test_double_card_valid_in_phase_3(self) -> None:
        """Double cards are valid in phase 3."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 3
        action = DoubleCardAction(Card.DOUBLE_PO, (GenericTileAction(), GenericTileAction()))
        assert state.valid_action(action) is True


class TestTurnStateYieldRequired:
    """Tests for yield_required behavior."""

    def test_yield_required_only_allows_specific_actions(self) -> None:
        """When yield_required, only certain actions are valid."""
        state = TurnState((Player.RED, Player.BLUE))
        state.yield_required = True

        # Valid actions when yield required
        assert state.valid_action(YieldTurn()) is True
        assert state.valid_action(OneGoodCardAction(Good.RED)) is True
        assert state.valid_action(FiveLiraCardAction()) is True
        assert state.valid_action(ArrestFamilyCardAction(ChooseReward(Card.ONE_GOOD))) is True
        assert state.valid_action(YellowTileAction(Location(5))) is True

        # Invalid actions when yield required
        assert state.valid_action(Move(Location(5), skip_assistant=False)) is False
        assert state.valid_action(Pay()) is False
        assert state.valid_action(GenericTileAction()) is False


class TestTurnStateTakeAction:
    """Tests for take_action state transitions."""

    def test_yield_advances_player(self) -> None:
        """Yielding turn advances to next player."""
        state = TurnState((Player.RED, Player.BLUE, Player.GREEN))
        state.current_phase = 2  # Yield valid in phase 2
        state.take_action(YieldTurn())
        assert state.current_player == Player.BLUE
        assert state.current_player_idx == 1

    def test_yield_cycles_to_first_player(self) -> None:
        """Yielding from last player cycles to first."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 2
        state.current_player_idx = 1  # Blue's turn
        state.take_action(YieldTurn())
        assert state.current_player == Player.RED
        assert state.current_player_idx == 0

    def test_yield_resets_phase(self) -> None:
        """Yielding resets to phase 1."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 4
        state.take_action(YieldTurn())
        assert state.current_phase == 1

    def test_yield_clears_yield_required(self) -> None:
        """Yielding clears yield_required flag."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 2
        state.yield_required = True
        state.take_action(YieldTurn())
        assert state.yield_required is False

    def test_move_advances_to_phase_2(self) -> None:
        """Moving advances to phase 2."""
        state = TurnState((Player.RED, Player.BLUE))
        move = Move(Location(5), skip_assistant=False)
        state.take_action(move)
        assert state.current_phase == 2

    def test_move_skip_assistant_sets_yield_required(self) -> None:
        """Moving with skip_assistant sets yield_required."""
        state = TurnState((Player.RED, Player.BLUE))
        move = Move(Location(5), skip_assistant=True)
        state.take_action(move)
        assert state.yield_required is True

    def test_pay_advances_to_phase_3(self) -> None:
        """Paying advances to phase 3."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 2
        state.take_action(Pay())
        assert state.current_phase == 3

    def test_tile_action_advances_to_phase_4(self) -> None:
        """Tile action advances to phase 4."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 3
        state.take_action(GenericTileAction())
        assert state.current_phase == 4

    def test_skip_phase_2(self) -> None:
        """Can skip phase 2 when alone on tile."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 2
        state.skip_phase_2()
        assert state.current_phase == 3

    def test_skip_phase_2_requires_phase_2(self) -> None:
        """Cannot skip phase 2 if not in phase 2."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 1
        with pytest.raises(AssertionError):
            state.skip_phase_2()

        state.current_phase = 3
        with pytest.raises(AssertionError):
            state.skip_phase_2()

    def test_no_move_advances_to_phase_2(self) -> None:
        """No move card advances to phase 2."""
        state = TurnState((Player.RED, Player.BLUE))
        action = NoMoveCardAction(skip_assistant=False)
        state.take_action(action)
        assert state.current_phase == 2

    def test_extra_move_advances_to_phase_2(self) -> None:
        """Extra move card advances to phase 2."""
        state = TurnState((Player.RED, Player.BLUE))
        action = ExtraMoveCardAction(Move(Location(5), skip_assistant=False))
        state.take_action(action)
        assert state.current_phase == 2

    def test_sell_any_card_valid_in_phase_3(self) -> None:
        """Sell any card is valid in phase 3."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 3
        action = SellAnyCardAction(MarketAction(
            goods=Counter({Good.RED: 1}),
            new_demand=Counter({Good.BLUE: 2, Good.GREEN: 2, Good.YELLOW: 1})
        ))
        assert state.valid_action(action) is True

    def test_governor_encounter_valid_in_phase_4(self) -> None:
        """Governor encounter is valid in phase 4."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 4
        action = EncounterGovernor(gain=Card.FIVE_LIRA, cost=Pay(), roll=(3, 4))
        assert state.valid_action(action) is True

    def test_smuggler_encounter_valid_in_phase_4(self) -> None:
        """Smuggler encounter is valid in phase 4."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 4
        action = EncounterSmuggler(gain=Good.RED, cost=Pay(), roll=(3, 4))
        assert state.valid_action(action) is True


class TestPhaseAllowedCards:
    """Tests for phase_allowed_cards function."""

    def test_all_phase_cards_constant(self) -> None:
        """ALL_PHASE_CARDS contains base cards usable any time."""
        assert Card.ONE_GOOD in ALL_PHASE_CARDS
        assert Card.FIVE_LIRA in ALL_PHASE_CARDS
        assert Card.ARREST_FAMILY in ALL_PHASE_CARDS
        assert len(ALL_PHASE_CARDS) == 3

    def test_phase_1_includes_movement_cards(self) -> None:
        """Phase 1 includes movement-related cards."""
        cards = phase_allowed_cards(1)
        assert Card.EXTRA_MOVE in cards
        assert Card.NO_MOVE in cards
        assert Card.RETURN_ASSISTANT in cards
        # Plus base cards
        assert Card.ONE_GOOD in cards

    def test_phase_2_only_base_cards(self) -> None:
        """Phase 2 only allows base cards."""
        cards = phase_allowed_cards(2)
        assert cards == ALL_PHASE_CARDS

    def test_phase_3_includes_tile_cards(self) -> None:
        """Phase 3 includes tile action cards."""
        cards = phase_allowed_cards(3)
        assert Card.SELL_ANY in cards
        assert Card.DOUBLE_SULTAN in cards
        assert Card.DOUBLE_PO in cards
        assert Card.DOUBLE_DEALER in cards
        # Plus base cards
        assert Card.ONE_GOOD in cards

    def test_phase_4_only_base_cards(self) -> None:
        """Phase 4 only allows base cards."""
        cards = phase_allowed_cards(4)
        assert cards == ALL_PHASE_CARDS

    def test_invalid_phase_raises(self) -> None:
        """Invalid phase raises assertion error."""
        with pytest.raises(AssertionError):
            phase_allowed_cards(0)
        with pytest.raises(AssertionError):
            phase_allowed_cards(5)


class TestEarlyTurnExit:
    """Tests for early turn exit scenarios."""

    def test_can_yield_in_phase_2_with_no_money(self) -> None:
        """Player can yield in phase 2 if they cannot pay."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]
        blue_player = game.player_states[Player.BLUE]

        # Set up: Red has no lira, Blue is at target tile
        red_player.lira = 0
        red_player.hand[Card.NO_MOVE] = 1
        target_loc = Location(3)
        target_tile = game.location_map[target_loc]

        # Place blue at target
        blue_player.location = target_loc
        game.tile_states[target_tile].players.add(Player.BLUE)

        # Move red to same tile
        move_player_to_tile(game, Player.RED, target_tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Now in phase 2, red cannot afford to pay
        assert game.turn_state.current_phase == 2
        assert game.turn_state.valid_action(YieldTurn())

        # Red yields
        game.take_action(YieldTurn())
        assert game.turn_state.current_player == Player.BLUE

    def test_must_yield_when_no_assistants_available(self) -> None:
        """Player with no assistants must skip assistant placement."""
        from tests.helpers import create_game
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]

        # Use all assistants
        red_player.stack_size = 0
        red_player.assistant_locations.clear()

        # Move to a different tile - must skip assistant since we have none
        target_loc = Location(3)
        move = Move(target_loc, skip_assistant=True)
        game.take_action(move)

        # Should set yield_required
        assert game.turn_state.yield_required

    def test_fountain_exempts_from_assistant_requirement(self) -> None:
        """At fountain, no assistant placement required."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]

        # Remove all assistants
        red_player.stack_size = 0
        red_player.assistant_locations.clear()

        # Move to fountain should work without assistants
        red_player.hand[Card.NO_MOVE] = 1
        move_player_to_tile(game, Player.RED, Tile.FOUNTAIN)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Should skip phase 2 automatically (fountain logic)
        assert game.turn_state.current_phase == 3


class TestSkipTileAction:
    """Tests for skipping tile actions."""

    def test_can_skip_tile_action(self) -> None:
        """Player can skip the tile action in phase 3."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]
        red_player.hand[Card.NO_MOVE] = 1

        move_player_to_tile(game, Player.RED, Tile.FABRIC_WAREHOUSE)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Now in phase 3
        assert game.turn_state.current_phase == 3

        # Skip tile action
        game.take_action(SkipTileAction())

        # Should advance to phase 4
        assert game.turn_state.current_phase == 4

    def test_skip_tile_action_valid_in_phase_3_only(self) -> None:
        """SkipTileAction is only valid in phase 3."""
        state = TurnState((Player.RED, Player.BLUE))

        state.current_phase = 1
        assert not state.valid_action(SkipTileAction())

        state.current_phase = 2
        assert not state.valid_action(SkipTileAction())

        state.current_phase = 3
        assert state.valid_action(SkipTileAction())

        state.current_phase = 4
        assert not state.valid_action(SkipTileAction())


class TestPaymentToOtherPlayers:
    """Tests for paying other players when not at fountain."""

    def test_must_pay_when_other_players_present(self) -> None:
        """Must pay when other players are at the tile."""
        from tests.helpers import create_game, move_player_to_tile

        game = create_game()
        red_player = game.player_states[Player.RED]
        blue_player = game.player_states[Player.BLUE]

        # Place blue at target location
        target_loc = Location(3)
        target_tile = game.location_map[target_loc]
        blue_player.location = target_loc
        game.tile_states[target_tile].players.add(Player.BLUE)

        # Red moves to same tile
        red_player.hand[Card.NO_MOVE] = 1
        red_player.lira = 10
        move_player_to_tile(game, Player.RED, target_tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Should be in phase 2 (payment phase)
        assert game.turn_state.current_phase == 2

        initial_red_lira = red_player.lira
        initial_blue_lira = blue_player.lira

        # Pay action
        game.take_action(Pay())

        # Red should have paid, blue should have received
        assert red_player.lira < initial_red_lira
        assert blue_player.lira > initial_blue_lira

    def test_no_payment_at_fountain(self) -> None:
        """No payment required when at fountain, even with other players."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]
        blue_player = game.player_states[Player.BLUE]

        # Both players start at fountain
        fountain_loc = game.location_map.inverse[Tile.FOUNTAIN]
        assert red_player.location == fountain_loc
        assert blue_player.location == fountain_loc

        # Red uses no-move card
        red_player.hand[Card.NO_MOVE] = 1
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Should skip phase 2 (no payment at fountain)
        assert game.turn_state.current_phase == 3

    def test_skip_phase_2_when_alone(self) -> None:
        """Phase 2 is skipped when player is alone on tile."""
        from tests.helpers import create_game
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]
        red_player.hand[Card.NO_MOVE] = 1

        # Move to empty tile
        target_loc = Location(5)
        move = Move(target_loc, skip_assistant=False)
        game.take_action(move)

        # Should skip phase 2 (alone on tile)
        assert game.turn_state.current_phase == 3


class TestFamilyMemberCapture:
    """Tests for capturing other family members."""

    def test_must_catch_other_family_members(self) -> None:
        """Player must choose reward after catching family members."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]
        blue_player = game.player_states[Player.BLUE]

        # Place blue's family member at target tile
        target_loc = Location(5)
        target_tile = game.location_map[target_loc]
        blue_player.family_location = target_loc
        game.tile_states[target_tile].family_members.add(Player.BLUE)

        # Red moves to target and performs action
        red_player.hand[Card.NO_MOVE] = 1
        move_player_to_tile(game, Player.RED, target_tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(GenericTileAction())

        # Should have outstanding reward choice
        assert game.outstanding_reward_choices == 1

        # Cannot yield without choosing reward
        with pytest.raises(AssertionError):
            game.take_action(YieldTurn())

        # Must choose reward
        game.take_action(ChooseReward(ChooseReward.LIRA))

        # Blue's family should be back at police station
        police_loc = game.location_map.inverse[Tile.POLICE_STATION]
        assert blue_player.family_location == police_loc

    def test_capture_multiple_family_members(self) -> None:
        """Can capture multiple family members at once."""
        from tests.helpers import create_game, move_player_to_tile

        # Create 3-player game
        game = create_game(players=(Player.RED, Player.BLUE, Player.GREEN))
        red_player = game.player_states[Player.RED]
        blue_player = game.player_states[Player.BLUE]
        green_player = game.player_states[Player.GREEN]

        # Place multiple family members at target
        target_loc = Location(5)
        target_tile = game.location_map[target_loc]
        blue_player.family_location = target_loc
        green_player.family_location = target_loc
        game.tile_states[target_tile].family_members.add(Player.BLUE)
        game.tile_states[target_tile].family_members.add(Player.GREEN)

        # Red captures them
        red_player.hand[Card.NO_MOVE] = 1
        move_player_to_tile(game, Player.RED, target_tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(GenericTileAction())

        # Should have 2 reward choices
        assert game.outstanding_reward_choices == 2

        # Choose rewards
        game.take_action(ChooseReward(ChooseReward.LIRA))
        assert game.outstanding_reward_choices == 1
        game.take_action(ChooseReward(Card.ONE_GOOD))
        assert game.outstanding_reward_choices == 0


class TestNPCEncounters:
    """Tests for governor and smuggler encounters."""

    def test_governor_encounter_optional(self) -> None:
        """Governor encounter is optional in phase 4."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.actions import Pay

        governor_loc = Location(5)
        game = create_game(governor_location=governor_loc)
        red_player = game.player_states[Player.RED]

        # Move to governor tile
        gov_tile = game.location_map[governor_loc]
        red_player.hand[Card.NO_MOVE] = 1
        red_player.lira = 10
        move_player_to_tile(game, Player.RED, gov_tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(SkipTileAction())

        # Now in phase 4, encounter is optional
        assert game.turn_state.current_phase == 4

        # Can yield without encountering
        game.take_action(YieldTurn())
        assert game.turn_state.current_player == Player.BLUE

    def test_governor_moves_after_encounter(self) -> None:
        """Governor moves to new location after encounter."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.actions import Pay

        governor_loc = Location(5)
        game = create_game(governor_location=governor_loc)
        red_player = game.player_states[Player.RED]

        # Move to governor tile
        gov_tile = game.location_map[governor_loc]
        red_player.hand[Card.NO_MOVE] = 1
        red_player.lira = 10
        move_player_to_tile(game, Player.RED, gov_tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(SkipTileAction())

        # Governor should be at this tile
        assert game.tile_states[gov_tile].governor

        # Encounter governor
        game.take_action(EncounterGovernor(
            gain=Card.FIVE_LIRA,
            cost=Pay(),
            roll=(3, 4)
        ))

        # Governor should no longer be at this tile
        assert not game.tile_states[gov_tile].governor

        # Governor should be at a new location (check that governor flag is set somewhere)
        gov_found = any(state.governor for state in game.tile_states.values())
        assert gov_found

    def test_smuggler_moves_after_encounter(self) -> None:
        """Smuggler relocates based on dice roll after encounter."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.actions import Pay

        smuggler_loc = Location(7)
        game = create_game(smuggler_location=smuggler_loc)
        red_player = game.player_states[Player.RED]

        # Move to smuggler tile
        smug_tile = game.location_map[smuggler_loc]
        red_player.hand[Card.NO_MOVE] = 1
        red_player.lira = 10
        move_player_to_tile(game, Player.RED, smug_tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(SkipTileAction())

        # Smuggler should be at this tile
        assert game.tile_states[smug_tile].smuggler

        # Encounter smuggler with a specific roll
        # Roll determines new location - smuggler moves regardless
        game.take_action(EncounterSmuggler(
            gain=Good.RED,
            cost=Pay(),
            roll=(3, 4)  # Sum = 7, will place smuggler at location determined by roll
        ))

        # Smuggler should be at location determined by roll (could be same location)
        # Just verify smuggler flag is set somewhere
        smug_found = any(state.smuggler for state in game.tile_states.values())
        assert smug_found

    def test_can_encounter_both_governor_and_smuggler(self) -> None:
        """Can encounter both NPCs if at same tile."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.actions import Pay

        # Place both at same location
        npc_loc = Location(5)
        game = create_game(governor_location=npc_loc, smuggler_location=npc_loc)
        red_player = game.player_states[Player.RED]

        # Move to their tile
        npc_tile = game.location_map[npc_loc]
        red_player.hand[Card.NO_MOVE] = 1
        red_player.lira = 20
        move_player_to_tile(game, Player.RED, npc_tile)
        game.take_action(NoMoveCardAction(skip_assistant=False))
        game.take_action(SkipTileAction())

        # Encounter governor
        game.take_action(EncounterGovernor(
            gain=Card.FIVE_LIRA,
            cost=Pay(),
            roll=(3, 4)
        ))

        # Still in phase 4, can encounter smuggler too
        assert game.turn_state.current_phase == 4
        game.take_action(EncounterSmuggler(
            gain=Good.RED,
            cost=Pay(),
            roll=(3, 4)
        ))


class TestAssistantPlacementRequirement:
    """Tests for assistant placement/pickup requirements."""

    def test_must_place_or_pick_assistant_unless_fountain(self) -> None:
        """Player must place or pick up assistant, except at fountain."""
        from tests.helpers import create_game
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]

        # Place assistant at target first
        target_loc = Location(5)
        red_player.assistant_locations.add(target_loc)
        game.tile_states[game.location_map[target_loc]].assistants.add(Player.RED)
        red_player.stack_size = 3

        # Move to tile with assistant - should pick it up
        red_player.hand[Card.NO_MOVE] = 1
        move = Move(target_loc, skip_assistant=False)
        game.take_action(move)

        # Assistant should be picked up
        assert red_player.stack_size == 4
        assert target_loc not in red_player.assistant_locations

    def test_skip_assistant_sets_yield_required(self) -> None:
        """Skipping assistant placement requires yield."""
        game = TurnState((Player.RED, Player.BLUE))
        move = Move(Location(5), skip_assistant=True)
        game.take_action(move)

        assert game.yield_required

    def test_fountain_no_assistant_requirement(self) -> None:
        """Fountain doesn't require assistant placement/pickup."""
        from tests.helpers import create_game, move_player_to_tile
        from istanbul_game.constants import Tile

        game = create_game()
        red_player = game.player_states[Player.RED]

        # Already at fountain, use no-move
        red_player.hand[Card.NO_MOVE] = 1
        game.take_action(NoMoveCardAction(skip_assistant=False))

        # Should skip to phase 3 (fountain exempts from payment and assistant requirements)
        assert game.turn_state.current_phase == 3
