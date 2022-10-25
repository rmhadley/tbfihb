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

    def is_equipped(self, equipment: Equipment, slot: str) -> bool:
        equipped_slot = getattr(equipment, slot)

        if equipped_slot:
            if equipped_slot.equippable == self:
                return True

        return False

class Dagger(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON)
