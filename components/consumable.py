from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import actions
import color
import components.ai
import components.inventory
from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import (
    ActionOrHandler,
    AreaRangedAttackHandler,
    SingleRangedAttackHandler, )

if TYPE_CHECKING:
    from entity import Actor, Item
    from Status import StatusEffect


class Consumable(BaseComponent):
    def __init__(self, time_cost: float | int = 0, effect: StatusEffect = None):
        self.time_cost = time_cost
        self.effect = effect

    parent: Item

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this item."""
        return actions.ItemAction(consumer, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        """Invoke this items ability.

        `action` is the context for this activation.
        """
        raise NotImplementedError()

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):
            inventory.items.remove(entity)


class HealingConsumable(Consumable):
    def __init__(self, amount: int, time_cost=1, effect: StatusEffect = None):
        super().__init__(time_cost, effect)
        self.amount = amount

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        if consumer.fighter.time < self.time_cost:
            raise Impossible(f"You don't have enough time.")

        amount_recovered = consumer.fighter.heal(self.amount)
        if self.effect:
            consumer.status_effect_manager.add_effect(self.effect)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You consume the {self.parent.name}, and recover {amount_recovered} HP!",
                color.health_recovered,
            )
            self.consume()
            consumer.fighter.time = consumer.fighter.time - self.time_cost
        else:
            raise Impossible(f"Your health is already full.")


class LightningDamageConsumable(Consumable):
    def __init__(self, damage: int, maximum_range: int):
        super().__init__(time_cost=3)
        self.damage = damage
        self.maximum_range = maximum_range

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        if consumer.fighter.time < self.time_cost:
            raise Impossible(f"You don't have enough time.")
        target = None
        closest_distance = self.maximum_range + 1.0

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    target = actor
                    closest_distance = distance

        if target:
            self.engine.message_log.add_message(
                f"A lighting bolt strikes the {target.name} with a loud thunder, for {self.damage} damage!"
            )
            target.fighter.take_damage(self.damage)
            consumer.fighter.time = consumer.fighter.time - self.time_cost
            self.consume()
        else:
            raise Impossible("No enemy is close enough to strike.")


class ConfusionConsumable(Consumable):
    def __init__(self, number_of_turns: int):
        super().__init__(time_cost=1.5)
        self.number_of_turns = number_of_turns

    def get_action(self, consumer: Actor) -> SingleRangedAttackHandler:
        self.engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return SingleRangedAttackHandler(
            self.engine,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        if consumer.fighter.time < self.time_cost:
            raise Impossible(f"You don't have enough time.")
        target = action.target_actor
        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")
        if not target:
            raise Impossible("You must select an enemy to target.")
        if target is consumer:
            raise Impossible("You cannot confuse yourself!")

        self.engine.message_log.add_message(
            f"The eyes of the {target.name} look vacant, as it starts to stumble around!",
            color.status_effect_applied,
        )
        target.ai = components.ai.ConfusedEnemy(
            entity=target, previous_ai=target.ai, turns_remaining=self.number_of_turns,
        )
        consumer.fighter.time = consumer.fighter.time - self.time_cost
        self.consume()


class FireballDamageConsumable(Consumable):
    def __init__(self, damage: int, radius: int):
        super().__init__(time_cost=5)
        self.damage = damage
        self.radius = radius

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        self.engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return AreaRangedAttackHandler(
            self.engine,
            radius=self.radius,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        if consumer.fighter.time < self.time_cost:
            raise Impossible(f"You don't have enough time.")
        target_xy = action.target_xy

        if not self.engine.game_map.visible[target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")

        targets_hit = False
        for actor in self.engine.game_map.actors:
            if actor.distance(*target_xy) <= self.radius:
                self.engine.message_log.add_message(
                    f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!"
                )
                actor.fighter.take_damage(self.damage)
                targets_hit = True

        if not targets_hit:
            raise Impossible("There are no targets in the radius.")
        consumer.fighter.time = consumer.fighter.time - self.time_cost
        self.consume()
