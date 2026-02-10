"""
Custom exceptions for Rob of the Shire game.

Provides a hierarchy of game-specific exceptions for proper error handling
throughout the application. Enables precise error catching and meaningful
error messages for debugging and user feedback.
"""

from typing import Optional, Any


class GameException(Exception):
    """
    Base exception class for all game-related errors.
    
    All custom exceptions in the game should inherit from this class
    to allow for broad exception catching when needed.
    
    Attributes:
        message: Human-readable error description.
        details: Optional dictionary with additional error context.
    """
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


# ============================================================================
# Character-related exceptions
# ============================================================================

class CharacterException(GameException):
    """Base exception for character-related errors."""
    pass


class CharacterNotFoundError(CharacterException):
    """Raised when a character cannot be found or loaded."""
    
    def __init__(self, character_name: Optional[str] = None):
        message = f"Character '{character_name}' not found" if character_name else "No character loaded"
        super().__init__(message, {"character_name": character_name})


class CharacterDeadError(CharacterException):
    """Raised when attempting actions on a dead character."""
    
    def __init__(self, character_name: str):
        super().__init__(
            f"Character '{character_name}' is dead and cannot perform actions",
            {"character_name": character_name}
        )


class InsufficientStatsError(CharacterException):
    """Raised when character lacks required stats for an action."""
    
    def __init__(self, stat_name: str, required: int, current: int):
        super().__init__(
            f"Insufficient {stat_name}: need {required}, have {current}",
            {"stat_name": stat_name, "required": required, "current": current}
        )


class MaxLevelReachedError(CharacterException):
    """Raised when character is already at maximum level."""
    
    def __init__(self, current_level: int):
        super().__init__(
            f"Character already at maximum level ({current_level})",
            {"current_level": current_level}
        )


# ============================================================================
# Inventory-related exceptions
# ============================================================================

class InventoryException(GameException):
    """Base exception for inventory-related errors."""
    pass


class ItemNotFoundError(InventoryException):
    """Raised when an item cannot be found in inventory."""
    
    def __init__(self, item_name: str):
        super().__init__(
            f"Item '{item_name}' not found in inventory",
            {"item_name": item_name}
        )


class InventoryFullError(InventoryException):
    """Raised when inventory cannot accept more items."""
    
    def __init__(self, max_size: int):
        super().__init__(
            f"Inventory is full (max {max_size} items)",
            {"max_size": max_size}
        )


class InvalidItemError(InventoryException):
    """Raised when item data is invalid or malformed."""
    
    def __init__(self, item_name: str, reason: str):
        super().__init__(
            f"Invalid item '{item_name}': {reason}",
            {"item_name": item_name, "reason": reason}
        )


class ItemNotUsableError(InventoryException):
    """Raised when an item cannot be used."""
    
    def __init__(self, item_name: str, reason: str = "Item cannot be used"):
        super().__init__(
            f"Cannot use '{item_name}': {reason}",
            {"item_name": item_name, "reason": reason}
        )


class ItemNotEquippableError(InventoryException):
    """Raised when an item cannot be equipped."""
    
    def __init__(self, item_name: str, item_type: str):
        super().__init__(
            f"Cannot equip '{item_name}' (type: {item_type})",
            {"item_name": item_name, "item_type": item_type}
        )


# ============================================================================
# Combat-related exceptions
# ============================================================================

class CombatException(GameException):
    """Base exception for combat-related errors."""
    pass


class NoCombatInProgressError(CombatException):
    """Raised when combat action attempted but no combat is active."""
    
    def __init__(self):
        super().__init__("No combat currently in progress")


class InvalidWeaponError(CombatException):
    """Raised when attempting to attack with invalid weapon."""
    
    def __init__(self, weapon_name: str):
        super().__init__(
            f"'{weapon_name}' is not a valid weapon",
            {"weapon_name": weapon_name}
        )


class EnemyDeadError(CombatException):
    """Raised when attempting to attack a dead enemy."""
    
    def __init__(self, enemy_name: str):
        super().__init__(
            f"Enemy '{enemy_name}' is already defeated",
            {"enemy_name": enemy_name}
        )


class FleeFailedError(CombatException):
    """Raised when flee attempt fails."""
    
    def __init__(self):
        super().__init__("Failed to flee from combat!")


# ============================================================================
# Save/Load exceptions
# ============================================================================

class SaveException(GameException):
    """Base exception for save/load related errors."""
    pass


class SaveFileNotFoundError(SaveException):
    """Raised when save file doesn't exist."""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"Save file not found: {file_path}",
            {"file_path": file_path}
        )


class SaveFileCorruptedError(SaveException):
    """Raised when save file is corrupted or invalid."""
    
    def __init__(self, file_path: str, reason: str):
        super().__init__(
            f"Save file corrupted: {reason}",
            {"file_path": file_path, "reason": reason}
        )


class SaveFailedError(SaveException):
    """Raised when saving fails."""
    
    def __init__(self, reason: str):
        super().__init__(f"Failed to save game: {reason}", {"reason": reason})


# ============================================================================
# Configuration/Data exceptions
# ============================================================================

class ConfigException(GameException):
    """Base exception for configuration errors."""
    pass


class DataFileNotFoundError(ConfigException):
    """Raised when a required data file is missing."""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"Required data file not found: {file_path}",
            {"file_path": file_path}
        )


class InvalidDataFormatError(ConfigException):
    """Raised when data file has invalid format."""
    
    def __init__(self, file_path: str, reason: str):
        super().__init__(
            f"Invalid data format in {file_path}: {reason}",
            {"file_path": file_path, "reason": reason}
        )


# ============================================================================
# Input validation exceptions
# ============================================================================

class ValidationException(GameException):
    """Base exception for input validation errors."""
    pass


class InvalidInputError(ValidationException):
    """Raised when user input is invalid."""
    
    def __init__(self, input_value: str, expected: str):
        super().__init__(
            f"Invalid input '{input_value}': expected {expected}",
            {"input_value": input_value, "expected": expected}
        )


class OutOfRangeError(ValidationException):
    """Raised when a value is outside acceptable range."""
    
    def __init__(self, value: Any, min_val: Any, max_val: Any):
        super().__init__(
            f"Value {value} is out of range [{min_val}, {max_val}]",
            {"value": value, "min": min_val, "max": max_val}
        )
