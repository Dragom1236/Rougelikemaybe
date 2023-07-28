from __future__ import annotations
from typing import Tuple, List, TYPE_CHECKING

if TYPE_CHECKING:
    from procgen import RectangularRoom, Corridor


def directional_line(start: Tuple[int, int], direction: Tuple[int, int], length: int) -> List[Tuple[int, int]]:
    line_points = []
    current_pos = start

    for i in range(length):
        line_points.append(current_pos)
        current_pos = vector2addition(current_pos, direction)
    # print(line_points)

    return line_points


def is_point_inside_room(point: Tuple[int, int], room: RectangularRoom) -> bool:
    return room.x1 < point[0] < room.x2 and room.y1 < point[1] < room.y2


def is_point_inside_corridor(point: Tuple[int, int], corridor: Corridor) -> bool:
    return point in corridor.corridor_points


def dir_line_checker(start: Tuple[int, int], direction: Tuple[int, int], length: int,
                     existing_rooms: List[RectangularRoom], existing_corridors: List[Corridor]) -> List or None:
    line_points = directional_line(start, direction, length)
    id_string = ""
    intersected_room_or_corridor = None
    intersection_point = None

    for point in line_points:
        for room in existing_rooms:
            if is_point_inside_room(point, room):
                intersected_room_or_corridor = room
                intersection_point = point
                id_string = "room"
                break
        if intersected_room_or_corridor is not None:
            break

        for corridor in existing_corridors:
            if is_point_inside_corridor(point, corridor):
                intersected_room_or_corridor = corridor
                intersection_point = point
                id_string = "corridor"
                break
        if intersected_room_or_corridor is not None:
            break

    if intersected_room_or_corridor is not None:
        # print(intersection_point)
        index_of_intersection = line_points.index(intersection_point)
        # print(index_of_intersection)
        points_up_to_intersection = line_points[0: index_of_intersection + 1]
        # print(points_up_to_intersection)
        # print(intersected_room_or_corridor)
        return [intersected_room_or_corridor, points_up_to_intersection]
    else:
        return None


def vector2addition(a: Tuple[int, int], b: Tuple[int, int]):
    a = list(a)
    a[0] += b[0]
    a[1] += b[1]
    a = tuple(a)
    return a


def list_list_to_tuple_list(a: List[List]):
    return [tuple(n) for n in a]
