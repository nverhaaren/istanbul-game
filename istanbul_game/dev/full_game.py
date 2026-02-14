"""A complete 3-player game where RED wins with 5 rubies.

Board layout (default, 4x4 grid, taxicab distances):
  Row 0: 1=GreatMosque  2=PostOffice   3=FabricWH    4=SmallMosque
  Row 1: 5=FruitWH      6=PoliceStation 7=Fountain    8=SpiceWH
  Row 2: 9=BlackMarket  10=Caravansary 11=SmallMarket 12=TeaHouse
  Row 3: 13=SultanPalace 14=LargeMarket 15=Wainwright 16=GemstoneDealer

RED rubies: mosque pair x2 (R4, R11), Gemstone Dealer x3 (R15, R17, R19).
RED lira: start 2, +2 (R3 BLUE pays RED), PO +3 (R8), PO +4 (R10),
          Tea House x3 +36 (R14, R16, R18) = 47. Gem costs: 14+15+16=45. Final=2.
"""

import json
import sys
from collections import Counter

from .. import serialize
from ..actions import (
    EncounterSmuggler,
    GenericTileAction,
    MosqueAction,
    Move,
    OneGoodCardAction,
    Pay,
    SkipTileAction,
    TeaHouseAction,
    YieldTurn,
)
from ..constants import DEFAULT_LOCATIONS, Card, Good, Location, Player
from ..game import GameState


