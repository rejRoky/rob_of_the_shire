class Enemy:
    def __init__(self, name: str, health: int):
        self.name = name
        self.health = health

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            print(f"{self.name} has been defeated!")
        else:
            print(f"{self.name} has {self.health} HP remaining.")
