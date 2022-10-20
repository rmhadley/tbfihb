from components.ai import HostileEnemy, NeutralEnemy, GoldfishAI
from components import consumable, equippable
from components.equipment import Equipment
from components.skills import Skills
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

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

goldfish = Actor(
    char="f",
    color=(255, 215, 0),
    name="Goldfish",
    ai_cls=GoldfishAI,
    equipment=Equipment(),
    skills=Skills(),
    fighter=Fighter(hp=8, mp=0, base_defense=0, min_damage=1, max_damage=8, strength=5, intelligence=0, dexterity=5, constitution=0, difficulty=60, avoidance=60),
    inventory=Inventory(capacity=0),
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
    inventory=Inventory(capacity=0),
    level=Level(xp_given=20),
)
