# Define some damage values for the skills
from components.SkillComponent import ActiveSkill, CombatSingleTarget, CombatAoe
from effect_factories import curse_effect

# melee_damage = 20
# ranged_damage = 15
# aoe_damage = 10
#
# # Create a melee attack skill
# melee_attack_skill = ActiveSkill(
#     name="Melee Attack",
#     description="A simple melee attack.",
#     activation_requirements=None,
#     sp_cost=10,
#     units=[CombatTarget(is_ranged=False, can_choose=False, num_hits=1, num_targets=1, damage=melee_damage)]
# )
#
# # Create a ranged attack skill
# ranged_attack_skill = ActiveSkill(
#     name="Ranged Attack",
#     description="A ranged attack with a bow.",
#     activation_requirements=None,
#     sp_cost=15,
#     units=[CombatTarget(is_ranged=True, can_choose=False, num_hits=1, num_targets=1, damage=ranged_damage)]
# )
#
# # Create the example skills
#
#
# # Melee Skill without can_choose
# cleave = ActiveSkill(
#     name="Cleave",
#     description="A swift melee attack that hits the closest enemy.",
#     activation_requirements=[],
#     sp_cost=5,
#     time_cost=3,
#     units=[CombatTarget(is_ranged=False, can_choose=False, num_hits=2, num_targets=1, damage=10)]
# )
#
# # Ranged Skill without can_choose
# snipe = ActiveSkill(
#     name="Snipe",
#     description="A precise shot that deals extra damage to a single target.",
#     activation_requirements=[],
#     sp_cost=10,
#     time_cost=4,
#     units=[CombatTarget(is_ranged=True, can_choose=False, num_hits=1, num_targets=1, damage=25)]
# )
#
# # Skills using AOE unit
# fireball_aoe = ActiveSkill(
#     name="Fireball",
#     description="Unleash a fiery explosion in a radius, damaging all enemies around.",
#     activation_requirements=[],
#     mp_cost=10,
#     cooldown=2,
#     time_cost=1.5,
#     units=[CombatAoe(is_ranged=True, can_choose=True, radius=2, damage=15)]
# )
#
# thunderstorm_aoe = ActiveSkill(
#     name="Thunderstorm",
#     description="Summon a powerful thunderstorm, striking enemies within a radius.",
#     activation_requirements=[],
#     mp_cost=15,
#     cooldown=3,
#     time_cost=2,
#     units=[CombatAoe(is_ranged=True, radius=3, damage=20)]
# )
#
# # Define more AOE skills as needed
# # Skills using both Target and AOE units
# ice_arrow = ActiveSkill(
#     name="Ice Arrow",
#     description="Shoot an ice arrow at a single enemy, causing additional frost damage to surrounding enemies.",
#     activation_requirements=[],
#     mp_cost=8,
#     cooldown=1,
#     time_cost=1,
#     units=[
#         CombatTarget(is_ranged=True, can_choose=False, num_hits=1, num_targets=1, damage=10),
#         CombatAoe(is_ranged=True, radius=1, damage=5)
#     ]
# )
#
# explosive_strike = ActiveSkill(
#     name="Explosive Strike",
#     description="Unleash a powerful melee attack that causes an explosion around the target.",
#     activation_requirements=[],
#     sp_cost=15,
#     cooldown=3,
#     time_cost=2,
#     units=[
#         CombatTarget(is_ranged=False, can_choose=False, num_hits=1, num_targets=1, damage=20),
#         CombatAoe(is_ranged=False, radius=2, damage=10)
#     ]
# )
#
# # Define more skills using both Target and AOE units as needed
# # Skills using movement units
# teleportation_skill = ActiveSkill(
#     name="Teleportation",
#     description="Teleport to a targeted location.",
#     activation_requirements=[],
#     mp_cost=10,
#     cooldown=2,
#     time_cost=1.5,
#     units=[MovementTeleportation(is_ranged=True, range_limit=6)]
# )
#
# # Right Dash
# rdash_skill = ActiveSkill(
#     name="Right Dash",
#     description="Dash quickly to the right.",
#     activation_requirements=[],
#     sp_cost=15,
#     cooldown=3,
#     time_cost=2,
#     units=[MovementDash(direction=(1, 0), distance=5)]
# )
#
# # Left Dash
# ldash_skill = ActiveSkill(
#     name="Left Dash",
#     description="Dash quickly to the left.",
#     activation_requirements=[],
#     sp_cost=15,
#     cooldown=3,
#     time_cost=2,
#     units=[MovementDash(direction=(-1, 0), distance=5)]
# )
#
# # Up Dash
# udash_skill = ActiveSkill(
#     name="Up Dash",
#     description="Dash quickly upwards.",
#     activation_requirements=[],
#     sp_cost=15,
#     cooldown=3,
#     time_cost=2,
#     units=[MovementDash(direction=(0, -1), distance=5)]
# )
#
# # Down Dash
# ddash_skill = ActiveSkill(
#     name="Down Dash",
#     description="Dash quickly downwards.",
#     activation_requirements=[],
#     sp_cost=15,
#     cooldown=3,
#     time_cost=2,
#     units=[MovementDash(direction=(0, 1), distance=5)]
# )
#
# # Bleed Status Unit
# bleed_status_unit = StatusUnit([bleed_effect])
#
# # Burn Status Unit
# burn_status_unit = StatusUnit([burn_effect])
#
# # Weaken Status Unit
# weaken_status_unit = StatusUnit([weaken_effect])
#
# # Stun Status Unit
# stun_status_unit = StatusUnit([stun_effect])
#
# # Curse Status Unit
# curse_status_unit = StatusUnit([curse_effect])
#
#
# # Skill that applies Bleed and Burn effects to targets in an area
# bleed_burn_skill = ActiveSkill(
#     name="Bleed & Burn",
#     description="Inflict Bleed and Burn effects on targets in an area.",
#     activation_requirements=[],
#     mp_cost=10,
#     cooldown=5,
#     time_cost=2,
#     units=[
#         CombatAoe(is_ranged=True, radius=2, damage=15, status_units=[bleed_status_unit, burn_status_unit])
#     ]
# )
#
# # Skill that applies the effects Weaken and Stun effects to a single target
# weaken_stun_skill = ActiveSkill(
#     name="Weaken & Stun",
#     description="Inflict Weaken and Stun effects on a single target.",
#     activation_requirements=[],
#     mp_cost=8,
#     cooldown=3,
#     time_cost=1.5,
#     units=[
#         CombatTarget(is_ranged=True, can_choose=False, num_hits=1, num_targets=1, damage=20,
#                      status_units=[weaken_status_unit, stun_status_unit])
#     ]
# )
#
# # Skill that applies Curse effect to targets in an area
# curse_skill = ActiveSkill(
#     name="Curse",
#     description="Inflict Curse effect on targets in an area.",
#     activation_requirements=[],
#     mp_cost=15,
#     cooldown=6,
#     time_cost=3,
#     units=[
#         CombatAoe(is_ranged=True, radius=3, damage=25, status_units=[curse_status_unit])
#     ]
# )

fireball_aoe = CombatAoe(effects=[], damage=25, radius=3, is_ranged=True, )
cursed_fireball_aoe = CombatAoe(effects=[curse_effect], damage=5, radius=5, is_ranged=True)
Fireball = ActiveSkill(name="Fireball",
                       description="A ball of fire",
                       activation_requirements=[],
                       mp_cost=5,
                       cooldown=2,
                       unit=fireball_aoe
                       )
Cursed_Fireball = ActiveSkill(name="Cursed Fireball",
                              description="A ball of cursed flames",
                              activation_requirements=[],
                              mp_cost=5,
                              cooldown=1,
                              unit=cursed_fireball_aoe
                              )

Arrow = CombatSingleTarget(effects=[], is_ranged=True, damage=10)
PowerShot = ActiveSkill(name="Power Shot",
                        description="A powerful shot from a bow.",
                        activation_requirements=[],
                        sp_cost=5,
                        cooldown=1,

                        unit=Arrow)
