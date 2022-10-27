from components.base_component import BaseComponent
from components.equipment import Equipment
from equipment_types import EquipmentType
from entity import Item

class Equippable(BaseComponent):
    parent: Item

    def __init__(
        self,
        equipment_type: EquipmentType,
    ):
        self.equipment_type = equipment_type

class BasicRod(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ROD)
