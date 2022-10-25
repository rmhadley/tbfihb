from __future__ import annotations

import random
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING

import tcod
import numpy as np

import entity_factories
from entity import Item
from game_map import GameMap
from rarity_levels import RarityLevel
import tile_types

class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1, self.x2), slice(self.y1, self.y2)

    @property
    def full(self) -> Tuple[slice, slice]:
        """Return the full area of this room as a 2D array index."""
        return slice(self.x1 - 1, self.x2 + 1), slice(self.y1 - 1, self.y2 + 1)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
            self.x1 - 1 <= other.x2 + 1
            and self.x2 + 1 >= other.x1 - 1
            and self.y1 - 1 <= other.y2 + 1
            and self.y2 + 1 >= other.y1 - 1
        )

    @property
    def door(self) -> Tuple[int, int]:
        side = random.randint(1, 4)
        match side:
            case 1: #top
                x = random.randint(self.x1, self.x2 - 1)
                y = self.y1 - 1 
            case 2: #right
                x = self.x2
                y = random.randint(self.y1, self.y2 - 1)
            case 3: #bottom
                x = random.randint(self.x1, self.x2 - 1)
                y = self.y2
            case 4: #left
                x = self.x1 - 1
                y = random.randint(self.y1, self.y2 - 1)
        return (x, y)

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

    dungeon.tiles = np.full((map_width, map_height), fill_value=tile_types.city_floor, order="F")
    dungeon.explored = np.full((map_width, map_height), fill_value=True, order="F")

    rooms: List[RectangularRoom] = []

    # Make the shore
    room_min_size = 5
    room_max_size = 10

    room_width = map_width
    room_height = random.randint(room_min_size, room_max_size)
    shore_height = room_height

    new_room = RectangularRoom(0, 0, room_width, room_height)
    dungeon.tiles[new_room.inner] = tile_types.ocean_wall
    rooms.append(new_room)

    # Make the shopping/crafting building
    room_not_valid = True

    room_min_size = 5
    room_max_size = 10

    while room_not_valid:
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(2, dungeon.width - room_width - 2)
        y = random.randint(shore_height + 2, dungeon.height - room_height - 2)

        new_room = RectangularRoom(x, y, room_width, room_height)

        if not any(new_room.intersects(other_room) for other_room in rooms):
            room_not_valid = False

    npc_x = random.randint(new_room.x1 + 1, new_room.x2 - 1)
    npc_y = random.randint(new_room.y1 + 1, new_room.y2 - 1)
    # crafter
    entity_factories.crafter.spawn(dungeon, npc_x, npc_y, "")

    dungeon.tiles[new_room.full] = tile_types.wall
    dungeon.tiles[new_room.inner] = tile_types.city_floor
    for door in range(random.randint(1, 4)):
        dungeon.tiles[new_room.door] = tile_types.city_floor

    rooms.append(new_room)

    # Make the pub building
    room_not_valid = True

    room_min_size = 5
    room_max_size = 5

    while room_not_valid:
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(2, dungeon.width - room_width - 2)
        y = random.randint(shore_height + 2, dungeon.height - room_height - 2)

        new_room = RectangularRoom(x, y, room_width, room_height)

        if not any(new_room.intersects(other_room) for other_room in rooms):
            room_not_valid = False

    dungeon.tiles[new_room.full] = tile_types.wall
    dungeon.tiles[new_room.inner] = tile_types.city_floor
    for door in range(random.randint(1, 1)):
        dungeon.tiles[new_room.door] = tile_types.city_floor

    rooms.append(new_room)

    # Make the spaceport building
    room_not_valid = True

    room_min_size = 10 
    room_max_size = 15

    while room_not_valid:
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(2, dungeon.width - room_width - 2)
        y = random.randint(shore_height + 2, dungeon.height - room_height - 2)

        new_room = RectangularRoom(x, y, room_width, room_height)

        if not any(new_room.intersects(other_room) for other_room in rooms):
            room_not_valid = False

    dungeon.tiles[new_room.full] = tile_types.wall
    dungeon.tiles[new_room.inner] = tile_types.city_floor
    for door in range(random.randint(1, 6)):
        dungeon.tiles[new_room.door] = tile_types.city_floor

    rooms.append(new_room)

    # Docks
    dock_width = random.randint(2, 4)
    dock_x = random.randint(5, dungeon.width - dock_width - 5)
    dock_y = 0
    dungeon.tiles[slice(dock_x, dock_x + dock_width), slice(dock_y, dock_y + shore_height)] = tile_types.dock_water

    # fisherman
    entity_factories.fisherman.spawn(dungeon, dock_x, shore_height - 1, "")

    bottom = 0
    dungeon.player_start = [random.randint(dock_x, dock_x + dock_width - 1), dock_y]

    player.place(*dungeon.player_start, dungeon)

    return dungeon
