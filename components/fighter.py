from __future__ import annotations

import math
from typing import TYPE_CHECKING

import color
from components.base_component import BaseComponent
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor


class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, mp: int, se: int, sp: int, strength: int, dexterity: int, agility: int,
                 constitution: int, magic: int, awareness: int, charisma: int):
        self.strength = strength
        self.dexterity = dexterity
        self.agility = agility
        self.constitution = constitution
        self.magic = magic
        self.awareness = awareness
        self.charisma = charisma
        self.extra_hp = hp
        self.extra_mp = mp
        self.extra_sp = sp
        self.extra_se = se
        self.max_hp = self.extra_hp + 2 * self.constitution
        self._hp = self.max_hp
        self.max_mp = self.extra_mp + self.magic
        self._mp = self.max_mp
        self.max_se = self.extra_se + self.charisma // 20
        self._se = self.max_se
        self.max_sp = self.extra_sp + self.constitution
        self._sp = self.max_sp

        self.magical_defense = 0  # Set to 0 initially
        self.critical_chance: float = (self.dexterity // 10) / 100
        self.critical_damage: float = (self.strength // 2) / 100
        self.max_time: float = 6
        self._time = self.max_time
        self.initiative: int = 1 + agility

    @property
    def time(self) -> float:
        return self._time

    @time.setter
    def time(self, value: float) -> None:
        # Set the time attribute to the new value
        self._time = value

        # # Check if the time pool is empty (no time remaining)
        # if self._time <= 0:
        #     # Trigger the engine to start the next turn
        #     self.engine.handle_next_turn()  # Replace 'handle_next_turn()' with the appropriate method in your engine
        #     self._time = self.max_time

    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp -= amount

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message_color = color.player_die
            death_message = "You died!"
        else:
            death_message_color = color.enemy_die
            death_message = f"{self.parent.name} is dead!"

        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE

        self.engine.message_log.add_message(death_message, death_message_color)

    @property
    def mp(self) -> int:
        return self._mp

    @mp.setter
    def mp(self, value: int) -> None:
        self._mp = max(0, min(value, self.max_mp))

    @property
    def se(self) -> int:
        return self._se

    @se.setter
    def se(self, value: int) -> None:
        self._se = max(0, min(value, self.max_se))

    @property
    def sp(self) -> int:
        return self._sp

    @sp.setter
    def sp(self, value: int) -> None:
        self._sp = max(0, min(value, self.max_sp))

    @property
    def defense(self) -> int:
        return self.defense_bonus

    @property
    def defense_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def power(self) -> int:
        return self.strength // 5

    @property
    def magical_attack(self) -> int:
        return self.magic

    @property
    def sight_range(self):
        return round(math.log2(self.awareness)) + 2

    def modify_hp(self, amount: int) -> None:
        self.hp += amount

    def modify_max_hp(self, amount: int) -> None:
        self.max_hp += amount
        self.hp += amount

    def modify_strength(self, amount: int) -> None:
        self.strength += amount

    def modify_mp(self, amount: int) -> None:
        self.mp += amount

    def modify_max_mp(self, amount: int) -> None:
        self.max_mp += amount
        self.mp += amount

    def modify_se(self, amount: int) -> None:
        self.se += amount

    def modify_max_se(self, amount: int) -> None:
        self.max_se += amount
        self.se += amount

    def modify_sp(self, amount: int) -> None:
        self.sp += amount

    def modify_max_sp(self, amount: int) -> None:
        self.max_sp += amount
        self.sp += amount

    def modify_dexterity(self, amount: int) -> None:
        self.dexterity += amount

    def modify_agility(self, amount: int) -> None:
        self.agility += amount

    def modify_constitution(self, amount: int) -> None:
        self.constitution += amount
        # Since Constitution affects Max HP, update Max HP too
        self.update_stats()

    def modify_magic(self, amount: int) -> None:
        self.magic += amount
        self.update_stats()

    def modify_awareness(self, amount: int) -> None:
        self.awareness += amount

    def modify_charisma(self, amount: int) -> None:
        self.charisma += amount
        # Since Charisma affects Max SE, update Max SE too
        self.update_stats()

    def update_stats(self) -> None:
        # Update HP and max HP based on constitution
        self.max_hp = self.extra_hp + 2 * self.constitution
        self.hp = min(self.hp, self.max_hp)
        self.max_mp = self.extra_mp + self.magic
        self.mp = min(self.mp, self.max_mp)
        self.max_se = self.extra_se + self.charisma // 20
        self.se = min(self.se, self.max_se)
        self.max_sp = self.extra_sp + self.constitution
        self.sp = min(self.sp, self.max_sp)
