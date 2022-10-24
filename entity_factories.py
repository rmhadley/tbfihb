from components.ai import HostileEnemy, NeutralEnemy, GoldfishAI, NPCAI
from components import consumable, equippable
from components.equipment import Equipment
from components.skills import Skills
from components.fighter import Fighter
from components.inventory import Inventory, Parts
from components.level import Level
from entity import Actor, Item, Fisherman

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    skills=Skills(),
    fighter=Fighter(hp=30, mp=4, base_defense=2, min_damage=1, max_damage=2, strength=5, intelligence=5, dexterity=5, constitution=5, difficulty=0, avoidance=0),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)

fisherman = Fisherman(
    char="@",
    color=(97, 237, 111),
    name="Fisherman",
    ai_cls=NPCAI,
)

goldfish = Actor(
    char="f",
    color=(255, 215, 0),
    name="Goldfish",
    ai_cls=GoldfishAI,
    equipment=Equipment(),
    skills=Skills(),
    fighter=Fighter(hp=8, mp=0, base_defense=0, min_damage=1, max_damage=8, strength=5, intelligence=0, dexterity=5, constitution=0, difficulty=60, avoidance=60),
    inventory=Parts(parts=["Goldfish Scale", "Goldfish Fin", "Goldfish Tail", "Goldfish Crest"], chances=[80, 90, 98, 100], min_drops=2, max_drops=4),
    level=Level(xp_given=20),
)

great_goldfish = Actor(
    char="F",
    color=(255, 215, 0),
    name="Great Goldfish",
    ai_cls=NeutralEnemy,
    equipment=Equipment(),
    skills=Skills(),
    fighter=Fighter(hp=8, mp=0, base_defense=0, min_damage=0, max_damage=0, strength=10, intelligence=0, dexterity=5, constitution=0, difficulty=80, avoidance=50),
    inventory=Parts(parts=["Great Goldfish Scale", "Great Goldfish Fin", "Great Goldfish Tail", "Great Goldfish Crest"], chances=[80, 90, 98, 100], min_drops=2, max_drops=8),
    level=Level(xp_given=20),
)

sky_fish = Actor(
    char="s",
    color=(186, 19, 191),
    name="Sky Fish",
    ai_cls=NeutralEnemy,
    equipment=Equipment(),
    skills=Skills(),
    fighter=Fighter(hp=8, mp=0, base_defense=0, min_damage=1, max_damage=8, strength=7, intelligence=0, dexterity=5, constitution=0, difficulty=80, avoidance=80),
    inventory=Parts(parts=["Sky Fish Scale", "Sky Fish Fin", "Sky Fish Tail", "Sky Fish Crest"], chances=[80, 90, 98, 100], min_drops=2, max_drops=4),
    level=Level(xp_given=20),
)

sky_shark = Actor(
    char="S",
    color=(186, 19, 191),
    name="Sky Shark",
    ai_cls=NeutralEnemy,
    equipment=Equipment(),
    skills=Skills(),
    fighter=Fighter(hp=8, mp=0, base_defense=0, min_damage=1, max_damage=8, strength=10, intelligence=0, dexterity=5, constitution=0, difficulty=90, avoidance=20),
    inventory=Parts(parts=["Sky Shark Scale", "Sky Shark Fin", "Sky Shark Tail", "Sky Shark Crest"], chances=[80, 90, 98, 100], min_drops=2, max_drops=8),
    level=Level(xp_given=20),
)

lightning_fish = Actor(
    char="z",
    color=(235, 255, 54),
    name="Lightning Fish",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    skills=Skills(),
    fighter=Fighter(hp=1, mp=0, base_defense=0, min_damage=8, max_damage=8, strength=1, intelligence=0, dexterity=5, constitution=0, difficulty=30, avoidance=0),
    inventory=Parts(parts=["Lightning Scale", "Lightning Fin", "Lightning Tail", "Lightning Crest"], chances=[80, 90, 98, 100], min_drops=2, max_drops=2),
    level=Level(xp_given=20),
)
