from __future__ import annotations

import random
from typing import TYPE_CHECKING, Union, List, Optional

import numpy as np

import actions
from components.base_component import BaseComponent
from damageType import ElementalType
from damagecalc import DamageCalculator
from exceptions import Impossible
from input_handlers import AreaRangedAttackHandler, SingleRangedAttackHandler

if TYPE_CHECKING:
    from entity import Actor
    from components.Status import StatusEffect


class DamageComponent:
    pass


class BaseDamageComponent(DamageComponent):
    def __init__(self, value):
        self.value = value
        self.category = "Base"

    def apply(self, user):
        return self.value


class ScalingDamageComponent(DamageComponent):
    def __init__(self, coefficient, stat, minimum=1):
        self.coefficient = coefficient
        self.stat = stat
        self.minimum = minimum
        self.category = "Scaling"

    def apply(self, user):
        value = self.coefficient * getattr(user.fighter, self.stat)
        if value > self.minimum:
            return value
        else:
            return self.minimum


class StatModComponent(DamageComponent):
    def __init__(self, fixed, divisor, stat, minimum=0):
        self.fixed = fixed
        self.divisor = divisor
        self.stat = stat
        self.minimum = minimum
        self.category = "Modifier"

    def apply(self, user):
        mod = getattr(user.fighter, self.stat) / self.divisor
        if mod > self.minimum:
            return self.fixed * mod
        else:
            return self.fixed * self.minimum


class Skill:
    manager: Abilities

    def __init__(self, name, description, activation_requirements, level=1, experience=0):
        self.name = name
        self.description = description
        self.activation_requirements = activation_requirements
        self.level = level
        self.experience = experience

    def activate(self):
        raise NotImplementedError("Subclasses must override the activate method.")


class Unit:
    owner: Union[Skill]

    def __init__(self, units: List[Union[CombatAoe]] = None, is_child: bool = False):
        self.units = units or None
        self.is_child = is_child
        self.type = None

    @property
    def user(self):
        return self.owner.manager.parent

    @property
    def user_is_player(self):
        if self.user == self.owner.manager.engine.player:
            return True
        else:
            return False

    def set_owners(self):
        if self.units:
            for unit in self.units:
                unit.owner = self.owner
                unit.set_owners()


class CombatUnit(Unit):
    owner: ActiveSkill

    def __init__(self, damage_type: ElementalType,
                 damage_components: List[Union[BaseDamageComponent, ScalingDamageComponent, StatModComponent]],
                 max_damage: int,
                 units: List[Unit] = None,
                 is_ranged=None,
                 is_child=False):
        super().__init__(units, is_child)
        self.max_damage = max_damage
        self.damage_components = damage_components
        self.is_ranged = is_ranged
        self.type = "Combat"
        self.damage_type = damage_type

    def calculate_base_damage(self, damage_components: List[
        Union[BaseDamageComponent, ScalingDamageComponent, StatModComponent]]):
        damage = 0
        for component in damage_components:
            damage += component.apply(self.user)
        if damage > self.max_damage:
            return self.max_damage
        else:
            return damage


