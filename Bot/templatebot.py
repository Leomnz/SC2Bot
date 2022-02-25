import math

import sc2
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.maps import get as get_map
from sc2.bot_ai import BotAI
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.position import Pointlike
from sc2.game_state import GameState
import random
from sc2.unit import Unit


class BotName(BotAI):
    async def on_building_construction_complete(self, unit: Unit):
        print(f"{unit} construction complete")

    async def on_unit_destroyed(self, unit_tag):
        print(f"{unit_tag} destroyed")

    async def on_step(self, iteration: int):
        if iteration % 10 == 0:
            print("iteration:", iteration, ", time:", round(self.time, 3), ", supply:", str(self.supply_used) + "/" + str(self.supply_cap), ", m:",
                  self.minerals, ", v:", self.vespene, sep="")



sc2.main.run_game(
    sc2.maps.get("AcropolisLE"),
    [Bot(sc2.data.Race.Protoss, BotName()), Computer(sc2.data.Race.Zerg, sc2.data.Difficulty.Easy)],
    realtime=False,
)
