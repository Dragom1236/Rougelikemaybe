from __future__ import annotations

import copy
import random
from typing import TYPE_CHECKING, Dict, List, Optional

import actions
from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Item, Actor
    from enchantment import Enchantment
    from components.SkillComponent import Skill, ActiveSkill


class Equippable(BaseComponent):
    parent: Item

    def __init__(self, equipment_type: EquipmentType, rarity: str):
        self.equipment_type = equipment_type
        self.rarity = rarity
        self.enchantments = []  # List of enchantments
        self.combat_rating = 0

    def add_enchantment(self, enchantment: Enchantment) -> None:
        self.enchantments.append(enchantment)

    def remove_enchantment(self, enchantment: Enchantment) -> None:
        if enchantment in self.enchantments:
            self.enchantments.remove(enchantment)
            # Implement logic to handle enchantment removal effects

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating based on the item's properties
        pass


class Weapon(Equippable):
    def __init__(self, rarity: str, damage_dice: tuple[int, int]):
        super().__init__(equipment_type=EquipmentType.WEAPON, rarity=rarity)
        self.damage_dice = damage_dice
        self.can_melee = False

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating based on the weapon's properties
        pass

    def roll_damage(self) -> int:
        """Roll the damage for the weapon."""
        num_dice, num_sides = self.damage_dice
        total_damage = sum(random.randint(1, num_sides) for _ in range(num_dice))
        return total_damage

    def damage_range(self) -> str:
        num_dice, num_sides = self.damage_dice
        damage_range = "{0}-{1}".format(1 * num_dice, num_sides * num_dice)
        return damage_range


class Armor(Equippable):
    def __init__(self, rarity: str, defense_bonus: int):
        super().__init__(equipment_type=EquipmentType.ARMOR, rarity=rarity)
        self.defense_bonus = defense_bonus

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating based on the armor's properties
        pass


class Accessory(Equippable):
    def __init__(self, rarity: str):
        super().__init__(equipment_type=EquipmentType.ACCESSORY, rarity=rarity)

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating based on the accessory's properties
        pass


class MeleeWeapon(Weapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], time_cost: float | int):
        super().__init__(rarity=rarity, damage_dice=damage_dice)
        self.time_cost = time_cost
        self.type = "Melee"
        self.category = None
        self.can_melee = True

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating based on the melee weapon's properties
        pass


class RangedWeapon(Weapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], time_cost: float | int, max_ammo: int,
                 reload_time: float | int, max_distance: int, ):
        super().__init__(rarity=rarity, damage_dice=damage_dice)
        self.time_cost = time_cost
        self.max_ammo = max_ammo
        self.reload_time = reload_time
        self.current_ammo: List[Item] = []
        self.type = "Ranged"
        self.category = None
        self.range = max_distance

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating based on the ranged weapon's properties
        pass

    @property
    def num_of_ammo(self):
        num_ammo = 0
        for ammo in self.current_ammo:
            num_ammo += ammo.ammo.stacks
        return num_ammo

    @property
    def ammo_full(self):
        num_ammo = self.num_of_ammo
        if num_ammo >= self.max_ammo:
            return True
        else:
            return False


class Bow(RangedWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], max_distance: int, ):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=5, max_ammo=1, reload_time=0,
                         max_distance=max_distance)
        self.category = "Bow"

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a bow
        pass


class Gun(RangedWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], max_ammo: int, reload_time: float | int,
                 shot_time: float | int, max_distance: int, ):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=0, max_ammo=max_ammo,
                         reload_time=reload_time, max_distance=max_distance)
        self.shot_time = shot_time
        self.category = "Gun"

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a gun
        pass


class Crossbow(RangedWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], max_distance: int, ):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=2, max_ammo=1, reload_time=3,
                         max_distance=max_distance)
        self.category = "Crossbow"

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a crossbow
        pass


class MagicWeapon(Weapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], time_cost: float, mp_cost: int):
        super().__init__(rarity=rarity, damage_dice=damage_dice)
        self.time_cost = time_cost
        self.type = "Magic"
        self.mp_cost = mp_cost
        self.category = None


class Staff(MagicWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], mp_cost: int):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=5, mp_cost=mp_cost)
        self.can_melee = True
        self.category = "Staff"

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a staff
        pass


class Orb(MagicWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], mp_cost: int):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=4, mp_cost=mp_cost)
        self.category = "Orb"

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for an orb
        pass


class Wand(MagicWeapon):
    def __init__(self, rarity: str, Skills: List[ActiveSkill] | ActiveSkill = None):
        super().__init__(rarity=rarity, damage_dice=(0, 0), time_cost=0, mp_cost=0)
        self.category = "Wand"
        self.skills: Dict[str, ActiveSkill] = {}
        self.active_skill: Optional[ActiveSkill] = None
        skills = copy.deepcopy(Skills)
        if skills:
            if skills is list:
                for skill in skills:
                    self.add_skill(skill)
            else:
                self.add_skill(Skills)
            self.active_skill = list(self.skills.values())[0]

    def add_skill(self, skill: ActiveSkill) -> None:
        # Add a skill to the wand's storage
        self.skills[skill.name] = skill

    def remove_skill(self, skill_name: str) -> None:
        # Remove a skill from the wand's storage
        if skill_name in self.skills:
            del self.skills[skill_name]

    def cycle_active_skill(self, direction: int) -> None:
        # Cycle through active skills by moving in the specified direction.
        # Direction can be 1 (forward) or -1 (backward).
        if self.skills:
            skill_list = list(self.skills.keys())
            current_index = skill_list.index(self.active_skill.name)
            new_index = (current_index + direction) % len(skill_list)
            new_skill_name = skill_list[new_index]
            self.active_skill = self.skills[new_skill_name]

    def update_manager(self, actor: Actor = None):
        if actor:
            for skill in self.skills.values():
                skill.manager = actor.abilities
            if self.active_skill:
                self.active_skill.manager = actor.abilities
        else:
            for skill in self.skills.values():
                skill.manager = None
            if self.active_skill:
                self.active_skill.manager = None

    def update_cooldowns(self):
        for skill in self.skills.values():
            skill.update_cooldowns()

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a wand
        pass

    def activate(self, xy):
        return actions.ExecuteAction(self.parent.parent.parent, self.active_skill, xy)

    def active_unit(self):
        if self.active_skill:
            return self.active_skill.unit

    def roll_damage(self) -> int:
        # Wands don't have damage die, so they can't deal damage.
        return 0


# class Dagger(Equippable):
#     def __init__(self) -> None:
#         super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)
#
#
# class Sword(Equippable):
#     def __init__(self) -> None:
#         super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)
#
#
# class LeatherArmor(Equippable):
#     def __init__(self) -> None:
#         super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1)
#
#
# class ChainMail(Equippable):
#     def __init__(self) -> None:
#         super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3)

class Container(Equippable):
    def __init__(self, rarity: str, capacity: int = 1, category: str = None):
        super().__init__(equipment_type=EquipmentType.Container, rarity=rarity)
        self.capacity = capacity
        self.items: List[Item] = []
        self.category = category

    @property
    def num_of_ammo(self):
        num_ammo = 0
        for ammo in self.items:
            num_ammo += ammo.ammo.stacks
        return num_ammo

    @property
    def ammo_full(self):
        num_ammo = self.num_of_ammo
        if num_ammo >= self.capacity:
            return True
        else:
            return False
