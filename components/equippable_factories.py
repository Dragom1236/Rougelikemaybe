# Create Melee Weapon - Iron Sword
from components.equippable import MeleeWeapon, Bow, Staff, Orb, Wand, Armor
from skill_factories import fireball_aoe

dagger = MeleeWeapon(rarity="common", damage_dice=(1, 6), time_cost=2)
iron_sword = MeleeWeapon(rarity="common", damage_dice=(2, 6), time_cost=2)

# Create Bow - Wooden Bow
wooden_bow = Bow(rarity="common", damage_dice=(1, 8))

# Create Staff
staff = Staff(rarity="uncommon", damage_dice=(1, 4), mp_cost=5)

# Create Orb - Mage Orb
mage_orb = Orb(rarity="rare", damage_dice=(2, 3), mp_cost=10)

fireball_wand = Wand(rarity="epic", Skills=fireball_aoe)

# Create Armor - Leather Armor
leather_armor = Armor(rarity="common", defense_bonus=2)

# Create Armor - Chainmail Armor
chainmail_armor = Armor(rarity="uncommon", defense_bonus=4)
