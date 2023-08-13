from __future__ import annotations

import lzma
import random
from typing import TYPE_CHECKING

import dill
from tcod.console import Console
from tcod.map import compute_fov

import color
import exceptions
import render_functions
from message_log import MessageLog

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.player = player
        self.mouse_location = (0, 0)

        # Create a turn based system

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    if entity.fighter.time > 0:
                        while entity.fighter.time > 0:
                            entity.ai.perform()
                            if entity.level.requires_level_up:
                                level_up_options = entity.level.level_up_options
                                level_up_option = random.choice(level_up_options)
                                level_up_option()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.
                # parent.status_effect_manager.add_effect(regeneration_effect)
                entity.status_effect_manager.update_effects()
                entity.conditions_manager.reduce_conditions_duration()
                entity.abilities.update_cooldowns()
                entity.fighter.time = entity.fighter.max_time

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=self.player.fighter.sight_range,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        self.game_map.render(console)
        self.message_log.render(console=console, x=21, y=45, width=40, height=5)
        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )
        render_functions.render_extra_bar(console=console,
                                          xpos=24,
                                          render_text="MP",
                                          fill_color=color.blue,
                                          empty_color=color.dark_blue,
                                          current_value=self.player.fighter.mp,
                                          maximum_value=self.player.fighter.max_mp,
                                          total_width=12)

        render_functions.render_extra_bar(console=console,
                                          xpos=39,
                                          render_text="SP",
                                          fill_color=color.yellow,
                                          empty_color=color.orange,
                                          current_value=self.player.fighter.sp,
                                          maximum_value=self.player.fighter.max_sp,
                                          total_width=12)

        render_functions.render_extra_bar(console=console,
                                          xpos=53,
                                          render_text="SE",
                                          fill_color=color.pink,
                                          empty_color=color.white,
                                          current_value=self.player.fighter.se,
                                          maximum_value=self.player.fighter.max_se,
                                          total_width=12)

        render_functions.render_extra_bar(console=console,
                                          xpos=68,
                                          render_text="Time",
                                          fill_color=color.dark_blue,
                                          empty_color=color.black,
                                          current_value=self.player.fighter.time,
                                          maximum_value=self.player.fighter.max_time,
                                          total_width=12)

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47),
        )

        render_functions.render_names_at_mouse_location(
            console=console, x=21, y=44, engine=self
        )
        if self.player.equipment.weapon and self.player.equipment.weapon.equippable.type == "Ranged":
            # Print ammo amount, then below the ammo name and damage
            if self.player.equipment.weapon.equippable.category == "Bow":
                if self.player.equipment.back:
                    quiver = self.player.equipment.back
                    console.print(x=62, y=46,
                                  string=f'''Ammo:{quiver.equippable.num_of_ammo}/{quiver.equippable.capacity}''')
                    if quiver.equippable.items:
                        console.print(x=62, y=47, string=f"Active Ammo: {quiver.equippable.items[0].name}")
                        console.print(x=62, y=48, string=f"Damage:{quiver.equippable.items[0].ammo.damage}")
            else:
                weapon = self.player.equipment.weapon
                console.print(x=58, y=46,
                              string=f'''Ammo:{weapon.equippable.num_of_ammo}/{weapon.equippable.max_ammo}''')
                if weapon.equippable.num_of_ammo>0:
                    console.print(x=58, y=47, string=f"Active Ammo: {weapon.equippable.current_ammo[0].name}")
                    console.print(x=58, y=48, string=f"Damage:{weapon.equippable.current_ammo[0].ammo.damage}")


    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(dill.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)
