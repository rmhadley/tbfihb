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

    @property
    def slots(self) -> List:
        return ["Rod", "Hat"]

    def equip(self, slot=str, item=Equippable) -> None:
        match slot:
            case "Rod":
                self.Rod = item
            case "Hat":
                self.Hat = item
        return None
