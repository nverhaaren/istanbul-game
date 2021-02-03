import typing
from collections import Counter

from constants import Good, Card
from lib.utils import ImmutableInvertibleMapping, ImmutableMapping

good_codes: typing.Mapping[str, Good] = ImmutableInvertibleMapping({g.name[0]: g for g in Good})


def load_good(s: str) -> Good:
    result = good_codes[s[0].upper()]
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
            result[good] = int(s[explicit_count_start:idx]) if explicit_count_start else 1
            explicit_count_start = None
            idx += 1
            continue

        if explicit_count_start is None:
            explicit_count_start = idx
        idx += 1
    assert not explicit_count_start
    return result


card_codes: typing.Mapping[str, Card] = ImmutableMapping({
    'OneGood': Card.ONE_GOOD,
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
