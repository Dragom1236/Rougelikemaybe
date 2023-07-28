from components.base_component import BaseComponent


class Skill:
    def __init__(self, name, description, cooldown, activation_requirements, effects):
        self.name = name
        self.description = description
        self.cooldown = cooldown
        self.activation_requirements = activation_requirements
        self.effects = effects

    def activate(self, user, target):
        # Check if the skill can be activated based on cooldown and activation requirements
        if self.can_activate(user):
            # Apply the skill's effects to the target
            for effect in self.effects:
                effect.apply(user, target)

            # Set the skill's cooldown for the user
            self.set_cooldown(user)

    def can_activate(self, user):
        # Check if the skill is off cooldown and activation requirements are met
        # Implement the logic here based on the specific requirements of your game
        pass

    def set_cooldown(self, user):
        # Set the cooldown for the skill on the user
        # Implement the logic here based on your game's cooldown mechanics
        pass


class Abilities(BaseComponent):
    def __init__(self):
        self.skills = []

    def add_skill(self, skill):
        self.skills.append(skill)

    def remove_skill(self, skill):
        self.skills.remove(skill)

    def activate_skill(self, skill_index, user, target):
        if 0 <= skill_index < len(self.skills):
            skill = self.skills[skill_index]
            skill.activate(user, target)
