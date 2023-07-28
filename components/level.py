from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Level(BaseComponent):
    parent: Actor

    def __init__(
        self,
        current_level: int = 1,
        current_xp: int = 0,
        level_up_base: int = 0,
        level_up_factor: int = 150,
        xp_given: int = 0,
    ):
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given

    @property
    def experience_to_next_level(self) -> int:
        return self.level_up_base + self.current_level * self.level_up_factor

    @property
    def requires_level_up(self) -> bool:
        return self.current_xp > self.experience_to_next_level

    def add_xp(self, xp: int) -> None:
        if xp == 0 or self.level_up_base == 0:
            return

        self.current_xp += xp
        if self.parent == self.engine.player:
            self.engine.message_log.add_message(f"You gain {xp} experience points.")

        if self.requires_level_up:
            if self.parent == self.engine.player:
                self.engine.message_log.add_message(
                    f"You advance to level {self.current_level + 1}!"
                )

    def increase_level(self) -> None:
        self.current_xp -= self.experience_to_next_level

        self.current_level += 1
        self.parent.fighter.update_stats()

    def increase_constitution(self, amount: int = 1) -> None:
        self.parent.fighter.modify_constitution(amount)
        if self.parent == self.engine.player:
            self.engine.message_log.add_message("Your constitution increases!")

        self.increase_level()

    def increase_strength(self, amount: int = 1) -> None:
        self.parent.fighter.modify_strength(amount)
        if self.parent == self.engine.player:
            self.engine.message_log.add_message("You feel stronger!")

        self.increase_level()

    def increase_dexterity(self, amount: int = 1) -> None:
        self.parent.fighter.modify_dexterity(amount)
        if self.parent == self.engine.player:
            self.engine.message_log.add_message("Your movements are getting swifter!")

        self.increase_level()

    def increase_agility(self, amount: int = 1) -> None:
        self.parent.fighter.modify_agility(amount)
        if self.parent == self.engine.player:
            self.engine.message_log.add_message("You feel more agile!")

        self.increase_level()

    def increase_magic(self, amount: int = 1) -> None:
        self.parent.fighter.modify_magic(amount)
        if self.parent == self.engine.player:
            self.engine.message_log.add_message("Your magical prowess grows!")

        self.increase_level()

    def increase_awareness(self, amount: int = 1) -> None:
        self.parent.fighter.modify_awareness(amount)
        if self.parent == self.engine.player:
            self.engine.message_log.add_message("You feel more aware of your surroundings!")

        self.increase_level()

    def increase_charisma(self, amount: int = 1) -> None:
        self.parent.fighter.modify_charisma(amount)
        if self.parent == self.engine.player:
            self.engine.message_log.add_message("Your charisma improves!")

        self.increase_level()

    @property
    def level_up_options(self):
        return [self.increase_strength,self.increase_dexterity,
                self.increase_agility,self.increase_constitution,
                self.increase_magic, self.increase_awareness,
                self.increase_charisma]