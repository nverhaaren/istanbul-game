import collections
from typing import Final, Counter, Set

from .constants import Player, Card, Location, Good


class PlayerState(object):
    def __init__(self, color: Player, hand: Card, lira: int, fountain: Location, police_station: Location):
        self.color: Final[Player] = color
        self.hand: Counter[Card] = collections.Counter({hand: 1})
        self.lira: int = lira

        self.rubies: int = 0
        self.cart_max: int = 2
        self.cart_contents: Counter[Good] = collections.Counter({g: 0 for g in Good})
        self.stack_size: int = 4
        self.tiles: Set[Good] = set()

        self.location: Location = fountain
        self.assistant_locations: Set[Location] = set()
        self.family_location: Location = police_station
