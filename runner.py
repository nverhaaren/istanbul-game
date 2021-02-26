import typing

from actions import PlayerAction
from game import GameState
from load.phases import PhaseLoader, TurnRow


class Runner(object):
    def __init__(self, phase_loader: PhaseLoader, turn_source: typing.Iterable[TurnRow]):
        self.phase_loader: typing.Final = phase_loader
        self.turn_source: typing.Final = turn_source

        self.game_state: typing.Final = self.phase_loader.gs

    def run(self):
        # idx for debugging
        for idx, turn in enumerate(self.turn_source):
            actions = self.phase_loader.load_turn(turn)
            for action in actions:
                self.game_state.take_action(action)

    def _turn_states(self, actions: typing.Iterable[PlayerAction]) -> typing.Iterator[GameState]:
        for action in actions:
            self.game_state.take_action(action)
            yield self.game_state

    def game_state_series(self) -> typing.Iterator[typing.Iterator[GameState]]:
        yield iter([self.game_state])
        for idx, turn in enumerate(self.turn_source):
            actions = self.phase_loader.load_turn(turn)
            yield self._turn_states(actions)
