# conditions.py
from __future__ import annotations
from typing import Dict, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Condition:
    def __init__(self, name: str, duration: int = None, permanent: bool = False, consumable: bool = False):
        self.name = name
        self.duration = duration
        self.permanent = permanent
        self.consumable = consumable

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
