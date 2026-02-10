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

    def test_skip_phase_2_not_allowed_when_yield_required(self) -> None:
        """Cannot skip phase 2 if yield is required."""
        state = TurnState((Player.RED, Player.BLUE))
        state.current_phase = 2
        state.yield_required = True
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
