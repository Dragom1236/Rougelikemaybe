from __future__ import annotations

import copy
from typing import List, TYPE_CHECKING
from components.base_component import BaseComponent
from damageType import normal, ElementalType

if TYPE_CHECKING:
    from components.Status import StatusEffect
    from entity import Actor, Item


class Ammo(BaseComponent):
    parent: Item

    def __init__(self, damage: int, category: str, effects: List[StatusEffect] = None, stacks=1, ):
        self.damage = damage
        self.effects = effects or []
        self.stacks = stacks
        self.category = category
        self.damage_type: ElementalType = normal

    def on_hit_effects(self, target: Actor):
        # Implement logic to trigger any effects when the ammo hits the target
        pass

    def fragment(self, required) -> Item:
        fragmented = copy.deepcopy(self.parent)
        fragmented.ammo.stacks = 0
        total = self.stacks
        self.stacks = required
        fragmented.ammo.stacks = total - required
        return fragmented
