from __future__ import annotations

import random
from typing import List, Tuple, TYPE_CHECKING, Optional, Type, Union

import numpy as np  # type: ignore
import tcod
from tcod.map import compute_fov

import actions
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Entity, Item

from actions import Action, MeleeAction, MovementAction, WaitAction, BumpAction
from abc import ABC, abstractmethod


class BaseAI(Action):

    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []
        self.approach_map = ApproachMap(entity)
        self.flee_map = FleeMap(entity)  # Not used in HostileEnemy, but useful in other AIs

    def vision_compute(self) -> List[Entity]:
        visible_map = self.return_visible_map()
        visible_entities = []
        for entity in self.entity.gamemap.entities:
            if visible_map[entity.x, entity.y]:
                visible_entities.append(entity)
        return visible_entities

    def return_visible_map(self):
        return compute_fov(self.entity.gamemap.tiles["transparent"], (self.entity.x, self.entity.y),
                           radius=self.entity.fighter.sight_range, )

    def actors_search(self) -> List[Actor]:
        visible_map = compute_fov(self.entity.gamemap.tiles["transparent"], (self.entity.x, self.entity.y),
                                  radius=self.entity.fighter.sight_range, )
        visible_actors = []
        for actor in self.entity.gamemap.actors:
            if visible_map[actor.x, actor.y] and actor is not self.entity:
                visible_actors.append(actor)
        return visible_actors

    def detect_player(self) -> Actor or None:
        for actor in self.actors_search():
            if actor == self.entity.gamemap.engine.player:
                return actor
        return

    def has_path(self) -> bool:
        return bool(self.path)

    def set_path(self, new_path: List[Tuple[int, int]]) -> None:
        if new_path:
            self.path = new_path

    def clear_path(self) -> None:
        self.path.clear()

    def get_next_path_destination(self) -> Tuple[int, int]:
        if self.path:
            return self.path[0]
        return self.entity.x, self.entity.y

    def move_along_path(self) -> None:
        if self.path:
            dest_x, dest_y = self.path[0]
            dx = dest_x - self.entity.x
            dy = dest_y - self.entity.y
            movement_action = MovementAction(self.entity, dx, dy)
            if self.entity.fighter.time >= movement_action.time_cost and not self.entity.gamemap.get_actor_at_location(
                    dest_x, dest_y):
                self.path.pop(0)
                return movement_action.perform()
            else:
                self.clear_path()
                return WaitAction(self.entity).perform()

    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]] or None:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an enitiy blocks movement and the cost isn't zero (blocking.)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        if path:
            return [(index[0], index[1]) for index in path]
        if not path:
            return WaitAction(self.entity).perform()


class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []
        self.target: Optional[Actor] = None
        self.approach_map.entity = self.entity
        self.flee_map.entity = self.entity

    def set_target(self, target: Actor) -> None:
        self.target = target

    def forget_target(self) -> None:
        self.target = None

    def has_target(self) -> bool:
        return self.target is not None

    def target_is_visible(self) -> bool:
        if self.target in self.actors_search():
            return True
        return False

    def perform(self) -> None:
        # If the enemy has a target, check if it is visible.
        if self.has_target():
            if self.target_is_visible():
                dx = self.target.x - self.entity.x
                dy = self.target.y - self.entity.y
                distance = max(abs(dx), abs(dy))
                # If close to target
                if distance <= 1:
                    melee_action = MeleeAction(self.entity, dx, dy)
                    if self.entity.fighter.time >= melee_action.time_cost:
                        return melee_action.perform()
                    else:
                        return WaitAction(self.entity).perform()
                # If not close but enemy has a path and the target is visible, move along the path.
                self.approach_map.set_goal_points([self.target])
                self.set_path(self.approach_map.get_path_to())
                if self.path:
                    return self.move_along_path()
                else:
                    return WaitAction(self.entity).perform()
            else:
                if self.has_path():
                    return self.move_along_path()
                else:
                    self.forget_target()
                    # If the enemy doesn't have a path, it will wait or move to the nearest room.
                    if random.random() < 0.5:
                        return WaitAction(self.entity).perform()
                    else:
                        self.set_path(self.get_path_to_nearest_room())
                        return self.move_along_path()
        # If the enemy doesn't have a target, look for the player.
        self.set_target(self.detect_player())

        if self.has_target():
            self.approach_map.set_goal_points([self.target])
            self.set_path(self.approach_map.get_path_to())
            return self.move_along_path()
        else:
            # If the enemy couldn't find a target (player) or a path to it, it will wait or move to the nearest room.
            if random.random() < 0.5:
                return WaitAction(self.entity).perform()
            else:
                if not self.path:
                    self.set_path(self.get_path_to_nearest_room())
                return self.move_along_path()

    def get_path_to_nearest_room(self) -> List[Tuple[int, int]]:
        room = random.choice(self.entity.gamemap.rooms)
        return self.get_path_to(*room.center)
        # Implement the logic to calculate and return the path to the nearest room.
        # You can use your existing pathfinding method in the BaseAI class to achieve this.
        # Return an empty list if no valid path is found.
        pass  # Replace this with your implementation.


