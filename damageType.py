class ElementalType:
    def __init__(self, name, resistances=None, weaknesses=None, immunities=None):
        self.name = name
        self.resistances = resistances or []
        self.weaknesses = weaknesses or []
        self.immunities = immunities or []


# Create instances for each type based on the provided information

normal = ElementalType(name="Normal")

fire = ElementalType(name="Fire", resistances=["Fire", "Wind", "Ice", "Metal", "Grass"], weaknesses=["Water", "Earth"])

water = ElementalType(name="Water", resistances=["Fire", "Water", "Light"], weaknesses=["Electric", "Ice", "Grass"])

wind = ElementalType(name="Wind", resistances=["Wind", "Grass"], weaknesses=["Fire", "Electric", "Ice"], immunities=["Earth"])

earth = ElementalType(name="Earth", resistances=["Fire"], weaknesses=["Water", "Wind", "Ice", "Grass"], immunities=["Electric"])

light = ElementalType(name="Light", resistances=["Light", "Primal"], weaknesses=["Dark", "Grass"])

dark = ElementalType(name="Dark", resistances=["Dark", "Grass", "Primal"], weaknesses=["Pure"], immunities=["Light"])

electric = ElementalType(name="Electric", resistances=["Wind", "Electric"], weaknesses=["Earth", "Primal"])

ice = ElementalType(name="Ice", resistances=["Water", "Ice"], weaknesses=["Fire", "Metal", "Primal"])

metal = ElementalType(name="Metal", resistances=["Wind", "Light", "Electric", "Ice", "Grass"], weaknesses=["Fire", "Earth", "Primal"], immunities=["Dark"])

grass = ElementalType(name="Grass", resistances=["Water", "Earth", "Light", "Grass"], weaknesses=["Fire", "Wind", "Dark", "Electric", "Ice", "Primal"])

pure = ElementalType(name="Pure", resistances=["Primal"], weaknesses=["Light"], immunities=["Dark"])

primal = ElementalType(name="Primal", resistances=["Fire", "Water", "Earth", "Wind"], weaknesses=["Light", "Dark", "Pure"], immunities=["Primal"])
