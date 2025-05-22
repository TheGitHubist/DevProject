class Boss :
    def __init__(self, name , key_word):
        self.name = ""
        self.health = 1000
        self.key_word = {}
        
    def take_dmg (self, dmg):
        self.health -= dmg
        