class FleeingAI(HostileEnemy):
    def perform(self) -> None:
        if self.has_target():
            if self.target_is_visible():
                # Calculate fleeing path using the FleeMap
                self.flee_map.set_goal_points([self.target])
                self.set_path(self.flee_map.get_flee_path_from())
                if self.path:
                    return self.move_along_path()
                else:
                    return WaitAction(self.entity).perform()
            else:
                if self.path:
                    return self.move_along_path()
                else:
                    self.forget_target()
                    # If the enemy doesn't have a path then it should believe it has evaded its pursuer,
                    # It will wait or move to the nearest room.
                    if random.random() < 0.5:
                        return WaitAction(self.entity).perform()
                    else:
                        self.set_path(self.get_path_to_nearest_room())
                        return self.move_along_path()
        # If the enemy doesn't have a target, look for the player.
        self.set_target(self.detect_player())
        if self.has_target():
            # Calculate fleeing path using the FleeMap
            self.flee_map.set_goal_points([self.target])
            self.set_path(self.flee_map.get_flee_path_from())
            if self.path:
                return self.move_along_path()
        else:
            # If the enemy couldn't find a target (player) or a path to it, it will wait or move to the nearest room.
            if random.random() < 0.5:
                return WaitAction(self.entity).perform()
            else:
                if not self.path:
                    self.set_path(self.get_path_to_nearest_room())
                return self.move_along_path()


