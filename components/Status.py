from __future__ import annotations

import copy
from typing import TYPE_CHECKING, List

import numpy as np  # type: ignore



if TYPE_CHECKING:
    from entity import Actor
    from components.conditions import Condition

from components.base_component import BaseComponent


class StatusEffectManager(BaseComponent):
    parent: Actor

    def __init__(self):
        self.active_effects: List[StatusEffect] = []

    def add_effect(self, effect: StatusEffect):
        for active_effect in self.active_effects:
            if active_effect.name == effect.name:
                active_effect.stacks += 1
                # Handle stacking effects here, for example, increase the duration
                active_effect.duration += effect.duration
                if active_effect.modifier_data:
                    active_effect.remove_effect(self.parent)
                    active_effect.apply_effect(self.parent)

                return

        # If the effect is not already applied, add it as a new instance
        clone = copy.deepcopy(effect)
        self.active_effects.append(clone)
        clone.apply_effect(self.parent)

    def remove_effect(self, effect: StatusEffect):
        if effect in self.active_effects:
            self.active_effects.remove(effect)
            effect.remove_effect(self.parent)

    def update_effects(self):
        effects_to_remove = []
        for effect in self.active_effects:
            effect.process_delay()
            if not effect.permanent and effect.delay == 0:
                effect.reduce_duration()
            if effect.duration <= 0 and not effect.permanent:
                effects_to_remove.append(effect)
            else:
                effect.tick_effect(self.parent)  # Call tick_effect for active effects

        for effect in effects_to_remove:
            self.remove_effect(effect)


class StatusEffect:
    def __init__(self, name: str,
                 duration: int,
                 modifier_data: dict,
                 cot_effect_data: dict,
                 conditions:List[Condition] = None,
                 permanent: bool = False,
                 can_delay: bool = False,
                 delay: int = 0):
        self.name = name
        self.duration = duration
        self.modifier_data = modifier_data.copy()
        self.cot_effect_data = cot_effect_data.copy()
        self.stacks = 1
        self.conditions = conditions
        self.permanent = permanent
        self.can_delay = can_delay
        self.delay = delay

    def apply_effect(self, entity: Actor):
        # Apply the modifiers to the parent based on the modifier_data
        for key, value in self.modifier_data.items():
            if key == "hp_modifier":
                entity.fighter.modify_max_hp(value)
            elif key == "strength_modifier":
                entity.fighter.modify_strength(value)
            # Add more conditions here to handle other modifier types
        if self.conditions:
            for condition in self.conditions:
                entity.conditions_manager.add_condition(condition)

    def remove_effect(self, entity: Actor):
        # Remove the modifiers from the parent.
        for key, value in self.modifier_data.items():
            if key == "hp_modifier":
                entity.fighter.modify_hp(-value * self.stacks)
            elif key == "strength_modifier":
                entity.fighter.modify_strength(-value * self.stacks)
            # Add more conditions here to handle other modifier types

    def tick_effect(self, entity: Actor):
        # Perform the appropriate action every turn for change-over-time effects
        if "hp_change_per_turn" in self.cot_effect_data:
            # print("My hp should have reduced.")
            # print(parent.fighter.hp)
            entity.fighter.modify_hp(self.cot_effect_data["hp_change_per_turn"] * self.stacks)
            # print(parent.fighter.hp)

        # Add more conditions here to handle other change-over-time effect types

    def reduce_duration(self, amount: int = 1):
        if not self.permanent:
            self.duration -= amount

    def process_delay(self, amount: int = 1):
        if self.can_delay:
            self.delay -= amount
            if self.delay < 0:
                self.delay = 0
        else:
            self.delay = 0
