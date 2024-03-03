from components.conditions import Condition, DrainCondition, BlindedCondition, AccuracyCondition, ChanceCondition, \
    TargetCondition

# When stunned you cannot take actions at all, but the duration is much shorter.
stun = Condition(name="Stunned", duration=2)

# You can't take any actions while petrified. However, you can't take damage either. Petrified is harder to break
# than sleep.
petrified = Condition(name="Petrified", duration=100)
# Usually inflicted by medusas or the likes. Same as petrification but effectively permanent unless dispelled.
# In other words, this is typically a gameover for any player or creature without reliable allies/
# ways to dispel it on their own.
true_petrification = Condition(name="Full Petrification", permanent=True)
# Infatuated is a lesser charmed effect. It prevents the holder from attacking the target
infatuated = TargetCondition(name="Infatuated", duration=3, chance=50)
# Charmed is a status that technically shouldn't be a condition. A charmed enemy is essentially under the user's
# control. Obviously I can't implement that yet...
charmed = Condition(name="Charmed", permanent=True)
# When paralyzed there is a 25% chance of not being able to take actions.
paralyzed = ChanceCondition(name="Paralyzed", duration=25, chance=25)
# When put to sleep you cannot take actions at all, but if you lose hp you wake up immediately.
sleep = Condition(name="Sleep", duration=30)

# Create instances for specific conditions

# Debuff Resistance. The chance here refers to the chance that a condition is successfully repelled.
debuff_resistance = ChanceCondition(name="Debuff Resistance", duration=25, chance=50)
# Completely blocks debuffs for a bit. Does not remove debuffs you already have.
debuff_block = Condition(name="Debuff Block", duration=5)
# Debuff Immunity. Blocks all debuffs and removes existing ones. Can be removed by certai spells.
debuff_immunity = Condition(name="Debuff Immunity", permanent=True)

# Final Breath, If you are to die, you are instead left at 1 hp.
final_breath = Condition(name="Final Breath", duration=None, permanent=True)

# Autorevive, instead of dying, your life is fully restored.
lifesaving = Condition(name="lifesaving", duration=None, permanent=True, consumable=True)
# Drain
drain = DrainCondition(name="Drain", percentage=3, duration=5, )

# Blinded
blinded = BlindedCondition(duration=2)

# Accuracy Lowered
Obscured = AccuracyCondition(name="Accuracy Lowered", accuracy_penalty=15, duration=3)
