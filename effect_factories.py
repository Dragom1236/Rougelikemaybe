from components.Status import StatusEffect
from condition_factories import stun

# Health Potion Effect
health_potion_effect = StatusEffect(
    name="Vitality Potion",
    duration=5,
    modifier_data={"hp_modifier": 20},
    cot_effect_data={},
)

# Strength Buff Effect
strength_buff_effect = StatusEffect(
    name="Strength Buff",
    duration=3,
    modifier_data={"strength_modifier": 10},
    cot_effect_data={},
)

# Poison Effect
poison_effect = StatusEffect(
    name="Poison",
    duration=4,
    modifier_data={},
    cot_effect_data={"hp_change_per_turn": -10},
)

# Regeneration Effect
regeneration_effect = StatusEffect(
    name="Regeneration",
    duration=6,
    modifier_data={},
    cot_effect_data={"hp_change_per_turn": 10},
)

# Slow Effect
slow_effect = StatusEffect(
    name="Slow",
    duration=4,
    modifier_data={"agility_modifier": -5},
    cot_effect_data={},
)

# Bleed Effect
bleed_effect = StatusEffect(
    name="Bleed",
    duration=3,
    modifier_data={"strength_modifier": -4},
    cot_effect_data={"hp_change_per_turn": -5},
)

# Burn Effect
burn_effect = StatusEffect(
    name="Burn",
    duration=3,
    modifier_data={},
    cot_effect_data={"hp_change_per_turn": -8},
)

# Weaken Effect
weaken_effect = StatusEffect(
    name="Weaken",
    duration=4,
    modifier_data={"strength_modifier": -5, "agility_modifier": -5},
    cot_effect_data={},
)

# Stun Effect
stun_effect = StatusEffect(
    name="Stun",
    duration=1,
    conditions=[stun],
    modifier_data={},
    cot_effect_data={},
)

# Curse Effect
curse_effect = StatusEffect(
    name="Curse",
    duration=5,
    modifier_data={"strength_modifier": -5, "agility_modifier": -5, "hp_modifier": -20},
    cot_effect_data={},
)