def main() -> None:
    gs = GameState(
        [Player.RED, Player.BLUE, Player.GREEN],
        DEFAULT_LOCATIONS,
        Counter({Good.RED: 2, Good.GREEN: 2, Good.YELLOW: 1}),
        Counter({Good.RED: 2, Good.GREEN: 1, Good.YELLOW: 1, Good.BLUE: 1}),
        Location(1),  # governor
        Location(2),  # smuggler
        {Player.RED: Card.ONE_GOOD, Player.BLUE: Card.ONE_GOOD, Player.GREEN: Card.ONE_GOOD},
    )

    def act(action):
        gs.take_action(action)

    def turn(player, *actions):
        """Execute a full turn: actions then YieldTurn."""
        for a in actions:
            act(a)
        act(YieldTurn())

    R, B, G = Player.RED, Player.BLUE, Player.GREEN

    def move(loc, skip=False):
        return Move(Location(loc), skip_assistant=skip)

    # Shorthand tile actions
    generic = GenericTileAction()
    skip_tile = SkipTileAction()

    # ==================== Round 1 ====================
    turn(R, move(8), GenericTileAction())  # RED: SpiceWH, fill G=2
    turn(
        B,
        move(2),
        GenericTileAction(),  # BLUE: PO pos 0->1, G+Y+2lira
        EncounterSmuggler(Good.RED, Good.GREEN, (3, 4)),
    )  # gain R, pay G. Smuggler -> Fountain
    turn(G, move(3), GenericTileAction())  # GREEN: FabricWH, fill R=2

    # ==================== Round 2 ====================
    turn(R, move(4), MosqueAction(Good.GREEN))  # RED: SmallMosque, Green tile (cost 2G)
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 3 ====================
    turn(R, move(3), GenericTileAction())  # RED: FabricWH, fill R=2
    turn(B, move(3), Pay(), GenericTileAction())  # BLUE: FabricWH (RED here), pay 2. fill R=2
    turn(G, move(8), GenericTileAction())  # GREEN: SpiceWH, fill G=2

    # ==================== Round 4 ====================
    turn(R, move(4), MosqueAction(Good.RED))  # RED: SmallMosque, Red tile (cost 2R). RUBY 1!
    assert gs.player_states[R].rubies == 1
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 5 ====================
    turn(R, move(7), GenericTileAction())  # RED: Fountain, recall from {8,4,3}
    turn(B, move(8), GenericTileAction())  # BLUE: SpiceWH, fill G=2
    turn(G, move(3), GenericTileAction())  # GREEN: FabricWH, fill R=2

    # ==================== Round 6 ====================
    turn(R, move(5), GenericTileAction())  # RED: FruitWH, fill Y=2
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 7 ====================
    turn(R, move(1), MosqueAction(Good.YELLOW))  # RED: GreatMosque, Yellow tile (cost 2Y)
    turn(B, move(5), GenericTileAction())  # BLUE: FruitWH, fill Y=2
    turn(G, move(8), GenericTileAction())  # GREEN: SpiceWH, fill G=2

    # ==================== Round 8 ====================
    # PO pos 1 -> 2: Red+Yellow+3lira. RED lira: 4+3=7.
    turn(R, move(2), GenericTileAction())  # RED: PO, R=1 Y=1 +3lira
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 9 ====================
    # RED can't stay at PO. Move to GreatMosque (dist 1), skip tile action. Pick up asst from R7.
    turn(R, move(1), SkipTileAction())  # RED: GreatMosque, skip
    turn(B, move(3), GenericTileAction())  # BLUE: FabricWH
    turn(G, move(8), GenericTileAction())  # GREEN: SpiceWH

    # ==================== Round 10 ====================
    # PO pos 2 -> 3: Red+Blue+4lira. RED lira: 7+4=11. Cart: R=2(full), B=1.
    # Play OneGood card for Blue. B=2.
    turn(R, move(2), GenericTileAction(), OneGoodCardAction(Good.BLUE))  # RED: PO, R=2 B=2 +4lira
    assert gs.player_states[R].lira == 11
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 11 ====================
    # RED: GreatMosque, Blue tile (cost 2B). Blue+Yellow pair -> RUBY 2!
    # Blue tile gives +1 stack.
    turn(R, move(1), MosqueAction(Good.BLUE))  # RED: GreatMosque, RUBY 2!
    assert gs.player_states[R].rubies == 2
    turn(B, move(8), GenericTileAction())  # BLUE: SpiceWH, fill G=2
    turn(G, move(3), GenericTileAction())  # GREEN: FabricWH

    # ==================== Round 12 ====================
    # RED: FruitWH (from GreatMosque loc 1, to loc 5: dist 2). Pick up asst from R6.
    turn(R, move(5), GenericTileAction())  # RED: FruitWH, fill Y=2. Cart: R=2,Y=2
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 13 ====================
    # RED: Fountain (from 5, dist 2). Recall remaining assts.
    turn(R, move(7), GenericTileAction())  # RED: Fountain, recall -> stack=5
    turn(B, move(5), GenericTileAction())  # BLUE: FruitWH, fill Y=2
    turn(G, move(8), GenericTileAction())  # GREEN: SpiceWH, fill G=2

    # ==================== Round 14 ====================
    # RED: TeaHouse (from 7, dist 2). Call 12, roll 6+6. lira: 11+12=23.
    turn(R, move(12), TeaHouseAction(12, (6, 6)))  # RED: TeaHouse, +12 lira
    assert gs.player_states[R].lira == 23
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 15 ====================
    # RED: GemstoneDealer (from 12, dist 1). Cost 14. lira: 23-14=9. RUBY 3!
    turn(R, move(16), GenericTileAction())  # RED: GemstoneDealer, RUBY 3!
    assert gs.player_states[R].rubies == 3
    assert gs.player_states[R].lira == 9
    turn(B, move(3), GenericTileAction())  # BLUE: FabricWH
    turn(G, move(3), Pay(), GenericTileAction())  # GREEN: FabricWH (BLUE there), pay 2

    # ==================== Round 16 ====================
    # RED: TeaHouse (from 16, dist 1). Pick up asst from R14. lira: 9+12=21.
    turn(R, move(12), TeaHouseAction(12, (6, 6)))  # RED: TeaHouse, +12 lira
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 17 ====================
    # RED: GemstoneDealer (from 12, dist 1). Pick up from R15. Cost 15. lira: 21-15=6. RUBY 4!
    turn(R, move(16), GenericTileAction())  # RED: GemstoneDealer, RUBY 4!
    assert gs.player_states[R].rubies == 4
    assert gs.player_states[R].lira == 6
    turn(B, move(5), GenericTileAction())  # BLUE: FruitWH
    turn(G, move(8), GenericTileAction())  # GREEN: SpiceWH

    # ==================== Round 18 ====================
    # RED: TeaHouse (from 16, dist 1). lira: 6+12=18.
    turn(R, move(12), TeaHouseAction(12, (6, 6)))  # RED: TeaHouse, +12 lira
    assert gs.player_states[R].lira == 18
    turn(B, move(7), GenericTileAction())  # BLUE: Fountain, recall
    turn(G, move(7), GenericTileAction())  # GREEN: Fountain, recall

    # ==================== Round 19 ====================
    # RED: GemstoneDealer (from 12, dist 1). Cost 16. lira: 18-16=2. RUBY 5!!!
    turn(R, move(16), GenericTileAction())  # RED: GemstoneDealer, RUBY 5!!!
    assert gs.player_states[R].rubies == 5
    assert gs.player_states[R].lira == 2

    # BLUE and GREEN take their turns. Game completes when GREEN (last player) yields.
    turn(B, move(3), GenericTileAction())  # BLUE: FabricWH
    assert not gs.completed
    turn(G, move(3), Pay(), GenericTileAction())  # GREEN: FabricWH (BLUE there)
    assert gs.completed

    # Output final game state
    json.dump(serialize.game_state(gs), sys.stdout, indent=4)
    print()


if __name__ == "__main__":
    main()
