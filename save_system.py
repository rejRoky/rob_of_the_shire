import json
from character import Character

def save_character(character, file_path="save.json"):
    data = {
        "name": character.name,
        "health": character.health,
        "inventory": character.inventory
    }
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_character(file_path="save.json"):
    with open(file_path, "r") as f:
        data = json.load(f)
    char = Character(name=data["name"], health=data["health"])
    for item in data["inventory"]:
        char.add_item(item)
    return char
