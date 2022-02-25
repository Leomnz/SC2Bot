import math

import sc2
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.maps import get as get_map
from sc2.bot_ai import BotAI
from sc2.player import Bot, Computer, Player
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.position import Pointlike
from sc2.game_state import GameState
import random

global scout_alive
scout_alive = False
global main_base
main_base = None
global build_order
build_order = [
    [UnitTypeId.PYLON, UnitTypeId.GATEWAY, UnitTypeId.CYBERNETICSCORE, UnitTypeId.ROBOTICSFACILITY, UnitTypeId.STARGATE], 0]
global early_game
early_game = True
global late_game
late_game = False


class MyBot(BotAI):
    async def on_building_construction_complete(self, unit):
        if unit.type_id == UnitTypeId.PYLON:
            global early_game
            early_game = False
            print("Early Game False")

    async def on_step(self, iteration: int):
        global scout_alive
        global build_order
        global build_order
        global early_game

        def worker_select():
            if self.workers.amount > 0:
                if self.workers.filter(lambda worker: worker.is_idle).amount > 0:
                    return self.workers.filter(lambda worker: worker.is_idle).random
                elif self.workers.filter(lambda worker: worker.is_collecting or worker.is_idle).amount > 0:
                    return self.workers.filter(lambda worker: worker.is_collecting or worker.is_idle).random
                else:
                    return self.workers.random
            return None

        def index_of_smallest_element(arr):
            # Find the index of the smallest element in arr
            smallest_index = 0
            smallest_element = arr[0]
            for i in range(1, len(arr)):
                if arr[i] < smallest_element:
                    smallest_index = i
                    smallest_element = arr[i]
            return smallest_index

        # early game
        if (iteration == 0):
            global late_game
            global main_base
            main_base = self.townhalls[0]
            main_base.train(UnitTypeId.PROBE)
            late_game = True

        if self.time > 60 and scout_alive is False:
            scout_worker = worker_select()
            if scout_worker is not None:
                scout_worker.move(self.enemy_start_locations[0])
                scout_alive = True

        if (self.townhalls.amount < round(self.time, 1) / 120) or self.workers.filter(lambda worker: worker.is_idle).amount > 6:
            if self.can_afford(UnitTypeId.NEXUS):
                await self.expand_now()

        for structure_to_build in build_order[0]:
            if self.can_afford(structure_to_build) and self.already_pending(structure_to_build) + self.structures.filter(
                    lambda structure: structure.type_id == structure_to_build and structure.is_ready).amount == 0:
                worker_candidates = self.workers.filter(
                    lambda worker: (worker.is_collecting or worker.is_idle) and worker.tag not in self.unit_tags_received_action)
                # Worker_candidates can be empty
                if worker_candidates:
                    map_center = self.game_info.map_center
                    position_towards_map_center = self.start_location.towards(map_center, distance=5)
                    placement_position = await self.find_placement(structure_to_build, near=position_towards_map_center, placement_step=1)
                    # Placement_position can be None
                    if placement_position:
                        build_worker = worker_candidates.closest_to(placement_position)
                        build_worker.build(structure_to_build, placement_position)
        def build_gas():  # gas geyser handling
            for nexus in self.townhalls:
                if nexus.is_ready:
                    both_geysers = self.vespene_geyser.closest_n_units(nexus, 2)  # find closest 2 geysers to the nexus
                    if both_geysers[0] != UnitTypeId.ASSIMILATOR:  # if the first geyser is not an assimilator
                        worker = worker_select()
                        if worker is not None:
                            worker.build_gas(both_geysers[0])
                            return True
                    if both_geysers[1] != UnitTypeId.ASSIMILATOR:  # if the second geyser is not an assimilator
                        worker = worker_select()
                        if worker is not None:
                            worker.build_gas(both_geysers[1])
                            return True
            return False

        # mineral gas ratio handling
        def too_much_gas():
            for geyser in self.gas_buildings:
                if geyser.assigned_harvesters > 0:
                    worker = None
                    if self.workers.amount > 0:
                        worker = self.workers.filter(lambda worker: worker.is_collecting).closest_to(geyser)
                    if worker is not None:
                        worker.stop()

        def too_many_minerals():
            for geyser in self.gas_buildings:
                if geyser.assigned_harvesters < geyser.ideal_harvesters:
                    worker = None
                    if self.workers.amount > 0:
                        worker = worker_select()
                    if worker is not None:
                        worker.gather(geyser)

        if iteration % 4 == 0:  # Check every 4 iterations
            if self.vespene == 0 or self.minerals / self.vespene > 2:  # too many minerals
                too_many_minerals()
            elif self.minerals == 0 or self.vespene / self.minerals > 2:  # too much gas
                too_much_gas()

        # building probes
        if self.workers.amount < 80 and (len(self.workers) < round(self.time / 5, 3)):
            if self.workers.filter(lambda worker: worker.is_idle).amount < 6:
                if self.can_afford(UnitTypeId.PROBE):
                    nexus = self.townhalls.random
                    nexus.train(UnitTypeId.PROBE)

        for nexus in self.townhalls:  # probe handling
            if nexus.is_ready:
                if nexus.assigned_harvesters < nexus.ideal_harvesters:  # if the nexus has less harvesters than it needs
                    worker = None
                    if self.workers.filter(lambda worker: worker.is_idle).amount > 0:
                        worker = self.workers.filter(lambda worker: worker.is_idle).closest_to(nexus)  # find closest worker that is idle
                    if worker is not None:
                        worker.gather(self.mineral_field.closest_to(nexus))  # gather the mineral field near the nexus


                elif nexus.assigned_harvesters > nexus.ideal_harvesters:  # if the nexus has more harvesters than it needs
                    possible_workers = self.workers.filter(lambda worker: worker.is_gathering)  # find all workers that are gathering
                    worker = possible_workers.sorted(
                        lambda worker: worker.distance_to(nexus)).first  # sort them by distance to nexus and take the first one
                    if worker is not None:
                        worker.stop()  # stop the worker


        # army handling
        if self.all_units is not None:
            for unit in self.all_units.filter(lambda unit: unit.type_id != UnitTypeId.PROBE):
                if unit.is_idle:
                    if self.enemy_units.amount > 0:
                        unit.attack(self.enemy_units.closest_to(unit))
                    elif self.enemy_structures.amount > 0:
                        unit.attack(self.enemy_structures.closest_to(unit))
                    else:
                        scout_pos = Pointlike((random.randint(0, 250), random.randint(0, 250)))
                        scout_pos = Point2(scout_pos)
                        unit.attack(scout_pos)

        # supply handling
        if self.supply_used + 5 > self.supply_cap:
            if self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON).exists:
                worker = worker_select()
                if worker is not None:
                    build_structure = self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON).random
                    if self.minerals > 1000 and self.supply_cap > 192:
                        build_pos = Pointlike(
                            (build_structure.position.x + random.randint(-1, 1) * 30, build_structure.position.y + random.randint(-1, 1) * 30))
                        build_pos = Point2(build_pos)
                        await self.build(UnitTypeId.PYLON, near=build_pos, placement_step=1, build_worker=worker)
                    if self.minerals < 1000 and self.supply_cap < 192:
                        build_pos = Pointlike(
                            (build_structure.position.x + random.randint(-1, 1) * 12, build_structure.position.y + random.randint(-1, 1) * 12))
                        build_pos = Point2(build_pos)
                        await self.build(UnitTypeId.PYLON, near=build_pos, placement_step=1, build_worker=worker)

        # late game
        if late_game:
            for structure in self.structures:
                if structure.is_idle:
                    if structure.type_id == UnitTypeId.GATEWAY:
                        if self.minerals / self.vespene > 2:
                            if self.can_afford(UnitTypeId.ZEALOT):
                                structure.train(UnitTypeId.ZEALOT)
                            elif self.can_afford(UnitTypeId.STALKER):
                                structure.train(UnitTypeId.STALKER)
                    elif structure.type_id == UnitTypeId.WARPGATE:
                        if self.can_afford(UnitTypeId.STALKER):
                            structure.train(UnitTypeId.STALKER)
                    elif structure.type_id == UnitTypeId.STARGATE:
                        if self.can_afford(UnitTypeId.VOIDRAY):
                            structure.train(UnitTypeId.VOIDRAY)
                    elif structure.type_id == UnitTypeId.ROBOTICSFACILITY:
                        if self.can_afford(UnitTypeId.IMMORTAL):
                            structure.train(UnitTypeId.IMMORTAL)
            if self.minerals > 500:
                if self.can_afford(UnitTypeId.GATEWAY):
                    await self.build(UnitTypeId.GATEWAY,
                                     near=self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON).random.position.towards(
                                         self.enemy_start_locations[0], distance=10))
                if self.can_afford(UnitTypeId.STARGATE):
                    await self.build(UnitTypeId.STARGATE,
                                     near=self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON).random.position.towards(
                                         self.enemy_start_locations[0], distance=10))
                if self.can_afford(UnitTypeId.ROBOTICSBAY):
                    await self.build(UnitTypeId.STARGATE,
                                     near=self.structures.filter(lambda structure: structure.type_id == UnitTypeId.PYLON).random.position.towards(
                                         self.enemy_start_locations[0], distance=10))

        if build_order[1] < len(build_order[0]):
            print("iteration:", iteration, ", time:", round(self.time, 3), ", supply:", str(self.supply_used) + "/" + str(self.supply_cap),
                  ", m:",
                  self.minerals, ", v:", self.vespene, ", build_order:", build_order[0][build_order[1]], sep="")
        else:
            print("iteration:", iteration, ", time:", round(self.time, 3), ", supply:", str(self.supply_used) + "/" + str(self.supply_cap),
                  ", m:",
                  self.minerals, ", v:", self.vespene, sep="")


sc2.main.run_game(
    sc2.maps.get("AcropolisLE"),
    #[Bot(sc2.data.Race.Protoss, MyBot()), Computer(sc2.data.Race.Zerg, sc2.data.Difficulty.Easy)],
    [Player(sc2.data.Race.Protoss), Bot(sc2.data.Race.Protoss, MyBot())],
    realtime=False,
)
