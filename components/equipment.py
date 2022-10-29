from __future__ import annotations

from typing import Optional

from components.base_component import BaseComponent
from components.equippable import Equippable
from entity import Actor

class Equipment(BaseComponent):
    parent: Actor

    def __init__(self):
        self.Rod = None
        self.Hat = None
        self.Vest = None
        self.Pants = None
        self.Boots = None
        self.Gloves = None

    @property
    def slots(self) -> List:
        return ["Rod", "Hat", "Vest", "Pants", "Boots", "Gloves"]

    def equip(self, slot=str, item=Equippable) -> None:
        match slot:
            case "Rod":
                self.Rod = item
            case "Hat":
                self.Hat = item
            case "Vest":
                self.Vest = item
            case "Pants":
                self.Pants = item
            case "Boots":
                self.Boots = item
            case "Gloves":
                self.Gloves = item
        return None
