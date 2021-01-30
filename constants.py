from enum import Enum
from typing import NewType, Literal, Tuple, Final, Dict

Location = NewType('Location', int)


class Card(Enum):
    ONE_GOOD = 'Take 1 good'
    FIVE_LIRA = 'Take 5 Lira'
    EXTRA_MOVE = 'Move 3-4 instead of 1-2'
    NO_MOVE = 'Stay put instead of moving'
    RETURN_ASSISTANT = 'Move 1 assistant back'
    ARREST_FAMILY = 'Send your family member to the police station, reward'
    SELL_ANY = 'Sell any goods at the small market'
    DOUBLE_SULTAN = 'Carry out the sultan\'s palace action twice'
    DOUBLE_PO = 'Carry out the post office action twice'
    DOUBLE_DEALER = 'Carry out the gemstone dealer action twice'


_Roll = Literal[1, 2, 3, 4, 5, 6]
Roll = Tuple[_Roll, _Roll]


class Good(Enum):
    RED = 'fabric'
    BLUE = 'jewelry'
    GREEN = 'spice'
    YELLOW = 'fruit'


class Player(Enum):
    RED = 'Red'
    GREEN = 'Green'
    BLUE = 'Blue'
    YELLOW = 'Yellow'
    WHITE = 'White'


class Tile(Enum):
    GREAT_MOSQUE = 'Great Mosque'
    POST_OFFICE = 'Post Office'
    FABRIC_WAREHOUSE = 'Fabric Warehouse'
    SMALL_MOSQUE = 'Small Mosque'
    FRUIT_WAREHOUSE = 'Fruit Warehouse'
    POLICE_STATION = 'Police Station'
    FOUNTAIN = 'Fountain'
    SPICE_WAREHOUSE = 'Spice Warehouse'
    BLACK_MARKET = 'Black Market'
    CARAVANSARY = 'Caravansary'
    SMALL_MARKET = 'Small Market'
    TEA_HOUSE = 'Tea House'
    SULTANS_PALACE = 'Sultan\'s Palace'
    LARGE_MARKET = 'Large Market'
    WAINWRIGHT = 'Wainwright'
    GEMSTONE_DEALER = 'Gemstone Dealer'


DEFAULT_LOCATIONS: Final[Dict[Location, Tile]] = {Location(i): t for i, t in enumerate(Tile, 1)}
ROLL_LOCATIONS: Final[Dict[Location, Tile]] = {
    Location(1): Tile.WAINWRIGHT,
    Location(2): Tile.FABRIC_WAREHOUSE,
    Location(3): Tile.SPICE_WAREHOUSE,
    Location(4): Tile.FRUIT_WAREHOUSE,
    Location(5): Tile.POST_OFFICE,
    Location(6): Tile.CARAVANSARY,
    Location(7): Tile.FOUNTAIN,
    Location(8): Tile.BLACK_MARKET,
    Location(9): Tile.TEA_HOUSE,
    Location(10): Tile.LARGE_MARKET,
    Location(11): Tile.SMALL_MARKET,
    Location(12): Tile.POLICE_STATION,
    Location(13): Tile.SULTANS_PALACE,
    Location(14): Tile.SMALL_MOSQUE,
    Location(15): Tile.GREAT_MOSQUE,
    Location(16): Tile.GEMSTONE_DEALER,
}
