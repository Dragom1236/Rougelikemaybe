from __future__ import annotations

import os
from typing import Optional, TYPE_CHECKING, Callable, Tuple, Union

import tcod.event
import tcod.event
from tcod import libtcodpy

import actions
import color
import exceptions
from actions import (
    Action,
    BumpAction,
    WaitAction,
    PickupAction
)
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item
    from components.SkillComponent import ActiveSkill

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.KeySym.UP: (0, -1),
    tcod.event.KeySym.DOWN: (0, 1),
    tcod.event.KeySym.LEFT: (-1, 0),
    tcod.event.KeySym.RIGHT: (1, 0),
    tcod.event.KeySym.HOME: (-1, -1),
    tcod.event.KeySym.END: (-1, 1),
    tcod.event.KeySym.PAGEUP: (1, -1),
    tcod.event.KeySym.PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.KeySym.KP_1: (-1, 1),
    tcod.event.KeySym.KP_2: (0, 1),
    tcod.event.KeySym.KP_3: (1, 1),
    tcod.event.KeySym.KP_4: (-1, 0),
    tcod.event.KeySym.KP_6: (1, 0),
    tcod.event.KeySym.KP_7: (-1, -1),
    tcod.event.KeySym.KP_8: (0, -1),
    tcod.event.KeySym.KP_9: (1, -1),
    # Vi keys.
    tcod.event.KeySym.h: (-1, 0),
    tcod.event.KeySym.j: (0, 1),
    tcod.event.KeySym.k: (0, -1),
    tcod.event.KeySym.l: (1, 0),
    tcod.event.KeySym.y: (-1, -1),
    tcod.event.KeySym.u: (1, -1),
    tcod.event.KeySym.b: (-1, 1),
    tcod.event.KeySym.n: (1, 1),
}

CONFIRM_KEYS = {
    tcod.event.KeySym.RETURN,
    tcod.event.KeySym.KP_ENTER,
}

