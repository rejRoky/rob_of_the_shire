# Rob of the Shire

A comprehensive text-based RPG adventure game written in Python. Experience classic RPG mechanics including character creation, turn-based combat, inventory management, and an expansive item system.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Gameplay Guide](#gameplay-guide)
- [Project Structure](#project-structure)
- [Technical Documentation](#technical-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

### Character System

- **4 Character Classes**: Warrior, Mage, Rogue, and Ranger
- **6 Core Stats**: Strength, Agility, Intelligence, Vitality, Luck
- **Leveling System**: Earn XP, level up, and allocate stat points
- **Health, Mana, and Stamina**: Resource management in combat

### Combat System

- **Turn-Based Combat**: Strategic battle mechanics
- **Multiple Actions**: Attack, Defend, Use Items, Flee
- **Critical Hits & Dodging**: Stat-influenced combat bonuses
- **Enemy AI**: Different enemy behaviors (Aggressive, Defensive, Berserker, etc.)
- **Boss Battles**: Epic encounters with powerful foes

### Enemy Variety

- **8+ Enemy Types**: Goblins, Orcs, Skeletons, Wolves, Trolls, Dragons, and more
- **Enemy Ranks**: Minion, Normal, Elite, Boss, Legendary
- **Special Abilities**: Bosses have unique combat abilities
- **Loot System**: Enemies drop gold, XP, and items

### Inventory & Equipment

- **30+ Items**: Weapons, armor, potions, consumables, accessories, quest items
- **Item Rarity**: Common, Uncommon, Rare, Epic, Legendary
- **Equipment Slots**: Weapon, Armor, Shield, Accessory
- **Filtering & Searching**: Advanced inventory management

### Save System

- **Multiple Save Slots**: Up to 10 save slots
- **Automatic Backups**: Never lose your progress
- **Save Metadata**: Track playtime, save count, timestamps
- **Backup Restoration**: Restore from any backup

### Additional Features

- **Logging System**: Complete game logging for debugging
- **Shop System**: Buy items with gold
- **Configuration System**: Customizable game settings
- **Error Handling**: Robust exception handling throughout

## Installation

### Prerequisites

- Python 3.10 or higher

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/rob_of_the_shire.git
   cd rob_of_the_shire
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game**

   ```bash
   python main.py
   ```

## Quick Start

1. Launch the game with `python main.py`
2. Select "Create New Character" from the main menu
3. Enter your character's name and choose a class
4. Use the menu to manage inventory, fight enemies, and save your progress

## Gameplay Guide

### Main Menu Options

| Option                        | Description                                  |
| ----------------------------- | -------------------------------------------- |
| **1. Create New Character**   | Start a new adventure with a fresh character |
| **2. Load Character**         | Continue a saved game                        |
| **3. View Character Status**  | Check stats, equipment, and level progress   |
| **4. Manage Inventory**       | View, use, equip, or drop items              |
| **5. Visit Shop**             | Purchase items with gold                     |
| **6. Adventure (Combat)**     | Fight enemies and earn rewards               |
| **7. Allocate Stat Points**   | Spend stat points from leveling up           |
| **8. Save Game**              | Save current progress                        |
| **9. Manage Saves**           | Advanced save file management                |
| **0. Exit Game**              | Quit the game                                |

### Character Classes

| Class       | HP Bonus | Mana Bonus | Primary Stat   | Play Style             |
| ----------- | -------- | ---------- | -------------- | ---------------------- |
| **Warrior** | +30      | +0         | Strength       | Tank, high damage      |
| **Mage**    | +0       | +50        | Intelligence   | Magic damage, utility  |
| **Rogue**   | +10      | +20        | Agility        | Critical hits, evasion |
| **Ranger**  | +15      | +25        | Balanced       | Versatile, ranged      |

### Combat Tips

- **Defend** when low on health to reduce incoming damage
- **Use potions** before they're needed - dead characters can't heal
- **Equip weapons** before combat for maximum damage
- Higher **Agility** increases dodge chance
- Higher **Luck** increases critical hit chance
- **Boss battles** don't allow fleeing - prepare before engaging!

### Item Types

| Type           | Description                                      |
| -------------- | ------------------------------------------------ |
| **Weapon**     | Equipped for combat, provides damage and defense |
| **Armor**      | Equipped for defense and health bonuses          |
| **Potion**     | Consumable, restores health or mana              |
| **Consumable** | Single-use items with temporary buffs            |
| **Accessory**  | Equipped for stat bonuses                        |
| **Quest**      | Special items for quests                         |

## Project Structure

```text
rob_of_the_shire/
├── main.py              # Main game entry point and UI
├── character.py         # Character class with stats and inventory
├── enemy.py             # Enemy classes with AI behaviors
├── combat.py            # Combat encounter system
├── config.py            # Game configuration and constants
├── exceptions.py        # Custom exception classes
├── logger.py            # Logging system
├── save_system.py       # Save/load functionality with backups
├── itemloader.py        # Item database and loading
├── getfilter.py         # Filtering utilities
├── items.json           # Item data definitions
├── save.json            # Current save file
├── game.log             # Game log file
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_character.py
│   ├── test_combat.py
│   ├── test_enemy.py
│   └── test_save_system.py
└── README.md            # This file
```

## Technical Documentation

### Module Overview

#### character.py

The `Character` class represents the player character with:

- Stats system using dataclasses
- Equipment management with separate slots
- Inventory with capacity limits
- Combat methods (attack, defend, take_damage)
- Serialization for save/load

#### enemy.py

The `Enemy` class supports:

- Multiple enemy types with configurable stats
- AI behavior patterns (Aggressive, Defensive, etc.)
- Special abilities with cooldowns
- Loot tables with random drops
- Rank-based scaling (Minion to Legendary)

#### combat.py

The `CombatEncounter` class manages:

- Turn-based combat flow
- Action selection UI
- Damage calculations with defense
- Combat statistics tracking
- Victory/defeat resolution and rewards

#### save_system.py

The `SaveManager` class provides:

- JSON-based persistence
- Multiple save slots
- Automatic backup creation
- Backup cleanup (keeps last N backups)
- Save metadata with timestamps

#### config.py

Contains all game constants:

- `GameConfig` dataclass with defaults
- `ItemType`, `CharacterClass` enums
- `CLASS_STATS` for class bonuses
- `ENEMY_TYPES` definitions

### API Examples

```python
# Creating a character
from character import Character
from config import CharacterClass

hero = Character(
    name="Frodo",
    character_class=CharacterClass.ROGUE,
    level=1
)

# Adding items
hero.add_item({"name": "Iron Sword", "type": "weapon", "damage": 25})

# Combat
from combat import start_combat
from enemy import create_goblin

enemy = create_goblin(level=2)
result = start_combat(hero, enemy)

# Saving
from save_system import save_character, load_character

save_character(hero)
loaded_hero = load_character()
```

## Configuration

Game settings can be modified in `config.py`:

```python
@dataclass(frozen=True)
class GameConfig:
    DEFAULT_HEALTH: int = 100
    DEFAULT_MANA: int = 50
    MAX_INVENTORY_SIZE: int = 50
    BASE_XP_REQUIREMENT: int = 100
    XP_SCALING_FACTOR: float = 1.5
    # ... more options
```

### Adding New Items

Edit `items.json` to add new items:

```json
{
    "name": "My Custom Sword",
    "type": "weapon",
    "damage": 40,
    "defense": 10,
    "rarity": "RARE",
    "description": "A powerful custom weapon.",
    "value": 200,
    "level_requirement": 10
}
```

### Adding New Enemies

Add to `ENEMY_TYPES` in `config.py`:

```python
ENEMY_TYPES["custom_enemy"] = {
    "base_health": 100,
    "base_damage": 20,
    "xp_reward": 50
}
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_character.py -v
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and returns
- Write docstrings for all public classes and methods
- Add unit tests for new functionality

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by classic text-based RPGs
- Built with Python's standard library
- No external dependencies required for core gameplay

---

**Happy adventuring in the Shire!**