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


class ActionWithLocation(Action):
    def __init__(self, entity: Actor, x: int, y: int, time_cost: int = 0):
        super().__init__(entity, time_cost=time_cost)
        self.x = x
        self.y = y

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.x, self.y

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
        weapon_action = None
        if self.entity.equipment.weapon:
            if self.entity.equipment.weapon.equippable.type == "Melee" or self.entity.equipment.weapon.equippable.can_melee:
                weapon_action = MeleeWeaponAction(self.entity, self.dx, self.dy)
        melee_action = MeleeAction(self.entity, self.dx, self.dy)
        movement_action = MovementAction(self.entity, self.dx, self.dy)
        if self.target_actor:
            if weapon_action:
                if self.entity.fighter.time >= weapon_action.time_cost:
                    return weapon_action.perform()
                else:
                    raise exceptions.Impossible("You do not have enough time.")
            elif self.entity.equipment.weapon:
                raise exceptions.Impossible("You don't have an appropriate weapon.")
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
                    if item.ammo:
                        exists_ammo = False
                        for existing_item in inventory.items:
                            if item.name == existing_item.name:
                                existing_item.ammo.stacks += item.ammo.stacks
                                exists_ammo = True
                                break
                        if exists_ammo:
                            pass
                        else:
                            item.parent = self.entity.inventory
                            inventory.items.append(item)
                        if item.ammo.stacks > 1:
                            self.engine.message_log.add_message(f"You picked up {item.ammo.stacks} {item.name}s!")
                        else:
                            self.engine.message_log.add_message(f"You picked up the {item.name}!")

                    else:
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


class ExecuteAction(Action):
    def __init__(self, entity, skill, xy=None):
        super().__init__(entity)
        self.skill = skill
        self.xy = xy

    def perform(self):
        if self.entity.fighter.time < self.time_cost:
            raise exceptions.Impossible("Not enough time to use this skill.")
        print(self.skill.remaining_cooldown)
        if self.skill.on_cooldown():
            raise exceptions.Impossible("Skill is on cooldown.")
        if not self.skill.can_afford(self.entity):
            raise exceptions.Impossible("Not enough resources (MP, SP, SE) to use this skill.")
        self.skill.activation(self.xy)


class LoadAction(Action):
    def __init__(self, entity, item):
        super().__init__(entity, time_cost=entity.equipment.weapon.equippable.reload_time)
        self.item = item

    def perform(self):
        weapon = self.entity.equipment.weapon
        ammo = self.item.ammo
        if weapon.equippable.type == "Ranged":
            if weapon.equippable.category == "Bow":
                if ammo.category != "Arrow":
                    raise exceptions.Impossible("Wrong Ammo Type")
                if weapon.equippable.ammo_full:
                    raise exceptions.Impossible("Ammo is already full.")
                if not self.entity.equipment.back:
                    raise exceptions.Impossible("No quiver.")
                if self.entity.equipment.back.equippable.ammo_full:
                    raise exceptions.Impossible("Quiver is fully stocked.")
            elif weapon.equippable.category == "Gun":
                if ammo.category != "Bullet":
                    raise exceptions.Impossible("Wrong Ammo Type.")
                if weapon.equippable.ammo_full:
                    raise exceptions.Impossible("Ammo is already full.")
            elif weapon.equippable.category == "Crossbow":
                if ammo.category != "Bolt":
                    raise exceptions.Impossible("Wrong Ammo Type.")
                if weapon.equippable.ammo_full:
                    raise exceptions.Impossible("Ammo is already full.")
            else:
                raise exceptions.Impossible("Invalid Ranged Weapon Category")
        else:
            raise exceptions.Impossible("You are wielding a non-ranged weapon (or not wielding a weapon).")

        if self.entity.fighter.time < weapon.equippable.reload_time:
            raise exceptions.Impossible("You don't have enough time.")

        # Get the number of ammo needed.
        self.entity.inventory.items.remove(self.item)
        if weapon.equippable.category == "Bow":
            required_ammo = self.entity.equipment.back.equippable.capacity - self.entity.equipment.back.equippable.num_of_ammo
            if ammo.stacks > required_ammo:
                fragment = ammo.fragment(required_ammo)
                self.entity.inventory.items.append(fragment)
            self.entity.equipment.back.equippable.items.append(self.item)
        else:
            required_ammo = weapon.equippable.max_ammo - weapon.equippable.num_of_ammo
            if ammo.stacks > required_ammo:
                fragment = ammo.fragment(required_ammo)
                self.entity.inventory.items.append(fragment)
            weapon.equippable.current_ammo.append(self.item)
            if weapon.equippable.category == "Crossbow":
                self.entity.fighter.time -= weapon.equippable.reload_time
            else:
                self.entity.fighter.time = 0


class RangedWeaponAction(ActionWithLocation):
    def __init__(self, entity, x, y):
        super().__init__(entity, x, y, time_cost=0)

    def perform(self) -> None:
        if not self.entity.has_direct_los(self.x, self.y):
            raise exceptions.Impossible("You don't have a direct line of fire.")
        weapon = self.entity.equipment.weapon
        if weapon and weapon.equippable.type == "Ranged":
            if self.entity.distance(self.x, self.y) > weapon.equippable.range:
                raise exceptions.Impossible("You wouldn't land a shot from this distance.")
            if weapon.equippable.category == "Bow":
                return BowWeaponAction(self.entity, self.x, self.y).perform()
            elif weapon.equippable.category == "Gun":
                return GunWeaponAction(self.entity, self.x, self.y).perform()
            elif weapon.equippable.category == "Crossbow":
                return CrossbowWeaponAction(self.entity, self.x, self.y).perform()

        else:
            raise exceptions.Impossible("You are wielding a non-ranged weapon(or not wielding a weapon).")


