import collections
from functools import partial
from typing import Final, Union, Counter, Dict, List

from actions import PlayerAction, YieldTurn, Move, Pay, ChooseReward, EncounterSmuggler, EncounterGovernor, \
    SkipTileAction, PlaceTileAction, GenericTileAction, GreenTileAction, RedTileAction, YellowTileAction, \
    CaravansaryAction, BlackMarketAction, TeaHouseAction, MarketAction, DoubleCardAction, SellAnyCardAction, \
    PoliceStationAction, SultansPalaceAction, MosqueAction, OneGoodCardAction, ExtraMoveCardAction, NoMoveCardAction, \
    FiveLiraCardAction, ReturnAssistantCardAction, ArrestFamilyCardAction
from constants import Location, Card, Roll, Good, Player, Tile, ROLL_LOCATIONS
from player import PlayerState
from tiles import TileState, MosqueTileState, PostOfficeTileState, CaravansaryTileState, WainwrightTileState, \
    MarketTileState, SultansPalaceTileState, GemstoneDealerTileState, initial_tile_state
from turn import TurnState


def taxicab_dist(loc1: Location, loc2: Location) -> int:
    coords1 = divmod(loc1 - 1, 4)
    coords2 = divmod(loc2 - 1, 4)
    return abs(coords1[0] - coords2[0]) + abs(coords1[1] - coords2[1])


