from components.Status import StatusEffect

# Health Potion Effect
health_potion_effect = StatusEffect(
    name="Health Potion",
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
    cot_effect_data={"hp_change_per_turn": 15},
)

# Slow Effect
slow_effect = StatusEffect(
    name="Slow",
    duration=4,
    modifier_data={"agility_modifier": -5},
    cot_effect_data={},
)