class CombatAoe(CombatUnit):
    def __init__(self, damage_type: ElementalType,
                 damage_components: List[Union[BaseDamageComponent, ScalingDamageComponent, StatModComponent]],
                 max_damage: int,
                 units: List[Union[CombatAoe]] = None,
                 is_ranged=None,
                 radius: int = 2, is_child=False):
        super().__init__(damage_type, damage_components, max_damage, units, is_ranged, is_child=is_child)
        self.radius = radius
        self.type = "Combat"

    def get_action(self, xy=None):
        if self.is_ranged:
            if self.user_is_player:
                return AreaRangedAttackHandler(self.user.gamemap.engine,
                                               self.radius,
                                               callback=lambda XY: actions.ExecuteAction(self.user, self.owner,
                                                                                         xy=XY))
            else:
                return actions.ExecuteAction(self.user, self.owner, xy=xy)
        else:
            return actions.ExecuteAction(self.user, self.owner)

    def execute(self, xy=None):
        # Ensuring only ranged AOEs use this logic
        weapon = self.user.equipment.weapon
        if xy and self.is_ranged:
            x, y = xy
            if not self.user.gamemap.visible[xy]:
                raise Impossible("You cannot target an area that you cannot see.")

            targets_hit = False
            for actor in self.user.gamemap.actors:
                if actor.distance(x, y) <= self.radius:
                    if weapon:
                        if weapon.equippable.type != "Magic":
                            weapon = None
                    damageCalc = DamageCalculator(self.user, "Magic", actor, weapon, self.owner, self)
                    damage = damageCalc.calculate_damage()
                    actor.gamemap.engine.message_log.add_message(
                        f"The {actor.name} is engulfed in a fiery explosion, taking {damage} damage!"
                    )
                    actor.fighter.create_damage_log(category="Attack", source_entity=self.user,
                                                    details=f"The {actor.name} is engulfed in a fiery explosion, taking {damage} damage!")
                    actor.fighter.take_damage(damage)
                    targets_hit = True

            if not targets_hit:
                if self.is_child:
                    pass
                else:
                    raise Impossible("There are no targets in the radius.")
            elif self.units:
                for unit in self.units:
                    unit.execute(xy)
        else:
            # If it's a melee AOE, we'll inflict damage to all enemies in the user's reach (within 1 tile).
            for target in self.user.gamemap.actors:
                if target is not self.user and target.is_alive:
                    distance = self.user.distance(target.x, target.y)
                    if distance <= 1:
                        # Since it's melee, defense is used.
                        if weapon:
                            if weapon.equippable.type != "Melee":
                                weapon = None
                        damageCalc = DamageCalculator(self.user, "Melee", target, weapon, self.owner, self)
                        damage = damageCalc.calculate_damage()
                        if damage > 0:
                            target.fighter.create_damage_log(category="Attack", source_entity=self.user,
                                                             details=f"The {target.name} is engulfed in a fiery explosion, taking {damage} damage!")
                            target.fighter.hp -= damage
            if self.units:
                for unit in self.units:
                    unit.execute(xy)
        if not self.is_child:
            self.owner.reset_cooldown()
            self.owner.deduct_costs(self.user)


class CombatSingleTarget(CombatUnit):
    def __init__(self, damage_type: ElementalType,
                 damage_components: List[Union[BaseDamageComponent, ScalingDamageComponent, StatModComponent]],
                 max_damage: int,
                 units: List[Union[CombatAoe]] = None,
                 turn_units: List[Union[CombatAoe]] = None,
                 is_ranged=None, is_child=False, num_hits: int = 1, radius: int = None):
        super().__init__(damage_type, damage_components, max_damage, units, is_ranged, is_child=is_child)
        self.radius = radius
        self.type = "Combat"
        self.turn_units = turn_units
        self.num_hits = num_hits
        if self.radius:
            self.is_ranged = False

    def get_action(self, xy=None):
        if self.is_ranged:
            if self.user_is_player:
                return SingleRangedAttackHandler(self.user.gamemap.engine,
                                                 callback=lambda XY: actions.ExecuteAction(self.user, self.owner,
                                                                                           xy=XY))
            else:
                return actions.ExecuteAction(self.user, self.owner, xy)

        else:
            return actions.ExecuteAction(self.user, self.owner, xy)

    def execute(self, xy=None):
        if xy:
            x, y = xy
            if not self.user.gamemap.visible[xy]:
                raise Impossible("You cannot target an area that you cannot see.")

            target = self.user.gamemap.get_actor_at_location(x, y)
            if target is self.user:
                raise Impossible("You cannot target yourself!")
            if target:
                if target.is_alive:
                    weapon = self.user.equipment.weapon
                    if weapon:
                        if weapon.equippable.type == "Melee":
                            weapon = None
                    damageCalc = DamageCalculator(self.user, "Ranged", target, weapon, self.owner, self)
                    damage = damageCalc.calculate_damage()
                    target.gamemap.engine.message_log.add_message(
                        f"The {target.name} is hit, taking {damage} damage!"
                    )
                    target.fighter.create_damage_log(category="Attack", source_entity=self.user,
                                                     details=f"The {target.name} is engulfed in a fiery explosion, taking {damage} damage!")
                    target.fighter.take_damage(damage)
                if self.units:
                    for unit in self.units:
                        unit.execute(xy)
            else:
                raise Impossible("There is no target at this location.")


        else:
            pass

        if not self.is_child:
            self.owner.reset_cooldown()
            self.owner.deduct_costs(self.user)


