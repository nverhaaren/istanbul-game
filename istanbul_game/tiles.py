import collections
from typing import Set, Dict, Tuple, List, Optional, Counter

from .constants import Player, Good, Card, Tile


class TileState(object):
    def __init__(self):
        self.governor: bool = False
        self.smuggler: bool = False
        self.assistants: Set[Player] = set()
        self.family_members: Set[Player] = set()
        self.players: Set[Player] = set()


class GenericTileState(TileState):
    pass


class MosqueTileState(TileState):
    def __init__(self, goods: Set[Good]):
        super(MosqueTileState, self).__init__()
        self.available_tiles: Dict[Good, int] = {good: 2 for good in goods}

    def take_action(self, good: Good):
        assert good in self.available_tiles, 'mosque does not have {} tile'.format(good)
        if self.available_tiles[good] < 5:
            self.available_tiles[good] += 1
        else:
            del self.available_tiles[good]


class PostOfficeTileState(TileState):
    MAIL = (
        (Good.RED, Good.GREEN),
        (2, 1),
        (Good.BLUE, Good.YELLOW),
        (2, 1),
    )

    def __init__(self):
        super(PostOfficeTileState, self).__init__()
        self.position: int = 0

    def available(self) -> Tuple[Set[Good], int]:
        goods: Set[Good] = set()
        lira = 0
        for i in range(len(self.MAIL)):
            idx = 0 if self.position > i else 1
            if i % 2 == 0:
                good = self.MAIL[i][idx]
                assert isinstance(good, Good)
                goods.add(good)
            else:
                lira_value = self.MAIL[i][idx]
                assert isinstance(lira_value, int)
                lira += lira_value
        return goods, lira

    def take_action(self) -> Tuple[Set[Good], int]:
        goods, lira = self.available()
        self.position = (self.position + 1) % 5
        return goods, lira


class CaravansaryTileState(TileState):
    def __init__(self):
        super(CaravansaryTileState, self).__init__()
        self.discard_pile: List[Card] = []
        self.awaiting_discard: bool = False

    def discard_onto(self, card: Card):
        self.discard_pile.append(card)
        self.awaiting_discard = False

    def take_action(self, count: int) -> List[Card]:
        assert not self.awaiting_discard
        assert 0 <= count <= 2
        self.awaiting_discard = True
        if count == 0:
            return []
        assert len(self.discard_pile) >= count
        result = self.discard_pile[-count:]
        self.discard_pile = self.discard_pile[:-count]
        return result


class WainwrightTileState(TileState):
    def __init__(self, extensions: int):
        super(WainwrightTileState, self).__init__()
        self.extensions = extensions

    def take_action(self):
        self.extensions -= 1
        assert self.extensions >= 0


class MarketTileState(TileState):
    def __init__(self, one_cost: int):
        super(MarketTileState, self).__init__()
        self.one_cost: int = one_cost

        self.expecting_demand: bool = True
        self.demand: Optional[Counter[Good]] = None

    def set_demand(self, demand: Counter[Good]):
        assert sum(demand.values()) == 5
        self.demand = demand
        self.expecting_demand = False

    def take_action(self, payment: Counter[Good]) -> int:
        assert not self.expecting_demand
        assert self.demand is not None
        for k in payment:
            assert payment[k] <= self.demand[k]
        self.expecting_demand = True
        count = sum(payment.values())
        return sum(range(self.one_cost, self.one_cost + count))


class SultansPalaceTileState(TileState):
    GOOD_CYCLE = (
        Good.BLUE,
        Good.RED,
        Good.GREEN,
        Good.YELLOW,
        None,  # using this to mean any
    )

    def __init__(self, init_advanced: bool):
        super(SultansPalaceTileState, self).__init__()
        self.required_count: int = 4 if not init_advanced else 5

    def required(self) -> Optional[Counter[Optional[Good]]]:
        assert self.required_count >= 4
        if self.required_count > 10:
            return None  # indicating no more rubies available

        result: Counter[Optional[Good]] = collections.Counter({None: 0})
        for i in range(self.required_count):
            result[self.GOOD_CYCLE[i % 5]] += 1
        return result

    def take_action(self, payment: Counter[Good]):
        required = self.required()
        assert required is not None
        payment = payment.copy()
        assert sum(required.values()) == sum(payment.values())
        for g in payment:
            assert payment[g] >= required[g]
        self.required_count += 1


class GemstoneDealerTileState(TileState):
    def __init__(self, initial_cost: int):
        super(GemstoneDealerTileState, self).__init__()
        self.cost: Optional[int] = initial_cost

    def take_action(self):
        assert self.cost is not None
        self.cost += 1
        if self.cost > 24:
            self.cost = None


def initial_tile_state(tile: Tile, player_count: int):
    assert 2 <= player_count <= 5
    if tile in {Tile.FABRIC_WAREHOUSE, Tile.FRUIT_WAREHOUSE, Tile.POLICE_STATION, Tile.FOUNTAIN, Tile.SPICE_WAREHOUSE,
                Tile.BLACK_MARKET, Tile.TEA_HOUSE}:
        return GenericTileState()
    simple_mapping = {
        Tile.POST_OFFICE: PostOfficeTileState,
        Tile.CARAVANSARY: CaravansaryTileState,
    }
    if tile in simple_mapping:
        return simple_mapping[tile]()

    if tile is Tile.GREAT_MOSQUE:
        return MosqueTileState({Good.BLUE, Good.YELLOW})
    if tile is Tile.SMALL_MOSQUE:
        return MosqueTileState({Good.RED, Good.GREEN})
    if tile is Tile.SMALL_MARKET:
        return MarketTileState(2)
    if tile is Tile.LARGE_MARKET:
        return MarketTileState(3)
    if tile is Tile.SULTANS_PALACE:
        return SultansPalaceTileState(player_count < 4)
    if tile is Tile.WAINWRIGHT:
        return WainwrightTileState(3 * player_count)
    if tile is Tile.GEMSTONE_DEALER:
        if player_count == 2:
            initial_cost = 15
        elif player_count == 3:
            initial_cost = 14
        else:
            initial_cost = 12
        return GemstoneDealerTileState(initial_cost)
