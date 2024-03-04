from __future__ import annotations

import random
from typing import List, Tuple, TYPE_CHECKING, Optional

import numpy as np  # type: ignore
import tcod
from tcod.map import compute_fov

from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Entity

from actions import Action, MeleeAction, MovementAction, WaitAction, BumpAction, PickupAction, EquipAction, \
    MeleeWeaponAction, LoadAction, RangedWeaponAction, MagicWeaponAction


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

    def item_search(self) -> List[Item]:
        visible_map = compute_fov(self.entity.gamemap.tiles["transparent"], (self.entity.x, self.entity.y),
                                  radius=self.entity.fighter.sight_range, )
        visible_items = []
        for item in self.entity.gamemap.items:
            if visible_map[item.x, item.y]:
                visible_items.append(item)
        return visible_items

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
            dest_x, dest_y = self.path.pop(0)
            dx = dest_x - self.entity.x
            dy = dest_y - self.entity.y
            movement_action = MovementAction(self.entity, dx, dy)
            if self.entity.fighter.actions >= 1 and not self.entity.gamemap.get_actor_at_location(
                    dest_x, dest_y):
                return movement_action.perform()
            else:
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
                    if self.entity.fighter.actions >= 1:
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


class HostileItemUser(HostileEnemy):
    def __init__(self, entity: Actor):
        super().__init__(entity)

    def switch_to_melee(self):
        weapon = self.entity.equipment.weapon
        inventory = self.entity.inventory
        for item in inventory.items:
            if item.equippable:
                if item.equippable.equipment_type == EquipmentType.WEAPON:
                    if item.equippable.type == "Melee":
                        equip_action = EquipAction(self.entity, item)
                        return equip_action.perform()


    def perform(self) -> None:
        weapon = self.entity.equipment.weapon
        # If the enemy has a target, check if it is visible.
        if self.entity.gamemap.get_item_at_location(self.entity.x,self.entity.y) and not self.entity.inventory.is_full:
            item = self.entity.gamemap.get_item_at_location(self.entity.x,self.entity.y)
            if item.equippable:
                if item.equippable.equipment_type == EquipmentType.WEAPON:
                    if item.equippable.type in ["Melee","Ranged","Magic"]:
                        pick_up_action = PickupAction(self.entity)
                        print("Picking up a weapon")
                        return pick_up_action.perform()
                elif item.equippable.equipment_type == EquipmentType.Container:
                    pick_up_action = PickupAction(self.entity)
                    print("Picking up a quiver")
                    return pick_up_action.perform()
            elif item.ammo:
                if weapon:
                    if weapon.equippable.type == "Ranged":
                        if weapon.equippable.category=="Bow":
                            if item.ammo.category == "Arrow":
                                pick_up_action = PickupAction(self.entity)
                                print("Picking up arrows")
                                return pick_up_action.perform()
                        if weapon.equippable.category=="Crossbow":
                            if item.ammo.category == "Bolt":
                                print("Picking up bolt")
                                pick_up_action = PickupAction(self.entity)
                                return pick_up_action.perform()
                        if weapon.equippable.category=="Gun":
                            if item.ammo.category == "Bullet":
                                print("Picking up bullet")
                                pick_up_action = PickupAction(self.entity)
                                return pick_up_action.perform()

        if not weapon and self.entity.inventory:
            for item in self.entity.inventory.items:
                if item.equippable and item.equippable.equipment_type==EquipmentType.WEAPON:
                    if item.equippable.type == "Melee":
                        print("Trying to equip a melee wep")
                        equip_action = EquipAction(self.entity,item)
                        return equip_action.perform()

                    elif item.equippable.type == "Ranged":
                        print("Trying to equip a ranged weapon")
                        equip_action = EquipAction(self.entity, item)
                        return equip_action.perform()

                    elif item.equippable.type == "Magic":
                        print("Trying to equip a magic weapon")
                        equip_action = EquipAction(self.entity, item)
                        return equip_action.perform()

        # If you don't have a quiver, try to equip one
        if weapon and not self.entity.equipment.back:
            for item in self.entity.inventory.items:
                if item.equippable and item.equippable.equipment_type==EquipmentType.Container:
                    print("Tryna load a quiver")
                    equip_action = EquipAction(self.entity, item)
                    return equip_action.perform()
        # You have a ranged weapon? Great! Check if its loaded.
        if weapon and weapon.equippable.type == "Ranged" :
            if weapon.equippable.category == "Bow" and self.entity.equipment.back:
                if not self.entity.equipment.back.equippable.ammo_full:
                    if not self.entity.equipment.back.equippable.items:
                        for item in self.entity.inventory.items:
                            if item.ammo:
                                if item.ammo.category=="Arrow":
                                    load_action = LoadAction(self.entity, item)
                                    print("Hi...")
                                    return load_action.perform()
            elif weapon.equippable.category == "Crossbow":
                if not weapon.equippable.current_ammo:
                    for item in self.entity.inventory.items:
                        if item.ammo:
                            if item.ammo.category == "Bolt":
                                load_action = LoadAction(self.entity, item)
                                print("Hi there!")
                                return load_action.perform()
            elif weapon.equippable.category == "Gun":
                if not weapon.equippable.current_ammo:
                    for item in self.entity.inventory.items:
                        if item.ammo:
                            if item.ammo.category == "Bullet":
                                load_action = LoadAction(self.entity, item)
                                print("Hi")
                                return load_action.perform()




        if self.has_target():
            if self.target_is_visible():
                # Now that we've established that the enemy has a target, we now have something to consider
                # What type of weapon does the enemy have, if it has any at all?
                if not weapon:
                    dx = self.target.x - self.entity.x
                    dy = self.target.y - self.entity.y
                    distance = max(abs(dx), abs(dy))
                    # If close to target
                    if distance <= 1:
                        melee_action = MeleeAction(self.entity, dx, dy)
                        if self.entity.fighter.actions >= 1:
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
                    # We do in fact have a weapon. Let's check if its a melee weapon.
                    if weapon.equippable.type == "Melee":
                        # We have a melee weapon. This is essentially the same as the default behaaviour so we copy and paste.
                        dx = self.target.x - self.entity.x
                        dy = self.target.y - self.entity.y
                        distance = max(abs(dx), abs(dy))
                        # If close to target
                        if distance <= 1:
                            melee_action = MeleeWeaponAction(self.entity, dx, dy)
                            if self.entity.fighter.actions >= 1:
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
                    elif weapon.equippable.type == "Ranged":
                        dx = self.target.x - self.entity.x
                        dy = self.target.y - self.entity.y
                        distance = max(abs(dx), abs(dy))
                        if distance<=weapon.equippable.range:
                            # Target is in range, stay in place.
                            if weapon.equippable.category == "Bow":
                                # Two cases, no quiver, or quiver but no ammo
                                if not self.entity.equipment.back:
                                    self.switch_to_melee()
                                    print("Don't have a quiver :(")
                                    item_check = self.item_search()
                                    for item in item_check:
                                        if item.equippable:
                                            if item.equippable.equipment_type == EquipmentType.Container:
                                                self.set_target(item)
                                                self.approach_map.set_goal_points([self.target])
                                                self.set_path(self.approach_map.get_path_to())
                                                return self.move_along_path()
                                    self.set_path(self.get_path_to_nearest_room())
                                    return self.move_along_path()
                                elif self.entity.equipment.back and not self.entity.equipment.back.equippable.items:
                                    self.switch_to_melee()
                                    print("Rip my arrows")
                                    item_check = self.item_search()
                                    for item in item_check:
                                        if item.ammo:
                                            if item.ammo.category == "Arrow":
                                                self.set_target(item)
                                                self.approach_map.set_goal_points([self.target])
                                                self.set_path(self.approach_map.get_path_to())
                                                return self.move_along_path()
                                    self.set_path(self.get_path_to_nearest_room())
                                    return self.move_along_path()

                            else:
                                if not weapon.equippable.current_ammo:
                                    self.switch_to_melee()
                                    print("Where's the damn ammo?")
                                    item_check = self.item_search()
                                    for item in item_check:
                                        if item.ammo:
                                            if weapon.equippable.category == "Crossbow":
                                                if item.ammo.category == "Bolt":
                                                    self.set_target(item)
                                                    self.approach_map.set_goal_points([self.target])
                                                    self.set_path(self.approach_map.get_path_to())
                                                    return self.move_along_path()
                                            elif weapon.equippable.category == "Gun":
                                                if item.ammo.category == "Bullet":
                                                    self.set_target(item)
                                                    self.approach_map.set_goal_points([self.target])
                                                    self.set_path(self.approach_map.get_path_to())
                                                    return self.move_along_path()
                                    self.set_path(self.get_path_to_nearest_room())
                                    return self.move_along_path()


                            ranged_action = RangedWeaponAction(self.entity, self.target.x,self.target.y)
                            if self.entity.fighter.actions >= 1:
                                return ranged_action.perform()
                            else:
                                return WaitAction(self.entity).perform()
                        # If not close but enemy has a path and the target is visible, move along the path.
                        self.approach_map.set_goal_points([self.target])
                        self.set_path(self.approach_map.get_path_to())
                        if self.path:
                            return self.move_along_path()
                        else:
                            return WaitAction(self.entity).perform()
                    elif weapon.equippable.type == "Magic":
                        print("I have magic")
                        dx = self.target.x - self.entity.x
                        dy = self.target.y - self.entity.y
                        distance = max(abs(dx), abs(dy))
                        mp_cost = weapon.equippable.mp_cost
                        print("My MP", self.entity.fighter.mp)
                        if weapon.equippable.category=="Staff":
                            if distance <= 1:
                                print("I want to melee for whatever reason")
                                if weapon.equippable.can_melee:
                                    melee_action = MeleeWeaponAction(self.entity, dx, dy)
                                    if self.entity.fighter.actions >= 1:
                                        return melee_action.perform()
                                    else:
                                        return WaitAction(self.entity).perform()
                            else:
                                print("Using magic with staff")
                                magic_action = MagicWeaponAction(self.entity,self.target.x,self.target.y)
                                if self.entity.fighter.mp >= mp_cost and self.entity.fighter.actions >= 1:
                                    print("I was able to use da magic with ma staff")
                                    return magic_action.perform()
                                elif self.entity.fighter.mp<mp_cost:
                                    print("No MP for staff :(")
                                    print("Dagger time ig")
                                    self.switch_to_melee()
                                    self.set_path(self.get_path_to_nearest_room())
                                    return self.move_along_path()
                                else:
                                    self.set_path(self.get_path_to_nearest_room())
                                    return self.move_along_path()

                        elif weapon.equippable.category == "Orb":
                            if distance <= 1:
                                print("Yeah no, I ain't dealin with this")
                                self.switch_to_melee()
                                self.set_path(self.get_path_to_nearest_room())
                                return self.move_along_path()
                            else:
                                print("What some of me magic?")
                                magic_action = MagicWeaponAction(self.entity,self.target.x,self.target.y)
                                if self.entity.fighter.mp >= mp_cost and self.entity.fighter.actions >= 1:
                                    print("Heck yeah take that")
                                    return magic_action.perform()
                                elif self.entity.fighter.mp<mp_cost:
                                    print("Shit I'm switching")
                                    self.switch_to_melee()
                                    self.set_path(self.get_path_to_nearest_room())
                                    return self.move_along_path()
                                else:
                                    self.set_path(self.get_path_to_nearest_room())
                                    return self.move_along_path()






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
            # However, first let's see if there are any items. If there are, let's move towards them.
            # For now we only want to know if these items are equippable, and if they are melee weapons.
            if not self.entity.inventory.is_full:
                weapon_list = ["Melee","Ranged","Magic"]
                for item in self.entity.inventory.items:
                    if item.equippable:
                        if item.equippable.equipment_type==EquipmentType.WEAPON:
                            if item.equippable.type == "Melee":
                                if "Melee" in weapon_list:
                                    weapon_list.remove("Melee")
                            elif item.equippable.type == "Ranged":
                                if "Ranged" in weapon_list:
                                    weapon_list.remove("Ranged")
                            elif item.equippable.type == "Magic":
                                if "Magic" in weapon_list:
                                    weapon_list.remove("Magic")
                item_check = self.item_search()
                for item in item_check:
                    if item.equippable:
                        if item.equippable.equipment_type == EquipmentType.WEAPON:
                            if item.equippable.type in weapon_list:
                                self.set_target(item)
                                self.approach_map.set_goal_points([self.target])
                                self.set_path(self.approach_map.get_path_to())
                                return self.move_along_path()
            if random.random() < 0.5:
                return WaitAction(self.entity).perform()
            else:
                if not self.path:
                    self.set_path(self.get_path_to_nearest_room())
                return self.move_along_path()
