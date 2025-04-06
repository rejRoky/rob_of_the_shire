import json

def load_items(file_path="items.json"):
    with open(file_path, "r") as f:
        return json.load(f)
