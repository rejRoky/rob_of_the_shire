class Character:
    def __init__(self, name: str, health: int = 100):
        self.name = name
        self.health = health
        self.inventory = []

    def add_item(self, item: dict):
        self.inventory.append(item)

    def use_item(self, item_name: str):
        for item in self.inventory:
            if item["name"].lower() == item_name.lower():
                if item["type"] == "potion":
                    if "heal" in item:
                        self.health += item["heal"]
                        print(f"{self.name} healed for {item['heal']} HP!")
                        self.inventory.remove(item)
                        return
                print("Item can't be used or has no effect.")
                return
        print("Item not found in inventory.")

    def attack(self, weapon_name: str, enemy):
        for item in self.inventory:
            if item["name"].lower() == weapon_name.lower() and item["type"] == "weapon":
                damage = item.get("damage", 0)
                enemy.take_damage(damage)
                print(f"{self.name} attacked {enemy.name} for {damage} damage!")
                return
        print("Weapon not found or invalid.")

    def inventory_str(self, type_filters=None) -> str:
        output = ""
        for item in self.inventory:
            if type_filters is None or item.get("type") in type_filters:
                output += f"  - {item['name']} ({item.get('type', 'unknown')})\n"
                for key, value in item.items():
                    if key not in ["name", "type"]:
                        output += f"      {key}: {value}\n"
        return output

    def __str__(self):
        return f"Character: {self.name}\nHealth: {self.health}\nInventory: {len(self.inventory)} items"
