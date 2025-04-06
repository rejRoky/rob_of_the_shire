from character import Character
from itemloader import load_items
import getfilter
from save_system import save_character, load_character
from enemy import Enemy

def show_menu():
    print("\n=== ROB OF THE SHIRE ===")
    print("1. Create New Character")
    print("2. Load Character")
    print("3. Show Inventory")
    print("4. Add Items to Inventory")
    print("5. Filter Inventory")
    print("6. Use Item")
    print("7. Fight Enemy")
    print("8. Save Character")
    print("9. Exit")

def main():
    items = load_items()
    character = None

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            name = input("Enter character name: ")
            character = Character(name)
            print(f"Character '{name}' created.")

        elif choice == "2":
            try:
                character = load_character()
                print(f"Loaded character '{character.name}'.")
            except:
                print("Failed to load character.")

        elif choice == "3":
            if character:
                print(character)
                print(character.inventory_str())
            else:
                print("No character loaded.")

        elif choice == "4":
            if not character:
                print("Create or load a character first.")
                continue
            print("\nAvailable Items:")
            for i, item in enumerate(items):
                print(f"{i + 1}. {item['name']}")
            indexes = input("Enter item numbers to add (comma-separated): ")
            for idx in indexes.split(","):
                try:
                    item = items[int(idx) - 1]
                    character.add_item(item)
                    print(f"Added {item['name']}")
                except:
                    print("Invalid index.")

        elif choice == "5":
            if not character:
                print("Load or create a character first.")
                continue
            filters = getfilter.get_filter("item type", end_code="q")
            print("Filtered Inventory:")
            print(character.inventory_str(filters))

        elif choice == "6":
            if not character:
                print("No character loaded.")
                continue
            item_name = input("Enter item name to use: ")
            character.use_item(item_name)

        elif choice == "7":
            if not character:
                print("No character loaded.")
                continue
            enemy = Enemy("Goblin", 50)
            weapon = input("Enter weapon name to attack with: ")
            character.attack(weapon, enemy)

        elif choice == "8":
            if not character:
                print("No character to save.")
                continue
            save_character(character)
            print("Character saved.")

        elif choice == "9":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
