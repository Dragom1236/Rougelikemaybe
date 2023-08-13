import components
from components import consumable, equippable_factories
from components.SkillComponent import Abilities
from components.Status import StatusEffectManager
from components.ai import HostileEnemy, FleeingAI
from components.conditions import ConditionManager
from components.equipment import Equipment
from components.equippable_factories import arrow, bolt, bullet
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from effect_factories import regeneration_effect
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
    equipment=Equipment(),
    conditions_manager=ConditionManager(),
    abilities=Abilities(),

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
    equipment=Equipment(),
    conditions_manager=ConditionManager(),
    abilities=Abilities(),
)

kobold = Actor(
    char="k",
    color=(125, 42, 42),
    name="Kobold",
    ai_cls=FleeingAI,
    fighter=Fighter(hp=0, mp=0, se=0, sp=0, strength=15, dexterity=30, magic=5, constitution=5, awareness=32,
                    charisma=5, agility=30),
    status_effect_manager=StatusEffectManager(),
    inventory=Inventory(capacity=2),
    level=Level(level_up_base=50, xp_given=10),
    equipment=Equipment(),
    conditions_manager=ConditionManager(),
    abilities=Abilities(),
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
    level=Level(level_up_base=250, xp_given=100),
    equipment=Equipment(),
    conditions_manager=ConditionManager(),
    abilities=Abilities(),
)

health_potion = Item(
    char="!",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=4, effect=regeneration_effect),
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

dagger = Item(
    char="/", color=(0, 191, 255), name="Dagger", equippable=components.equippable_factories.dagger
)

sword = Item(char="/", color=(191, 191, 191), name="Sword", equippable=equippable_factories.iron_sword)

leather_armor = Item(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable_factories.leather_armor,
)

chain_mail = Item(
    char="[", color=(139, 69, 19), name="Chain Mail", equippable=equippable_factories.chainmail_armor
)

Basic_Quiver = Item(
    char="(", color=(80, 42, 42), name="Quiver", equippable=equippable_factories.quiver
)

Wooden_Arrow = Item(char=",", color=(120, 99, 49), name="Arrow", ammo=arrow)

Bow = Item(char=")", color=(160, 82, 45), name="Bow", equippable=equippable_factories.wooden_bow)

Wooden_Bolt = Item(char=",", color=(90, 69, 19), name="Bolt", ammo=bolt)

Crossbow = Item(char=")", color=(165, 42, 42), name="Crossbow", equippable=equippable_factories.wooden_crossbow)

iron_bullet = Item(char=",", color=(97, 102, 106), name="Bullet", ammo=bullet)

Pistol = Item(char=")", color=(77, 82, 86), name="Pistol", equippable=equippable_factories.pistol)

Wooden_Staff = Item(char="|", color=(160, 82, 45), name="Staff", equippable=equippable_factories.staff)

Mage_Orb = Item(char="*", color=(0, 0, 255), name="Mage Orb", equippable=equippable_factories.mage_orb)

Fireball_Wand = Item(char="~", color=(255, 30, 0), name="Wand of Fireball", equippable=equippable_factories.fireball_wand)
