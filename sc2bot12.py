import sc2
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.maps import get as get_map
from sc2.bot_ai import BotAI
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
import random


class MyBot(BotAI):
    async def on_step(self, iteration: int):
        print(f"This is my bot in iteration {iteration}!")
        global scout_alive
        global main_base
        if(iteration==0):
            main_base = self.townhalls[0]
            main_base.train(UnitTypeId.PROBE)
            scout_alive = False
        if self.time>60 and scout_alive == False:
            scout_worker = self.workers.filter(lambda worker: worker.is_collecting or worker.is_idle).random
            scout_worker.move(self.enemy_start_locations[0])
            scout_alive = True
        if self.can_afford(UnitTypeId.PYLON) and self.already_pending(
                UnitTypeId.PYLON) + self.structures.filter(
                lambda structure: structure.type_id == UnitTypeId.PYLON and structure.is_ready).amount == 0:
            map_center = self.game_info.map_center
            position_towards_map_center = self.start_location.towards(map_center, distance=5)
            await self.build(UnitTypeId.PYLON, near=position_towards_map_center, placement_step=1)
        elif len(self.workers)<15 and self.can_afford(UnitTypeId.PROBE):
            main_base.train(UnitTypeId.PROBE)
        if self.can_afford(UnitTypeId.FORGE) and self.already_pending(
                UnitTypeId.FORGE) + self.structures.filter(
                lambda structure: structure.type_id == UnitTypeId.FORGE and structure.is_ready).amount == 0:
            map_center = self.game_info.map_center
            position_towards_map_center = self.start_location.towards(map_center, distance=7)
            await self.build(UnitTypeId.FORGE, near=position_towards_map_center, placement_step=1)
        if self.time>100:
            if self.can_afford(UnitTypeId.PYLON):
                map_center = self.game_info.map_center
                position_towards_map_center = self.start_location.towards(map_center, distance=random.randint(1, 30))
                await self.build(UnitTypeId.PYLON, near=position_towards_map_center, placement_step=1)
            if self.can_afford(UnitTypeId.PHOTONCANNON):
                map_center = self.game_info.map_center
                position_towards_map_center = self.start_location.towards(map_center, distance=random.randint(1, 30))
                await self.build(UnitTypeId.PHOTONCANNON, near=position_towards_map_center, placement_step=1)




sc2.main.run_game(
    sc2.maps.get("AcropolisLE"),
    [Bot(sc2.data.Race.Protoss, MyBot()), Computer(sc2.data.Race.Zerg, sc2.data.Difficulty.Hard)],
    realtime=False,
)