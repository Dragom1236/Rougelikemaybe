from __future__ import annotations

import random
from typing import Type, Tuple, TYPE_CHECKING

from damageType import ElementalType, normal
from entity import Entity, Actor, Item
if TYPE_CHECKING:
    from components.SkillComponent import Skill, ActiveSkill, CombatUnit

class DamageCalculator:
    def __init__(self, attacker: Actor, attack_type: str, defender: Actor = None,
                 weapon: Item = None, skill: ActiveSkill = None, unit: CombatUnit = None,
                 ammo: Item = None):
        self.attacker = attacker
        self.defender = None
        self.unit = None
        self.ammo = None
        if defender:
            self.defender = defender
        self.weapon = None
        self.skill = None
        self.attack_type = attack_type
        self.attacking_damage_type: ElementalType = None
        self.defending_damage_type: Tuple[ElementalType, ElementalType] = (None, None)
        if self.defender:
            self.defending_damage_type: Tuple[ElementalType, ElementalType] = self.defender.elemental_type
        if weapon:
            self.weapon = weapon
            if ammo:
                self.ammo = ammo
        if skill:
            if unit:
                self.skill = skill
                self.unit = unit

    def base_damage(self):
        base_damage = 0
        if self.weapon:
            base_damage += self.weapon.equippable.roll_damage()
        if self.unit:
            base_damage += self.unit.calculate_base_damage(self.unit.damage_components)
        return base_damage

    def attack_bonus(self):
        attack_bonus = 0
        if not self.unit:
            if self.attack_type == "Melee":
                attack_bonus += self.attacker.fighter.strength / 5
            elif self.attack_type == "Magic":
                attack_bonus += self.attacker.fighter.magical_attack
        if self.ammo:
            attack_bonus += self.ammo.ammo.damage
        return attack_bonus

    def crit_chance(self):
        # Calculates the actual critical chance.
        # Currently, not implementing this since I don't have anything that really determines crit chance.
        return 5

    def crit_multi(self):
        # Calculates the critical chance multiplier, not the damage.
        # Does nothing atm since I don't have much that affects the multiplier.
        return 1.5

    def attack_damage_type(self):
        attacking_damage_type = normal
        if self.attack_type == "Ranged":
            if self.ammo:
                self.attacking_damage_type = self.ammo.ammo.damage_type
                return attacking_damage_type
        if self.skill:
            self.attacking_damage_type = self.unit.damage_type
            return attacking_damage_type
        if self.weapon:
            self.attacking_damage_type = self.weapon.equippable.elemental_type
        self.attacking_damage_type = attacking_damage_type

    def total_stab_bonus(self):
        stab_bonus = 1
        if self.attack_type == "Ranged":
            if self.ammo:
                # If the ammo's damage type isn't the same as whatever the main damage type would have been if the mmo weren't in use the stab bonus is forfeited
                if self.skill:
                    if self.ammo.ammo.damage_type.name != self.unit.damage_type.name:
                        return stab_bonus
                elif self.weapon:
                    if self.ammo.ammo.damage_type.name != self.weapon.equippable.elemental_type.name:
                        return stab_bonus
        if self.attacking_damage_type.name in [etype.name for etype in self.attacker.elemental_type]:
            stab_bonus += 0.25
        if self.weapon:
            if self.weapon.equippable.elemental_type.name == self.attacking_damage_type.name:
                stab_bonus += 0.25
        if self.skill:
            if self.unit.damage_type.name == self.attacking_damage_type.name:
                stab_bonus += 0.25
        return stab_bonus

    def defending_type_resistance_modifier(self):
        modifier = 1
        if self.defender:
            defending_types = self.defending_damage_type
            dtype1 = defending_types[0]
            dtype2 = defending_types[1]
            atype = self.attacking_damage_type
            if atype.name in dtype1.immunities:
                modifier = 0
            elif atype.name in dtype1.resistances:
                modifier -= 0.25
            elif atype.name in dtype1.weaknesses:
                modifier += 0.25
            if atype.name in dtype2.immunities:
                modifier = 0
            elif atype.name in dtype2.resistances:
                modifier -= 0.25
            elif atype.name in dtype2.weaknesses:
                modifier += 0.25
        return modifier

    def res_modifier(self):
        # Calculates resistance modifier based on defender's armor and skills.
        return 0

    def prof_bonus(self):
        # Calculates modifier based on proficiencies. Value should be a decimal representing a percentage.
        return 0

    def passive_def_modifier(self):
        # returns attack modifiers based on passive skills
        return 0

    def passive_attack_modifier(self):
        # returns attack buffs based on passive skills
        return 0

    def calculate_defensive_value(self):
        defense = 0
        if self.attack_type != "Magic":
            defense += self.defender.fighter.defense_bonus
        else:
            defense += 0  # This will eventually correspond to the magical defense part of an armor
        return defense

    def calculate_damage(self, simulate: bool = False):
        # Calculates damage. If simulate is set to True, it will not try to return final damage for a critical hit.
        # Extract relevant information from attacker and defender
        self.attack_damage_type()
        final_damage = self.base_damage()
        base_damage = self.base_damage()
        primary_attack_bonus = self.attack_bonus()
        attack_muliplier = self.calculate_secondary_attack_bonus()
        stab_bonus = self.total_stab_bonus()

        base_critical_hit_chance = self.attacker.fighter.critical_chance
        base_critical_hit_multiplier = self.attacker.fighter.critical_damage
        # armor_value is the only "defense value" you can have. Natural armor counts as defense,
        # and magic armor can grant specific fixed defense values against magic, but that's it.
        # If there's a crit, the defense is divided by halved, then factored in, before crit multi is applied.
        # Also note, if the defender is not provided, then the final damage won't factor in critical damage or defenses
        damage = (base_damage + primary_attack_bonus) * attack_muliplier * stab_bonus
        if self.defender:
            defense = self.calculate_defensive_value()
            defense_multiplier = self.calculate_secondary_defense_bonus()
            defense *= defense_multiplier
            damage *= self.defending_type_resistance_modifier()
        else:
            # Assume simulate is True
            simulate = True
            defense = 0
        if simulate:
            # Calculate without factoring crits
            final_damage = damage - defense
        else:
            # Try to crit:
            if base_critical_hit_chance > 100 or random.randint(1, 100) < base_critical_hit_chance:
                print("Crit")
                final_damage = (damage - (defense / 2)) * base_critical_hit_multiplier
            else:
                final_damage = damage - defense


        # Return the final damage value
        return round(final_damage)

    def calculate_secondary_attack_bonus(self):
        # Calculates bonuses from proficiencies and passive skills and conditions all in one.
        return 1 + self.prof_bonus() + self.passive_attack_modifier()

    def calculate_secondary_defense_bonus(self):
        # Calculates bonuses from proficiencies and passive skills and conditions all in one.
        return 1 + self.res_modifier() + self.passive_def_modifier()
