from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

import numpy as np  # type: ignore

if TYPE_CHECKING:
    from entity import Actor
    from components.SkillComponent import Skill, ActiveSkill

from components.base_component import BaseComponent


class Race(BaseComponent):
    parent: Actor

    def __init__(self, strength: int, dexterity: int, agility: int,
                 constitution: int, magic: int, awareness: int, charisma: int,
                 level_up_base: int, level_up_factor: int, xp_given: int,
                 skills: List[Union[Skill, ActiveSkill]]):
        self.strength = strength
        self.dexterity = dexterity
        self.agility = agility
        self.constitution = constitution
        self.magic = magic
        self.awareness = awareness
        self.charisma = charisma
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given
        self.skills: List[Union[Skill, ActiveSkill]] = skills
