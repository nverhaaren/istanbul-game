import typing
from collections import Counter, defaultdict

from ..constants import Player, Location, Good, Tile, DEFAULT_LOCATIONS, Card
from ..game import GameState
from ..lib.utils import ImmutableInvertibleMapping
from .core import load_player, load_good_counter, load_exact_card, load_tile
from .location_transformer import LocationTransformer
from .phases import PhaseLoader


class SetupRow(object):
    def __init__(self, head: str, values: typing.Sequence[str]):
        self.head: typing.Final = '_'.join(head.upper().split())
        self.values: typing.Final = values


class SetupLoader(object):
    def __init__(self) -> None:
        self.players: typing.Sequence[Player] = ()
        self.tiles: typing.List[str] = []
        self.small_demand: typing.Counter[Good] = Counter()
        self.large_demand: typing.Counter[Good] = Counter()
        self.governor_location: typing.Optional[Location] = None
        self.smuggler_location: typing.Optional[Location] = None
        self.cards: typing.Sequence[Card] = ()

        self._location_spec: typing.Optional[str] = None

    @classmethod
    def load_tiles(cls, tiles: typing.Sequence[str]) -> ImmutableInvertibleMapping[Location, Tile]:
        tile_locations: typing.Dict[str, Location] = {s: Location(idx) for idx, s in enumerate(tiles, 1)}
        tile_possibilities: typing.Dict[str, typing.Set[Tile]] = {s: load_tile(s) for s in tiles}

        final_mapping: typing.Dict[Location, Tile] = {}
        possibility_categories: typing.MutableMapping[int, typing.Set[str]] = defaultdict(set)
        for s, possibilities in tile_possibilities.items():
            assert possibilities, f'Could not determine any tile matching "{s}"'
            possibility_categories[len(possibilities)].add(s)

        while len(final_mapping) < 16:
            solved = possibility_categories[1]
            assert len(solved) > 0, \
                f'Unable to solve tile mapping: {[k for k, v in tile_locations.items() if v not in final_mapping]}'
            for s in solved:
                assert len(tile_possibilities[s]) == 1
                possibility_categories[1].remove(s)
                t: Tile = tile_possibilities[s].pop()
                final_mapping[tile_locations[s]] = t
                for spec, possibilities in tile_possibilities.items():
                    if t in possibilities:
                        possibility_categories[len(possibilities)].remove(spec)
                        possibility_categories[len(possibilities)].add(spec)
                        tile_possibilities[spec].remove(t)

        return ImmutableInvertibleMapping(final_mapping)

    def load_row(self, setup_row: SetupRow) -> None:
        if setup_row.head == 'NAMES':
            return
        if setup_row.head == 'ORDER':
            self.players = tuple(map(load_player, setup_row.values))
            return
        if setup_row.head == 'GOVERNOR':
            assert len(setup_row.values) == 1
            self.governor_location = Location(int(setup_row.values[0]))
            return
        if setup_row.head == 'SMUGGLER':
            assert len(setup_row.values) == 1
            self.smuggler_location = Location(int(setup_row.values[0]))
            return
        if setup_row.head == 'SMALL_MARKET':
            assert len(setup_row.values) == 1
            self.small_demand = load_good_counter(setup_row.values[0])
            return
        if setup_row.head == 'LARGE_MARKET':
            assert len(setup_row.values) == 1
            self.large_demand = load_good_counter(setup_row.values[0])
            return
        if setup_row.head == 'CARDS':
            self.cards = tuple(load_exact_card(v.replace(' ', '')) for v in setup_row.values)
            return
        if setup_row.head == 'LOCATION_SPEC':
            assert len(setup_row.values) == 1
            self._location_spec = setup_row.values[0].title()
            return
        if setup_row.head == 'TILE_LOCATIONS':
            assert len(setup_row.values) == 4
            assert len(self.tiles) < 13
            # Remove apostrophes from tile names
            self.tiles += [s.replace("'", "") for s in setup_row.values]
            return

    def create_phase_loader(self) -> PhaseLoader:
        if not self.tiles:
            location_map = DEFAULT_LOCATIONS
        else:
            location_map = self.load_tiles(self.tiles)

        assert self._location_spec in {LocationTransformer.ROLL_SPEC, LocationTransformer.DIRECT_SPEC}, \
            f'Unknown location spec {self._location_spec}'
        location_transformer = LocationTransformer(
            typing.cast(typing.Literal['Roll', 'Direct'], self._location_spec),
            location_map
        )

        assert 0 < len(self.players) == len(self.cards) <= 5, 'Improper number of players/cards'
        assert len(set(self.players)) == len(self.players), 'Players not unique'
        player_hands = dict(zip(self.players, self.cards))

        assert self.governor_location is not None and self.smuggler_location is not None, \
            'Missing location of governor or smuggler'
        governor_location = location_transformer.apply(self.governor_location)
        smuggler_location = location_transformer.apply(self.smuggler_location)

        assert sum(self.small_demand.values()) == sum(self.large_demand.values()) == 5, 'Missing large or small demand'

        game_state = GameState(
            self.players,
            location_map,
            self.small_demand,
            self.large_demand,
            governor_location,
            smuggler_location,
            player_hands,
        )

        return PhaseLoader(game_state, location_transformer)
