from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction, NeutralAction

if TYPE_CHECKING:
    from entity import Actor

class BaseAI(Action):
    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an enitiy blocks movement and the cost isn't zero (blocking.)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]

class NPCAI(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        return None

class NeutralEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))

        chance = random.randint(0, 100)
        target_chance = 100 - self.entity.fighter.avoidance
        if distance <= 2 or (distance < (self.entity.fighter.avoidance / 10) and chance >= target_chance):
            # too close move away if possible
            direction_x = -1 if (self.entity.x - target.x) < 0 else 1
            direction_y = -1 if (self.entity.y - target.y) < 0 else 1
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )

        return NeutralAction(self.entity, direction_x, direction_y,).perform()

class GoldfishAI(NeutralEnemy):
    def perform(self) -> None:
        if self.engine.player.skills.hooked != None:
            if self.engine.player.skills.hooked.name == "Great Goldfish":
                chance = random.randint(1, 2)
                if chance == 1:
                    self.entity.color = (255,69,0)
                else:
                    self.entity.color=(255, 215, 0)
                temp_ai = HostileEnemy(self.entity)
                temp_ai.perform()
            else:
                super().perform()
        else:
            self.entity.color=(255, 215, 0)
            super().perform()

class HookedEnemy(BaseAI):
    def __init__(self, entity: Actor, previous_ai: BaseAI):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []
        self.previous_ai = previous_ai

    def perform(self) -> None:
        chance = random.randint(0, 100)
        target_chance = 100 - self.entity.fighter.difficulty + self.entity.fighter.fatigue

        if chance >= target_chance or chance == 100:
            self.entity.fighter.fatigue += random.randint(5, 10)
            if self.entity.fighter.fatigue > 100:
                self.entity.fighter.fatigue = 100

            self.entity.fighter.hooked = self.entity.fighter.hooked - (self.entity.fighter.strength * random.randint(1, 2))
            if self.entity.fighter.hooked <= 0:
                self.entity.fighter.hooked = 0
                self.engine.player.skills.unhook()
                self.entity.ai = ScaredEnemy(self.entity, self.entity.ai)

            direction_x = -1 if (self.entity.x - self.engine.player.x) < 0 else 1
            direction_y = -1 if (self.entity.y - self.engine.player.y) < 0 else 1

            return NeutralAction(self.entity, direction_x, direction_y,).perform()
        else:
            self.entity.fighter.fatigue += random.randint(5, 10)
            if self.entity.fighter.fatigue > 100:
                self.entity.fighter.fatigue = 100
            return None

    def reel(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y

        self.path = self.get_path_to(target.x, target.y)

        dest_x, dest_y = self.path.pop(0)
        return MovementAction(
            self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
        ).perform()

    def unhook(self) -> None:
        self.entity.ai = self.previous_ai

class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()

class ScaredEnemy(BaseAI):
    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI]
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.previous_color = entity.color
        self.previous_difficulty = entity.fighter.difficulty
        entity.fighter.difficulty = entity.fighter.difficulty * 3
        entity.color = (255,69,0)

        # Let's do some bad coding and brute force a spot far away
        random_x = random.randint(0, self.engine.game_map.width)
        random_y = random.randint(0, self.engine.game_map.height)
        self.dest_x = 0
        self.dest_y = 0
        target = self.engine.player

        while self.dest_x == 0 and self.dest_y == 0:
            try:
                if self.engine.game_map.tiles[random_x, random_y]["walkable"]:
                    dx = target.x - random_x
                    dy = target.y - random_y
                    distance = max(abs(dx), abs(dy))

                    if distance >= 30:
                        self.dest_x = random_x
                        self.dest_y = random_y
            except:
                print("out of bounds I guess")
            random_x = random.randint(0, self.engine.game_map.width)
            random_y = random.randint(0, self.engine.game_map.height)

        self.engine.message_log.add_message(
            f"You've freightened {self.entity.name}!"
        )

    def perform(self) -> None:
        target = self.entity
        dx = target.x - self.dest_x
        dy = target.y - self.dest_y
        distance = max(abs(dx), abs(dy))
        if distance <= 1:
            self.engine.message_log.add_message(
                f"The {self.entity.name} is no longer scared."
            )
            self.entity.ai = self.previous_ai
            self.entity.fighter.difficulty = self.previous_difficulty
            self.entity.color = self.previous_color
        else:
            self.path = self.get_path_to(self.dest_x, self.dest_y)
            x, y = self.path.pop(0)
            return MovementAction(
                self.entity, x - self.entity.x, y - self.entity.y,
            ).perform()
