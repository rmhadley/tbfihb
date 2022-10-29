from collections import OrderedDict

import components.equippable

class CraftingTree():
    def __init__(
        self,
        name: str,
    ):
        self.name = name
        self.Rod = OrderedDict()
        self.Hat = OrderedDict()
        self.Vest = OrderedDict()
        self.Pants = OrderedDict()
        self.Boots = OrderedDict()
        self.Gloves = OrderedDict()

    @property
    def visible(self) -> bool:
        return True

class GoldfishTree(CraftingTree):
    def __init__(self) -> None:
        super().__init__(name="Goldfish")
        self.Rod[0] = components.equippable.GoldRod()
        self.Rod[1] = components.equippable.GoldRod2()
        self.Rod[2] = components.equippable.GreatGoldRod()

        self.Hat[0] = components.equippable.GoldHat()
        self.Hat[1] = components.equippable.GoldHat2()
        self.Hat[2] = components.equippable.GreatGoldHat()

        self.Vest[0] = components.equippable.GoldVest()
        self.Vest[1] = components.equippable.GoldVest2()
        self.Vest[2] = components.equippable.GreatGoldVest()

        self.Pants[0] = components.equippable.GoldPants()
        self.Pants[1] = components.equippable.GoldPants2()
        self.Pants[2] = components.equippable.GreatGoldPants()

        self.Boots[0] = components.equippable.GoldBoots()
        self.Boots[1] = components.equippable.GoldBoots2()
        self.Boots[2] = components.equippable.GreatGoldBoots()

        self.Gloves[0] = components.equippable.GoldGloves()
        self.Gloves[1] = components.equippable.GoldGloves2()
        self.Gloves[2] = components.equippable.GreatGoldGloves()

CraftingTrees = [GoldfishTree()]
