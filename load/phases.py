import itertools
import typing

from actions import PlayerAction, Move, YieldTurn, NoMoveCardAction, ExtraMoveCardAction, ReturnAssistantCardAction, \
    YellowTileAction, Pay, SkipTileAction, GenericTileAction, DoubleCardAction, SultansPalaceAction, GreenTileAction, \
    PoliceStationAction, PlaceTileAction, SellAnyCardAction, MarketAction, ChooseReward, EncounterGovernor, \
    EncounterSmuggler
from constants import Card, Tile, Location
from game import GameState
from load.actions import load_all_phase_card_action, load_mosque_action, \
    load_warehouse_action, load_black_market_action, load_caravansary_action, load_market_action, load_tea_house_action, \
    load_sultans_palace_action
from load.core import tokens_match, phase_subtokens, action_subtokens, load_card, tokens, load_good_counter, \
    load_exact_card, load_roll, load_good
from load.location_transformer import LocationTransformer
from tiles import MarketTileState
from turn import phase_allowed_cards


class TurnRow(object):
    def __init__(self, move: str, action: str, rewards: str, gov: str, smug: str):
        self.move: typing.Final = move
        self.action: typing.Final = action
        self.rewards: typing.Final = rewards
        self.gov: typing.Final = gov
        self.smug: typing.Final = smug


