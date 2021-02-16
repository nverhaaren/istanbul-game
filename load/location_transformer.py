import typing

from constants import Location, Tile, ROLL_LOCATIONS
from lib.utils import ImmutableInvertibleMapping


class LocationTransformer(object):
    ROLL_SPEC = 'Roll'
    DIRECT_SPEC = 'Direct'

    def __init__(self, spec: typing.Union[ROLL_SPEC, DIRECT_SPEC], locations: ImmutableInvertibleMapping):
        self.spec: typing.Final = spec
        self.locations: typing.Final = locations

    def apply(self, location: Location) -> Location:
        if self.spec is self.DIRECT_SPEC:
            return location
        assert self.spec is self.ROLL_SPEC, f'Unknown spec {self.spec}'
        tile: Tile = ROLL_LOCATIONS[location]
        return self.locations.inverse[tile]

    def unapply(self, location: Location) -> Location:
        if self.spec is self.DIRECT_SPEC:
            return location
        assert self.spec is self.ROLL_SPEC, f'Unknown spec {self.spec}'
        tile: Tile = self.locations[location]
        return ROLL_LOCATIONS.inverse[tile]
