from __future__ import annotations
import random
from typing import Iterator, List, Tuple, TYPE_CHECKING, Dict

from tcod import tcod

import Algorithim
import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

max_items_by_floor = [
    (1, 30),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35), (entity_factories.dagger, 5), (entity_factories.Wooden_Arrow, 35),
        (entity_factories.Pistol, 35), (entity_factories.Crossbow, 35), (entity_factories.iron_bullet, 35),
        (entity_factories.Wooden_Bolt, 35), ],
    2: [(entity_factories.confusion_scroll, 100), (entity_factories.leather_armor, 5)],
    4: [(entity_factories.lightning_scroll, 25), (entity_factories.sword, 5)],
    6: [(entity_factories.fireball_scroll, 25), (entity_factories.chain_mail, 15)],
}

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.kobold, 80)],
    1: [(entity_factories.orc, 80)],
    3: [(entity_factories.troll, 15)],
    5: [(entity_factories.troll, 30)],
    7: [(entity_factories.troll, 60)],
}


def get_entities_at_random(
        weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
        number_of_entities: int,
        floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities


def get_max_value_for_floor(
        max_value_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        self.connections: List = []

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    @property
    def midpoints(self) -> List[Tuple]:
        top_mid = (int((self.x1 + self.x2) / 2), self.y1)

        bottom_mid = (int((self.x1 + self.x2) / 2), self.y2)

        left_mid = (self.x1, int((self.y1 + self.y2) / 2))

        right_mid = (self.x2, int((self.y1 + self.y2) / 2))
        return [top_mid, bottom_mid, left_mid, right_mid]

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
                self.x1 <= other.x2
                and self.x2 >= other.x1
                and self.y1 <= other.y2
                and self.y2 >= other.y1
        )


class Corridor:
    def __init__(self, start: Tuple[int, int], end: Tuple[int, int], points: List[Tuple[int, int]]):
        self.start_position = start
        self.end_position = end
        self.corridor_points = points
        self.connected_rooms: List[RectangularRoom] = []
        self.connected_corridors: List[Corridor] = []


def generate_dungeon(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []
    corridors: List[Corridor] = []
    upstairs_center = (0, 0)
    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor
        center_of_last_room = new_room.center

        if len(rooms) == 0:
            # The first room, where the player starts.
            upstairs_center = new_room.center
            player.place(*new_room.center, dungeon)
        # else:  # All rooms after the first.
        #     # Dig out a tunnel between this room and the previous one.
        #     for x, y in tunnel_between(rooms[-1].center, new_room.center):
        #         dungeon.tiles[x, y] = tile_types.floor
        place_entities(new_room, dungeon, engine.game_world.current_floor)
        # Finally, append the new room to the list.
        rooms.append(new_room)
    create_corridors(rooms, corridors)
    while any(r.connections is [] for r in rooms):
        create_corridors(rooms, corridors)
    # print(corridors)
    for c in corridors:
        for x, y in c.corridor_points:
            dungeon.tiles[x, y] = tile_types.floor
    dungeon.tiles[center_of_last_room] = tile_types.down_stairs
    dungeon.downstairs_location = center_of_last_room
    dungeon.tiles[upstairs_center] = tile_types.up_stairs
    dungeon.upstairs_location = upstairs_center
    dungeon.rooms = rooms
    dungeon.corridors = corridors
    return dungeon


def tunnel_between(
        start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def tunnel_between2(
        start: Tuple[int, int], end: Tuple[int, int]
) -> List:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2
    points = []
    # Generate the coordinates for this tunnel.
    points.extend(tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist())
    points.extend(tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist())
    return points


def create_corridors(rooms: List[RectangularRoom], corridors: List[Corridor]) -> None:
    for r in rooms:
        if random.randint(1, 2) == 1:
            choice = r
            while choice == r:
                choice = random.choice(rooms)
            # Dig out a tunnel between this room and the previous one.
            new_corridor = Corridor(r.center, choice.center,
                                    Algorithim.list_list_to_tuple_list(tunnel_between2(r.center, choice.center)))
            for point in new_corridor.corridor_points:
                for e in rooms:
                    if Algorithim.is_point_inside_room(point,
                                                       e) and e is not r and e not in new_corridor.connected_rooms:
                        new_corridor.connected_rooms = [r, e]
                        r.connections.append([new_corridor, e])
                        e.connections.append([new_corridor, r])
                        continue
                for t in corridors:
                    if Algorithim.is_point_inside_corridor(point,
                                                           t) and t is not new_corridor and t not in new_corridor.connected_corridors:
                        if r not in t.connected_rooms:
                            r.connections.extend([new_corridor, t, z] for z in t.connected_rooms)
                            new_corridor.connected_corridors.append(t)
                            new_corridor.connected_rooms.extend(t.connected_rooms)
                            t.connected_corridors.append(new_corridor)
                            t.connected_rooms.append(r)
                            continue
                corridors.append(new_corridor)
        else:
            i = 0
            for midpoint in r.midpoints:
                # print("mid", midpoint)
                i += 1
                # print("i", i)
                if i == 1:
                    intersection_data = Algorithim.dir_line_checker(midpoint, (0, -1), 30,
                                                                    rooms, corridors)
                    if intersection_data is None:
                        continue
                    intersection_object = intersection_data[0]
                    intersection_points = intersection_data[1]
                elif i == 2:
                    intersection_data = Algorithim.dir_line_checker(midpoint, (0, 1), 30,
                                                                    rooms, corridors)
                    if intersection_data is None:
                        continue
                    intersection_object = intersection_data[0]
                    intersection_points = intersection_data[1]
                elif i == 3:
                    intersection_data = Algorithim.dir_line_checker(midpoint, (-1, 0), 30,
                                                                    rooms, corridors)
                    if intersection_data is None:
                        continue
                    intersection_object = intersection_data[0]
                    intersection_points = intersection_data[1]
                else:
                    intersection_data = Algorithim.dir_line_checker(midpoint, (1, 0), 30,
                                                                    rooms, corridors)

                    if intersection_data is None:
                        continue
                    intersection_object = intersection_data[0]
                    intersection_points = intersection_data[1]

                if intersection_object is None:
                    # print("Yo")
                    continue
                # print("object", intersection_object)
                # print("check", intersection_object in rooms)
                if intersection_object in rooms:
                    # print("yep")
                    new_corridor = Corridor(midpoint, intersection_points[-1], intersection_points)
                    new_corridor.connected_rooms = [r, intersection_object]
                    corridors.append(new_corridor)
                    r.connections.append([new_corridor, intersection_object])
                    intersection_object.connections.append([new_corridor, r])
                else:  # intersection object is a corridor
                    # print("yessir")
                    if r not in intersection_object.connected_rooms:
                        new_corridor = Corridor(midpoint, intersection_points[-1], intersection_points)
                        # print(new_corridor)
                        # print(intersection_object)
                        new_corridor.connected_corridors = [intersection_object]
                        new_corridor.connected_rooms = [r]
                        new_corridor.connected_rooms.extend(intersection_object.connected_rooms)
                        intersection_object.connected_corridors.append(new_corridor)
                        intersection_object.connected_rooms.append(r)
                        corridors.append(new_corridor)
                        r.connections.append(new_corridor.connected_rooms)


def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int, ) -> None:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )
    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        if not any(other.x == x and other.y == y for other in dungeon.entities):
            entity.spawn(dungeon, x, y)
