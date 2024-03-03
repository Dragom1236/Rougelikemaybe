# Define the Race instances
from components.Race import Race
from damageType import normal
from faction_factories import humanoid_faction, monster_faction

human_race = Race(
    strength=10,
    dexterity=10,
    agility=10,
    constitution=10,
    magic=10,
    awareness=10,
    charisma=10,
    level_up_base=100,
    level_up_factor=50,
    xp_given=100,
    skills=[],
    starting_faction=(["humanoid_faction"], ["monster_faction","demihuman_faction"])
)

orc_race = Race(
    strength=15,
    dexterity=8,
    agility=7,
    constitution=12,
    magic=2,
    awareness=6,
    charisma=5,
    level_up_base=120,
    level_up_factor=60,
    xp_given=120,
    skills=[],
    starting_faction=(["monster_faction","troll_faction"], ["humanoid_faction"])
)

troll_race = Race(
    strength=20,
    dexterity=5,
    agility=4,
    constitution=18,
    magic=1,
    awareness=4,
    charisma=3,
    level_up_base=150,
    level_up_factor=75,
    xp_given=150,
    skills=[],
    starting_faction=(["monster_faction", "troll_faction"], ["humanoid_faction", "kobold_faction"])
)

kobold_race = Race(
    strength=6,
    dexterity=12,
    agility=15,
    constitution=8,
    magic=8,
    awareness=14,
    charisma=5,
    level_up_base=80,
    level_up_factor=40,
    xp_given=80,
    skills=[],
    starting_faction=(["demihuman_faction", "kobold_faction"], ["humanoid_faction", "troll_faction"])
)

goblin_race = Race(
    strength=6,
    dexterity=14,
    agility=15,
    constitution=8,
    magic=8,
    awareness=12,
    charisma=5,
    level_up_base=80,
    level_up_factor=40,
    xp_given=80,
    skills=[],
    starting_faction=(["monster_faction"], ["humanoid_faction"])
)