#
# class CombatAoe:
#     def __init__(self, is_ranged: bool, can_choose: bool = False, radius: int = 0, damage: int = 0,
#                  status_units: List[StatusUnit] = None):
#         self.is_ranged = is_ranged
#         self.radius = radius
#         self.damage = damage
#         self.status_units = status_units or []
#         self.can_choose = can_choose
#
#     def execute_combat_aoe(self, actor: Actor, xy=None):
#         is_ranged = self.is_ranged
#         radius = self.radius
#         damage = self.damage
#         x, y = (0, 0)
#         if xy:
#             x, y = xy
#             if not actor.gamemap.visible[xy]:
#                 raise Impossible("You cannot target an area that you cannot see.")
#
#             targets_hit = False
#             for actor in actor.gamemap.actors:
#                 if actor.distance(x, y) <= self.radius:
#                     actor.gamemap.engine.message_log.add_message(
#                         f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!"
#                     )
#                     actor.fighter.take_damage(self.damage)
#                     targets_hit = True
#
#             if not targets_hit:
#                 raise Impossible("There are no targets in the radius.")
#
#         elif is_ranged:
#             # If it's a ranged AOE, get a random target within the specified radius.
#             if actor.ai.actors_search():
#                 entity = random.choice(actor.ai.actors_search())
#             else:
#                 return
#             xy = entity.x, entity.y
#             calculated_damage = damage - entity.fighter.defense
#             if calculated_damage > 0:
#                 entity.fighter.hp -= calculated_damage
#                 if not entity.is_alive and entity is not actor.gamemap.engine.player:
#                     actor.level.add_xp(entity.level.xp_given)
#                 if self.status_units:
#                     for status in self.status_units:
#                         status.execute(actor, entity)
#
#             # Apply the AOE attack to all targets within the given radius around the random target's location.
#             for target in actor.gamemap.actors:
#                 if target.distance(*xy) <= radius and target is not actor and target.is_alive:
#                     # Since it's a ranged attack, we will use defense.
#                     calculated_damage = damage - target.fighter.defense
#                     if calculated_damage > 0:
#                         target.fighter.hp -= calculated_damage
#                         if not target.is_alive and target is not actor.gamemap.engine.player:
#                             actor.level.add_xp(target.level.xp_given)
#                         elif self.status_units:
#                             for status in self.status_units:
#                                 status.execute(actor, target)
#
#         else:
#             # If it's a melee AOE, we'll inflict damage to all enemies in the user's reach (within 1 tile).
#             for target in actor.gamemap.actors:
#                 if target is not actor and target.is_alive:
#                     distance = actor.distance(target.x, target.y)
#                     if distance <= 1:
#                         # Since it's melee, defense is used.
#                         calculated_damage = damage - target.fighter.defense
#                         if calculated_damage > 0:
#                             target.fighter.hp -= calculated_damage
#                             if not target.is_alive and target is not actor.gamemap.engine.player:
#                                 actor.level.add_xp(target.level.xp_given)
#                             elif self.status_units:
#                                 for status in self.status_units:
#                                     status.execute(actor, target)
# if skill.second_units:
#     skill.process_queue(actor)

# def get_action(self, skill: ActiveSkill, actor: Actor):
#     actor.gamemap.engine.message_log.add_message(
#         "Select a target location.", color.needs_target
#     )
#     return AreaRangedAttackHandler(actor.gamemap.engine,
#                                    self.radius,
#                                    callback=lambda xy: actions.ExecuteAction(actor, self, skill, xy))


# class CombatTarget:
#     def __init__(self, is_ranged: bool, can_choose: bool, num_hits: int = 1, num_targets: int = 1, damage: int = 0,
#                  status_units: List[StatusUnit] = None):
#         self.is_ranged = is_ranged
#         self.can_choose = can_choose
#         self.num_hits = num_hits
#         self.num_targets = num_targets
#         self.damage = damage
#         self.status_units = status_units or []


class MovementTeleportation:
    def __init__(self, is_ranged: bool, range_limit: int = 0):
        self.can_choose = True
        self.is_ranged = is_ranged
        self.range_limit = range_limit

    def execute_movement_teleportation(self, actor: Actor, x: int, y: int) -> None:
        """Execute the teleportation movement to the specified location."""
        if not self.is_ranged:
            raise Exception("Teleportation can only be used for ranged skills.")
        if 0 < self.range_limit < actor.distance(x, y):
            raise Exception("Target location is out of range.")
        actor.place(x, y)
        actor.fighter.time -= 1


