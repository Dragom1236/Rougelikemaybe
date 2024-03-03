# conditions.py
from __future__ import annotations
from typing import Dict, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Condition:
    def __init__(self, name: str, duration: int = None, permanent: bool = False, consumable: bool = False,
                 condition_type: str = "other", accuracy: int = 100):
        self.accuracy = accuracy
        self.name = name
        self.duration = duration
        self.permanent = permanent
        self.consumable = consumable
        self.type = condition_type
        self.category = "General"

    def consume(self) -> bool:
        if self.consumable:
            return True
        else:
            return False


# conditions.py

class ConditionManager(BaseComponent):
    parent: Actor

    def __init__(self):
        self.conditions: Dict[str:Condition] = {}

    def add_condition(self, condition: Condition):
        """Add a condition to the actor's condition manager."""
        self.conditions[condition.name] = condition

    def remove_condition(self, condition_name: str):
        """Remove a condition from the actor's condition manager."""
        if condition_name in self.conditions:
            del self.conditions[condition_name]

    def has_condition(self, condition_name: str) -> bool:
        """Check if the actor has a specific condition."""
        return condition_name in self.conditions

    def get_condition_duration(self, condition_name: str) -> int:
        """Get the remaining duration of a condition."""
        if condition_name in self.conditions:
            return self.conditions[condition_name].duration
        return 0

    def reduce_conditions_duration(self):
        """Reduce the remaining duration of a condition."""
        for key in self.conditions:
            if not self.conditions[key].permanent:
                self.conditions[key].duration -= 1
            if self.conditions[key].duration <= 0 and not self.conditions[key].permanent:
                self.remove_condition(key)


class DrainCondition(Condition):
    def __init__(self, name: str, percentage: float, duration: int = None, permanent: bool = False):
        super().__init__(name, duration, permanent)
        self.percentage = percentage
        self.category = "Drain"

class ChanceCondition(Condition):
    # Universal class for classes with a chance of the condition activating.
    # Note again that chance here means "chance of the condition activating".
    # Accuracy is dependent on whatever is inflicting the condition.

    def __init__(self, name: str, chance: int, duration: int = None, permanent: bool = False, condition_type="Harmful"):
        super().__init__(name, duration, permanent, condition_type=condition_type)
        self.chance = chance
        self.category = "Chance"


class TargetCondition(ChanceCondition):
    def __init__(self, name: str, chance: int, duration: int = None, permanent: bool = False, condition_type="Harmful"):
        super().__init__(name, chance, duration, permanent, condition_type=condition_type)
        self.target = None
        self.category = "Target"
        # Needs to set a target in order to function.

    def set_target(self, target: Actor):
        self.target = target


class AccuracyCondition(Condition):
    def __init__(self, name: str, accuracy_penalty: int, duration: int = None, permanent: bool = False):
        super().__init__(name, duration, permanent, condition_type="Harmful")
        self.accuracy_penalty = accuracy_penalty
        self.category = "Accuracy"


class BlindedCondition(AccuracyCondition):
    def __init__(self, duration: int = None, permanent: bool = False, sight_range_reduction: int = 2):
        super().__init__("Blinded", accuracy_penalty=20, duration=duration, permanent=permanent)
        self.sight_reduction = sight_range_reduction
        self.category = "Blind"
