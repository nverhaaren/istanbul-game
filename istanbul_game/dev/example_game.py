from collections import Counter

from ..actions import (
    BlackMarketAction,
    EncounterGovernor,
    EncounterSmuggler,
    GenericTileAction,
    MosqueAction,
    Move,
    OneGoodCardAction,
    Pay,
    PoliceStationAction,
    YieldTurn,
)
from ..constants import DEFAULT_LOCATIONS, Card, Good, Location, Player
from ..game import GameState

if __name__ == "__main__":
    gs = GameState(
        [Player.BLUE, Player.YELLOW, Player.RED, Player.GREEN],
        DEFAULT_LOCATIONS,
        Counter({Good.BLUE: 1, Good.RED: 1, Good.GREEN: 1, Good.YELLOW: 2}),
        Counter({Good.YELLOW: 1, Good.BLUE: 2, Good.RED: 2}),
        Location(9),
        Location(5),
        {
            Player.BLUE: Card.ONE_GOOD,
            Player.YELLOW: Card.SELL_ANY,
            Player.RED: Card.RETURN_ASSISTANT,
            Player.GREEN: Card.ARREST_FAMILY,
        },
    )

    # Round 1
    gs.take_action(Move(Location(5), skip_assistant=False))
    gs.take_action(GenericTileAction())
    gs.take_action(EncounterSmuggler(Good.BLUE, Good.YELLOW, (4, 4)))
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(3), skip_assistant=False))
    gs.take_action(GenericTileAction())
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(8), skip_assistant=False))
    gs.take_action(GenericTileAction())
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(2), skip_assistant=False))
    gs.take_action(GenericTileAction())
    gs.take_action(YieldTurn())

    # Round 2
    gs.take_action(Move(Location(1), skip_assistant=False))
    gs.take_action(OneGoodCardAction(Good.BLUE))
    gs.take_action(MosqueAction(Good.BLUE))
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(4), skip_assistant=False))
    gs.take_action(MosqueAction(Good.RED))
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(6), skip_assistant=False))
    gs.take_action(PoliceStationAction(Location(4), MosqueAction(Good.GREEN)))
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(5), skip_assistant=False))
    gs.take_action(GenericTileAction())
    gs.take_action(YieldTurn())

    # Round 3
    gs.take_action(Move(Location(2), skip_assistant=False))
    gs.take_action(GenericTileAction())
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(8), skip_assistant=False))
    gs.take_action(GenericTileAction())
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(9), skip_assistant=False))
    gs.take_action(BlackMarketAction(Good.GREEN, (4, 1)))
    gs.take_action(EncounterGovernor(Card.FIVE_LIRA, Pay(), (2, 3)))
    gs.take_action(EncounterSmuggler(Good.BLUE, Good.GREEN, (2, 5)))
    gs.take_action(YieldTurn())

    gs.take_action(Move(Location(6), skip_assistant=False))
    gs.take_action(PoliceStationAction(Location(15), GenericTileAction()))
    gs.take_action(YieldTurn())

    pass
