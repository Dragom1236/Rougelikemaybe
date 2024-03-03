from __future__ import annotations

from components.base_component import BaseComponent
import random
from typing import List, Tuple, TYPE_CHECKING, Optional, Type, Union, Dict

if TYPE_CHECKING:
    from entity import Actor


class Personality(BaseComponent):
    parent: Actor

    def __init__(self, traits: Dict[str, int] = None, preferences: Dict[str, int] = None):
        if not traits:
            traits = {}
        if not preferences:
            preferences = {}
        self.traits: Dict[str, int] = traits  # Dictionary of personality traits and their values
        self.preferences: Dict[str, int] = preferences

    def add_trait(self, trait: str, value: int) -> None:
        """Add a personality trait to the entity"""
        self.traits[trait] = value

    def get_trait_value(self, trait: str) -> int:
        """Get the value of a specific personality trait"""
        return self.traits.get(trait, 0)

    def has_trait(self, trait: str) -> bool:
        """Check if the entity has a specific personality trait"""
        return trait in self.traits

    def add_preference(self, preference: str, value: int) -> None:
        """Add a preference to the entity's personality"""
        self.preferences[preference] = value

    def get_preference_value(self, preference: str) -> int:
        """Get the value of a specific preference"""
        return self.preferences.get(preference, 0)

    def has_preference(self, preference: str) -> bool:
        """Check if the entity has a specific preference"""
        return preference in self.preferences
