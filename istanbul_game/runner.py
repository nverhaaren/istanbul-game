import logging
import typing

from . import serialize
from .actions import PlayerAction
from .game import GameState
from .load.phases import PhaseLoader, TurnRow


class Runner:
    def __init__(self, phase_loader: PhaseLoader, turn_source: typing.Iterable[TurnRow]):
        self.phase_loader: typing.Final = phase_loader
        self.turn_source: typing.Final = turn_source

        self.game_state: typing.Final = self.phase_loader.gs

    def run(self) -> None:
        # idx for debugging
        for idx, turn in enumerate(self.turn_source):
            actions = self.phase_loader.load_turn(turn)
            for action in actions:
                try:
                    self.game_state.take_action(action)
                except Exception:
                    logging.error(f"Got exception at turn {idx}, action {action}")
                    raise

    def _turn_states(self, actions: typing.Iterable[PlayerAction]) -> typing.Iterator[GameState]:
        for action in actions:
            self.game_state.take_action(action)
            yield self.game_state

    def run_with_trace(self) -> list[dict]:
        """Run the game and return serialized game state after each turn.

        Returns a list of serialized game states: the initial state followed by
        the state after each turn completes.
        """
        trace = [serialize.game_state(self.game_state)]
        for idx, turn in enumerate(self.turn_source):
            actions = self.phase_loader.load_turn(turn)
            for action in actions:
                try:
                    self.game_state.take_action(action)
                except Exception:
                    logging.error(f"Got exception at turn {idx}, action {action}")
                    raise
            trace.append(serialize.game_state(self.game_state))
        return trace

    def game_state_series(self) -> typing.Iterator[typing.Iterator[GameState]]:
        yield iter([self.game_state])
        for idx, turn in enumerate(self.turn_source):
            actions = self.phase_loader.load_turn(turn)
            try:
                game_state = self._turn_states(actions)
            except Exception:
                logging.error(f"Got exception at turn {idx}, actions: {actions}")
                raise
            yield game_state