class GameState(object):
    def __init__(self, players: List[Player], location_map: Dict[Location, Tile], small_demand: Counter[Good],
                 large_demand: Counter[Good], governor_location: Location, smuggler_location: Location,
                 player_hands: Dict[Player, Card]):
        self.players: Final = tuple(players)
        self.player_count: Final[int] = len(self.players)
        assert 2 <= self.player_count <= 5
        self.victory_threshold: Final[int] = 5 if self.player_count != 2 else 6
        self.location_map: Final[Dict[Location, Tile]] = location_map
        self.inverse_location_map: Final[Dict[Tile, Location]] = {v: k for k, v in self.location_map.items()}

        self.tile_states: Dict[Tile, TileState] = {tile: initial_tile_state(tile, self.player_count)
                                                   for loc, tile in self.location_map.items()}
        # noinspection PyUnresolvedReferences
        self.tile_states[Tile.SMALL_MARKET].set_demand(small_demand)
        # noinspection PyUnresolvedReferences
        self.tile_states[Tile.LARGE_MARKET].set_demand(large_demand)
        self.tile_states[Tile.POLICE_STATION].family_members |= set(self.players)
        self.tile_states[Tile.FOUNTAIN].players |= set(self.players)
        self.tile_states[self.location_map[governor_location]].governor = True
        self.tile_states[self.location_map[smuggler_location]].smuggler = True

        self.player_states: Dict[Player, PlayerState] = collections.OrderedDict()
        for lira, p in enumerate(self.players, 2):
            self.player_states[p] = PlayerState(
                p,
                player_hands[p],
                lira,
                self.inverse_location_map[Tile.FOUNTAIN],
                self.inverse_location_map[Tile.POLICE_STATION]
            )

        self.turn_state = TurnState(self.players)
        self.outstanding_reward_choices: int = 0

        self.completed = False

    def _check_completed(self):
        if self.turn_state.current_player != self.players[-1]:
            return False
        if any(self.player_states[p].rubies >= self.victory_threshold for p in self.players):
            self.completed = True
            return True
        return False

    def ranking(self):
        scores = [(p.rubies, p.lira, sum(p.cart_contents.values()), sum(p.hand.values()), i)
                  for i in range(self.player_count) if (p := self.player_states[self.players[i]]) is p]
        return {self.players[i]: score for *score, i in sorted(scores, reverse=True)}

    def _move_to(self, location: Location):
        player = self.turn_state.current_player
        player_state = self.player_states[player]
        self.tile_states[self.location_map[player_state.location]].players.remove(player)
        player_state.location = location
        self.tile_states[self.location_map[location]].players.add(player)

    def _discard(self, card: Card):
        hand = self.player_states[self.turn_state.current_player].hand
        assert hand[card] >= 1, '{} does not have {}'.format(self.turn_state.current_player, card)
        hand[card] -= 1
        # noinspection PyUnresolvedReferences
        self.tile_states[Tile.CARAVANSARY].discard_onto(card)

    def _spend(self, lira: int):
        player_state = self.player_states[self.turn_state.current_player]
        assert player_state.lira >= lira, '{} does not have {} lira'.format(
            self.turn_state.current_player, player_state.lira)
        player_state.lira -= lira

    def _acquire(self, good: Good):
        player_state = self.player_states[self.turn_state.current_player]
        if player_state.cart_contents[good] == player_state.cart_max:
            return
        player_state.cart_contents[good] += 1

    def _max_cart(self, good: Good):
        assert good is not Good.BLUE
        player_state = self.player_states[self.turn_state.current_player]
        player_state.cart_contents[good] = player_state.cart_max

    def _trade(self, goods: Counter[Good]):
        player_state = self.player_states[self.turn_state.current_player]
        for good, amount in goods.items():
            assert player_state.cart_contents[good] >= amount, '{} does not have {} {}'.format(
                self.turn_state.current_player, amount, good)
            player_state.cart_contents[good] -= amount

    def _choose_reward(self, choice: ChooseReward):
        if choice.choice is ChooseReward.LIRA:
            self.player_states[self.turn_state.current_player].lira += 3
        else:
            assert isinstance(choice.choice, Card)
            self.player_states[self.turn_state.current_player].hand[choice.choice] += 1
        self.outstanding_reward_choices -= 1

    def _encounter_family_members(self):
        current_tile = self.location_map[self.player_states[self.turn_state.current_player].location]
        if current_tile is Tile.POLICE_STATION:
            return
        tile_state = self.tile_states[current_tile]
        police_station_state = self.tile_states[Tile.POLICE_STATION]
        to_capture = tile_state.family_members - {self.turn_state.current_player}
        self.outstanding_reward_choices += len(to_capture)
        tile_state.family_members -= to_capture
        police_station_state.family_members |= to_capture
        for other_player in to_capture:
            self.player_states[other_player].family_location = self.inverse_location_map[Tile.POLICE_STATION]

    def _location_from_roll(self, roll: Roll) -> Location:
        tile = ROLL_LOCATIONS[Location(sum(roll))]
        return self.inverse_location_map[tile]

    def _check_roll(self, roll: Union[Roll, RedTileAction]) -> int:
        if isinstance(roll, RedTileAction):
            assert Good.RED in self.player_states[self.turn_state.current_player].tiles, \
                '{} does not have the red tile'.format(self.turn_state.current_player)
            if roll.method is RedTileAction.TO_FOUR:
                assert (roll.initial_roll[0] == roll.final_roll[0] and roll.final_roll[1] == 4) or \
                       (roll.initial_roll[1] == roll.final_roll[1] and roll.final_roll[0] == 4) or \
                       (roll.initial_roll[0] == roll.final_roll[1] and roll.final_roll[0] == 4) or \
                       (roll.initial_roll[1] == roll.final_roll[0] and roll.final_roll[1] == 4), \
                       'Red tile not used correctly'
            return sum(roll.final_roll)
        return sum(roll)

    def take_action(self, action: PlayerAction):
        assert not self.completed
        if self.outstanding_reward_choices:
            assert not isinstance(action, YieldTurn), 'Player needs to choose a reward for capturing family members'
        if isinstance(action, ChooseReward):
            assert self.outstanding_reward_choices, 'No more rewards to choose'
            self._choose_reward(action)
            return
        if isinstance(action, YieldTurn):
            self._check_completed()
            self.turn_state.take_action(action)
            return

        self.turn_state.take_action(action)
        player = self.turn_state.current_player
        player_state = self.player_states[player]
        if isinstance(action, (Move, ExtraMoveCardAction)):
            if isinstance(action, Move):
                move_range = (1, 2)
            else:
                move_range = (3, 4)
                action = action.move
                self._discard(Card.EXTRA_MOVE)
            destination = action.tile
            distance = taxicab_dist(player_state.location, destination)
            assert distance in move_range, 'Cannot move {} spaces'.format(distance)
            self._move_to(action.tile)

        tile = self.location_map[player_state.location]
        tile_state = self.tile_states[tile]
        if isinstance(action, (Move, ExtraMoveCardAction, NoMoveCardAction)):
            if isinstance(action, NoMoveCardAction):
                self._discard(Card.NO_MOVE)
            if isinstance(action, ExtraMoveCardAction):
                skip_assistant = action.move.skip_assistant
            else:
                skip_assistant = action.skip_assistant
            if not skip_assistant:
                if player in tile_state.assistants:
                    tile_state.assistants.remove(player)
                    player_state.stack_size += 1
                    player_state.assistant_locations.remove(player_state.location)
                else:
                    # You can move and then play the return assistant card, this is exactly equivalent to reversing the
                    # order, so in this case it is probably easier to invert (if I were doing this again I would
                    # make the action more explicit and have a separate action for interacting with the assistant,
                    # leaving the inference high-level)
                    assert player_state.stack_size > 0, 'If no assistants in stack or at destination must end turn'
                    player_state.stack_size -= 1
                    player_state.assistant_locations.add(player_state.location)
                    tile_state.assistants.add(player)
            if len(tile_state.players) == 1 or tile is Tile.FOUNTAIN:
                self.turn_state.skip_phase_2()
            return

        if isinstance(action, Pay):
            cost = (len(tile_state.players) - 1) * 2
            assert 0 < cost <= player_state.lira, 'Cannot pay {} when you have {}'.format(cost, player_state.lira)
            for other_player in tile_state.players:
                if other_player == player:
                    continue
                self.player_states[other_player].lira += 2
                player_state.lira -= 2
            return

        if isinstance(action, SkipTileAction):
            self._encounter_family_members()
            return

        if isinstance(action, EncounterGovernor):
            assert tile_state.governor, 'Governor is not at {} ({})'.format(tile, player_state.location)
            player_state.hand[action.gain] += 1
            if isinstance(action.cost, Pay):
                self._spend(2)
            else:
                self._discard(action.cost)
            tile_state.governor = False
            self.tile_states[self.location_map[self._location_from_roll(action.roll)]].governor = True
            return

        if isinstance(action, EncounterSmuggler):
            assert tile_state.smuggler, 'Smuggler is not at {} ({})'.format(tile, player_state.location)
            player_state.cart_contents[action.gain] = min(player_state.cart_contents[action.gain] + 1,
                                                          player_state.cart_max)
            if isinstance(action.cost, Pay):
                self._spend(2)
            else:
                self._trade(collections.Counter({action.cost: 1}))
            tile_state.smuggler = False
            self.tile_states[self.location_map[self._location_from_roll(action.roll)]].smuggler = True
            return

        if isinstance(action, OneGoodCardAction):
            self._discard(Card.ONE_GOOD)
            self._acquire(action.good)
            return

        if isinstance(action, FiveLiraCardAction):
            self._discard(Card.FIVE_LIRA)
            player_state.lira += 5
            return

        if isinstance(action, ArrestFamilyCardAction):
            assert player_state.family_location != self.inverse_location_map[Tile.POLICE_STATION]
            self._discard(Card.ARREST_FAMILY)
            self.tile_states[self.location_map[player_state.family_location]].family_members.remove(player)
            self.tile_states[Tile.POLICE_STATION].family_members.add(player)
            player_state.family_location = self.inverse_location_map[Tile.POLICE_STATION]
            self.outstanding_reward_choices += 1
            self._choose_reward(action.reward)
            return

        if isinstance(action, (YellowTileAction, ReturnAssistantCardAction)):
            if isinstance(action, ReturnAssistantCardAction):
                self._discard(Card.RETURN_ASSISTANT)
            else:
                assert Good.YELLOW in player_state.tiles, '{} does not have yellow tile'.format(player)
                self._spend(2)
            self.tile_states[self.location_map[action.from_tile]].assistants.remove(player)
            player_state.stack_size += 1
            player_state.assistant_locations.remove(action.from_tile)
            return

        # Phase 3 actions

        if isinstance(action, DoubleCardAction):
            self._discard(action.card)
            if action.card is Card.DOUBLE_SULTAN:
                for sub in action.actions:
                    assert isinstance(sub, SultansPalaceAction)
                    self._handle_sultans_palace_action(sub)
                self._encounter_family_members()
                return
            assert all(isinstance(sub, GenericTileAction) for sub in action.actions)
            act = {Card.DOUBLE_PO: self._handle_post_office_action,
                   Card.DOUBLE_DEALER: self._handle_gemstone_dealer_action}[action.card]
            act()
            act()
            self._encounter_family_members()
            return

        if isinstance(action, SellAnyCardAction):
            self._discard(Card.SELL_ANY)
            assert tile is Tile.SMALL_MARKET, 'Can only use sell any card at small market'
            self._trade(action.action.goods)
            n = sum(action.action.goods.values())
            gain = ((n + 1) * (n + 2)) // 2 - 1
            player_state.lira += gain
            # noinspection PyUnresolvedReferences
            tile_state.set_demand(action.action.new_demand)
            self._encounter_family_members()
            return

        if isinstance(action, GreenTileAction):
            assert Good.GREEN in player_state.tiles, '{} does not have green tile'.format(player)
            warehouse_good_map = {
                Tile.FABRIC_WAREHOUSE: Good.RED,
                Tile.SPICE_WAREHOUSE: Good.GREEN,
                Tile.FRUIT_WAREHOUSE: Good.YELLOW,
            }
            assert tile in warehouse_good_map, 'Green tile can only be used at a warehouse, not {}'.format(tile)
            self._max_cart(warehouse_good_map[tile])
            self._spend(2)
            self._acquire(action.good)
            self._encounter_family_members()
            return

        assert isinstance(action, PlaceTileAction)
        if isinstance(action, GenericTileAction):
            generic_action_map = {
                Tile.POST_OFFICE: self._handle_post_office_action,
                Tile.FABRIC_WAREHOUSE: partial(self._max_cart, Good.RED),
                Tile.FRUIT_WAREHOUSE: partial(self._max_cart, Good.YELLOW),
                Tile.FOUNTAIN: self._handle_fountain_action,
                Tile.SPICE_WAREHOUSE: partial(self._max_cart, Good.GREEN),
                Tile.WAINWRIGHT: self._handle_wainwright_action,
                Tile.GEMSTONE_DEALER: self._handle_gemstone_dealer_action,
            }
            generic_action_map[tile]()
            self._encounter_family_members()
            return

        tile_action_map = {
            MosqueAction: self._handle_mosque_action,
            PoliceStationAction: self._handle_police_station_action,
            BlackMarketAction: self._handle_black_market_action,
            CaravansaryAction: self._handle_caravansary_action,
            MarketAction: self._handle_market_action,
            TeaHouseAction: self._handle_tea_house_action,
            SultansPalaceAction: self._handle_sultans_palace_action,
        }
        # noinspection PyTypeChecker
        tile_action_map[action.__class__](action)
        self._encounter_family_members()

    def _handle_mosque_action(self, action: MosqueAction):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        tile = self.location_map[player_state.location]
        tile_state = self.tile_states[tile]

        assert isinstance(tile_state, MosqueTileState), 'Not at a mosque'
        assert action.good_color not in player_state.tiles, '{} already got {} tile'.format(player, action.good_color)
        cost = tile_state.available_tiles[action.good_color]
        self._trade(collections.Counter({action.good_color: cost}))
        tile_state.take_action(action.good_color)
        if action.good_color is Good.BLUE:
            player_state.stack_size += 1

        for pair in ((Good.BLUE, Good.YELLOW), (Good.RED, Good.GREEN)):
            if (action.good_color is pair[0] and pair[1] in player_state.tiles) or \
                    (action.good_color is pair[1] and pair[0] in player_state.tiles):
                player_state.rubies += 1
            player_state.tiles.add(action.good_color)

    def _handle_post_office_action(self):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        # noinspection PyTypeChecker
        tile_state: PostOfficeTileState = self.tile_states[Tile.POST_OFFICE]

        goods, lira = tile_state.take_action()
        for good in goods:
            self._acquire(good)
        player_state.lira += lira

    def _handle_police_station_action(self, action: PoliceStationAction):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        tile = self.location_map[player_state.location]
        tile_state = self.tile_states[tile]
        assert tile is Tile.POLICE_STATION, '{} not at police station'.format(player)
        assert player in tile_state.family_members, '{} does not have family at police station'.format(player)
        assert player_state.location is not action.location, 'Cannot send family member to police station'

        tile_state.family_members.remove(player)
        destination_tile_state = self.tile_states[self.location_map[action.location]]
        destination_tile_state.family_members.add(player)
        player_state.family_location = action.location

        # As a bit of an oversight the handlers expect the player to be at the location, so we move temporarily
        tile_state.players.remove(player)
        destination_tile_state.players.add(player)
        player_state.location = action.location
        self.take_action(action.action)
        destination_tile_state.players.remove(player)
        tile_state.players.add(player)
        player_state.location = self.inverse_location_map[Tile.POLICE_STATION]

    def _handle_fountain_action(self):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        for location in list(player_state.assistant_locations):
            player_state.stack_size += 1
            player_state.assistant_locations.remove(location)
            self.tile_states[self.location_map[location]].assistants.remove(player)

    def _handle_black_market_action(self, action: BlackMarketAction):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        tile = self.location_map[player_state.location]
        assert tile is Tile.BLACK_MARKET

        self._acquire(action.good)
        total = self._check_roll(action.roll)
        times = 0
        if total >= 11:
            times = 3
        elif total >= 9:
            times = 2
        elif total >= 7:
            times = 1
        for _ in range(times):
            self._acquire(Good.BLUE)

    def _handle_caravansary_action(self, action: CaravansaryAction):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        tile = self.location_map[player_state.location]
        # noinspection PyTypeChecker
        tile_state: CaravansaryTileState = self.tile_states[tile]
        assert tile is Tile.CARAVANSARY

        count = 0
        for gain in action.gains:
            if gain is CaravansaryAction.DISCARD:
                count += 1
                continue
            player_state.hand[gain] += 1

        for card in tile_state.take_action(count):
            player_state.hand[card] += 1

        self._discard(action.cost)

    def _handle_market_action(self, action: MarketAction):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        tile = self.location_map[player_state.location]
        tile_state = self.tile_states[tile]
        assert isinstance(tile_state, MarketTileState)

        self._trade(action.goods)
        lira = tile_state.take_action(action.goods)
        player_state.lira += lira
        tile_state.set_demand(action.new_demand)

    def _handle_tea_house_action(self, action: TeaHouseAction):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        tile = self.location_map[player_state.location]
        assert tile is Tile.TEA_HOUSE

        total = self._check_roll(action.roll)
        player_state.lira += action.call if total >= action.call else 2

    def _handle_sultans_palace_action(self, action: SultansPalaceAction):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        tile = self.location_map[player_state.location]
        assert tile is Tile.SULTANS_PALACE
        # noinspection PyTypeChecker
        tile_state: SultansPalaceTileState = self.tile_states[tile]

        self._trade(action.goods)
        tile_state.take_action(action.goods)
        player_state.rubies += 1

    def _handle_wainwright_action(self):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        # noinspection PyTypeChecker
        tile_state: WainwrightTileState = self.tile_states[Tile.WAINWRIGHT]

        assert player_state.cart_max <= 5, 'No room for additional extensions for {}'.format(player)
        self._spend(7)
        tile_state.take_action()
        player_state.cart_max += 1
        if player_state.cart_max == 5:
            player_state.rubies += 1

    def _handle_gemstone_dealer_action(self):
        player = self.turn_state.current_player
        player_state = self.player_states[player]

        # noinspection PyTypeChecker
        tile_state: GemstoneDealerTileState = self.tile_states[Tile.GEMSTONE_DEALER]
        assert tile_state.cost is not None, 'No more rubies to buy at the Gemstone Dealer'
        self._spend(tile_state.cost)
        tile_state.take_action()

        player_state.rubies += 1
