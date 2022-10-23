from __future__ import annotations

import random

import color
import actions
from components.base_component import BaseComponent
from components.ai import HostileEnemy, NeutralEnemy, HookedEnemy, ScaredEnemy
from input_handlers import BeamRangedAttackHandler

class Skills(BaseComponent):
    parent: Actor
    hooked: Actor

    def __init__(self):
        self.known_normal = []
        self.known_hooked = []
        self.learn(self.known_normal, CastLine())
        self.learn(self.known_hooked, Reel())
        self.learn(self.known_hooked, Unhook())
        self.hooked = None

    def learn(self, known: [], skill: Skill) -> None:
        skill.parent = self
        known.append(skill)

    @property
    def known(self) -> List:
        if self.hooked == None:
            return self.known_normal
        else:
            return self.known_hooked

    def unhook(self) -> None:
        if not self.hooked.ai == None:
            self.hooked.ai.unhook()
        self.hooked = None

class Skill(BaseComponent):
    parent: Actor

    def __init__(self, name: str) -> None:
        self.level = 1
        self.name = name

    def get_action(self, user: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this ability."""
        return actions.AbilityAction(user, self)

class Reel(Skill):
    def __init__(self) -> None:
        super().__init__(
            name="Reel in Line",
        )

    @property
    def description(self) -> str:
        description = f"Attempt to reel in your fishing line."

        return description

    def activate(self, action: actions.AbilityAction, path: Tuple[int, int]) -> None:
        chance = random.randint(0, 100)
        target_chance = self.parent.hooked.fighter.difficulty + (self.level * 2)
        if chance < target_chance and chance != 0:
            target = self.engine.player
            dx = self.parent.parent.x - self.parent.hooked.x

            dy = self.parent.parent.y - self.parent.hooked.y
            distance = max(abs(dx), abs(dy))  # Chebyshev distance.

            if distance == 1:
                self.engine.caught.append(self.parent.hooked)
                self.parent.hooked.char = ""
                self.parent.hooked.blocks_movement = False
                self.parent.hooked.ai = None
                self.parent.unhook()
                self.engine.message_log.add_message(
                    f"You captured it woo."
                )
            else:
                self.engine.message_log.add_message(
                    f"You reel in your line."
                )
                self.parent.hooked.ai.reel()
        else:
            self.parent.hooked.fighter.hooked = self.parent.hooked.fighter.hooked - (self.parent.hooked.fighter.strength * random.randint(1, 2))
            if self.parent.hooked.fighter.hooked <= 0:
                fish = self.parent.hooked
                fish.fighter.hooked = 0
                self.parent.unhook()
                fish.ai = ScaredEnemy(fish, fish.ai)

            self.engine.message_log.add_message(
                f"It resists."
            )

class Unhook(Skill):
    def __init__(self) -> None:
        super().__init__(
            name="Unhook fish",
        )

    @property
    def description(self) -> str:
        description = f"Release fish from hook."

        return description

    def activate(self, action: actions.AbilityAction, path: Tuple[int, int]) -> None:
        self.parent.unhook()
        self.engine.message_log.add_message(
            f"You release the fish from your hook."
        )

class CastLine(Skill):
    def __init__(self) -> None:
        super().__init__(
            name="Cast Line",
        )

    @property
    def description(self) -> str:
        description = f"Cast your fishing line."

        return description

    def get_action(self, user: Actor) -> BeamRangedAttackHandler:
        self.engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return BeamRangedAttackHandler(
            self.engine,
            callback=lambda xy: actions.AbilityAction(user, self, xy),
        )

    def activate(self, action: actions.AbilityAction, path: Tuple[int, int]) -> None:
        for xy in path:
            target = self.engine.game_map.get_actor_at_location(xy[0], xy[1])
            if target:
                chance = random.randint(0, 100)
                target_chance = target.fighter.difficulty - self.level - target.fighter.fatigue
                print(f"{chance} >= {target_chance}")
                if chance >= target_chance and chance != 0:
                    self.engine.message_log.add_message(
                        f"You hook a {target.name}!"
                    )
                    target.ai = HookedEnemy(entity=target, previous_ai=target.ai)
                    target.fighter.hooked = int(chance - target_chance + (self.level * 1.7))
                    if target.fighter.hooked > 100:
                        target.fighter.hooked = 100
                    self.parent.hooked = target
                else:
                    self.engine.message_log.add_message(
                        f"The {target.name} got away!"
                    )
