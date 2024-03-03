from __future__ import annotations

import copy
import math
from typing import Tuple, TypeVar, TYPE_CHECKING, Optional, Type, Union

from tcod.map import compute_fov


from render_order import RenderOrder

if TYPE_CHECKING:
    from game_map import GameMap
    from components.ai import BaseAI
    from components.fighter import Fighter
    from components.inventory import Inventory
    from components.consumable import Consumable
    from components.equippable import Equippable, Accessory, RangedWeapon, Armor, Weapon, Bow, Container, Crossbow, Gun, \
    MagicWeapon, Wand
    from components.equipment import Equipment
    from components.Status import StatusEffectManager
    from components.conditions import ConditionManager
    from components.SkillComponent import Abilities
    from components.level import Level
    from components.Ammo import Ammo
    from components.Race import Race

T = TypeVar("T", bound="Entity")


class Entity:
    parent: Union[GameMap, Inventory]

    """
    A generic object to represent players, enemies, items, etc.
    """

    def __init__(
            self,
            parent: Optional[GameMap] = None,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            blocks_movement: bool = False,
            render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        if parent:
            # If gamemap isn't provided now then it will be set later.
            self.parent = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        # Move the parent by a given amount
        self.x += dx
        self.y += dy

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Place this parent at a new location.  Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):  # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)


class Actor(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            ai_cls: Type[BaseAI],
            fighter: Fighter,
            inventory: Inventory,
            level: Level,
            equipment: Equipment,
            conditions_manager: ConditionManager,
            status_effect_manager: StatusEffectManager,
            abilities: Abilities,
            race:Race,
    ):
        super().__init__(x=x, y=y, char=char, color=color, name=name, blocks_movement=True,
                         render_order=RenderOrder.ACTOR)

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.fighter = fighter
        self.fighter.parent = self
        self.inventory = inventory
        self.inventory.parent = self
        self.status_effect_manager = status_effect_manager
        self.status_effect_manager.parent = self
        self.level = level
        self.level.parent = self
        self.conditions_manager = conditions_manager
        self.conditions_manager.parent = self
        self.abilities = abilities
        self.abilities.parent = self
        self.equipment: Equipment = equipment
        self.equipment.parent = self
        self.race = race
        self.race.parent = self
        self.fighter.set_stats()
        self.level.override_level_info()

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)

    def has_direct_los(self, target_x: int, target_y: int):
        # Perform ray casting to check for direct line of sight
        visible_map = compute_fov(self.gamemap.tiles["transparent"], (self.x, self.y),
                                  radius=self.fighter.sight_range, )
        if target_x == self.x and target_y == self.y:
            return False
        dx = int(target_x - self.x)
        dy = int(target_y - self.y)
        steps = max(abs(dx), abs(dy))
        x_step = dx / steps
        y_step = dy / steps

        x, y = self.x, self.y

        for _ in range(steps):
            x += x_step
            y += y_step

            # Check if there's an obstacle at (x, y), if yes, return False
            if self.gamemap.is_tile_blocked(x, y):
                return False
            if not visible_map[int(x), int(y)]:
                return False

        # If the loop completes without finding an obstacle, return True
        return True


class Item(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            consumable: Optional[Consumable] = None,
            equippable: Optional[
                Union[
                    Equippable, Weapon, Armor, Accessory, RangedWeapon, Bow, Crossbow, Gun, MagicWeapon,Wand, Container]] = None,
            ammo: Optional[Ammo] = None
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )

        self.consumable = consumable
        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable

        if self.equippable:
            self.equippable.parent = self
        self.ammo = ammo
        if self.ammo:
            self.ammo.parent = self
