import typing
from collections import Counter

from ..actions import MosqueAction, GenericTileAction, GreenTileAction, RedTileAction, BlackMarketAction, TeaHouseAction, \
    SultansPalaceAction, CaravansaryAction, MarketAction, PlayerAction, FiveLiraCardAction, OneGoodCardAction, \
    ArrestFamilyCardAction, ChooseReward
from ..constants import Roll, Good, Card
from .core import load_good, tokens, tokens_match, load_roll, load_good_counter, load_exact_card, action_subtokens
from ..player import PlayerState
from ..tiles import MarketTileState


def load_mosque_action(s: str) -> MosqueAction:
    good = load_good(s)
    return MosqueAction(good)


def load_generic_action(s: str) -> GenericTileAction:
    assert not s, 'Action [{}] is not generic'.format(s)
    return GenericTileAction()


def load_warehouse_action(s: str) -> typing.Union[GenericTileAction, GreenTileAction]:
    if not s:
        return GenericTileAction()
    gt, good = action_subtokens(s)
    assert tokens_match(tokens(gt), ['GREEN', 'TILE']), '{} is not GreenTile'.format(gt)
    return GreenTileAction(load_good(good))


def load_possible_red_tile_action(s: str) -> typing.Union[Roll, RedTileAction]:
    subtokens = action_subtokens(s)
    if len(subtokens) == 1:
        return load_roll(subtokens[0])

    first = subtokens[0]
    assert tokens_match(tokens(first), ['RED', 'TILE']), '{} is not RedTile'.format(first)
    assert len(subtokens) == 4, 'RedTile requires 3 inputs, got {}'.format(len(subtokens) - 1)
    initial_roll = load_roll(subtokens[1])
    final_roll = load_roll(subtokens[3])
    method_map: dict[str, typing.Literal['change a die to four', 'reroll']] = {
        'F': 'change a die to four', 'R': 'reroll', '4': 'change a die to four'
    }
    return RedTileAction(initial_roll, final_roll, method_map[subtokens[2]])


def load_black_market_action(s: str) -> BlackMarketAction:
    good_str, rest = s.split(' ', maxsplit=1)
    rest = rest.strip()
    good = load_good(good_str)
    assert good in {Good.RED, Good.YELLOW, Good.GREEN}, f'Invalid black market good: {good}'
    return BlackMarketAction(typing.cast(typing.Literal[Good.RED, Good.YELLOW, Good.GREEN], good), load_possible_red_tile_action(rest))


def load_caravansary_action(s: str) -> CaravansaryAction:
    subtokens = action_subtokens(s)
    assert len(subtokens) == 3, f'Expected 3 subtokens for caravansary action; got {s}'

    first, second = subtokens[:2]
    _Gain = typing.Union[Card, typing.Literal['top of discard pile']]
    first_gain: _Gain
    second_gain: _Gain

    if 'DISCARD'.startswith(first.upper()):
        first_gain = CaravansaryAction.DISCARD
    else:
        first_gain = load_exact_card(first)

    if 'DISCARD'.startswith(second.upper()):
        second_gain = CaravansaryAction.DISCARD
    else:
        second_gain = load_exact_card(second)

    cost = load_exact_card(subtokens[2])

    return CaravansaryAction((first_gain, second_gain), cost)


def load_market_action(s: str, ps: PlayerState, ts: MarketTileState) -> MarketAction:
    subtokens = action_subtokens(s)
    assert len(subtokens) == 2, f'Expected 2 subtokens for market action; got {s}'
    assert ts.demand is not None, 'No demand currently set on tile'

    goods_str, new_demand_str = subtokens
    goods_counter: typing.Counter[Good]
    if 'ALL'.startswith(goods_str.upper()):
        max_demand: typing.Counter[Good] = Counter()
        for good in Good:
            max_demand[good] = min(ps.cart_contents[good], ts.demand[good])
        assert 0 < sum(max_demand.values()) <= 5, f'All would imply {sum(max_demand.values())} goods'
        goods_counter = max_demand
    else:
        goods_counter = load_good_counter(goods_str)

    new_demand_counter = load_good_counter(new_demand_str)

    return MarketAction(goods_counter, new_demand_counter)


def load_tea_house_action(s: str) -> TeaHouseAction:
    call, rest = s.split(' ', maxsplit=1)
    rest = rest.strip()
    return TeaHouseAction(int(call), load_possible_red_tile_action(rest))


def load_sultans_palace_action(s: str) -> SultansPalaceAction:
    return SultansPalaceAction(load_good_counter(s))


def load_all_phase_card_action(card: Card, ts: typing.List[str]) -> PlayerAction:
    if card is Card.FIVE_LIRA:
        assert not ts
        return FiveLiraCardAction()

    if card is Card.ONE_GOOD:
        assert len(ts) == 1
        return OneGoodCardAction(load_good(ts[0]))

    if card is Card.ARREST_FAMILY:
        assert len(ts) == 1
        if ts[0] == '3':
            return ArrestFamilyCardAction(ChooseReward(ChooseReward.LIRA))
        return ArrestFamilyCardAction(ChooseReward(load_exact_card(ts[0])))

    raise Exception(f'Card {card} is not always allowed')
