from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from components.equippable import Equippable


class Enchantment:
    def __init__(self, name: str):
        self.name = name

    def apply_enchantment(self, equipment: Equippable) -> None:
        # Implement logic to apply the effects of the enchantment to the equipment
        pass

    def remove_enchantment(self, equipment: Equippable) -> None:
        # Implement logic to remove the effects of the enchantment from the equipment
        pass


class SharpnessEnchantment(Enchantment):
    def __init__(self):
        super().__init__("Sharpness")

    def apply_enchantment(self, equipment: Equippable) -> None:
        # Implement logic to apply the sharpness enchantment to the weapon
        pass

    def remove_enchantment(self, equipment: Equippable) -> None:
        # Implement logic to remove the sharpness enchantment from the weapon
        pass

# Add more specific enchantments as needed
