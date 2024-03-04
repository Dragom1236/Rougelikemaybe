from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Item


class Equipment(BaseComponent):
    parent: Actor

    def __init__(self, weapon: Optional[Item] = None, armor: Optional[Item] = None, ):
        self.weapon = weapon
        self.armor = armor
        self.back: Optional[Item] = None

    @property
    def damage_range(self):
        if self.weapon and self.weapon.equippable:
            return self.weapon.equippable.damage_range()
        else:
            return "N/A"

    @property
    def defense_bonus(self) -> int:
        bonus = 0

        if self.armor and self.armor.equippable and \
                self.armor.equippable.equipment_type == EquipmentType.ARMOR:
            bonus += self.armor.equippable.defense_bonus

        return bonus

    def item_is_equipped(self, item: Item) -> bool:
        return self.weapon == item or self.armor == item or self.back == item

    def unequip_message(self, item_name: str) -> None:
        if self.parent == self.engine.player:
            self.parent.gamemap.engine.message_log.add_message(
                f"You remove the {item_name}."
            )
        elif self.parent in self.engine.player.ai.actors_search():
            self.parent.gamemap.engine.message_log.add_message(
                f"{self.parent.name} removes the {item_name}."
            )

    def equip_message(self, item_name: str) -> None:
        if self.parent == self.engine.player:
            self.parent.gamemap.engine.message_log.add_message(
                f"You equip the {item_name}."
            )
        elif self.parent in self.engine.player.ai.actors_search():
            self.parent.gamemap.engine.message_log.add_message(
                f"{self.parent.name} equips the {item_name}."
            )

    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        if item.equippable.equipment_type == EquipmentType.WEAPON:
            if item.equippable.type == "Magic":
                if item.equippable.category == "Wand":
                    item.equippable.update_manager(self.parent)
        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        current_item = getattr(self, slot)
        if current_item.equippable.equipment_type == EquipmentType.WEAPON:
            if current_item.equippable.type == "Magic":
                if current_item.equippable.category == "Wand":
                    current_item.equippable.update_manager()

        if add_message:
            self.unequip_message(current_item.name)

        setattr(self, slot, None)

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        if (
                equippable_item.equippable
                and equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"
        elif (
                equippable_item.equippable
                and equippable_item.equippable.equipment_type == EquipmentType.Container
        ):
            slot = "back"
        else:
            slot = "armor"

        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)
