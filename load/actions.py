import typing

from actions import MosqueAction, GenericTileAction, GreenTileAction, RedTileAction, BlackMarketAction, TeaHouseAction, \
    SultansPalaceAction
from constants import Roll
from load.core import load_good, tokens, tokens_match, load_roll, load_good_counter


def load_mosque_action(s: str) -> MosqueAction:
    good = load_good(s)
    return MosqueAction(good)


def load_generic_action(s: str) -> GenericTileAction:
    assert not s, 'Action [{}] is not generic'.format(s)
    return GenericTileAction()


def load_warehouse_action(s: str) -> typing.Union[GenericTileAction, GreenTileAction]:
    if not s:
        return GenericTileAction()
    gt, good = s.split(' ')
    assert tokens_match(tokens(gt), ['GREEN', 'TILE']), '{} is not GreenTile'.format(gt)
    return GreenTileAction(load_good(good))


def load_possible_red_tile_action(s: str) -> typing.Union[Roll, RedTileAction]:
    subtokens = s.split(' ')
    if len(subtokens) == 1:
        return load_roll(subtokens[0])

    first = subtokens[0]
    assert tokens_match(tokens(first), ['RED', 'TILE']), '{} is not RedTile'.format(first)
    assert len(subtokens) == 4, 'RedTile requires 3 inputs, got'.format(len(subtokens) - 1)
    initial_roll = load_roll(subtokens[1])
    final_roll = load_roll(subtokens[3])
    method = {'F': RedTileAction.TO_FOUR, 'R': RedTileAction.REROLL, '4': RedTileAction.TO_FOUR}[subtokens[2]]
    return RedTileAction(initial_roll, final_roll, method)


def load_black_market_action(s: str) -> BlackMarketAction:
    good, rest = s.split(' ', maxsplit=1)
    return BlackMarketAction(load_good(good), load_possible_red_tile_action(rest))


def load_tea_house_action(s: str) -> TeaHouseAction:
    call, rest = s.split(' ', maxsplit=1)
    return TeaHouseAction(int(call), load_possible_red_tile_action(rest))


def load_sultans_palace_action(s: str) -> SultansPalaceAction:
    return SultansPalaceAction(load_good_counter(s))
