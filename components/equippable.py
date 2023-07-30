from __future__ import annotations

import copy
import random
from typing import TYPE_CHECKING, Dict, List, Type

from components.base_component import BaseComponent

from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Item
    from enchantment import Enchantment
    from components.SkillComponent import Skill


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
    def __init__(self, rarity: str, damage_dice: tuple[int, int], time_cost: float):
        super().__init__(rarity=rarity, damage_dice=damage_dice)
        self.time_cost = time_cost
        self.attack_type = "melee"

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating based on the melee weapon's properties
        pass


class RangedWeapon(Weapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], time_cost: float, max_ammo: int, reload_time: float):
        super().__init__(rarity=rarity, damage_dice=damage_dice)
        self.time_cost = time_cost
        self.attack_type = "ranged"
        self.max_ammo = max_ammo
        self.reload_time = reload_time
        self.current_ammo = max_ammo

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating based on the ranged weapon's properties
        pass


class Bow(RangedWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int]):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=5, max_ammo=1, reload_time=0)

    def load_ammo(self) -> None:
        # Bows instantly load their ammo, so no additional implementation needed
        pass

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a bow
        pass


class Gun(RangedWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], max_ammo: int, reload_time: float, shot_time: float):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=0, max_ammo=max_ammo,
                         reload_time=reload_time)
        self.shot_time = shot_time

    def load_ammo(self) -> None:
        if self.current_ammo < self.max_ammo:
            self.current_ammo += 1

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a gun
        pass


class Crossbow(RangedWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int]):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=2, max_ammo=1, reload_time=2)

    def load_ammo(self) -> None:
        if self.current_ammo < self.max_ammo:
            self.current_ammo += 1

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a crossbow
        pass


class MagicWeapon(Weapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], time_cost: float, mp_cost: int):
        super().__init__(rarity=rarity, damage_dice=damage_dice)
        self.time_cost = time_cost
        self.attack_type = "magic"
        self.mp_cost = mp_cost


class Staff(MagicWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], mp_cost: int):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=5, mp_cost=mp_cost)

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a staff
        pass


class Orb(MagicWeapon):
    def __init__(self, rarity: str, damage_dice: tuple[int, int], mp_cost: int):
        super().__init__(rarity=rarity, damage_dice=damage_dice, time_cost=4, mp_cost=mp_cost)

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for an orb
        pass


class Wand(MagicWeapon):
    def __init__(self, rarity: str, Skills: List[Skill] | Skill = None):
        super().__init__(rarity=rarity, damage_dice=(0, 0), time_cost=0, mp_cost=0)
        self.skills: Dict[str, Skill] = {}
        skills = copy.deepcopy(Skills)
        if skills:
            if skills is list:
                for skill in skills:
                    self.add_skill(skill)
            else:
                self.add_skill(Skills)

    def add_skill(self, skill: Skill) -> None:
        # Add a skill to the wand's storage
        self.skills[skill.name] = skill

    def remove_skill(self, skill_name: str) -> None:
        # Remove a skill from the wand's storage
        if skill_name in self.skills:
            del self.skills[skill_name]

    def update_combat_rating(self) -> None:
        # Implement logic to calculate the combat rating for a wand
        pass

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
