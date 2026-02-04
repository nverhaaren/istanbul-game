import itertools
import typing
from collections import Counter
from functools import partial

from ..constants import Good, Card, Roll, Player, Tile
from ..lib.utils import ImmutableInvertibleMapping, ImmutableMapping

good_codes: typing.Mapping[str, Good] = ImmutableInvertibleMapping({g.name[0]: g for g in Good})
player_codes: typing.Mapping[str, Player] = ImmutableInvertibleMapping({p.name[0]: p for p in Player})


def load_good(s: str) -> Good:
    result = good_codes[s[0].upper()]
    assert result.name.startswith(s.upper())
    return result


def load_player(s: str) -> Player:
    result = player_codes[s[0].upper()]
    assert result.name.startswith(s.upper())
    return result


def load_good_counter(s: str) -> typing.Counter[Good]:
    result = Counter()
    is_digit = [c.isdigit() for c in s]
    idx = 0
    explicit_count_start: typing.Optional[int] = None
    while idx < len(s):
        if not is_digit[idx]:
            good = load_good(s[idx])
            assert good not in result
            result[good] = int(s[explicit_count_start:idx]) if explicit_count_start is not None else 1
            explicit_count_start = None
            idx += 1
            continue

        if explicit_count_start is None:
            explicit_count_start = idx
        idx += 1
    assert not explicit_count_start
    return result


def action_subtokens(s: str) -> typing.List[str]:
    return list(filter(None, s.split(' ')))


def phase_subtokens(s: str) -> typing.List[str]:
    return [t.strip() for t in s.split(';')]


def tokens(s: str) -> typing.List[str]:
    result = [[s[0]]]
    last = s[0]
    for c in itertools.islice(s, 1, len(s)):
        if c.isupper() or (c.isdigit() and not last.isdigit()):
            result.append([c])
        else:
            result[-1].append(c)
        last = c

    return [''.join(cs).upper() for cs in result]


def tokens_match(ts: typing.Iterable[str], canonical: typing.Iterable[str]) -> bool:
    if not ts:
        return True
    iter_ts = iter(ts)
    current = next(iter_ts)
    for token in canonical:
        if token.startswith(current):
            try:
                current = next(iter_ts)
            except StopIteration:
                return True
    return False


card_codes: typing.Mapping[str, Card] = ImmutableMapping({
    'OneGood': Card.ONE_GOOD,
    '1Good': Card.ONE_GOOD,
    '5Lira': Card.FIVE_LIRA,
    'FiveLira': Card.FIVE_LIRA,
    'ExtraMove': Card.EXTRA_MOVE,
    'Move34': Card.EXTRA_MOVE,
    'NoMove': Card.NO_MOVE,
    'Move0': Card.NO_MOVE,
    'StayPut': Card.NO_MOVE,
    'ReturnAssistant': Card.RETURN_ASSISTANT,
    'ArrestFamily': Card.ARREST_FAMILY,
    'SellAny': Card.SELL_ANY,
    'SmallMarket': Card.SELL_ANY,
    '2xSultan': Card.DOUBLE_SULTAN,
    'DoubleSultan': Card.DOUBLE_SULTAN,
    '2xPostOffice': Card.DOUBLE_PO,
    'DoublePostOffice': Card.DOUBLE_PO,
    '2xGemstoneDealer': Card.DOUBLE_DEALER,
    'DoubleGemstoneDealer': Card.DOUBLE_DEALER,
})

card_tokens: typing.Mapping[typing.Tuple[str, ...], Card] = {tuple(tokens(k)): v for k, v in card_codes.items()}
tile_tokens: typing.Mapping[typing.Tuple[str, ...], Tile] = {tuple(t.name.split('_')): t for t in Tile}


T = typing.TypeVar('T')


def _load(mapping: typing.Mapping[typing.Tuple[str, ...], T], s: str) -> typing.Set[T]:
    ts = tokens(s)
    result: typing.Set[T] = set()
    for canon_ts, v in mapping.items():
        if v in result:
            continue
        if tokens_match(ts, canon_ts):
            result.add(v)

    return result


load_card: typing.Callable[[str], typing.Set[Card]] = partial(_load, card_tokens)
load_tile: typing.Callable[[str], typing.Set[Tile]] = partial(_load, tile_tokens)


def load_exact_card(s: str) -> Card:
    cards = load_card(s)
    assert cards, f'"{s}" did not match any card'
    assert len(cards) == 1, f'Ambiguous card spec "{s}"'
    return cards.pop()


def load_roll(s: str) -> Roll:
    first, second = s.split('+')
    return int(first), int(second)