class PhaseLoader(object):
    GENERIC_ACTION_TILES = frozenset({
        Tile.POST_OFFICE, Tile.FABRIC_WAREHOUSE, Tile.FRUIT_WAREHOUSE, Tile.FOUNTAIN, Tile.SPICE_WAREHOUSE,
        Tile.WAINWRIGHT, Tile.GEMSTONE_DEALER
    })

    def __init__(self, gs: GameState, location_transformer: LocationTransformer):
        self.gs: typing.Final = gs
        self.location_transformer: typing.Final = location_transformer

    @classmethod
    def allowed_cards(cls, gs: GameState, tile: typing.Optional[Tile] = None) -> typing.FrozenSet[Card]:
        phase = gs.turn_state.current_phase
        allowed = set(phase_allowed_cards(phase))
        player_state = gs.player_states[gs.turn_state.current_player]
        if player_state.family_location == gs.location_map.inverse[Tile.POLICE_STATION]:
            allowed.discard(Card.ARREST_FAMILY)
        if phase == 1 and not player_state.assistant_locations:
            allowed.discard(Card.RETURN_ASSISTANT)
        if phase == 3:
            tile = gs.location_map[player_state.location] if tile is None else tile
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
    def determine_card(cls, card_action: str, gs: GameState, tile: typing.Optional[Tile] = None) -> Card:
        subtokens = action_subtokens(card_action)
        player_state = gs.player_states[gs.turn_state.current_player]
        if subtokens[0].upper() == 'CARD':
            cards: typing.Set[Card] = {k for k, v in player_state.hand.items() if v > 0}
        else:
            pre, card_desc = subtokens[0].split('-')
            assert pre.upper() == 'CARD'
            cards = load_card(card_desc)
        possible_cards = cards & cls.allowed_cards(gs, tile)
        assert possible_cards, f'{card_action} does not match any currently legal cards'
        assert len(possible_cards) == 1, f'{card_action} matched multiple legal cards: {possible_cards}'
        return possible_cards.pop()

    def load_turn(self, turn: TurnRow) -> typing.Iterator[PlayerAction]:
        # todo: wrap in some assertion about yielding
        if '!' in turn.move:
            return self.load_phases_12(turn.move)
        return itertools.chain(
            self.load_phases_12(turn.move),
            self.load_phase_3(turn.action),
            self.load_choose_reward(turn.rewards),
            self.load_governor(turn.gov),
            self.load_smuggler(turn.smug),
            [YieldTurn()],
        )

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

    def load_phase_3(self, s: str, tile: typing.Optional[Tile] = None) -> typing.Iterator[PlayerAction]:
        actions = phase_subtokens(s)
        player_state = self.gs.player_states[self.gs.turn_state.current_player]
        tile = self.gs.location_map[player_state.location] if tile is None else tile
        tile_state = typing.cast(MarketTileState, self.gs.tile_states[tile])
        for idx, action in enumerate(actions):
            if action == '!':
                yield SkipTileAction()
                return
            if action == '':
                assert tile in self.GENERIC_ACTION_TILES, f'{tile} is not generic'
                yield GenericTileAction()
                continue
            subtokens = action_subtokens(action)
            if action.upper().startswith('CARD'):
                card = self.determine_card(action, self.gs, tile)
                if card in {Card.DOUBLE_PO, Card.DOUBLE_DEALER}:
                    assert len(subtokens) == 1
                    yield DoubleCardAction(card, (GenericTileAction(), GenericTileAction()))
                    continue
                if card is Card.DOUBLE_SULTAN:
                    _, first_cost, second_cost = subtokens
                    yield DoubleCardAction(
                        card,
                        (SultansPalaceAction(load_good_counter(first_cost)),
                         SultansPalaceAction(load_good_counter(second_cost)))
                    )
                    continue
                if card is Card.SELL_ANY:
                    assert len(subtokens) == 3, 'Incorrect number of arguments for sell any goods card'
                    assert tile is Tile.SMALL_MARKET, 'Can only use sell any goods card at small marker'
                    if not 'ALL'.startswith(subtokens[1].upper()):
                        yield SellAnyCardAction(load_market_action(action, player_state, tile_state))
                        continue
                    assert 0 < sum(player_state.cart_contents.values()) <= 5, \
                        f'All is ambiguous with {sum(player_state.cart_contents.values())} goods'
                    yield SellAnyCardAction(MarketAction(player_state.cart_contents.copy(),
                                                         load_good_counter(subtokens[2])))
                    continue
                yield load_all_phase_card_action(card, subtokens[1:])
                continue
            # Just 'Y' could match if we don't require the length of name_subtokens to be 2, which would be an issue
            name_subtokens = tokens(subtokens[0])
            if tokens_match(name_subtokens, ['YELLOW', 'TILE']) and len(name_subtokens) == 2:
                assert len(subtokens) == 2, 'Location required with yellow tile'
                yield YellowTileAction(self.location_transformer.apply(Location(int(subtokens[1]))))
                continue

            if tile is Tile.POLICE_STATION:
                location = Location(int(subtokens[0]))
                dest_tile = self.gs.location_map[self.location_transformer.apply(location)]
                args = ' '.join(subtokens[1:])
                dest_actions = list(self.load_phase_3(args, tile=dest_tile))
                assert len(dest_actions) == 1
                # This is manually type checked in the constructor
                dest_action = typing.cast(
                    typing.Union[PlaceTileAction, GreenTileAction, DoubleCardAction, SellAnyCardAction],
                    dest_actions[0]
                )
                yield PoliceStationAction(location, dest_action)
                continue

            if tile in {Tile.SMALL_MARKET, Tile.LARGE_MARKET}:
                yield load_market_action(action, player_state, tile_state)
                continue

            lookup_table = {
                Tile.GREAT_MOSQUE: load_mosque_action,
                # Post office is always generic or card
                Tile.FABRIC_WAREHOUSE: load_warehouse_action,
                Tile.SMALL_MOSQUE: load_mosque_action,
                Tile.FRUIT_WAREHOUSE: load_warehouse_action,
                # Police station is special, above
                # Fountain is always generic
                Tile.SPICE_WAREHOUSE: load_warehouse_action,
                Tile.BLACK_MARKET: load_black_market_action,
                Tile.CARAVANSARY: load_caravansary_action,
                Tile.TEA_HOUSE: load_tea_house_action,
                Tile.SULTANS_PALACE: load_sultans_palace_action,
                # Wainwright is always generic
                # Gemstone dealer is always generic
            }
            yield lookup_table[tile](action)

    def load_choose_reward(self, s: str) -> typing.Iterator[PlayerAction]:
        actions = phase_subtokens(s)
        for idx, action in enumerate(actions):
            if not action:
                assert idx == len(actions) - 1
                break
            subtokens = action_subtokens(action)
            if action.upper().startswith('CARD'):
                card = self.determine_card(action, self.gs)
                yield load_all_phase_card_action(card, subtokens[1:])
                continue
            # Just 'Y' could match if we don't require the length of name_subtokens to be 2, which would be an issue
            name_subtokens = tokens(subtokens[0])
            if tokens_match(name_subtokens, ['YELLOW', 'TILE']) and len(name_subtokens) == 2:
                assert len(subtokens) == 2, 'Location required with yellow tile'
                yield YellowTileAction(self.location_transformer.apply(Location(int(subtokens[1]))))
                continue
            for subtoken in subtokens:
                if subtoken in {'3', '6', '9', '12'}:
                    for _ in range(int(subtoken) // 3):
                        yield ChooseReward(ChooseReward.LIRA)
                    continue
                card = load_exact_card(subtoken)
                yield ChooseReward(card)

    def load_governor(self, s: str) -> typing.Iterator[PlayerAction]:
        actions = phase_subtokens(s)
        for idx, action in enumerate(actions):
            if not action:
                assert idx == len(actions) - 1
                break
            subtokens = action_subtokens(action)
            if action.upper().startswith('CARD'):
                card = self.determine_card(action, self.gs)
                yield load_all_phase_card_action(card, subtokens[1:])
                continue
            # Just 'Y' could match if we don't require the length of name_subtokens to be 2, which would be an issue
            name_subtokens = tokens(subtokens[0])
            if tokens_match(name_subtokens, ['YELLOW', 'TILE']) and len(name_subtokens) == 2:
                assert len(subtokens) == 2, 'Location required with yellow tile'
                yield YellowTileAction(self.location_transformer.apply(Location(int(subtokens[1]))))
                continue
            gain, cost, roll = subtokens
            yield EncounterGovernor(
                load_exact_card(gain),
                Pay() if cost == '-2' else load_exact_card(cost),
                load_roll(roll)
            )

    def load_smuggler(self, s: str):
        actions = phase_subtokens(s)
        for idx, action in enumerate(actions):
            if not action:
                assert idx == len(actions) - 1
                break
            subtokens = action_subtokens(action)
            if action.upper().startswith('CARD'):
                card = self.determine_card(action, self.gs)
                yield load_all_phase_card_action(card, subtokens[1:])
                continue
            # Just 'Y' could match if we don't require the length of name_subtokens to be 2, which would be an issue
            name_subtokens = tokens(subtokens[0])
            if tokens_match(name_subtokens, ['YELLOW', 'TILE']) and len(name_subtokens) == 2:
                assert len(subtokens) == 2, 'Location required with yellow tile'
                yield YellowTileAction(self.location_transformer.apply(Location(int(subtokens[1]))))
                continue
            gain, cost, roll = subtokens
            yield EncounterSmuggler(
                load_good(gain),
                Pay() if cost == '-2' else load_good(cost),
                load_roll(roll)
            )
