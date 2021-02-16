import typing

from actions import PlayerAction, Move, YieldTurn
from constants import Card, Tile, Location
from game import GameState
from load.location_transformer import LocationTransformer
from turn import phase_allowed_cards


class PhaseLoader(object):
    def __init__(self, gs: GameState, location_transformer: LocationTransformer):
        self.gs: typing.Final = gs
        self.location_transformer: typing.Final = location_transformer

    @classmethod
    def allowed_cards(cls, phase: int, gs: GameState) -> typing.FrozenSet[Card]:
        allowed = set(phase_allowed_cards(phase))
        player_state = gs.player_states[gs.turn_state.current_player]
        if phase == 1 and not player_state.assistant_locations:
            allowed.discard(Card.RETURN_ASSISTANT)
        if phase == 3:
            tile = gs.location_map[player_state.location]
            card_tile_matches = {
                Card.SELL_ANY: Tile.SMALL_MARKET,
                Card.DOUBLE_PO: Tile.POST_OFFICE,
                Card.DOUBLE_SULTAN: Tile.SULTANS_PALACE,
                Card.DOUBLE_DEALER: Tile.GEMSTONE_DEALER,
            }
            for c, t in card_tile_matches.items():
                if tile is not t:
                    allowed.discard(c)
        return frozenset(allowed)

    def load_phases_12(self, s: str) -> typing.Iterator[PlayerAction]:
        dont_pay = False
        if s.endswith('!$'):
            dont_pay = True
            s = s[:-2]
        actions = s.split(';')
        player_state = self.gs.player_states[self.gs.turn_state.current_player]
        for idx, action in enumerate(actions):
            skip_assistant = False
            if action.endswith('!'):
                skip_assistant = True
                action = action[:-1]
            action = action.rstrip()
            if action.isdigit():
                yield Move(self.location_transformer.apply(Location(int(action))), skip_assistant=skip_assistant)
                if skip_assistant:
                    assert idx == len(actions) - 1, 'Assistant skip was not last action'
                    yield YieldTurn()
                    return
            # todo: Yellow tile, various cards
