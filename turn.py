from typing import Final

from actions import PlayerAction, YieldTurn, OneGoodCardAction, FiveLiraCardAction, ArrestFamilyCardAction, \
    YellowTileAction, Move, ExtraMoveCardAction, NoMoveCardAction, ReturnAssistantCardAction, Pay, PlaceTileAction, \
    SkipTileAction, DoubleCardAction, SellAnyCardAction, ChooseReward, EncounterGovernor, EncounterSmuggler, \
    PoliceStationAction


class TurnState(object):
    def __init__(self, players):
        self.players: Final = players
        self.current_player_idx: int = 0
        self.current_phase: int = 1
        self.yield_required: bool = False  # This requires explicit yields, inferring them can be done higher up

    @property
    def current_player(self):
        return self.players[self.current_player_idx]

    def skip_phase_2(self):
        assert self.current_phase == 2 and not self.yield_required
        self.current_phase = 3

    def valid_action(self, action: PlayerAction):
        # possible todo: maybe a flag indicating whether to prevent using governor/smuggler multiple times a turn?
        # (I think rules suggest that is illegal but there is some ambiguity)
        assert isinstance(action, PlayerAction)
        if self.yield_required:
            return isinstance(action, (YieldTurn, OneGoodCardAction, FiveLiraCardAction, ArrestFamilyCardAction,
                                       YellowTileAction))
        if isinstance(action, YieldTurn):
            return self.current_phase in (2, 4)

        if isinstance(action, (Move, ExtraMoveCardAction, NoMoveCardAction, ReturnAssistantCardAction)):
            return self.current_phase == 1
        if isinstance(action, Pay):
            return self.current_phase == 2
        if isinstance(action, (PlaceTileAction, SkipTileAction, DoubleCardAction, SellAnyCardAction)):
            return self.current_phase == 3
        if isinstance(action, (ChooseReward, EncounterGovernor, EncounterSmuggler)):
            return self.current_phase == 4
        return True  # All other actions can be taken at any time

    def take_action(self, action: PlayerAction):
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
        if isinstance(action, (PlaceTileAction, SkipTileAction, DoubleCardAction, SellAnyCardAction)):
            if not isinstance(action, PoliceStationAction):
                self.current_phase = 4
        # All other actions do not alter turn state
