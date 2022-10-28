from components.base_component import BaseComponent
from entity import Item

class Equippable(BaseComponent):
    parent: Item

    def __init__(
        self,
        name: str,
        slot: str,
    ):
        self.name = name
        self.slot = slot

class BasicRod(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Basic Fishing Rod", slot="Rod")

class GoldRod(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Rod", slot="Rod")
