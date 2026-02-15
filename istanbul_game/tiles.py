import collections
from collections import Counter
from typing import NamedTuple

from .constants import Card, Good, Player, Tile
from .lib.utils import OrderedSet


class MailSlot(NamedTuple):
    """A slot in the post office mail grid."""

    good_early: Good  # Good received when position has passed this slot
    good_late: Good  # Good received when position hasn't passed this slot
    lira_early: int  # Lira received when position has passed this slot
    lira_late: int  # Lira received when position hasn't passed this slot


class TileState:
    def __init__(self) -> None:
        self.governor: bool = False
        self.smuggler: bool = False
        self.assistants: OrderedSet[Player] = OrderedSet()
        self.family_members: OrderedSet[Player] = OrderedSet()
        self.players: OrderedSet[Player] = OrderedSet()


class GenericTileState(TileState):
    pass


class MosqueTileState(TileState):
    def __init__(self, goods: set[Good]):
        super().__init__()
        self.available_tiles: dict[Good, int] = {good: 2 for good in goods}

    def take_action(self, good: Good) -> None:
        assert good in self.available_tiles, f"mosque does not have {good} tile"
        if self.available_tiles[good] < 5:
            self.available_tiles[good] += 1
        else:
            del self.available_tiles[good]


class PostOfficeTileState(TileState):
    MAIL_SLOTS: tuple[MailSlot, MailSlot] = (
        MailSlot(Good.RED, Good.GREEN, 2, 1),
        MailSlot(Good.BLUE, Good.YELLOW, 2, 1),
    )

    def __init__(self) -> None:
        super().__init__()
        self.position: int = 0

    def available(self) -> tuple[set[Good], int]:
        goods: set[Good] = set()
        lira = 0
        for i, slot in enumerate(self.MAIL_SLOTS):
            # Position > slot index means we've passed it, use "early" values
            if self.position > i:
                goods.add(slot.good_early)
                lira += slot.lira_early
            else:
                goods.add(slot.good_late)
                lira += slot.lira_late
        return goods, lira

    def take_action(self) -> tuple[set[Good], int]:
        goods, lira = self.available()
        self.position = (self.position + 1) % 5
        return goods, lira


class CaravansaryTileState(TileState):
    def __init__(self) -> None:
        super().__init__()
        self.discard_pile: list[Card] = []
        self.awaiting_discard: bool = False

    def discard_onto(self, card: Card) -> None:
        self.discard_pile.append(card)
        self.awaiting_discard = False

    def take_action(self, count: int) -> list[Card]:
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
        super().__init__()
        self.extensions = extensions

    def take_action(self) -> None:
        self.extensions -= 1
        assert self.extensions >= 0


class MarketTileState(TileState):
    def __init__(self, one_cost: int):
        super().__init__()
        self.one_cost: int = one_cost

        self.expecting_demand: bool = True
        self.demand: Counter[Good] | None = None

    def set_demand(self, demand: Counter[Good]) -> None:
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
        super().__init__()
        self.required_count: int = 4 if not init_advanced else 5

    def required(self) -> Counter[Good | None] | None:
        assert self.required_count >= 4
        if self.required_count > 10:
            return None  # indicating no more rubies available

        result: Counter[Good | None] = collections.Counter({None: 0})
        for i in range(self.required_count):
            result[self.GOOD_CYCLE[i % 5]] += 1
        return result

    def take_action(self, payment: Counter[Good]) -> None:
        required = self.required()
        assert required is not None
        payment = payment.copy()
        assert sum(required.values()) == sum(payment.values())
        for g in payment:
            assert payment[g] >= required[g]
        self.required_count += 1


class GemstoneDealerTileState(TileState):
    def __init__(self, initial_cost: int):
        super().__init__()
        self.cost: int | None = initial_cost

    def take_action(self) -> None:
        assert self.cost is not None
        self.cost += 1
        if self.cost > 24:
            self.cost = None


def initial_tile_state(tile: Tile, player_count: int) -> TileState:
    assert 2 <= player_count <= 5
    if tile in {
        Tile.FABRIC_WAREHOUSE,
        Tile.FRUIT_WAREHOUSE,
        Tile.POLICE_STATION,
        Tile.FOUNTAIN,
        Tile.SPICE_WAREHOUSE,
        Tile.BLACK_MARKET,
        Tile.TEA_HOUSE,
    }:
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

    raise ValueError(f"Unknown tile: {tile}")
