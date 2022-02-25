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

global stage
stage = 0
global scout_alive
scout_alive = False


class ImmortalBot(BotAI):
    async def on_building_construction_complete(self, unit: Unit):
        print(f"{unit} construction complete")

    async def on_unit_destroyed(self, unit_tag):
        print(f"{unit_tag} destroyed")

    async def on_step(self, iteration: int):
        def worker_select():
            if len(self.workers) > 0:
                if len(self.workers.filter(lambda worker: worker.is_idle)) > 0:
                    return self.workers.filter(lambda worker: worker.is_idle).random
                elif len(self.workers.filter(lambda worker: worker.is_collecting or worker.is_idle)) > 0:
                    return self.workers.filter(lambda worker: worker.is_collecting or worker.is_idle).random
                else:
                    return self.workers.random
            return None

        if iteration == 0:
            await self.chat_send("Hello I am ImmortalBot")
            await self.chat_send("(glhf)")
        global stage
        if iteration % 10 == 0:
            print("iteration:", iteration, ", time:", round(self.time, 3), ", supply:", str(self.supply_used) + "/" + str(self.supply_cap), ", m:",
                  self.minerals, ", v:", self.vespene, ", stage:", stage, sep="")
        global scout_alive
        if self.time > 60 and scout_alive is False:
            scout_worker = worker_select()
            if scout_worker is not None:
                scout_worker.move(self.enemy_start_locations[0])
                scout_alive = True


sc2.main.run_game(
    sc2.maps.get("AcropolisLE"),
    [Bot(sc2.data.Race.Protoss, ImmortalBot()), Computer(sc2.data.Race.Zerg, sc2.data.Difficulty.Easy)],
    realtime=False,
)
