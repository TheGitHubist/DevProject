class Player :
    def __init__(self):
        self.username = None
        self.hp = 100
        self.difficulty = 1
        
    def setDifficulty(self, difficulty):
        self.difficulty = difficulty