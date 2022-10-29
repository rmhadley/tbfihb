from components.base_component import BaseComponent

class Equippable(BaseComponent):
    def __init__(
        self,
        name: str,
        slot: str,
        materials: dict,
    ):
        self.name = name
        self.slot = slot
        self.materials = materials
        self.skills = {}

    def can_craft(self, parts: dict) -> bool:
        can = True
        for mat in self.materials:
            try:
                count = self.materials[mat]
                part_count = parts[mat]
                if part_count < count:
                    can = False
            except KeyError:
                can = False

        return can

    def crafting_description(self, parts: dict) -> str:
        description = ""

        for mat in self.materials:
            try:
                count = self.materials[mat]
                part_count = parts[mat]
            except KeyError:
                part_count = 0

            description += f"{part_count}/{count} {mat}\n"

        return description

    def craft(self, parts: dict, stash: list):
        for mat in self.materials:
            for x in range(self.materials[mat]):
                parts.remove(mat)

        stash.append(self)

##Rods
class BasicRod(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Basic Fishing Rod", slot="Rod", materials={})
        self.skills["CastLine"] = 2
##  Goldfish Rods
class GoldRod(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Rod", slot="Rod", materials={"Goldfish Scale": 10, "Goldfish Fin": 2})
        self.skills["CastLine"] = 5
        self.skills["Reel"] = 5

class GoldRod2(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Rod 2", slot="Rod", materials={"Goldfish Scale": 10, "Goldfish Fin": 10})
        self.skills["CastLine"] = 10
        self.skills["Reel"] = 10

class GreatGoldRod(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Great Gold Rod", slot="Rod", materials={"Great Goldfish Scale": 10, "Great Goldfish Fin": 2, "Goldfish Crest": 1})
        self.skills["CastLine"] = 20
        self.skills["Reel"] = 20

##Hats
##  Goldfish Hats
class GoldHat(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Hat", slot="Hat", materials={"Goldfish Scale": 10, "Goldfish Fin": 2, "Goldfish Tail": 1})
        self.skills["CastLine"] = 5
        self.skills["Reel"] = 5

class GoldHat2(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Hat 2", slot="Hat", materials={"Goldfish Scale": 10, "Goldfish Fin": 10, "Goldfish Tail": 2})
        self.skills["CastLine"] = 10
        self.skills["Reel"] = 10

class GreatGoldHat(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Great Gold Hat", slot="Hat", materials={"Great Goldfish Scale": 10, "Great Goldfish Fin": 2, "Goldfish Crest": 1, "Great Goldfish Tail": 1})
        self.skills["CastLine"] = 20
        self.skills["Reel"] = 20

##Vests
##  Goldfish Vests
class GoldVest(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Vest", slot="Vest", materials={"Goldfish Scale": 10, "Goldfish Fin": 2, "Goldfish Tail": 1})
        self.skills["CastLine"] = 5
        self.skills["Reel"] = 5

class GoldVest2(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Vest 2", slot="Vest", materials={"Goldfish Scale": 10, "Goldfish Fin": 10, "Goldfish Tail": 2})
        self.skills["CastLine"] = 10
        self.skills["Reel"] = 10

class GreatGoldVest(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Great Gold Vest", slot="Vest", materials={"Great Goldfish Scale": 10, "Great Goldfish Fin": 2, "Goldfish Crest": 1, "Great Goldfish Tail": 1})
        self.skills["CastLine"] = 20
        self.skills["Reel"] = 20

##Pants
##  Goldfish Pants
class GoldPants(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Pants", slot="Pants", materials={"Goldfish Scale": 10, "Goldfish Fin": 2, "Goldfish Tail": 1})
        self.skills["CastLine"] = 5
        self.skills["Reel"] = 5

class GoldPants2(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Pants 2", slot="Pants", materials={"Goldfish Scale": 10, "Goldfish Fin": 10, "Goldfish Tail": 2})
        self.skills["CastLine"] = 10
        self.skills["Reel"] = 10

class GreatGoldPants(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Great Gold Pants", slot="Pants", materials={"Great Goldfish Scale": 10, "Great Goldfish Fin": 2, "Goldfish Crest": 1, "Great Goldfish Tail": 1})
        self.skills["CastLine"] = 20
        self.skills["Reel"] = 20

##Boots
##  Goldfish Boots
class GoldBoots(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Boots", slot="Boots", materials={"Goldfish Scale": 10, "Goldfish Fin": 2, "Goldfish Tail": 1})
        self.skills["CastLine"] = 5
        self.skills["Reel"] = 5

class GoldBoots2(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Boots 2", slot="Boots", materials={"Goldfish Scale": 10, "Goldfish Fin": 10, "Goldfish Tail": 2})
        self.skills["CastLine"] = 10
        self.skills["Reel"] = 10

class GreatGoldBoots(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Great Gold Boots", slot="Boots", materials={"Great Goldfish Scale": 10, "Great Goldfish Fin": 2, "Goldfish Crest": 1, "Great Goldfish Tail": 1})
        self.skills["CastLine"] = 20
        self.skills["Reel"] = 20

##Gloves
##  Goldfish Gloves
class GoldGloves(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Gloves", slot="Gloves", materials={"Goldfish Scale": 10, "Goldfish Fin": 2, "Goldfish Tail": 1})
        self.skills["CastLine"] = 5
        self.skills["Reel"] = 5

class GoldGloves2(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Gold Gloves 2", slot="Gloves", materials={"Goldfish Scale": 10, "Goldfish Fin": 10, "Goldfish Tail": 2})
        self.skills["CastLine"] = 10
        self.skills["Reel"] = 10

class GreatGoldGloves(Equippable):
    def __init__(self) -> None:
        super().__init__(name="Great Gold Gloves", slot="Gloves", materials={"Great Goldfish Scale": 10, "Great Goldfish Fin": 2, "Goldfish Crest": 1, "Great Goldfish Tail": 1})
        self.skills["CastLine"] = 20
        self.skills["Reel"] = 20
