from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Optional

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity, Actor, Item


class Action:
    def __init__(self, entity: Actor, time_cost: float | int = 0) -> None:
        super().__init__()
        self.entity = entity
        self.time_cost = time_cost

    @property
    def cost(self) -> float:
        return self.time_cost

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.parent` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()


class TakeDownStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.move_down()
            self.engine.message_log.add_message(
                "You descend the staircase.", color.descend
            )
            self.entity.fighter.time = self.entity.fighter.max_time
        elif (self.entity.x, self.entity.y) == self.engine.game_map.upstairs_location:
            raise exceptions.Impossible("Wrong stairs.")
        else:
            raise exceptions.Impossible("There are no stairs here.")


class TakeUpStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.upstairs_location:
            self.engine.game_world.move_up()
            self.engine.message_log.add_message(
                "You ascend the staircase.", color.descend
            )
        elif (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            raise exceptions.Impossible("Wrong stairs.")
        else:
            raise exceptions.Impossible("There are no stairs here.")


class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int, time_cost: int = 0):
        super().__init__(entity, time_cost=time_cost)
        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking parent at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()


class WaitAction(Action):
    def perform(self) -> None:
        self.time_cost = self.entity.fighter.time
        self.entity.fighter.time = 0
        # if self.entity == self.engine.player:
        #     self.engine.message_log.add_message(
        #         f"{self.entity.name} waits, ending their turn.", color.white
        #     )


class MovementAction(ActionWithDirection):
    def __init__(self, entity: Actor, dx: int, dy: int) -> None:
        super().__init__(entity, dx, dy, time_cost=4)

    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)
        self.entity.fighter.time = self.entity.fighter.time - self.time_cost


class MeleeAction(ActionWithDirection):
    def __init__(self, entity: Actor, dx: int, dy: int) -> None:
        super().__init__(entity, dx, dy, time_cost=5)

    def perform(self) -> None:
        target = self.target_actor

        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk
        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.hp -= damage
            if not target.is_alive and target is not self.engine.player:
                self.entity.level.add_xp(target.level.xp_given)
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )
        self.entity.fighter.time = self.entity.fighter.time - self.time_cost


class MeleeWeaponAction(ActionWithDirection):
    def __init__(self, entity, dx, dy):
        super().__init__(entity, dx, dy, time_cost=entity.equipment.weapon.equippable.time_cost)

    def perform(self) -> None:
        target = self.target_actor

        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        damage = self.entity.equipment.weapon.equippable.roll_damage() + self.entity.fighter.power - target.fighter.defense

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.hp -= damage
            if not target.is_alive and target is not self.engine.player:
                self.entity.level.add_xp(target.level.xp_given)
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )

        self.entity.fighter.time -= self.time_cost


class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        self.time_cost = 0
        weapon_action = MeleeWeaponAction(self.entity,self.dx,self.dy)
        melee_action = MeleeAction(self.entity, self.dx, self.dy)
        movement_action = MovementAction(self.entity, self.dx, self.dy)
        if self.target_actor:
            if self.entity.equipment.weapon and self.entity.equipment.weapon.equippable.attack_type =="melee":
                if self.entity.fighter.time >= weapon_action.time_cost:
                    return weapon_action.perform()
                else:
                    if self.entity.fighter.time >= melee_action.time_cost:
                        return melee_action.perform()
            else:
                raise exceptions.Impossible("You do not have enough time.")

        else:
            if self.entity.fighter.time >= movement_action.time_cost:
                return movement_action.perform()
            else:
                raise exceptions.Impossible("You do not have enough time.")


class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity, time_cost=0.5)

        self.item = item

    def perform(self) -> None:
        if self.entity.fighter.time >= self.cost:
            self.entity.equipment.toggle_equip(self.item)
            self.entity.fighter.time = self.entity.fighter.time - self.cost
        else:
            raise exceptions.Impossible("You don't have enough time.")


class ItemAction(Action):
    def __init__(
            self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity, time_cost=0)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            if self.entity.fighter.time >= self.item.consumable.time_cost:
                if self.item in self.entity.inventory.items:
                    self.item.consumable.activate(self)
                else:
                    exceptions.Impossible(f"Item exhausted.")
            else:
                raise exceptions.Impossible(f"Not enough time to proceed.")


class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity, time_cost=0.5)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory
        if self.entity.fighter.time >= self.cost:
            for item in self.engine.game_map.items:
                if actor_location_x == item.x and actor_location_y == item.y:
                    if len(inventory.items) >= inventory.capacity:
                        raise exceptions.Impossible("Your inventory is full.")

                    self.engine.game_map.entities.remove(item)
                    item.parent = self.entity.inventory
                    inventory.items.append(item)

                    self.engine.message_log.add_message(f"You picked up the {item.name}!")
                    self.entity.fighter.time = self.entity.fighter.time - self.cost
                    return
        else:
            raise exceptions.Impossible("You do not have enough time.")

        raise exceptions.Impossible("There is nothing here to pick up.")


class DropItem(ItemAction):
    def perform(self) -> None:
        self.time_cost = 0.1
        if self.entity.fighter.time >= self.cost:
            if self.entity.equipment.item_is_equipped(self.item):
                self.entity.equipment.toggle_equip(self.item)
            self.entity.inventory.drop(self.item)
        else:
            raise exceptions.Impossible("You do not have enough time.")