class ApproachMap:
    def __init__(self, entity: Actor, cost_coefficient: int = 10):
        self.entity = entity
        self.cost_coefficient = cost_coefficient
        self.cost_map = tcod.path.maxarray((2, 2), dtype=np.int32, order="F")
        self.goal_points = []
        self.approach_map = tcod.path.maxarray((2, 2), dtype=np.int32, order="F")

    # Generates the cost_map
    def generate_cost_map(self) -> np.ndarray:
        # Copy the walkable array.
        cost = np.array(np.where(self.entity.gamemap.tiles["walkable"], 1, 0), dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an parent blocks movement and the cost isn't zero (blocking).
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                cost[entity.x, entity.y] += self.cost_coefficient

        return cost

    # Generates the distance map based on current goal_points.
    def generate_map(self) -> np.ndarray:
        dist = tcod.path.maxarray(self.cost_map.shape, dtype=np.int32, order="F")

        if self.goal_points:
            for target in self.goal_points:
                dist[target.x, target.y] = 0

        tcod.path.dijkstra2d(dist, self.cost_map, 1, 2, out=dist)
        return dist

    # Processes the map and returns the given path.
    def process_map(self, dist: np.ndarray) -> List[Tuple[int, int]]:
        path = tcod.path.hillclimb2d(dist, (self.entity.x, self.entity.y), True, True)
        return path.tolist()[1:]

    # Updates the map whenever the goal points change. A new map will be calculated regardless. Process the map.
    def get_path_to(self, targets: List[Optional[Actor]] = None, coefficient: int = None) -> List[Tuple[int, int]]:
        self.update_map(targets, coefficient)
        path = self.process_map(self.approach_map)
        return [(index[0], index[1]) for index in path]

    def set_cost_coefficient(self, cost_coefficient: int) -> None:
        self.cost_coefficient = cost_coefficient

    def set_goal_points(self, targets: List[Optional[Actor]]) -> None:
        self.cost_map = self.generate_cost_map()
        self.goal_points = targets
        self.approach_map = self.generate_map()

    # Updates the map for ease of getting paths.
    def update_map(self, targets: List[Optional[Actor]] = None, coefficient: int = None) -> None:
        if coefficient:
            self.set_cost_coefficient(coefficient)
        if targets:
            self.set_goal_points(targets)
        else:
            self.approach_map = self.generate_map()


class FleeMap(ApproachMap):
    def __init__(self, entity: Actor, cost_coefficient: int = 10):
        super().__init__(entity, cost_coefficient)
        self.flee_map = tcod.path.maxarray((2, 2), dtype=np.int32, order="F")

    def set_flee_map(self, targets: List[Optional[Actor]] = None, coefficient: int = None) -> np.ndarray:
        self.update_map(targets, coefficient)

        # Generate the inverse map by multiplying every value in the approach map with a negative coefficient.
        dist = self.approach_map * -1.2
        dist = dist.astype(np.int64)

        # Recalculate the distances using Dijkstra's algorithm.
        tcod.path.dijkstra2d(dist, self.cost_map, 1, 2, out=dist)

        return dist

    def get_flee_path_from(self, targets: List[Optional[Actor]] = None, coefficient: int = None) -> List[
        Tuple[int, int]]:
        self.flee_map = self.set_flee_map(targets, coefficient)
        path = self.process_map(self.flee_map)
        return [(index[0], index[1]) for index in path]


class GeneralAI(FleeingAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []
        self.target: Optional[Actor] = None
        self.approach_map.entity = self.entity
        self.flee_map.entity = self.entity
        self.item = None
        self.state = "Hostile"

    def hostile_actors(self):
        actors = self.actors_search()
        hostile = set()
        f = self.entity.faction_manager
        for actor in actors:
            af = actor.faction_manager
            for faction in af.member_factions:
                if faction in f.hostile_factions:
                    hostile.add(actor)
            for faction in f.member_factions:
                if faction in af.hostile_factions:
                    hostile.add(actor)
        return list(hostile)

    def random_hostile(self):
        if self.hostile_actors():
            return random.choice(self.hostile_actors())
    def perform(self) -> None:
        if self.state == "Fleeing":
            if self.has_target():
                if self.target_is_visible():
                    # Calculate fleeing path using the FleeMap
                    self.flee_map.set_goal_points([self.target])
                    self.set_path(self.flee_map.get_flee_path_from())
                    if self.path:
                        return self.move_along_path()
                    else:
                        return WaitAction(self.entity).perform()
                else:
                    if self.path:
                        return self.move_along_path()
                    else:
                        self.forget_target()
                        # If the enemy doesn't have a path then it should believe it has evaded its pursuer,
                        # It will wait or move to the nearest room.
                        if random.random() < 0.5:
                            return WaitAction(self.entity).perform()
                        else:
                            self.set_path(self.get_path_to_nearest_room())
                            return self.move_along_path()
            # If the enemy doesn't have a target, look for the player.
            self.set_target(self.random_hostile())
            if self.has_target():
                # Calculate fleeing path using the FleeMap
                self.flee_map.set_goal_points([self.target])
                self.set_path(self.flee_map.get_flee_path_from())
                if self.path:
                    return self.move_along_path()
            else:
                # If the enemy couldn't find a target or a path to it, it will wait or move to the nearest room,
                self.state = "Hostile"
                if random.random() < 0.5:
                    return WaitAction(self.entity).perform()

        elif self.state == "Hostile":
            # If the enemy has a target, check if it is visible.
            if self.has_target():
                if self.target_is_visible():
                    if self.run_away_check():
                        self.state = "Fleeing"
                        self.flee_map.set_goal_points([self.target])
                        self.set_path(self.flee_map.get_flee_path_from())
                        if self.path:
                            return self.move_along_path()
                        else:
                            return WaitAction(self.entity).perform()
                    dx = self.target.x - self.entity.x
                    dy = self.target.y - self.entity.y
                    distance = max(abs(dx), abs(dy))
                    # If close to target
                    if distance <= 1:
                        melee_action = MeleeAction(self.entity, dx, dy)
                        if self.entity.fighter.time >= melee_action.time_cost:
                            return melee_action.perform()
                        else:
                            return WaitAction(self.entity).perform()
                    # If not close but enemy has a path and the target is visible, move along the path.
                    self.approach_map.set_goal_points([self.target])
                    self.set_path(self.approach_map.get_path_to())
                    if self.path:
                        return self.move_along_path()
                    else:
                        return WaitAction(self.entity).perform()
                else:
                    if self.has_path():
                        return self.move_along_path()
                    else:
                        self.forget_target()
                        # If the enemy doesn't have a path, it will wait or move to the nearest room.
                        if random.random() < 0.5:
                            return WaitAction(self.entity).perform()
                        else:
                            self.set_path(self.get_path_to_nearest_room())
                            return self.move_along_path()
            # If the enemy doesn't have a target, look for the player.
            self.set_target(self.random_hostile())

            if self.has_target():
                self.approach_map.set_goal_points([self.target])
                self.set_path(self.approach_map.get_path_to())
                return self.move_along_path()
            else:
                # If the enemy couldn't find a target (player) or a path to it, it will wait or move to the nearest room.
                if random.random() < 0.5:
                    return WaitAction(self.entity).perform()
                else:
                    if not self.path:
                        self.set_path(self.get_path_to_nearest_room())
                    return self.move_along_path()

    def run_away_check(self):
        if self.entity.personality.has_trait("Fearful"):
            chance = random.randint(1, 100)
            if self.entity.personality.get_trait_value("Fearful") > chance:
                return True
            else:
                return False

    def get_path_to_nearest_room(self) -> List[Tuple[int, int]]:
        room = random.choice(self.entity.gamemap.rooms)
        return self.get_path_to(*room.center)
        # Implement the logic to calculate and return the path to the nearest room.
        # You can use your existing pathfinding method in the BaseAI class to achieve this.
        # Return an empty list if no valid path is found.
        pass  # Replace this with your implementation.


# TODO: Implement Desire Driven Dijkstra maps.
# TODO: Consider an AI State Machine

class ConfusedEnemy(BaseAI):
    """
    A confused enemy will stumble around aimlessly for a given number of turns, then revert back to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack.
    """

    def __init__(
            self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} is no longer confused."
            )
            self.entity.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # Its possible the actor will just bump into the wall, wasting a turn.
            return BumpAction(self.entity, direction_x, direction_y, ).perform()

# class GeneralAI(HostileEnemy):
#     def __init__(self, entity: Actor):
#         super().__init__(entity)
#         self.item = None
#         self.state = "Wander"
#         self.timer = -1
#
#     def select_target(self) -> Actor | None:
#
#         # Implement the logic to select a suitable target based on AI's behavior
#         # This could involve checking visible actors, their factions, and other factors
#         hostile_actors = self.hostile_actors()
#         if self.entity in self.entity.gamemap.engine.player.ai.vision_compute() and hostile_actors:
#             print("Hostile Actors:", [x.name for x in hostile_actors ])
#         # If there are hostile actors, choose one as the target
#         if hostile_actors:
#             return random.choice(hostile_actors)
#
#         return None  # No suitable target found
#
#     def execute_approach(self):
#         # If not close but enemy has a path and the target is visible, move along the path.
#         self.approach_map.set_goal_points([self.target])
#         self.set_path(self.approach_map.get_path_to())
#         if self.path:
#             return self.move_along_path()
#         else:
#             return WaitAction(self.entity).perform()
#
#     def hostile_actors(self):
#         f = self.entity.faction_manager
#         actors = self.actors_search()
#         hostile_actors = []
#         for actor in actors:
#             if actor.name == self.entity.name:
#                 continue
#             else:
#                 hostile_actors.append(actor)
#         return hostile_actors
#
#     def execute_attack(self):
#         dx = self.target.x - self.entity.x
#         dy = self.target.y - self.entity.y
#         distance = max(abs(dx), abs(dy))
#         # If close to target
#         if distance <= 1:
#             melee_action = MeleeAction(self.entity, dx, dy)
#             if self.entity.fighter.time >= melee_action.time_cost:
#                 return melee_action.perform()
#             else:
#                 return WaitAction(self.entity).perform()
#         else:
#             self.execute_approach()
#
#     def execute_flee(self):
#         # Calculate fleeing path using the FleeMap
#         self.flee_map.set_goal_points([self.target])
#         self.set_path(self.flee_map.get_flee_path_from())
#         if self.path:
#             return self.move_along_path()
#         else:
#             return WaitAction(self.entity).perform()
#
#     def run_away_check(self):
#         if self.entity.personality.has_trait("Fearful"):
#             chance = random.randint(1, 100)
#             if self.entity.personality.get_trait_value("Fearful") > chance:
#                 return True
#         else:
#             return False
#
#     def perform(self) -> None:
#         if self.has_target():
#             if self.target_is_visible():
#                 if self.run_away_check() or self.state == "Flee":
#                     print("RUN")
#                     self.execute_flee()
#                 else:
#                     self.execute_attack()
#             else:
#                 self.forget_target()
#                 if self.path:
#                     self.move_along_path()
#                 else:
#                     self.clear_path()
#         self.set_target(self.select_target())
#         if self.has_target():
#             if self.run_away_check() or self.state == "Flee":
#                 self.state = "Flee"
#                 self.execute_flee()
#             else:
#                 self.state = "Combat"
#                 self.execute_attack()
#         if self.state == "Wander":
#             if self.timer > 0:
#                 self.timer -= 1
#                 return WaitAction(self.entity).perform()
#             else:
#                 if not self.has_path():
#                     self.set_path(self.get_path_to_nearest_room())
#                 else:
#                     return self.move_along_path()
#
#         else:
#             self.state = "Wander"
#             self.timer = random.randint(1, 5)
#             return WaitAction(self.entity).perform()

# # Step 2: Check if the entity has a weapon and preference
# has_weapon = self.entity.equipment.weapon
# prefers_weapon = (
#         not self.entity.personality.has_preference("no_weapon")
#         and not has_weapon
# )
# if prefers_weapon:
#     # Step 3: Search for weapons based on preferences
#     visible_items = self.visible_items()
#     visible_weapons = [item for item in visible_items if item.equippable.equipment_type == EquipmentType.WEAPON]
#     melee, ranged, magic = self.filter_weapons_by_type(visible_weapons)
#     preference_weapons = self.filter_preference_weapons(melee, ranged, magic)
#
#     if not preference_weapons:
#         if self.entity.personality.has_trait("Fearful"):
#             if self.calculate_run_probability():
#                 return self.entity.ai.transition_to_state(IdleState)
#     else:
#         chosen_weapon_type = self.choose_weapon_type(preference_weapons)
#         weapon = random.choice(chosen_weapon_type)
#
#

# def select_target(self) -> Actor | None:
#     # Implement the logic to select a suitable target based on AI's behavior
#     # This could involve checking visible actors, their factions, and other factors
#     hostile_actors = self.hostile_actors()
#     # If there are hostile actors, choose one as the target
#     if hostile_actors:
#         return random.choice(hostile_actors)
#
#     return None  # No suitable target found
#
# def filter_preference_weapons(self, melee, ranged, magic):
#     preference_weapons = []
#     if self.entity.personality.has_preference("melee_weapon"):
#         preference_weapons.extend(melee)
#     if self.entity.personality.has_preference("ranged_weapon"):
#         preference_weapons.extend(ranged)
#     if self.entity.personality.has_preference("magic_weapon"):
#         preference_weapons.extend(magic)
#     return preference_weapons
#
# @staticmethod
# def filter_weapons_by_type(visible_items: List[Item]):
#     melee_list, ranged_list, magic_list = [], [], []
#     weapon_types = ["melee", "ranged", "magic"]
#     for weapon_type in weapon_types:
#         for item in visible_items:
#             if item.equippable.type == weapon_type:
#                 if weapon_type == "melee":
#                     melee_list.append(item)
#                 elif weapon_type == "ranged":
#                     ranged_list.append(item)
#                 elif weapon_type == "magic":
#                     magic_list.append(item)
#     return melee_list, ranged_list, magic_list
#
# def calculate_run_probability(self):
#     num = random.randint(1, 100)
#     if num >= self.entity.personality.get_trait_value("Fearful"):
#         return True
#
# def choose_weapon_type(self, preference_weapons):
#     melee, ranged, magic = self.filter_weapons_by_type(preference_weapons)
#     preference_list = [key for key in self.entity.personality.preferences if "weapon" in key]
#     preference_weights = [value for key, value in self.entity.personality.preferences.items() if "weapon" in key]
#     choice = random.choices(preference_list, preference_weights)
#     b = choice.pop()
#     if b == "melee_weapon":
#         return random.choice(melee)
#     elif b == "ranged_weapon":
#         return random.choice(ranged)
#     elif b == "magic_weapon":
#         return random.choice(magic)
