# Create Melee Weapon - Iron Sword
from components.Ammo import Ammo
from components.equippable import MeleeWeapon, Bow, Staff, Orb, Wand, Armor, Container, Crossbow, Gun
from skill_factories import Fireball, PowerShot

dagger = MeleeWeapon(rarity="common", damage_dice=(1, 6))
iron_sword = MeleeWeapon(rarity="common", damage_dice=(2, 6))

# Create Bow - Wooden Bow
wooden_bow = Bow(rarity="common", damage_dice=(1, 2), max_distance=5)

wooden_crossbow = Crossbow(rarity="common", damage_dice=(2, 3), max_distance=10)

pistol = Gun(rarity="common", damage_dice=(1, 3), max_distance=7, max_ammo=3)

# Create Staff
staff = Staff(rarity="uncommon", damage_dice=(1, 4), mp_cost=2)

# Create Orb - Mage Orb
mage_orb = Orb(rarity="rare", damage_dice=(2, 3), mp_cost=3)

fireball_wand = Wand(rarity="epic", Skills=[Fireball, PowerShot])

quiver = Container(rarity="common", capacity=10)

# Create Armor - Leather Armor
leather_armor = Armor(rarity="common", defense_bonus=2)

# Create Armor - Chainmail Armor
chainmail_armor = Armor(rarity="uncommon", defense_bonus=4)

arrow = Ammo(4, "Arrow", stacks=6)
bolt = Ammo(4, "Bolt", stacks=1)
bullet = Ammo(3, "Bullet", stacks=20)