WAIT_KEYS = {
    tcod.event.KeySym.PERIOD,
    tcod.event.KeySym.KP_5,
    tcod.event.KeySym.CLEAR,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False

        try:
            if self.engine.player.fighter.time >= action.time_cost:  # Check if player has enough time to perform the action.
                action.perform()
                self.engine.update_fov()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # Skip enemy turn on exceptions.

        if self.engine.player.fighter.time <= 0:
            # self.engine.player.status_effect_manager.add_effect(regeneration_effect)
            self.engine.player.status_effect_manager.update_effects()
            self.engine.player.abilities.update_cooldowns()
            self.engine.player.conditions_manager.reduce_conditions_duration()
            if self.engine.player.equipment.weapon:
                weapon = self.engine.player.equipment.weapon
                if weapon.equippable.equipment_type == EquipmentType.WEAPON:
                    if weapon.equippable.type == "Magic":
                        if weapon.equippable.category == "Wand":
                            weapon.equippable.update_cooldowns()
            self.engine.player.fighter.time = self.engine.player.fighter.max_time
            self.engine.handle_enemy_turns()
            self.engine.update_fov()  # Update the FOV before the players next action.
            return True

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y


class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod
        player = self.engine.player
        if key == tcod.event.KeySym.PERIOD and modifier & (
                tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return actions.TakeDownStairsAction(player)
        if key == tcod.event.KeySym.COMMA and modifier & (
                tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return actions.TakeUpStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.KeySym.ESCAPE:
            raise SystemExit()
        elif key == tcod.event.KeySym.v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.KeySym.g:
            action = PickupAction(player)
        elif key == tcod.event.KeySym.z:
            if self.engine.player.equipment.weapon:
                weapon = self.engine.player.equipment.weapon
                if weapon.equippable.equipment_type == EquipmentType.WEAPON:
                    if weapon.equippable.type == "Magic":
                        if weapon.equippable.category == "Wand":
                            weapon.equippable.cycle_active_skill(-1)
        elif key == tcod.event.KeySym.x:
            if self.engine.player.equipment.weapon:
                weapon = self.engine.player.equipment.weapon
                if weapon.equippable.equipment_type == EquipmentType.WEAPON:
                    if weapon.equippable.type == "Magic":
                        if weapon.equippable.category == "Wand":
                            weapon.equippable.cycle_active_skill(1)
        elif key == tcod.event.KeySym.i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.KeySym.a:
            return AbilitiesActivateHandler(self.engine)
        elif key == tcod.event.KeySym.d:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.KeySym.f and modifier & (
                tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            if self.engine.player.equipment.weapon:
                if self.engine.player.equipment.weapon.equippable.type == "Ranged":
                    # Create the ranged weapon action and return it with the target location
                    return SingleRangedAttackHandler(self.engine,
                                                     callback=lambda xy: actions.RangedWeaponAction(self.engine.player,
                                                                                                    *xy))
                elif self.engine.player.equipment.weapon.equippable.type == "Magic":
                    if self.engine.player.equipment.weapon.equippable.category != "Wand":
                        return SingleRangedAttackHandler(self.engine,
                                                         callback=lambda xy: actions.MagicWeaponAction(
                                                             self.engine.player,
                                                             *xy))
                    else:
                        if self.engine.player.equipment.weapon.equippable.active_unit():
                            return self.engine.player.equipment.weapon.equippable.active_skill.unit.get_action()

        elif key == tcod.event.KeySym.c and modifier & (
                tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return ConditionsViewerEventHandler(self.engine)
        elif key == tcod.event.KeySym.c:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.KeySym.SLASH:
            return LookHandler(self.engine)

        # No valid key was pressed
        return action

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        super().ev_mousebuttondown(event)
        # Check if the event was a left mouse button click
        if event.button == 1:
            # Check if the player has a ranged weapon equipped
            if self.engine.player.equipment.weapon:
                if self.engine.player.equipment.weapon.equippable.type == "Ranged":
                    # Create the ranged weapon action and return it with the target location
                    return actions.RangedWeaponAction(self.engine.player, event.tile.x, event.tile.y)
                elif self.engine.player.equipment.weapon.equippable.type == "Magic":
                    return actions.MagicWeaponAction(self.engine.player, event.tile.x, event.tile.y)


class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.KeySym.ESCAPE:
            self.on_quit()


CURSOR_Y_KEYS = {
    tcod.event.KeySym.UP: -1,
    tcod.event.KeySym.DOWN: 1,
    tcod.event.KeySym.PAGEUP: -10,
    tcod.event.KeySym.PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.console.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=libtcodpy.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.KeySym.HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.KeySym.END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
        return None


class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default, any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.KeySym.LSHIFT,
            tcod.event.KeySym.RSHIFT,
            tcod.event.KeySym.LCTRL,
            tcod.event.KeySym.RCTRL,
            tcod.event.KeySym.LALT,
            tcod.event.KeySym.RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """By default, any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default, this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)


class InventoryEventHandler(AskUserEventHandler):
    """This handler lets the user select an item.

    What happens then depends on the subclass.
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                is_equipped = self.engine.player.equipment.item_is_equipped(item)
                item_string = f"({item_key}) {item.name}"
                if item.ammo:
                    if item.ammo.stacks > 1:
                        item_string = f"({item_key}) {item.ammo.stacks} {item.name}s"
                elif is_equipped:
                    if item.equippable.equipment_type == EquipmentType.Container:
                        item_string = f"({item_key}) {item.name} {item.equippable.num_of_ammo}/ {item.equippable.capacity} (E)"
                    else:
                        item_string = f"{item_string} (E)"
                elif item.equippable:
                    if item.equippable.equipment_type == EquipmentType.Container:
                        item_string = f"({item_key}) {item.name} {item.equippable.num_of_ammo}/ {item.equippable.capacity}"
                else:
                    item_string = f"({item_key}) {item.name}"

                console.print(x + 1, y + i + 1, item_string)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)
        elif item.ammo:
            if self.engine.player.equipment.weapon:
                if self.engine.player.equipment.weapon.equippable.type == "Ranged":
                    return actions.LoadAction(self.engine.player, item)
                else:
                    raise exceptions.Impossible("You can't load ammo without the appropriate weapon.")
            else:
                raise exceptions.Impossible("No weapon.")
        else:
            return None


class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item."""
        return actions.DropItem(self.engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.rgb["bg"][x, y] = color.white
        console.rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """Lets the player look around using the keyboard."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return to main handler."""
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
            self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
            self,
            engine: Engine,
            radius: int,
            callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.rgb["fg"] //= 8
        console.rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=libtcodpy.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=50,
            height=14,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=1, string="Congratulations! You level up!")
        console.print(x=x + 1, y=2, string="Select an attribute to increase.")

        console.print(
            x=x + 1,
            y=4,
            string=f"a) Constitution (+1 Constitution, from {self.engine.player.fighter.constitution})",
        )
        console.print(
            x=x + 1,
            y=5,
            string=f"b) Strength (+1 Strength, from {self.engine.player.fighter.strength})",
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"c) Dexterity (+1 Dexterity, from {self.engine.player.fighter.dexterity})",
        )
        console.print(
            x=x + 1,
            y=7,
            string=f"d) Agility (+1 Agility, from {self.engine.player.fighter.agility})",
        )
        console.print(
            x=x + 1,
            y=8,
            string=f"e) Magic (+1 Magic, from {self.engine.player.fighter.magic})",
        )
        console.print(
            x=x + 1,
            y=9,
            string=f"f) Awareness (+1 Awareness, from {self.engine.player.fighter.awareness})",
        )
        console.print(
            x=x + 1,
            y=10,
            string=f"g) Charisma (+1 Charisma, from {self.engine.player.fighter.charisma})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if 0 <= index <= 6:
            if index == 0:
                player.level.increase_constitution()
            elif index == 1:
                player.level.increase_strength()
            elif index == 2:
                player.level.increase_dexterity()
            elif index == 3:
                player.level.increase_agility()
            elif index == 4:
                player.level.increase_magic()
            elif index == 5:
                player.level.increase_awareness()
            else:
                player.level.increase_charisma()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=22,  # Updated height to accommodate additional stats
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(
            x=x + 1, y=y + 1, string=f"Health Points: {self.engine.player.fighter.hp}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"Mana Points: {self.engine.player.fighter.mp}"
        )
        console.print(
            x=x + 1, y=y + 3, string=f"Stamina Points: {self.engine.player.fighter.sp}"
        )
        console.print(
            x=x + 1, y=y + 4, string=f"Soul Points: {self.engine.player.fighter.se}"
        )

        console.print(
            x=x + 1, y=y + 5, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 6, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 7,
            string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
        )
        console.print(
            x=x + 1, y=y + 8, string=f"Attack: {self.engine.player.fighter.power}"
        )
        console.print(
            x=x + 1, y=y + 9, string=f"Weapon Damage: {self.engine.player.equipment.damage_range}"
        )
        console.print(
            x=x + 1, y=y + 10, string=f"Defense: {self.engine.player.fighter.defense}"
        )
        console.print(
            x=x + 1, y=y + 11, string=f"Magical Attack: {self.engine.player.fighter.magical_attack}"
        )
        console.print(
            x=x + 1, y=y + 12, string=f"Sight Range: {self.engine.player.fighter.sight_range}"
        )
        console.print(
            x=x + 1, y=y + 13, string=f"Strength: {self.engine.player.fighter.strength}"
        )
        console.print(
            x=x + 1, y=y + 14, string=f"Dexterity: {self.engine.player.fighter.dexterity}"
        )
        console.print(
            x=x + 1, y=y + 15, string=f"Agility: {self.engine.player.fighter.agility}"
        )
        console.print(
            x=x + 1, y=y + 16, string=f"Constitution: {self.engine.player.fighter.constitution}"
        )
        console.print(
            x=x + 1, y=y + 17, string=f"Magic: {self.engine.player.fighter.magic}"
        )
        console.print(
            x=x + 1, y=y + 18, string=f"Awareness: {self.engine.player.fighter.awareness}"
        )
        console.print(
            x=x + 1, y=y + 19, string=f"Charisma: {self.engine.player.fighter.charisma}"
        )


class ConditionsViewerEventHandler(AskUserEventHandler):
    TITLE = "Active Conditions"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 15
        height = len(self.engine.player.status_effect_manager.active_effects) + 2

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        for i, effect in enumerate(self.engine.player.status_effect_manager.active_effects):
            duration_str = f" ({effect.duration} turns left)"
            console.print(x=x + 1, y=y + i + 1, string=effect.name + duration_str)


class AbilitiesEventHandler(AskUserEventHandler):
    """This handler lets the user select an item.

    What happens then depends on the subclass.
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """Render a skill menu, which displays the skills in abilities, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_skills_in_abilities = len(self.engine.player.abilities.active_skills)

        height = number_of_skills_in_abilities + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_skills_in_abilities > 0:
            for i, item in enumerate(self.engine.player.abilities.active_skills):
                item_key = chr(ord("a") + i)

                item_string = f"({item_key}) {item.name}"
                console.print(x + 1, y + i + 1, item_string)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if 0 <= index <= 26:
            try:
                selected_skill = player.abilities.active_skills[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_skill_selected(selected_skill)
        return super().ev_keydown(event)

    def on_skill_selected(self, skill: ActiveSkill) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()


class AbilitiesActivateHandler(AbilitiesEventHandler):
    """Handle using a skill."""

    TITLE = "Select a skill to use"

    def on_skill_selected(self, skill: ActiveSkill) -> Optional[ActionOrHandler]:
        return skill.activate()
