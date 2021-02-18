import typing

from actions import PlayerAction, Move, YieldTurn, NoMoveCardAction, ExtraMoveCardAction, ReturnAssistantCardAction, \
    YellowTileAction, Pay, SkipTileAction, GenericTileAction
from constants import Card, Tile, Location
from game import GameState
from load.actions import load_all_phase_card_action
from load.core import tokens_match, phase_subtokens, action_subtokens, load_card, tokens
from load.location_transformer import LocationTransformer
from turn import phase_allowed_cards


class PhaseLoader(object):
    GENERIC_ACTION_TILES = frozenset({
        Tile.POST_OFFICE, Tile.FABRIC_WAREHOUSE, Tile.FRUIT_WAREHOUSE, Tile.FOUNTAIN, Tile.SPICE_WAREHOUSE,
        Tile.WAINWRIGHT, Tile.GEMSTONE_DEALER
    })

    def __init__(self, gs: GameState, location_transformer: LocationTransformer):
        self.gs: typing.Final = gs
        self.location_transformer: typing.Final = location_transformer

    @classmethod
    def allowed_cards(cls, gs: GameState) -> typing.FrozenSet[Card]:
        phase = gs.turn_state.current_phase
        allowed = set(phase_allowed_cards(phase))
        player_state = gs.player_states[gs.turn_state.current_player]
        if player_state.family_location == gs.location_map.inverse[Tile.POLICE_STATION]:
            allowed.discard(Card.ARREST_FAMILY)
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

    @classmethod
    def determine_card(cls, card_action: str, gs: GameState) -> Card:
        subtokens = action_subtokens(card_action)
        player_state = gs.player_states[gs.turn_state.current_player]
        if subtokens[0].upper() == 'CARD':
            cards: typing.Set[Card] = {k for k, v in player_state.hand.items() if v > 0}
        else:
            pre, card_desc = subtokens[0].split('-')
            assert pre.upper() == 'CARD'
            cards = load_card(card_desc)
        possible_cards = cards & cls.allowed_cards(gs)
        assert possible_cards, f'{card_action} does not match any currently legal cards'
        assert len(possible_cards) == 1, f'{card_action} matched multiple legal cards: {possible_cards}'
        return possible_cards.pop()

    def load_phases_12(self, s: str) -> typing.Iterator[PlayerAction]:
        dont_pay = False
        if s.endswith('!$'):
            dont_pay = True
            s = s[:-2].strip()
        actions = phase_subtokens(s)
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
                continue

            subtokens = action_subtokens(action)
            assert subtokens, 'Empty action not allowed in phase 1'
            if action.upper().startswith('CARD'):
                card = self.determine_card(action, self.gs)

                if card is Card.NO_MOVE:
                    assert len(subtokens) == 1
                    yield NoMoveCardAction(skip_assistant)
                    if skip_assistant:
                        assert idx == len(actions) - 1, 'Assistant skip was not last action'
                        yield YieldTurn()
                        return
                    continue

                if card is Card.EXTRA_MOVE:
                    assert len(subtokens) == 2, 'Location required with extra move card'
                    yield ExtraMoveCardAction(Move(self.location_transformer.apply(Location(int(subtokens[1]))),
                                                   skip_assistant=skip_assistant))
                    if skip_assistant:
                        assert idx == len(actions) - 1, 'Assistant skip was not last action'
                        yield YieldTurn()
                        return
                    continue

                if card is Card.RETURN_ASSISTANT:
                    assert len(subtokens) == 2, 'Location required with return assistant card'
                    yield ReturnAssistantCardAction(self.location_transformer.apply(Location(int(subtokens[1]))))
                    continue

                yield load_all_phase_card_action(card, subtokens[1:])
                continue

            assert tokens_match(tokens(subtokens[0]), ['YELLOW', 'TILE']), f'Unknown action {action}'
            assert len(subtokens) == 2, 'Location required with yellow tile'
            yield YellowTileAction(self.location_transformer.apply(Location(int(subtokens[1]))))
            continue

        # After applying all the explicit actions
        tile_state = self.gs.tile_states[self.gs.location_map[player_state.location]]
        if len(tile_state.players) > 1 and self.gs.location_map[player_state.location] is not Tile.FOUNTAIN:
            if dont_pay:
                yield YieldTurn()
            else:
                yield Pay()
        else:
            assert not dont_pay, 'Payment not required'

    def load_phase_3(self, s: str) -> typing.Iterator[PlayerAction]:
        actions = phase_subtokens(s)
        player_state = self.gs.player_states[self.gs.turn_state.current_player]
        tile = self.gs.location_map[player_state.location]
        for idx, action in enumerate(actions):
            if action == '!':
                yield SkipTileAction()
                return
            if action == '':
                assert tile in self.GENERIC_ACTION_TILES, f'{tile} is not generic'
                yield GenericTileAction()
            if action.upper().startswith('CARD'):
                card = self.determine_card(action, self.gs)
                # todo


