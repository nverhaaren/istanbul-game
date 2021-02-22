import typing

from load.phases import PhaseLoader, TurnRow


class Runner(object):
    def __init__(self, phase_loader: PhaseLoader, turn_source: typing.Iterable[TurnRow]):
        self.phase_loader: typing.Final = phase_loader
        self.turn_source: typing.Final = turn_source

        self.game_state: typing.Final = self.phase_loader.gs

    def run(self):
        for turn in self.turn_source:
            actions = self.phase_loader.load_turn(turn)
            for action in actions:
                self.game_state.take_action(action)
