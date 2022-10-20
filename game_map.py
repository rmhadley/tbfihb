from __future__ import annotations

from typing import Iterable, Iterator, Optional, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console
import random
import tcod

from entity import Actor, Item
from components.ai import HookedEnemy
import tile_types
import color

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player has seen before
        self.downstairs_location = (0, 0)
        self.upstairs_location = (0, 0)

    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this maps living actors."""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Item)
        )

    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int,
    ) -> Optional[Entity]:
        for entity in self.entities:
            if (
                entity.blocks_movement
                and entity.x == location_x
                and entity.y == location_y
            ):
                return entity

        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor

        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the "light" colors.
        If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
        Otherwise, the default is "SHROUD".
        """

        for tile in np.nditer(self.tiles, op_flags=['readwrite']):
            random_tile = random.randint(1, 4)
            if random_tile == 1:
                tile["light"] = tile["light1"]
                tile["dark"] = tile["dark1"]
            elif random_tile == 2:
                tile["light"] = tile["light2"]
                tile["dark"] = tile["dark2"]
            elif random_tile == 3:
                tile["light"] = tile["light3"]
                tile["dark"] = tile["dark3"]
            elif random_tile == 4:
                tile["light"] = tile["light4"]
                tile["dark"] = tile["dark4"]

        console.rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            # Only print entities that are in the FOV
            if self.visible[entity.x, entity.y]:
                console.print(
                    x=entity.x, y=entity.y, string=entity.char, fg=entity.color
                )
                if isinstance(entity.ai, HookedEnemy):
                    cost = np.array(self.tiles["walkable"], dtype=np.int8)
                    graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
                    pathfinder = tcod.path.Pathfinder(graph)

                    pathfinder.add_root((self.engine.player.x, self.engine.player.y))  # Start position.

                    # Compute the path to the destination and remove the starting point.
                    path: List[List[int]] = pathfinder.path_to((entity.x, entity.y))[1:].tolist()

                    # Convert from List[List[int]] to List[Tuple[int, int]].
                    path = [(index[0], index[1]) for index in path]
                    for xy in path:
                        console.tiles_rgb["bg"][xy[0], xy[1]] = color.white
                        console.tiles_rgb["fg"][xy[0], xy[1]] = color.black

class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 1
    ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.current_floor = current_floor

        self.game_maps = {}

    def generate_floor(self) -> None:
        from maps.ocean import generate_dungeon

        self.game_maps[self.current_floor] = generate_dungeon(
            max_rooms=self.max_rooms,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            engine=self.engine,
        )

    def move(self, direction: int) -> None:
        self.current_floor += direction
        if not self.current_floor in self.game_maps:
            self.generate_floor()
        self.engine.game_map = self.game_maps[self.current_floor]
        
        if direction < 0:
            self.engine.player.place(*self.engine.game_map.downstairs_location, self.engine.game_map)
        else:
            self.engine.player.place(*self.engine.game_map.upstairs_location, self.engine.game_map)