class MovementDash:
    def __init__(self, direction: tuple[int, int], distance: int):
        self.can_choose = True
        self.direction = direction
        self.distance = distance

    def execute_movement_dash(self, actor: Actor) -> None:
        """Execute the dash movement in the specified direction."""
        dx, dy = self.direction
        for _ in range(self.distance):
            new_x, new_y = actor.x + dx, actor.y + dy
            if np.array(actor.gamemap.tiles["walkable"], dtype=np.int8)[
                new_x, new_y] and not actor.gamemap.get_blocking_entity_at_location(new_x,
                                                                                    new_y):
                actor.move(dx, dy)
                actor.fighter.time -= 0.5
            else:
                break


class StatusUnit:
    def __init__(self, effects: List[StatusEffect]):
        self.effects = effects
        self.can_choose = True

    def execute(self, user: Actor, targets: Optional[List[Actor]] = None) -> None:
        """Execute the status unit's effects on the user and targets."""
        # Apply the effects on the targets if provided
        if targets:
            for target in targets:
                for effect in self.effects:
                    target.status_effect_manager.add_effect(effect)


class ActiveSkill(Skill):

    def __init__(self, name, description, activation_requirements, mp_cost=0, sp_cost=0, se_cost=0, cooldown=0,
                 time_cost: int | float = 0, level=1, experience=0,
                 unit: Union[CombatAoe, CombatSingleTarget] = None):
        super().__init__(name, description, activation_requirements, level, experience)
        self.mp_cost = mp_cost
        self.sp_cost = sp_cost
        self.se_cost = se_cost
        self.cooldown = cooldown
        self.remaining_cooldown = 0
        self.time_cost = time_cost
        self.unit = unit or None
        self.unit.owner = self
        if self.unit.units:
            for unit in self.unit.units:
                unit.owner = self

    def activation(self, xy):
        self.unit.execute(xy)

    def update_cooldowns(self):
        self.remaining_cooldown -= 1
        if self.remaining_cooldown < 0:
            self.remaining_cooldown = 0

    def on_cooldown(self):
        if self.remaining_cooldown == 0:
            return False
        else:
            return True

    def activate(self, xy=None):
        return self.unit.get_action(xy)

    def reset_cooldown(self):
        self.remaining_cooldown = self.cooldown

    def deduct_costs(self, user: Actor):
        # Deduct the resource costs (MP, SP, SE) from the user
        user.fighter.sp -= self.sp_cost
        user.fighter.mp -= self.mp_cost
        user.fighter.se -= self.se_cost
        user.fighter.time -= self.time_cost

    def can_afford(self, user: Actor):
        # Check if the user has enough resources (MP, SP, SE) to use the skill
        if user.fighter.sp >= self.sp_cost:
            if user.fighter.mp >= self.mp_cost:
                if user.fighter.se >= self.se_cost:
                    return True
        return False


class Abilities(BaseComponent):
    parent: Actor

    def __init__(self):
        self.active_skills: List[ActiveSkill] = []
        self.passive_skills: List[Skill] = []
        self.hybrid_skills: List[Skill] = []

    def update_cooldowns(self):
        for skill in self.active_skills:
            skill.update_cooldowns()

    def is_skill_ready(self, skill: ActiveSkill, actor: Actor) -> bool:
        """Check if the skill is ready to be used (not on cooldown and enough resources)."""
        if skill.on_cooldown():
            return False
        return skill.can_afford(actor)

    def activate_skill(self, skill: ActiveSkill, actor: Actor, targets: Optional[Actor] | Optional[List[Actor]] = None):
        """Activate the skill and handle cooldowns, costs, and status effects."""
        if not self.is_skill_ready(skill, actor):
            raise Exception("Skill is not ready to be used.")

        skill.activate(actor, targets)

    def add_active_skill(self, skill: ActiveSkill):
        """Add an active skill to the abilities."""
        self.active_skills.append(skill)
        skill.manager = self

    def add_passive_skill(self, skill: Skill):
        """Add a passive skill to the abilities."""
        self.passive_skills.append(skill)

    def add_hybrid_skill(self, skill: Skill):
        """Add a hybrid skill to the abilities."""
        self.hybrid_skills.append(skill)

# Add a SkillAction
