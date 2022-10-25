from __future__ import annotations

from typing import Optional

from components.base_component import BaseComponent
from equipment_types import EquipmentType
from entity import Actor, Item

class Equipment(BaseComponent):
    parent: Actor

    def __init__(self, weapon: Optional[Item] = None, armor: Optional[Item] = None, hands: Optional[Item] = None, pants: Optional[Item] = None, shoes: Optional[Item] = None, head: Optional[Item] = None):
        self.weapon = weapon
        self.armor = armor
        self.hands = hands
        self.pants = pants
        self.shoes = shoes
        self.head = head

    @property
    def equipped_items(self) -> List:
        equipped = []
        if self.weapon:
            equipped.append(self.weapon)
        if self.armor:
            equipped.append(self.armor)
        if self.hands:
            equipped.append(self.hands)
        if self.pants:
            equipped.append(self.pants)
        if self.shoes:
            equipped.append(self.shoes)
        if self.head:
            equipped.append(self.head)

        return equipped

    @property
    def min_damage(self) -> int:
        adjusted_damage = 0
        if self.weapon:
            return self.weapon.equippable.min_dmg + adjusted_damage

    @property
    def max_damage(self) -> int:
        adjusted_damage = 0
        if self.weapon:
            return self.weapon.equippable.max_dmg + adjusted_damage

    def item_is_equipped(self, item: Item) -> bool:
        if item.equippable:
            match item.equippable.equipment_type:
                case EquipmentType.WEAPON:
                    slot = "weapon"
                case EquipmentType.ARMOR:
                    slot = "armor"
                case EquipmentType.HANDS:
                    slot = "hands"
                case EquipmentType.PANTS:
                    slot = "pants"
                case EquipmentType.SHOES:
                    slot = "shoes"
                case EquipmentType.HEAD:
                    slot = "head"

            return getattr(self, slot) == item
        return False

    def unequip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You equip the {item_name}."
        )

    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if add_message:
            self.unequip_message(current_item.name)

        setattr(self, slot, None)

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        if equippable_item.equippable:
            match equippable_item.equippable.equipment_type:
                case EquipmentType.WEAPON:
                    slot = "weapon"
                case EquipmentType.ARMOR:
                    slot = "armor"
                case EquipmentType.HANDS:
                    slot = "hands"
                case EquipmentType.PANTS:
                    slot = "pants"
                case EquipmentType.SHOES:
                    slot = "shoes"
                case EquipmentType.HEAD:
                    slot = "head"

        if equippable_item.equippable.is_equipped(self, slot):
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)