class BowWeaponAction(ActionWithLocation):
    def perform(self) -> None:
        self.time_cost = self.entity.equipment.weapon.equippable.time_cost
        if self.entity.fighter.time < self.time_cost:
            raise exceptions.Impossible("Not enough time.")
        if not self.entity.equipment.back:
            raise exceptions.Impossible("No quiver.")
        target = self.target_actor
        print(target)
        if not target:
            raise exceptions.Impossible("Nothing to attack.")
        elif target == self.entity:
            raise exceptions.Impossible("You can't target yourself.")
        for item in self.entity.equipment.back.equippable.items:
            if item.ammo.stacks <= 0:
                self.entity.equipment.back.equippable.items.remove(item)
        if not self.entity.equipment.back.equippable.items:
            raise exceptions.Impossible("No ammo.")
        weapon = self.entity.equipment.weapon
        item = self.entity.equipment.back.equippable.items[0]
        ammo = item.ammo
        ammo.stacks -= 1
        if ammo.stacks <= 0:
            self.entity.equipment.back.equippable.items.remove(item)
        print(ammo)
        damage = weapon.equippable.roll_damage() + ammo.damage - target.fighter.defense
        print("Damage", damage)

        attack_desc = f"{self.entity.name.capitalize()} shoots {target.name}"
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


class CrossbowWeaponAction(ActionWithLocation):
    def perform(self) -> None:
        self.time_cost = self.entity.equipment.weapon.equippable.time_cost
        if self.entity.fighter.time < self.time_cost:
            raise exceptions.Impossible("Not enough time.")
        target = self.target_actor
        print(target)
        if not target:
            raise exceptions.Impossible("Nothing to attack.")
        elif target == self.entity:
            raise exceptions.Impossible("You can't target yourself.")
        weapon = self.entity.equipment.weapon
        for item in weapon.equippable.current_ammo:
            if item.ammo.stacks <= 0:
                self.entity.equipment.weapon.equippable.current_ammo.remove(item)
        if not self.entity.equipment.weapon.equippable.current_ammo:
            raise exceptions.Impossible("No ammo.")
        item = self.entity.equipment.weapon.equippable.current_ammo[0]
        ammo = item.ammo
        ammo.stacks -= 1
        if ammo.stacks <= 0:
            self.entity.equipment.weapon.equippable.current_ammo.remove(item)
        print(ammo)
        damage = weapon.equippable.roll_damage() + ammo.damage - target.fighter.defense
        print("Damage", damage)

        attack_desc = f"{self.entity.name.capitalize()} shoots {target.name}"
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


class GunWeaponAction(ActionWithLocation):
    def perform(self) -> None:
        self.time_cost = self.entity.equipment.weapon.equippable.shot_time
        total_time_cost = 0
        if self.entity.fighter.time < self.time_cost:
            raise exceptions.Impossible("Not enough time.")
        target = self.target_actor
        print(target)
        if not target:
            raise exceptions.Impossible("Nothing to attack.")
        elif target == self.entity:
            raise exceptions.Impossible("You can't target yourself.")
        weapon = self.entity.equipment.weapon
        for item in weapon.equippable.current_ammo:
            if item.ammo.stacks <= 0:
                self.entity.equipment.weapon.equippable.current_ammo.remove(item)
        if not self.entity.equipment.weapon.equippable.current_ammo:
            raise exceptions.Impossible("No ammo.")
        while total_time_cost < self.entity.fighter.time and weapon.equippable.num_of_ammo > 0:
            item = self.entity.equipment.weapon.equippable.current_ammo[0]
            ammo = item.ammo
            ammo.stacks -= 1
            if ammo.stacks <= 0:
                self.entity.equipment.weapon.equippable.current_ammo.remove(item)
            print(ammo)
            damage = weapon.equippable.roll_damage() + ammo.damage - target.fighter.defense
            print("Damage", damage)

            attack_desc = f"{self.entity.name.capitalize()} shoots {target.name}"
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
                    break
            else:
                self.engine.message_log.add_message(
                    f"{attack_desc} but does no damage.", attack_color
                )
            total_time_cost += self.time_cost

        self.entity.fighter.time -= total_time_cost


class MagicWeaponAction(ActionWithLocation):
    def __init__(self, entity, x, y):
        super().__init__(entity, x, y, time_cost=0)

    def perform(self) -> None:
        if not self.entity.has_direct_los(self.x, self.y):
            raise exceptions.Impossible("You don't have a direct line of fire.")
        weapon = self.entity.equipment.weapon
        if weapon and weapon.equippable.type == "Magic":
            if weapon.equippable.category == "Wand":
                weapon.equippable.activate((self.x, self.y))
            else:
                self.time_cost = weapon.equippable.time_cost
                mp_cost = weapon.equippable.mp_cost
                if self.entity.fighter.time < self.time_cost:
                    raise exceptions.Impossible("Not enough time.")
                if self.entity.fighter.mp < mp_cost:
                    raise exceptions.Impossible("Not enough time.")
                target = self.target_actor
                print(target)
                if not target:
                    raise exceptions.Impossible("Nothing to attack.")
                elif target == self.entity:
                    raise exceptions.Impossible("You can't target yourself.")
                damage = weapon.equippable.roll_damage() + self.entity.fighter.magical_attack - target.fighter.magical_defense

                attack_desc = f"{self.entity.name.capitalize()} fires magic energy at {target.name}"
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
                self.entity.fighter.mp -= mp_cost
                self.entity.fighter.time -= self.time_cost

        else:
            raise exceptions.Impossible("You are wielding a non-magic weapon(or not wielding a weapon).")
