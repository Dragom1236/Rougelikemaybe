from __future__ import annotations

import random
from typing import TYPE_CHECKING, Union, List, Optional, Type

import numpy as np

if TYPE_CHECKING:
    from entity import Actor
    from components.Status import StatusEffect


class Skill:
    def __init__(self, name, description, activation_requirements, level=1, experience=0):
        self.name = name
        self.description = description
        self.activation_requirements = activation_requirements
        self.level = level
        self.experience = experience

    def activate(self, user, target=None):
        raise NotImplementedError("Subclasses must override the activate method.")


class CombatAoe:
    def __init__(self, is_ranged: bool, radius: int = 0, damage: int = 0, status_units: List[StatusUnit] = None):
        self.is_ranged = is_ranged
        self.radius = radius
        self.damage = damage
        self.status_units = status_units or []


class CombatTarget:
    def __init__(self, is_ranged: bool, can_choose: bool, num_hits: int = 1, num_targets: int = 1, damage: int = 0,
                 status_units: List[StatusUnit] = None):
        self.is_ranged = is_ranged
        self.can_choose = can_choose
        self.num_hits = num_hits
        self.num_targets = num_targets
        self.damage = damage
        self.status_units = status_units or []


class MovementTeleportation:
    def __init__(self, is_ranged: bool, range_limit: int = 0):
        self.is_ranged = is_ranged
        self.range_limit = range_limit

    def execute_movement_teleportation(self, actor: Actor, x: int, y: int) -> None:
        """Execute the teleportation movement to the specified location."""
        if not self.is_ranged:
            raise Exception("Teleportation can only be used for ranged skills.")
        if self.range_limit > 0 and actor.distance(x, y) > self.range_limit:
            raise Exception("Target location is out of range.")
        actor.place(x, y)
        actor.fighter.time -= 1


class MovementDash:
    def __init__(self, direction: tuple[int, int], distance: int):
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
                 units: List[Union[CombatAoe, CombatTarget, MovementTeleportation, MovementDash]] = None):
        super().__init__(name, description, activation_requirements, level, experience)
        self.mp_cost = mp_cost
        self.sp_cost = sp_cost
        self.se_cost = se_cost
        self.cooldown = cooldown
        self.remaining_cooldown = 0
        self.time_cost = time_cost
        self.units = units or []

    def update_cooldowns(self):
        self.cooldown -= 1
        if self.cooldown < 0:
            self.cooldown = 0

    def on_cooldown(self):
        if self.cooldown == 0:
            return False
        else:
            return True

    def activate(self, actor, target=None):
        if actor.fighter.time < self.time_cost:
            raise Exception("Not enough time to use this skill.")
        if self.on_cooldown():
            raise Exception("Skill is on cooldown.")
        if not self.can_afford(actor):
            raise Exception("Not enough resources (MP, SP, SE) to use this skill.")
        for unit in self.units:
            if isinstance(unit, MovementDash):  # Execute movement first
                unit.execute_movement_dash(actor)

        for unit in self.units:
            if isinstance(unit, CombatAoe):
                self.execute_combat_aoe(actor, unit)
            elif isinstance(unit, CombatTarget):
                self.execute_combat_target(actor, unit)

        self.deduct_costs(actor)
        self.remaining_cooldown = self.cooldown

    def execute_combat_aoe(self, actor, unit: CombatAoe):
        is_ranged = unit.is_ranged
        radius = unit.radius
        damage = unit.damage

        if is_ranged:
            # If it's a ranged AOE, get a random target within the specified radius.
            entity = random.choice(actor.ai.actor_search())
            xy = entity.x, entity.y
            calculated_damage = damage - entity.fighter.defense
            if calculated_damage > 0:
                entity.fighter.hp -= calculated_damage
                if not entity.is_alive and entity is not actor.gamemap.engine.player:
                    actor.level.add_xp(entity.level.xp_given)
                if unit.status_units:
                    for status in unit.status_units:
                        status.execute(actor, entity)

            # Apply the AOE attack to all targets within the given radius around the random target's location.
            for target in actor.gamemap.actors:
                if target.distance(*xy) <= radius and target is not actor and target.is_alive:
                    # Since it's a ranged attack, we will use defense.
                    calculated_damage = damage - target.fighter.defense
                    if calculated_damage > 0:
                        target.fighter.hp -= calculated_damage
                        if not target.is_alive and target is not actor.gamemap.engine.player:
                            actor.level.add_xp(target.level.xp_given)
                        elif unit.status_units:
                            for status in unit.status_units:
                                status.execute(actor, target)


        else:
            # If it's a melee AOE, we'll inflict damage to all enemies in the user's reach (within 1 tile).
            for target in actor.gamemap.actors:
                if target is not actor and target.is_alive:
                    distance = actor.distance(target.x, target.y)
                    if distance <= 1:
                        # Since it's melee, defense is used.
                        calculated_damage = damage - target.fighter.defense
                        if calculated_damage > 0:
                            target.fighter.hp -= calculated_damage
                            if not target.is_alive and target is not actor.gamemap.engine.player:
                                actor.level.add_xp(target.level.xp_given)
                            elif unit.status_units:
                                for status in unit.status_units:
                                    status.execute(actor, target)

    def execute_combat_target(self, user: Actor, unit: CombatTarget):
        is_ranged = unit.is_ranged
        can_choose = unit.can_choose
        num_hits = unit.num_hits
        damage = unit.damage
        num_targets = unit.num_targets

        targets = []

        if can_choose:
            pass
        else:
            if is_ranged:
                # If the player cannot choose targets, use the provided code to target the nearest enemy
                for actor in user.gamemap.actors:
                    if actor is not user and actor in user.ai.actors_search() and len(targets) <= num_targets:
                        targets.append(actor)
            else:
                # If the player cannot choose targets, use the provided code to target the nearest enemy
                for actor in user.gamemap.actors:
                    if actor is not user and actor in user.ai.actors_search() and len(targets) <= num_targets:
                        distance = user.distance(actor.x, actor.y)

                        if distance <= 1:
                            targets.append(actor)

        if targets:
            if unit.status_units:
                for status in unit.status_units:
                    status.execute(user, targets)
            for _ in range(num_hits):
                for target in targets:
                    if target.is_alive:
                        # Since it's melee, defense is used
                        taken_damage = damage - target.fighter.defense
                        if taken_damage > 0:
                            target.fighter.hp -= taken_damage
                            if not target.is_alive and target is not user.gamemap.engine.player:
                                user.level.add_xp(target.level.xp_given)
                    else:
                        continue

    def deduct_costs(self, user: Actor):
        # Deduct the resource costs (MP, SP, SE) from the user
        user.fighter.sp -= self.sp_cost
        user.fighter.mp -= self.mp_cost
        user.fighter.se -= self.se_cost

    def can_afford(self, user: Actor):
        # Check if the user has enough resources (MP, SP, SE) to use the skill
        if user.fighter.sp >= self.sp_cost:
            if user.fighter.mp >= self.mp_cost:
                if user.fighter.se >= self.se_cost:
                    return True
        return False


class Abilities:
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

    def add_passive_skill(self, skill: Skill):
        """Add a passive skill to the abilities."""
        self.passive_skills.append(skill)

    def add_hybrid_skill(self, skill: Skill):
        """Add a hybrid skill to the abilities."""
        self.hybrid_skills.append(skill)

# Add a SkillAction