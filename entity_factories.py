from components import consumable
from components.Status import StatusEffectManager
from components.ai import HostileEnemy, FleeingAI
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=70, mp=20, se=1, sp=25, strength=100, dexterity=15, magic=15, constitution=100, awareness=100,
                    charisma=10, agility=10),
    inventory=Inventory(capacity=26),
    status_effect_manager=StatusEffectManager(),
    level=Level(level_up_base=200),

    # strength default is 10, constitution is 10 or 20, awareness is 16
)
orc = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=0, mp=0, se=0, sp=0, strength=15, dexterity=5, magic=5, constitution=15, awareness=8,
                    charisma=5, agility=6),
    status_effect_manager=StatusEffectManager(),
    inventory=Inventory(capacity=1),
    level=Level(level_up_base=150, xp_given=50),
)

kobold = Actor(
    char="k",
    color=(125, 42, 42),
    name="Orc",
    ai_cls=FleeingAI,
    fighter=Fighter(hp=0, mp=0, se=0, sp=0, strength=15, dexterity=30, magic=5, constitution=5, awareness=32,
                    charisma=5, agility=30),
    status_effect_manager=StatusEffectManager(),
    inventory=Inventory(capacity=2),
    level=Level(level_up_base=50, xp_given=10),
)

troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=10, mp=0, se=0, sp=0, strength=20, dexterity=3, magic=3, constitution=20, awareness=4,
                    charisma=3, agility=4),
    inventory=Inventory(capacity=3),
    status_effect_manager=StatusEffectManager(),
    level=Level(level_up_base=250,xp_given=100),
)

health_potion = Item(
    char="!",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=4),
)
lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
)

confusion_scroll = Item(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)

fireball_scroll = Item(
    char="~",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),
)
