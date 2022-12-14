from __future__ import annotations

import copy
import math
import random
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union
    
import components.quests
import components.menus
from render_order import RenderOrder


T = TypeVar("T", bound="Entity")

class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """
    is_npc = False

    parent: Union[GameMap, Inventory]

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
            # If parent isn't provided now then it will be set later.
            self.parent = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int, rarity_chances: Optional[{}]) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Place this entity at a new location.  Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):  # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy

class NPC(Entity):
    is_npc = True

    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type[BaseAI],
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

    def spawn(self: T, gamemap: GameMap, x: int, y: int, rarity_chances: {}) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)

        return clone

    def interact(self) -> None:
        raise NotImplementedError()

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)

class Fisherman(NPC):
    HELLO = "Sup? I got a job for you."
    quests = []
    menu = None

    def interact(self) -> None:
        self.quests = []

        self.quests.append(components.quests.OceanQuest())
        self.quests.append(components.quests.CloudsQuest())

        self.gamemap.engine.npc = self
        return None

class Crafter(NPC):
    HELLO = "Let's craft some gear."
    quests = []
    menu = None

    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type[BaseAI],
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            ai_cls=ai_cls,
        )
        self.menu = components.menus.CraftMenu()

    def interact(self) -> None:
        self.gamemap.engine.npc = self
        return None

class Stash(NPC):
    HELLO = "Your Stash"
    quests = []

    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type[BaseAI],
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            ai_cls=ai_cls,
        )
        self.menu = components.menus.StashMenu()

    def interact(self) -> None:
        self.gamemap.engine.npc = self
        return None

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
        equipment: Equipment,
        skills: Skills,
        fighter: Fighter,
        inventory: Inventory,
        level: Level,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.equipment: Equipment = equipment
        self.equipment.parent = self

        self.skills: Skills = skills
        self.skills.parent = self

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.level = level
        self.level.parent = self

    def spawn(self: T, gamemap: GameMap, x: int, y: int, rarity_chances: {}) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)

        return clone

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)

class Item(Entity):
    count = 1

    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        stackable: bool = False,
        consumable: Optional[Consumable] = None,
        equippable: Optional[Equippable] = None,
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


        self.stackable = stackable

        self.consumable = consumable

        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable

        if self.equippable:
            self.equippable.parent = self

    def spawn(self: T, gamemap: GameMap, x: int, y: int, rarity_chances: {}) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)

        if self.equippable:
            min_ilvl = int(gamemap.engine.game_world.current_floor * 0.5)
            max_ilvl = int(gamemap.engine.game_world.current_floor * 1.5)

            clone.equippable.rarity = random.choices(
                list(rarity_chances.keys()), weights=list(rarity_chances.values())
            )[0]
            clone.color = clone.equippable.get_color()
            clone.equippable.ilvl = random.randint(min_ilvl, max_ilvl)
            clone.name = "+" + str(clone.equippable.ilvl) + " " + clone.name
            clone.equippable.enchant()

        return clone

    def get_use_text(self, player: Actor) -> str:
        if self.equippable:
            if self.equippable.is_equipped(player.equipment, "weapon") or self.equippable.is_equipped(player.equipment, "armor") or self.equippable.is_equipped(player.equipment, "head") or self.equippable.is_equipped(player.equipment, "hands") or self.equippable.is_equipped(player.equipment, "pants") or self.equippable.is_equipped(player.equipment, "shoes"):
                return "(U)nequip"
            else:
                return "(E)quip"
        elif self.consumable:
            return self.consumable.get_use_text()

    @property
    def description(self) -> str:
        description = f"{self.name}\n\n"
        if self.equippable:
            description += self.equippable.description
        elif self.consumable:
            description += self.consumable.description

        return description
