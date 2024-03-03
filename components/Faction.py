from __future__ import annotations
from typing import Dict, TYPE_CHECKING, List

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class FactionComponent(BaseComponent):
    parent: Actor

    def __init__(self):
        self.member_factions: set = set()
        self.hostile_factions: set = set()

    def init_racial_faction(self):
        race = self.parent.race
        if race.factions:
            self.member_factions.update(race.factions[0])
            self.hostile_factions.update(race.factions[1])
