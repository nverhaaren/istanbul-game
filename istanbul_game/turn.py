import typing

from .actions import (
    ArrestFamilyCardAction,
    ChooseReward,
    DoubleCardAction,
    EncounterGovernor,
    EncounterSmuggler,
    ExtraMoveCardAction,
    FiveLiraCardAction,
    GreenTileAction,
    Move,
    NoMoveCardAction,
    OneGoodCardAction,
    Pay,
    PlaceTileAction,
    PlayerAction,
    PoliceStationAction,
    ReturnAssistantCardAction,
    SellAnyCardAction,
    SkipTileAction,
    YellowTileAction,
    YieldTurn,
)
from .constants import Card, Player


class TurnState:
    def __init__(self, players: typing.Sequence[Player]):
        self.players: typing.Final = players
        self.current_player_idx: int = 0
        self.current_phase: int = 1
        self.yield_required: bool = False  # This requires explicit yields, inferring them can be done higher up

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    def skip_phase_2(self) -> None:
        assert self.current_phase == 2
        self.current_phase = 3

    def valid_action(self, action: PlayerAction) -> bool:
        # possible todo: maybe a flag indicating whether to prevent using governor/smuggler multiple times a turn?
        # (I think rules suggest that is illegal but there is some ambiguity)
        # Also a flag about enforcing using the return assistant to stack via card only in phase 1, which is kinda
        # pointless, although most common
        assert isinstance(action, PlayerAction)
        if self.yield_required:
            return isinstance(
                action, (YieldTurn, OneGoodCardAction, FiveLiraCardAction, ArrestFamilyCardAction, YellowTileAction)
            )
        if isinstance(action, YieldTurn):
            return self.current_phase in (2, 4)

        if isinstance(action, (Move, ExtraMoveCardAction, NoMoveCardAction, ReturnAssistantCardAction)):
            return self.current_phase == 1
        if isinstance(action, Pay):
            return self.current_phase == 2
        if isinstance(action, (PlaceTileAction, SkipTileAction, DoubleCardAction, SellAnyCardAction, GreenTileAction)):
            return self.current_phase == 3
        if isinstance(action, (ChooseReward, EncounterGovernor, EncounterSmuggler)):
            return self.current_phase == 4
        return True  # All other actions can be taken at any time

    def take_action(self, action: PlayerAction) -> None:
        assert self.valid_action(action)
        if isinstance(action, YieldTurn):
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            self.current_phase = 1
            self.yield_required = False
            return

        if isinstance(action, ExtraMoveCardAction):
            action = action.move
        if isinstance(action, (Move, NoMoveCardAction)):
            self.current_phase = 2
            if action.skip_assistant:
                self.yield_required = True
            return
        if isinstance(action, Pay):
            self.current_phase = 3
        if isinstance(  # noqa: SIM102 - nested check for subtype exclusion is clearer
            action, (PlaceTileAction, SkipTileAction, DoubleCardAction, SellAnyCardAction, GreenTileAction)
        ):
            if not isinstance(action, PoliceStationAction):
                self.current_phase = 4
        # All other actions do not alter turn state


ALL_PHASE_CARDS: frozenset[Card] = frozenset({Card.ONE_GOOD, Card.FIVE_LIRA, Card.ARREST_FAMILY})


def phase_allowed_cards(phase: int) -> frozenset[Card]:
    assert 1 <= phase <= 4, f"Invalid phase: {phase}"

    if phase in {2, 4}:
        return ALL_PHASE_CARDS

    if phase == 1:
        return frozenset(ALL_PHASE_CARDS | {Card.EXTRA_MOVE, Card.NO_MOVE, Card.RETURN_ASSISTANT})

    assert phase == 3
    return frozenset(ALL_PHASE_CARDS | {Card.SELL_ANY, Card.DOUBLE_SULTAN, Card.DOUBLE_PO, Card.DOUBLE_DEALER})
