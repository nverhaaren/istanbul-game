import typing

from ..constants import ROLL_LOCATIONS, Location, Tile
from ..lib.utils import ImmutableInvertibleMapping


class LocationTransformer:
    ROLL_SPEC: typing.Final = "Roll"
    DIRECT_SPEC: typing.Final = "Direct"

    def __init__(self, spec: typing.Literal["Roll", "Direct"], locations: ImmutableInvertibleMapping[Location, Tile]):
        self.spec: typing.Final = {
            self.ROLL_SPEC: self.ROLL_SPEC,
            self.DIRECT_SPEC: self.DIRECT_SPEC,
        }[spec]
        self.locations: typing.Final = locations

    def apply(self, location: Location) -> Location:
        if self.spec is self.DIRECT_SPEC:
            return location
        assert self.spec is self.ROLL_SPEC, f"Unknown spec {self.spec}"
        tile: Tile = ROLL_LOCATIONS[location]
        return self.locations.inverse[tile]

    def unapply(self, location: Location) -> Location:
        if self.spec is self.DIRECT_SPEC:
            return location
        assert self.spec is self.ROLL_SPEC, f"Unknown spec {self.spec}"
        tile: Tile = self.locations[location]
        return ROLL_LOCATIONS.inverse[tile]
