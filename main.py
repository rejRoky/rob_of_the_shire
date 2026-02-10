#!/usr/bin/env python3
"""
Rob of the Shire - A Text-Based RPG Adventure Game

A comprehensive text-based RPG featuring:
- Character creation with multiple classes
- Turn-based combat system
- Inventory and equipment management
- Save/Load functionality with backups
- Experience and leveling system
- Multiple enemy types with AI behaviors

Author: Game Developer
Version: 2.0.0
"""

from __future__ import annotations
import sys
from typing import Optional

from character import Character
from enemy import (
    Enemy, EnemyRank, create_goblin, create_orc, 
    create_skeleton, create_wolf, create_troll, 
    create_dragon, create_random_enemy
)
from combat import start_combat, start_boss_battle, CombatEncounter
from itemloader import load_items, get_item_database, ItemFilter
from getfilter import get_filter, get_single_filter, ItemFilter as FilterClass
from save_system import (
    save_character, load_character, SaveManager, 
    get_save_manager, SaveMetadata
)
from config import config, CharacterClass, ItemType, CombatResult
from exceptions import (
    GameException, CharacterNotFoundError, SaveFileNotFoundError,
    InventoryFullError, ItemNotFoundError
)
from logger import get_logger, info, warning, error


class GameUI:
    """
    User interface manager for the game.
    
    Handles all display and input operations, providing a clean
    separation between game logic and presentation.
    """
    
    BORDER = "═" * 50
    THIN_BORDER = "─" * 50
    
    @staticmethod
    def clear_screen() -> None:
        """Clear the terminal screen."""
        print("\n" * 2)
    
    @staticmethod
    def print_header(title: str) -> None:
        """Print a formatted header."""
        print(f"\n╔{GameUI.BORDER}╗")
        print(f"║{title:^50}║")
        print(f"╚{GameUI.BORDER}╝")
    
    @staticmethod
    def print_section(title: str) -> None:
        """Print a section divider."""
        print(f"\n┌{GameUI.THIN_BORDER}┐")
        print(f"│ {title:<48} │")
        print(f"└{GameUI.THIN_BORDER}┘")
    
    @staticmethod
    def print_menu(options: list[tuple[str, str]]) -> None:
        """
        Print a menu with numbered options.
        
        Args:
            options: List of (key, description) tuples.
        """
        for key, description in options:
            print(f"  [{key}] {description}")
    
    @staticmethod
    def get_input(prompt: str = "> ") -> str:
        """Get user input with prompt."""
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            return ""
    
    @staticmethod
    def get_int_input(prompt: str, min_val: int = None, max_val: int = None) -> Optional[int]:
        """
        Get integer input with optional range validation.
        
        Returns None if input is invalid.
        """
        try:
            value = int(input(prompt).strip())
            if min_val is not None and value < min_val:
                print(f"  Value must be at least {min_val}")
                return None
            if max_val is not None and value > max_val:
                print(f"  Value must be at most {max_val}")
                return None
            return value
        except ValueError:
            print("  Please enter a valid number.")
            return None
    
    @staticmethod
    def confirm(prompt: str, default: bool = True) -> bool:
        """
        Get yes/no confirmation from user.
        
        Args:
            prompt: Question to ask.
            default: Default value if user presses Enter.
        """
        suffix = " [Y/n]: " if default else " [y/N]: "
        response = input(prompt + suffix).strip().lower()
        
        if not response:
            return default
        return response in ('y', 'yes')


