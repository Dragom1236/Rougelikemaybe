from __future__ import annotations

import random
from typing import TYPE_CHECKING, Union, List, Optional

import numpy as np

import actions
from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import AreaRangedAttackHandler, SingleRangedAttackHandler

if TYPE_CHECKING:
    from entity import Actor
    from components.Status import StatusEffect


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

    def __init__(self):
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


class CombatUnit(Unit):
    owner: ActiveSkill

    def __init__(self, damage: int = 0, is_ranged=None):
        super().__init__()
        self.damage = damage
        self.is_ranged = is_ranged
        self.type = "Combat"


class CombatAoe(CombatUnit):
    def __init__(self, effects: List[StatusEffect], damage: int = 0, is_ranged=None, radius: int = 2):
        super().__init__(damage, is_ranged)
        self.effects = effects
        self.radius = radius
        self.type = "Combat"

    def get_action(self, xy=None):
        if self.is_ranged:
            if self.user_is_player:
                return AreaRangedAttackHandler(self.user.gamemap.engine,
                                               self.radius,
                                               callback=lambda ab: actions.ExecuteAction(self.user, self.owner,
                                                                                         xy=ab))
            else:
                return actions.ExecuteAction(self.user, self.owner, xy=xy)
        else:
            return actions.ExecuteAction(self.user, self.owner)

    def execute(self, xy=None):
        # Ensuring only ranged AOEs use this logic
        if xy and self.is_ranged:
            x, y = xy
            if not self.user.gamemap.visible[xy]:
                raise Impossible("You cannot target an area that you cannot see.")

            targets_hit = False
            for actor in self.user.gamemap.actors:
                if actor.distance(x, y) <= self.radius:
                    actor.gamemap.engine.message_log.add_message(
                        f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!"
                    )
                    actor.fighter.create_damage_log(category="Attack", source_entity=self.user,
                                                    details=f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!")
                    actor.fighter.take_damage(self.damage)
                    for effect in self.effects:
                        actor.status_effect_manager.add_effect(effect)
                    targets_hit = True

            if not targets_hit:
                raise Impossible("There are no targets in the radius.")
        else:
            # If it's a melee AOE, we'll inflict damage to all enemies in the user's reach (within 1 tile).
            for target in self.user.gamemap.actors:
                if target is not self.user and target.is_alive:
                    distance = self.user.distance(target.x, target.y)
                    if distance <= 1:
                        # Since it's melee, defense is used.
                        calculated_damage = self.damage - target.fighter.defense
                        if calculated_damage > 0:
                            target.fighter.create_damage_log(category="Attack", source_entity=self.user,
                                                             details=f"The {target.name} is engulfed in a fiery explosion, taking {self.damage} damage!")
                            target.fighter.hp -= calculated_damage
                            for effect in self.effects:
                                target.status_effect_manager.add_effect(effect)
        self.owner.reset_cooldown()
        self.owner.deduct_costs(self.user)


class CombatSingleTarget(CombatUnit):
    def __init__(self, effects: List[StatusEffect], damage: int = 0, is_ranged=None, num_hits: int = 1, radius: int = None):
        super().__init__(damage, is_ranged)
        self.effects = effects
        self.radius = radius
        self.type = "Combat"
        self.num_hits = num_hits
        if self.radius:
            self.is_ranged = False

    def get_action(self, xy=None):
        if self.is_ranged:
            if self.user_is_player:
                return SingleRangedAttackHandler(self.user.gamemap.engine,
                                                 callback=lambda ab: actions.ExecuteAction(self.user, self.owner,
                                                                                           xy=ab))
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
                    target.gamemap.engine.message_log.add_message(
                        f"The {target.name} is hit, taking {self.damage} damage!"
                    )
                    target.fighter.create_damage_log(category="Attack", source_entity=self.user,
                                                     details=f"The {target.name} is engulfed in a fiery explosion, taking {self.damage} damage!")
                    target.fighter.take_damage(self.damage)
                    for effect in self.effects:
                        target.status_effect_manager.add_effect(effect)
            else:
                raise Impossible("There is no target at this location.")


        else:
            # This unit can't be called without a target.
            raise Impossible("This skill must target something.")

        self.owner.reset_cooldown()
        self.owner.deduct_costs(self.user)


class MovementTeleportation(Unit):
    def __init__(self, range_limit: int = 0):
        super().__init__()
        self.range_limit = range_limit

    def get_action(self, xy):
        if not self.user_is_player:
            return actions.ExecuteAction(self.user, self.owner, xy)
        else:
            return SingleRangedAttackHandler(self.user.gamemap.engine,
                                             callback=lambda ab: actions.ExecuteAction(self.user, self.owner, xy=ab))

    def execute(self, xy) -> None:
        x, y = xy
        """Execute the teleportation movement to the specified location."""
        if not self.user.gamemap.visible[xy]:
            raise Impossible("You cannot target an area that you cannot see.")
        target = self.user.gamemap.get_actor_at_location(x, y)
        if target:
            raise Impossible("You cannot teleport inside another creature!")
        # if not self.is_ranged:
        #     raise Exception("Teleportation can only be used for ranged skills.")
        if 0 < self.range_limit < self.user.distance(x, y):
            raise Exception("Target location is out of range.")
        self.user.place(x, y)
        self.user.fighter.actions -= 1


class StatusUnit:
    def __init__(self, effects: List[StatusEffect]):
        self.effects = effects
        self.can_choose = True

    def execute(self, targets: Optional[List[Actor]] = None) -> None:
        """Execute the status unit's effects on the user and targets."""
        # Apply the effects on the targets if provided
        if targets:
            for target in targets:
                for effect in self.effects:
                    target.status_effect_manager.add_effect(effect)


class ActiveSkill(Skill):

    def __init__(self, name, description, activation_requirements, mp_cost=0, sp_cost=0, se_cost=0, cooldown=0,
                 level=1, experience=0,
                 unit: Union[CombatAoe, CombatSingleTarget] = None):
        super().__init__(name, description, activation_requirements, level, experience)
        self.mp_cost = mp_cost
        self.sp_cost = sp_cost
        self.se_cost = se_cost
        self.cooldown = cooldown
        self.remaining_cooldown = 0
        self.unit = unit or None
        self.unit.owner = self

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
        user.fighter.actions -= 1

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
        skill.manager = self

    def add_hybrid_skill(self, skill: Skill):
        """Add a hybrid skill to the abilities."""
        self.hybrid_skills.append(skill)
        skill.manager = self

# Add a SkillAction
