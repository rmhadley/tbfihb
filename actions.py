from __future__ import annotations

import random
import math
from typing import Optional, Tuple, TYPE_CHECKING

import color
import exceptions
from render_functions import get_names_at_location

class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.sorted_stacked_items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You picked up the {item.name}!")
                return

        raise exceptions.Impossible("There is nothing here to pick up.")

class AbilityAction(Action):
    def __init__(
        self, entity: Actor, ability: Enchant, targets_xy: Optional[List[Tuple[int, int]]] = None
    ):
        super().__init__(entity)
        self.ability = ability
        if not targets_xy:
            target_xy = entity.x, entity.y
        self.target_xy = targets_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        self.ability.activate(self, self.target_xy)

class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self)

class DropItem(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)

        self.entity.inventory.drop(self.item)

class WaitAction(Action):
    def perform(self) -> None:
        pass

class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        if self.entity.equipment.weapon:
            damage = random.randint(self.entity.equipment.min_damage, self.entity.equipment.max_damage)
        else:
            damage = random.randint(self.entity.fighter.unarmed_min_damage, self.entity.fighter.unarmed_max_damage)


        spicy = ""
        if self.entity.fighter.empowered > 0:
            damage = damage * 2
            self.entity.fighter.empowered -= 1
            spicy = "..... SPICY!"

        damage_reduction = random.randint(0, target.fighter.defense)
        guranteed_damage_reduction_percent = ((target.fighter.defense ** 0.25) * 16) / 100
        guranteed_damage_reduction = int(damage * guranteed_damage_reduction_percent)
        if guranteed_damage_reduction > (target.fighter.defense / 2):
            guranteed_damage_reduction = (target.fighter.defense / 2)
        if damage_reduction < guranteed_damage_reduction:
            damage_reduction = guranteed_damage_reduction

        final_damage = damage - damage_reduction

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if final_damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {final_damage} hit points.{spicy}", attack_color
            )
            target.fighter.hp -= final_damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )

class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")

        entity = self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
        if entity:
            if entity.is_npc:
                return entity.interact()
            else:
                # Destination is blocked by an entity.
                raise exceptions.Impossible("That way is blocked.")
        
        if self.entity == self.engine.player:
            names = ", ".join(
                entity.name for entity in self.engine.game_map.entities if entity.x == self.entity.x + self.dx and entity.y == self.entity.y + self.dy and entity.char != ""
            )
            if names:
                self.engine.message_log.add_message(
                    "You see here: " + names, color.white
                )
            if self.entity.skills.hooked:
                self.entity.skills.unhook()
                self.engine.message_log.add_message(
                    "You lose your hook as you move."
                )

        self.entity.move(self.dx, self.dy)

class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()

class NeutralAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return None
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()

class DownStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs down
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            #self.engine.game_world.generate_floor()
            self.engine.game_world.move(1)
            self.engine.message_log.add_message(
                "You descend the staircase.", color.stairs_move
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")

class EmbarkAction(Action):
    def perform(self) -> None:
        if self.engine.quest != None:
            self.engine.game_world.embark()
            self.engine.message_log.add_message(
                "You embark on your quest", color.stairs_move
            )
        else:
            raise exceptions.Impossible("You must accept a quest first.")

class ReturnAction(Action):
    def perform(self) -> None:
        if self.engine.quest != None:
            if self.engine.quest.embarked:
                self.engine.game_world.return_city()
                self.engine.quest.embarked = False
                self.engine.quest = None
                self.engine.caught = []
                self.engine.player.fighter.heal(10000)
                self.engine.message_log.add_message(
                    "You retrun from your quest.", color.stairs_move
                )
            else:
                raise exceptions.Impossible("You must embark on a quest first.")
        else:
            raise exceptions.Impossible("You must accept a quest first.")

class UpStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs up
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.upstairs_location:
            self.engine.game_world.move(-1)
            self.engine.message_log.add_message(
                "You ascend the staircase.", color.stairs_move
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")

class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)