class Game:
    """
    Main game class that manages the game loop and state.
    
    Coordinates between characters, combat, inventory, and save systems.
    
    Attributes:
        character: The current player character.
        items: Available items database.
        save_manager: Save/load manager.
        running: Whether the game loop is running.
    """
    
    VERSION = "2.0.0"
    
    def __init__(self):
        """Initialize the game."""
        self.logger = get_logger()
        self.ui = GameUI()
        
        self.character: Optional[Character] = None
        self.items: list[dict] = []
        self.save_manager = get_save_manager()
        self.running = True
        
        self.logger.info("Game initialized")
    
    def initialize(self) -> bool:
        """
        Initialize game resources.
        
        Returns:
            True if initialization successful.
        """
        try:
            self.items = load_items()
            self.logger.info(f"Loaded {len(self.items)} items")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load items: {e}")
            print(f"Error loading game data: {e}")
            return False
    
    def show_title_screen(self) -> None:
        """Display the title screen."""
        title = """
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║     ██████╗  ██████╗ ██████╗                        ║
    ║     ██╔══██╗██╔═══██╗██╔══██╗                       ║
    ║     ██████╔╝██║   ██║██████╔╝                       ║
    ║     ██╔══██╗██║   ██║██╔══██╗                       ║
    ║     ██║  ██║╚██████╔╝██████╔╝                       ║
    ║     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝                        ║
    ║                                                      ║
    ║              OF THE SHIRE                            ║
    ║                                                      ║
    ║     A Text-Based RPG Adventure    v{version}           ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
        """.format(version=self.VERSION)
        print(title)
    
    def show_main_menu(self) -> None:
        """Display the main menu."""
        self.ui.print_header("MAIN MENU")
        
        options = [
            ("1", "Create New Character"),
            ("2", "Load Character"),
            ("3", "View Character Status"),
            ("4", "Manage Inventory"),
            ("5", "Visit Shop"),
            ("6", "Adventure (Combat)"),
            ("7", "Allocate Stat Points"),
            ("8", "Save Game"),
            ("9", "Manage Saves"),
            ("0", "Exit Game"),
        ]
        
        self.ui.print_menu(options)
        
        if self.character:
            print(f"\n  Current: {self.character.name} (Lvl {self.character.level})")
            print(f"  HP: {self.character.health}/{self.character.max_health}")
    
    def create_character(self) -> None:
        """Create a new character."""
        self.ui.print_header("CHARACTER CREATION")
        
        # Get name
        name = self.ui.get_input("  Enter character name: ")
        if not name:
            print("  Character creation cancelled.")
            return
        
        # Choose class
        self.ui.print_section("Choose Your Class")
        classes = [
            (CharacterClass.WARRIOR, "Warrior - High HP, Strong attacks"),
            (CharacterClass.MAGE, "Mage - High Mana, Magic power"),
            (CharacterClass.ROGUE, "Rogue - High Agility, Critical hits"),
            (CharacterClass.RANGER, "Ranger - Balanced, Ranged combat"),
        ]
        
        for i, (cls, desc) in enumerate(classes, 1):
            print(f"  {i}. {desc}")
        
        choice = self.ui.get_int_input("\n  Select class (1-4): ", 1, 4)
        if choice is None:
            choice = 1
        
        selected_class = classes[choice - 1][0]
        
        # Create character
        self.character = Character(name=name, character_class=selected_class)
        
        # Give starting items
        starting_items = ["Iron Sword", "Healing Potion", "Healing Potion"]
        for item_name in starting_items:
            for item in self.items:
                if item["name"] == item_name:
                    self.character.add_item(item.copy())
                    break
        
        print(f"\n  ✅ Character '{name}' created as a {selected_class.name}!")
        print("  You received some starting equipment.")
        self.logger.info(f"Character created: {name} ({selected_class.name})")
    
    def load_character_menu(self) -> None:
        """Load a saved character."""
        self.ui.print_header("LOAD CHARACTER")
        
        # List available saves
        saves = self.save_manager.list_saves()
        
        if not saves:
            print("  No saved games found.")
            return
        
        print("\n  Available Saves:")
        for i, save in enumerate(saves, 1):
            metadata = save.get("metadata")
            if metadata:
                print(f"  {i}. Slot {save['slot']}: {metadata.character_name} (Lvl {metadata.character_level})")
            else:
                print(f"  {i}. Slot {save['slot']}: (Unknown)")
        
        choice = self.ui.get_int_input("\n  Select save to load (0 to cancel): ", 0, len(saves))
        
        if choice is None or choice == 0:
            return
        
        slot = saves[choice - 1]["slot"]
        
        try:
            self.character = self.save_manager.load(slot)
            print(f"\n  ✅ Character loaded successfully!")
        except SaveFileNotFoundError:
            print("  Save file not found.")
        except Exception as e:
            print(f"  Error loading save: {e}")
            self.logger.exception("Failed to load character")
    
    def view_character_status(self) -> None:
        """Display detailed character status."""
        if not self.character:
            print("\n  No character loaded. Create or load a character first.")
            return
        
        self.ui.print_header("CHARACTER STATUS")
        print(self.character.status_str())
        
        self.ui.print_section("Equipment")
        print(self.character.equipment_str())
        
        if self.character.available_stat_points > 0:
            print(f"\n  📊 {self.character.available_stat_points} stat points available!")
    
    def manage_inventory(self) -> None:
        """Inventory management submenu."""
        if not self.character:
            print("\n  No character loaded.")
            return
        
        while True:
            self.ui.print_header("INVENTORY")
            print(f"  Items: {len(self.character.inventory)}/{config.MAX_INVENTORY_SIZE}")
            print(f"  Gold: {self.character.gold}")
            
            options = [
                ("1", "View All Items"),
                ("2", "Filter Items by Type"),
                ("3", "Use Item"),
                ("4", "Equip Item"),
                ("5", "Unequip Item"),
                ("6", "Drop Item"),
                ("0", "Back to Main Menu"),
            ]
            self.ui.print_menu(options)
            
            choice = self.ui.get_input("\n  Select option: ")
            
            if choice == "1":
                self._view_inventory()
            elif choice == "2":
                self._filter_inventory()
            elif choice == "3":
                self._use_item()
            elif choice == "4":
                self._equip_item()
            elif choice == "5":
                self._unequip_item()
            elif choice == "6":
                self._drop_item()
            elif choice == "0":
                break
    
    def _view_inventory(self) -> None:
        """Display full inventory."""
        self.ui.print_section("Inventory Contents")
        
        if not self.character.inventory:
            print("  Your inventory is empty.")
            return
        
        # Group by type
        from getfilter import group_items_by
        grouped = group_items_by(self.character.inventory, "type")
        
        for item_type, items in grouped.items():
            print(f"\n  [{item_type.upper()}]")
            for item in items:
                rarity = item.get("rarity", "COMMON")
                rarity_symbol = {"COMMON": "⚪", "UNCOMMON": "🟢", "RARE": "🔵", 
                                "EPIC": "🟣", "LEGENDARY": "🟡"}.get(rarity, "⚪")
                print(f"    {rarity_symbol} {item['name']}")
    
    def _filter_inventory(self) -> None:
        """Filter and display inventory."""
        types = list(set(item.get("type", "misc") for item in self.character.inventory))
        
        if not types:
            print("  No items to filter.")
            return
        
        print("\n  Available types:", ", ".join(types))
        filters = get_filter("item type", end_code="q", all_code="all")
        
        print("\n  Filtered Inventory:")
        print(self.character.inventory_str(filters))
    
    def _use_item(self) -> None:
        """Use an item from inventory."""
        usable = [item for item in self.character.inventory 
                  if item.get("type") in ["potion", "consumable"]]
        
        if not usable:
            print("\n  No usable items in inventory.")
            return
        
        print("\n  Usable Items:")
        for i, item in enumerate(usable, 1):
            effect = ""
            if "heal" in item:
                effect = f"+{item['heal']} HP"
            if "mana" in item:
                effect += f" +{item['mana']} MP"
            print(f"  {i}. {item['name']} - {effect}")
        
        choice = self.ui.get_int_input("\n  Select item (0 to cancel): ", 0, len(usable))
        
        if choice and choice > 0:
            item = usable[choice - 1]
            try:
                self.character.use_item(item["name"])
            except Exception as e:
                print(f"  Error: {e}")
    
    def _equip_item(self) -> None:
        """Equip an item."""
        equippable = [item for item in self.character.inventory 
                      if item.get("type") in ["weapon", "armor", "accessory"]]
        
        if not equippable:
            print("\n  No equippable items in inventory.")
            return
        
        print("\n  Equippable Items:")
        for i, item in enumerate(equippable, 1):
            stats = []
            if "damage" in item:
                stats.append(f"DMG: {item['damage']}")
            if "defense" in item:
                stats.append(f"DEF: {item['defense']}")
            stat_str = " | ".join(stats) if stats else ""
            print(f"  {i}. {item['name']} [{item['type']}] {stat_str}")
        
        choice = self.ui.get_int_input("\n  Select item (0 to cancel): ", 0, len(equippable))
        
        if choice and choice > 0:
            item = equippable[choice - 1]
            try:
                self.character.equip_item(item["name"])
            except Exception as e:
                print(f"  Error: {e}")
    
    def _unequip_item(self) -> None:
        """Unequip an item."""
        slots = ["weapon", "armor", "accessory", "shield"]
        
        print("\n  Equipment Slots:")
        for i, slot in enumerate(slots, 1):
            item = getattr(self.character.equipment, slot, None)
            status = item["name"] if item else "(empty)"
            print(f"  {i}. {slot.capitalize()}: {status}")
        
        choice = self.ui.get_int_input("\n  Select slot (0 to cancel): ", 0, len(slots))
        
        if choice and choice > 0:
            slot = slots[choice - 1]
            try:
                self.character.unequip_item(slot)
            except Exception as e:
                print(f"  Error: {e}")
    
    def _drop_item(self) -> None:
        """Drop an item from inventory."""
        if not self.character.inventory:
            print("\n  No items to drop.")
            return
        
        print("\n  Inventory:")
        for i, item in enumerate(self.character.inventory, 1):
            print(f"  {i}. {item['name']}")
        
        choice = self.ui.get_int_input("\n  Select item to drop (0 to cancel): ", 
                                       0, len(self.character.inventory))
        
        if choice and choice > 0:
            item = self.character.inventory[choice - 1]
            if self.ui.confirm(f"  Drop {item['name']}?"):
                self.character.remove_item(item["name"])
                print(f"  Dropped {item['name']}.")
    
    def visit_shop(self) -> None:
        """Shop for items."""
        if not self.character:
            print("\n  No character loaded.")
            return
        
        self.ui.print_header("ITEM SHOP")
        print(f"\n  Your Gold: {self.character.gold}")
        
        # Show available items
        shop_items = [item for item in self.items 
                      if item.get("level_requirement", 1) <= self.character.level + 5]
        
        if not shop_items:
            print("  No items available.")
            return
        
        print("\n  Available Items:")
        for i, item in enumerate(shop_items[:15], 1):
            value = item.get("value", 10)
            rarity = item.get("rarity", "COMMON")
            print(f"  {i}. {item['name']} - {value} gold [{rarity}]")
        
        print("\n  Enter item number to buy, or 0 to exit")
        choice = self.ui.get_int_input("  Select: ", 0, len(shop_items))
        
        if choice and choice > 0:
            item = shop_items[choice - 1]
            value = item.get("value", 10)
            
            if self.character.gold < value:
                print("  Not enough gold!")
                return
            
            try:
                self.character.add_item(item.copy())
                self.character.gold -= value
                print(f"  ✅ Purchased {item['name']} for {value} gold!")
            except InventoryFullError:
                print("  Inventory is full!")
    
    def adventure_menu(self) -> None:
        """Adventure/combat submenu."""
        if not self.character:
            print("\n  No character loaded.")
            return
        
        if not self.character.is_alive:
            print("\n  Your character has fallen. Please heal or load a save.")
            return
        
        self.ui.print_header("ADVENTURE")
        
        options = [
            ("1", "Random Encounter"),
            ("2", "Hunt Goblins (Easy)"),
            ("3", "Fight Orcs (Medium)"),
            ("4", "Challenge Troll (Hard)"),
            ("5", "Face the Dragon (Boss)"),
            ("0", "Back"),
        ]
        self.ui.print_menu(options)
        
        choice = self.ui.get_input("\n  Select: ")
        
        enemy = None
        is_boss = False
        
        if choice == "1":
            enemy = create_random_enemy(
                min_level=max(1, self.character.level - 2),
                max_level=self.character.level + 1
            )
        elif choice == "2":
            enemy = create_goblin(level=self.character.level)
        elif choice == "3":
            enemy = create_orc(level=self.character.level)
        elif choice == "4":
            enemy = create_troll(level=self.character.level)
        elif choice == "5":
            enemy = create_dragon(level=self.character.level)
            is_boss = True
        elif choice == "0":
            return
        
        if enemy:
            if is_boss:
                result = start_boss_battle(self.character, enemy)
            else:
                result = start_combat(self.character, enemy)
            
            if result == CombatResult.VICTORY:
                print("\n  🎉 Victory! Press Enter to continue...")
            elif result == CombatResult.DEFEAT:
                print("\n  💀 You were defeated. Press Enter to continue...")
            elif result == CombatResult.FLED:
                print("\n  💨 You escaped. Press Enter to continue...")
            
            self.ui.get_input()
    
    def allocate_stats(self) -> None:
        """Allocate available stat points."""
        if not self.character:
            print("\n  No character loaded.")
            return
        
        if self.character.available_stat_points <= 0:
            print("\n  No stat points available.")
            return
        
        while self.character.available_stat_points > 0:
            self.ui.print_header("ALLOCATE STAT POINTS")
            print(f"\n  Available Points: {self.character.available_stat_points}")
            print(f"\n  Current Stats:")
            print(f"    1. Strength:     {self.character.stats.strength}")
            print(f"    2. Agility:      {self.character.stats.agility}")
            print(f"    3. Intelligence: {self.character.stats.intelligence}")
            print(f"    4. Vitality:     {self.character.stats.vitality}")
            print(f"    5. Luck:         {self.character.stats.luck}")
            print(f"    0. Done")
            
            choice = self.ui.get_int_input("\n  Add point to (1-5, 0 to finish): ", 0, 5)
            
            if choice is None or choice == 0:
                break
            
            stat_names = ["strength", "agility", "intelligence", "vitality", "luck"]
            stat = stat_names[choice - 1]
            self.character.allocate_stat_point(stat)
    
    def save_game(self) -> None:
        """Save the current game."""
        if not self.character:
            print("\n  No character to save.")
            return
        
        try:
            self.save_manager.save(self.character, slot=0)
        except Exception as e:
            print(f"  Error saving: {e}")
            self.logger.exception("Failed to save game")
    
    def manage_saves(self) -> None:
        """Save file management submenu."""
        self.ui.print_header("SAVE MANAGEMENT")
        
        options = [
            ("1", "List All Saves"),
            ("2", "Save to New Slot"),
            ("3", "List Backups"),
            ("4", "Restore Backup"),
            ("5", "Delete Save"),
            ("0", "Back"),
        ]
        self.ui.print_menu(options)
        
        choice = self.ui.get_input("\n  Select: ")
        
        if choice == "1":
            saves = self.save_manager.list_saves()
            if not saves:
                print("\n  No saves found.")
            else:
                for save in saves:
                    meta = save.get("metadata")
                    if meta:
                        print(f"\n  Slot {save['slot']}:")
                        print(f"    {meta.display()}")
        
        elif choice == "2" and self.character:
            slot = self.ui.get_int_input("  Enter slot number (1-9): ", 1, 9)
            if slot:
                self.save_manager.save(self.character, slot=slot)
        
        elif choice == "3":
            backups = self.save_manager.list_backups(slot=0)
            if not backups:
                print("\n  No backups found.")
            else:
                for i, backup in enumerate(backups, 1):
                    print(f"  {i}. {backup['name']}")
        
        elif choice == "4":
            backups = self.save_manager.list_backups(slot=0)
            if backups:
                for i, backup in enumerate(backups, 1):
                    print(f"  {i}. {backup['name']}")
                idx = self.ui.get_int_input("  Select backup: ", 1, len(backups))
                if idx:
                    try:
                        self.character = self.save_manager.restore_backup(
                            backups[idx - 1]["path"], slot=0
                        )
                        print("  Backup restored!")
                    except Exception as e:
                        print(f"  Error: {e}")
        
        elif choice == "5":
            slot = self.ui.get_int_input("  Enter slot to delete (0-9): ", 0, 9)
            if slot is not None and self.ui.confirm("  Are you sure?", default=False):
                self.save_manager.delete_save(slot)
                print("  Save deleted.")
    
    def exit_game(self) -> None:
        """Exit the game with optional save."""
        if self.character:
            if self.ui.confirm("\n  Save before exiting?"):
                self.save_game()
        
        print("\n  Thanks for playing Rob of the Shire!")
        print("  Farewell, adventurer!\n")
        self.running = False
    
    def run(self) -> None:
        """Main game loop."""
        self.show_title_screen()
        
        if not self.initialize():
            print("Failed to initialize game. Exiting.")
            return
        
        print("\n  Press Enter to start...")
        self.ui.get_input()
        
        while self.running:
            try:
                self.show_main_menu()
                choice = self.ui.get_input("\n  Select option: ")
                
                if choice == "1":
                    self.create_character()
                elif choice == "2":
                    self.load_character_menu()
                elif choice == "3":
                    self.view_character_status()
                elif choice == "4":
                    self.manage_inventory()
                elif choice == "5":
                    self.visit_shop()
                elif choice == "6":
                    self.adventure_menu()
                elif choice == "7":
                    self.allocate_stats()
                elif choice == "8":
                    self.save_game()
                elif choice == "9":
                    self.manage_saves()
                elif choice == "0":
                    self.exit_game()
                else:
                    print("  Invalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n")
                if self.ui.confirm("  Exit game?"):
                    self.exit_game()
            except Exception as e:
                self.logger.exception(f"Unhandled error: {e}")
                print(f"\n  An error occurred: {e}")
                print("  The game will attempt to continue...")


def main() -> int:
    """
    Main entry point for the game.
    
    Returns:
        Exit code (0 for success).
    """
    try:
        game = Game()
        game.run()
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
