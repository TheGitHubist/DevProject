class Boss :
    def __init__(self):
        self.name = "Boss"
        self.health = 200
        self.key_word = "boss"
        self.script = ""
        self.world_boss = False  # Indicates this is a world boss
        
    def take_dmg (self, dmg):
        self.health -= dmg
        
    def set_attributes(self, name , key_word, script, health, wb):
        self.health = health
        self.name = name
        self.key_word = key_word
        self.script = script
        self.world_boss = wb  # Set to True for world bosses