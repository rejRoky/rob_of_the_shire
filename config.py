"""
Configuration module for Rob of the Shire game.

Contains game constants, enums, and configuration settings used throughout
the application. Centralizes all magic numbers and configuration values.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Final


class ItemType(Enum):
    """Enumeration of all valid item types in the game."""
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    QUEST = "quest"
    CONSUMABLE = "consumable"
    ACCESSORY = "accessory"


class CharacterClass(Enum):
    """Character class types affecting stats and abilities."""
    WARRIOR = auto()
    MAGE = auto()
    ROGUE = auto()
    RANGER = auto()


class DifficultyLevel(Enum):
    """Game difficulty settings."""
    EASY = 0.5
    NORMAL = 1.0
    HARD = 1.5
    NIGHTMARE = 2.0


class CombatResult(Enum):
    """Possible outcomes of combat encounters."""
    VICTORY = auto()
    DEFEAT = auto()
    FLED = auto()
    ONGOING = auto()


@dataclass(frozen=True)
class GameConfig:
    """Immutable game configuration settings."""
    
    # Character defaults
    DEFAULT_HEALTH: int = 100
    DEFAULT_MANA: int = 50
    DEFAULT_STAMINA: int = 100
    MAX_HEALTH: int = 999
    MAX_MANA: int = 500
    MAX_STAMINA: int = 200
    
    # Level and experience
    BASE_XP_REQUIREMENT: int = 100
    XP_SCALING_FACTOR: float = 1.5
    MAX_LEVEL: int = 100
    STAT_POINTS_PER_LEVEL: int = 5
    
    # Combat settings
    BASE_CRIT_CHANCE: float = 0.05
    CRIT_DAMAGE_MULTIPLIER: float = 1.5
    DODGE_BASE_CHANCE: float = 0.1
    FLEE_BASE_CHANCE: float = 0.3
    
    # Inventory limits
    MAX_INVENTORY_SIZE: int = 50
    MAX_STACK_SIZE: int = 99
    
    # File paths
    SAVE_FILE: str = "save.json"
    ITEMS_FILE: str = "items.json"
    ENEMIES_FILE: str = "enemies.json"
    LOG_FILE: str = "game.log"
    BACKUP_DIR: str = "backups"
    
    # Display settings
    SCREEN_WIDTH: int = 60
    SEPARATOR_CHAR: str = "="


@dataclass(frozen=True)
class ClassStats:
    """Base stats for each character class."""
    health_bonus: int
    mana_bonus: int
    stamina_bonus: int
    strength_bonus: int
    agility_bonus: int
    intelligence_bonus: int


# Class-specific stat bonuses
CLASS_STATS: dict[CharacterClass, ClassStats] = {
    CharacterClass.WARRIOR: ClassStats(
        health_bonus=30,
        mana_bonus=0,
        stamina_bonus=20,
        strength_bonus=5,
        agility_bonus=2,
        intelligence_bonus=1
    ),
    CharacterClass.MAGE: ClassStats(
        health_bonus=0,
        mana_bonus=50,
        stamina_bonus=10,
        strength_bonus=1,
        agility_bonus=2,
        intelligence_bonus=5
    ),
    CharacterClass.ROGUE: ClassStats(
        health_bonus=10,
        mana_bonus=20,
        stamina_bonus=30,
        strength_bonus=2,
        agility_bonus=5,
        intelligence_bonus=2
    ),
    CharacterClass.RANGER: ClassStats(
        health_bonus=15,
        mana_bonus=25,
        stamina_bonus=25,
        strength_bonus=3,
        agility_bonus=4,
        intelligence_bonus=3
    ),
}


# Enemy type definitions
ENEMY_TYPES: Final[dict[str, dict]] = {
    "goblin": {"base_health": 30, "base_damage": 5, "xp_reward": 15},
    "orc": {"base_health": 60, "base_damage": 12, "xp_reward": 35},
    "troll": {"base_health": 100, "base_damage": 20, "xp_reward": 75},
    "dragon": {"base_health": 300, "base_damage": 50, "xp_reward": 500},
    "skeleton": {"base_health": 25, "base_damage": 8, "xp_reward": 20},
    "wolf": {"base_health": 35, "base_damage": 10, "xp_reward": 25},
    "bandit": {"base_health": 45, "base_damage": 15, "xp_reward": 40},
    "dark_knight": {"base_health": 150, "base_damage": 35, "xp_reward": 150},
}


# Singleton instance
config = GameConfig()
