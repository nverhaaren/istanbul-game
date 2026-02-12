from typing import Final, Union, Literal, Tuple, Counter, Iterable

from .constants import Location, Card, Good, Roll


class PlayerAction(object):
    pass


class YieldTurn(PlayerAction):
    pass


class Move(PlayerAction):
    def __init__(self, tile: Location, skip_assistant: bool):
        self.tile: Final = tile
        self.skip_assistant: Final = skip_assistant


class Pay(PlayerAction):
    pass


class ChooseReward(PlayerAction):
    LIRA = 'Lira'
    _RewardChoice = Union[Card, Literal['Lira']]

    def __init__(self, choice: _RewardChoice):
        self.choice: Final = choice


class EncounterSmuggler(PlayerAction):
    def __init__(self, gain: Good, cost: Union[Good, Pay], roll: Roll):
        self.gain: Final = gain
        self.cost: Final = cost
        self.roll: Final = roll


class EncounterGovernor(PlayerAction):
    def __init__(self, gain: Card, cost: Union[Card, Pay], roll: Roll):
        self.gain: Final = gain
        self.cost: Final = cost
        self.roll: Final = roll


class SkipTileAction(PlayerAction):
    pass


class PlaceTileAction(PlayerAction):
    pass


class GenericTileAction(PlaceTileAction):
    pass


class GreenTileAction(PlayerAction):
    """
    This represents using the green tile at a warehouse

    It both takes the warehouse action and allows an additional good.
    """
    def __init__(self, good: Good):
        self.good: Final = good


class RedTileAction(PlayerAction):
    TO_FOUR = 'change a die to four'
    REROLL = 'reroll'
    _Method = Literal['change a die to four', 'reroll']

    def __init__(self, initial_roll: Roll, final_roll: Roll, method: _Method):
        self.initial_roll: Final = initial_roll
        self.final_roll: Final = final_roll
        self.method: Final = method

    # validate method here?


class YellowTileAction(PlayerAction):
    def __init__(self, from_tile: Location):
        self.from_tile: Final = from_tile


class CaravansaryAction(PlaceTileAction):
    DISCARD = 'top of discard pile'
    _Gain = Union[Card, Literal['top of discard pile']]

    def __init__(self, gains: Tuple[_Gain, _Gain], cost: Card):
        self.gains: Final = gains
        self.cost: Final = cost


class BlackMarketAction(PlaceTileAction):
    _Choices = Literal[Good.RED, Good.YELLOW, Good.GREEN]

    def __init__(self, good: _Choices, roll: Union[Roll, RedTileAction]):
        self.good: Final = good
        self.roll: Final = roll


class TeaHouseAction(PlaceTileAction):
    def __init__(self, call: int, roll: Union[Roll, RedTileAction]):
        self.call: Final = call
        self.roll: Final = roll


class MarketAction(PlaceTileAction):
    def __init__(self, goods: Counter[Good], new_demand: Counter[Good]):
        self.goods: Final = goods
        self.new_demand: Final = new_demand


class DoubleCardAction(PlayerAction):
    def __init__(self, card: Card, actions: Tuple[PlaceTileAction, PlaceTileAction]):
        self.card: Final = card
        self.actions: Final = actions


class SellAnyCardAction(PlayerAction):
    def __init__(self, action: MarketAction):
        self.action: Final = action


class PoliceStationAction(PlaceTileAction):
    def __init__(self, location: Location,
                 action: Union[PlaceTileAction, GreenTileAction, DoubleCardAction, SellAnyCardAction]):
        # Do a manual type check
        assert isinstance(action, (PlaceTileAction, GreenTileAction, DoubleCardAction, SellAnyCardAction))
        self.location: Final = location
        self.action: Final = action


class SultansPalaceAction(PlaceTileAction):
    def __init__(self, goods: Counter[Good]):
        self.goods = goods


class MosqueAction(PlaceTileAction):
    def __init__(self, good_color: Good):
        self.good_color = good_color


class FountainAction(PlaceTileAction):
    def __init__(self, assistant_locations: Iterable[Location]):
        self.assistant_locations: Final = frozenset(assistant_locations)


class OneGoodCardAction(PlayerAction):
    def __init__(self, good: Good):
        self.good: Final = good


class ExtraMoveCardAction(PlayerAction):
    def __init__(self, move: Move):
        self.move: Final = move


class NoMoveCardAction(PlayerAction):
    def __init__(self, skip_assistant: bool):
        self.skip_assistant = skip_assistant


class FiveLiraCardAction(PlayerAction):
    pass


class ReturnAssistantCardAction(PlayerAction):
    def __init__(self, from_tile: Location):
        self.from_tile: Final = from_tile


class ArrestFamilyCardAction(PlayerAction):
    def __init__(self, reward: ChooseReward):
        self.reward: Final = reward
