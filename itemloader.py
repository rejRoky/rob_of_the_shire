"""
Item loader module for Rob of the Shire game.

Provides functionality for loading, validating, and managing game items
from JSON data files. Includes item generation and rarity systems.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum, auto
import random

from config import config, ItemType
from exceptions import DataFileNotFoundError, InvalidDataFormatError, InvalidItemError
from logger import get_logger


class ItemRarity(Enum):
    """Item rarity levels affecting stats and value."""
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5
    
    @property
    def color(self) -> str:
        """Get display color for rarity."""
        colors = {
            ItemRarity.COMMON: "⚪",
            ItemRarity.UNCOMMON: "🟢",
            ItemRarity.RARE: "🔵",
            ItemRarity.EPIC: "🟣",
            ItemRarity.LEGENDARY: "🟡"
        }
        return colors.get(self, "⚪")
    
    @property
    def stat_multiplier(self) -> float:
        """Get stat multiplier for this rarity."""
        return 1.0 + (self.value - 1) * 0.25


@dataclass
class Item:
    """
    Represents a game item with full metadata.
    
    Attributes:
        name: Item display name.
        item_type: Type of item (weapon, armor, etc.).
        rarity: Item rarity level.
        properties: Dictionary of item-specific properties.
        description: Optional item description.
        value: Gold value of the item.
        level_requirement: Minimum level to use/equip.
    """
    name: str
    item_type: str
    rarity: ItemRarity = ItemRarity.COMMON
    properties: dict = None
    description: str = ""
    value: int = 10
    level_requirement: int = 1
    
    def __post_init__(self):
        """Initialize properties if None."""
        if self.properties is None:
            self.properties = {}
    
    def to_dict(self) -> dict:
        """Convert item to dictionary format."""
        result = {
            "name": self.name,
            "type": self.item_type,
            "rarity": self.rarity.name,
            "description": self.description,
            "value": self.value,
            "level_requirement": self.level_requirement
        }
        result.update(self.properties)
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        """Create Item from dictionary."""
        # Extract known fields
        name = data.get("name", "Unknown Item")
        item_type = data.get("type", "misc")
        
        rarity_str = data.get("rarity", "COMMON")
        try:
            rarity = ItemRarity[rarity_str.upper()]
        except KeyError:
            rarity = ItemRarity.COMMON
        
        description = data.get("description", "")
        value = data.get("value", 10)
        level_req = data.get("level_requirement", 1)
        
        # Everything else goes into properties
        excluded = {"name", "type", "rarity", "description", "value", "level_requirement"}
        properties = {k: v for k, v in data.items() if k not in excluded}
        
        return cls(
            name=name,
            item_type=item_type,
            rarity=rarity,
            properties=properties,
            description=description,
            value=value,
            level_requirement=level_req
        )
    
    def display(self) -> str:
        """Get formatted display string."""
        lines = [f"{self.rarity.color} {self.name} [{self.item_type}]"]
        
        if self.description:
            lines.append(f"   {self.description}")
        
        for key, value in self.properties.items():
            lines.append(f"   • {key}: {value}")
        
        lines.append(f"   Value: {self.value} gold | Req. Level: {self.level_requirement}")
        
        return "\n".join(lines)


class ItemDatabase:
    """
    Database of all game items loaded from data files.
    
    Provides methods for querying, filtering, and generating items.
    Supports caching and lazy loading.
    
    Attributes:
        items: List of all loaded items.
        items_by_name: Dictionary for name-based lookup.
        items_by_type: Dictionary for type-based lookup.
    """
    
    def __init__(self, file_path: str = None):
        """
        Initialize the item database.
        
        Args:
            file_path: Path to items JSON file.
        """
        self.logger = get_logger()
        self.file_path = Path(file_path) if file_path else Path(config.ITEMS_FILE)
        
        self.items: list[dict] = []
        self.items_by_name: dict[str, dict] = {}
        self.items_by_type: dict[str, list[dict]] = {}
        
        self._loaded = False
    
    def load(self, force: bool = False) -> list[dict]:
        """
        Load items from the data file.
        
        Args:
            force: Force reload even if already loaded.
            
        Returns:
            List of item dictionaries.
            
        Raises:
            DataFileNotFoundError: If file doesn't exist.
            InvalidDataFormatError: If file is malformed.
        """
        if self._loaded and not force:
            return self.items
        
        if not self.file_path.exists():
            raise DataFileNotFoundError(str(self.file_path))
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataFormatError(str(self.file_path), f"Invalid JSON: {e}")
        
        if not isinstance(data, list):
            raise InvalidDataFormatError(str(self.file_path), "Expected array of items")
        
        self.items = []
        self.items_by_name.clear()
        self.items_by_type.clear()
        
        for item_data in data:
            self._validate_item(item_data)
            self.items.append(item_data)
            
            # Index by name (lowercase for case-insensitive lookup)
            name_key = item_data["name"].lower()
            self.items_by_name[name_key] = item_data
            
            # Index by type
            item_type = item_data.get("type", "misc")
            if item_type not in self.items_by_type:
                self.items_by_type[item_type] = []
            self.items_by_type[item_type].append(item_data)
        
        self._loaded = True
        self.logger.info(f"Loaded {len(self.items)} items from {self.file_path}")
        
        return self.items
    
    def _validate_item(self, item: dict) -> None:
        """
        Validate an item dictionary.
        
        Args:
            item: Item data to validate.
            
        Raises:
            InvalidItemError: If item is invalid.
        """
        if "name" not in item:
            raise InvalidItemError("unknown", "Missing 'name' field")
        
        if "type" not in item:
            raise InvalidItemError(item["name"], "Missing 'type' field")
    
    def get_all(self) -> list[dict]:
        """Get all items."""
        self.load()
        return self.items.copy()
    
    def get_by_name(self, name: str) -> Optional[dict]:
        """
        Get an item by name.
        
        Args:
            name: Item name (case-insensitive).
            
        Returns:
            Item dictionary or None if not found.
        """
        self.load()
        return self.items_by_name.get(name.lower())
    
    def get_by_type(self, item_type: str) -> list[dict]:
        """
        Get all items of a given type.
        
        Args:
            item_type: Type to filter by.
            
        Returns:
            List of matching items.
        """
        self.load()
        return self.items_by_type.get(item_type, []).copy()
    
    def search(
        self,
        name_pattern: str = None,
        item_types: list[str] = None,
        min_damage: int = None,
        max_damage: int = None,
        min_defense: int = None,
        max_defense: int = None
    ) -> list[dict]:
        """
        Search items with multiple filters.
        
        Args:
            name_pattern: Substring to match in name.
            item_types: List of types to include.
            min_damage: Minimum damage value.
            max_damage: Maximum damage value.
            min_defense: Minimum defense value.
            max_defense: Maximum defense value.
            
        Returns:
            List of matching items.
        """
        self.load()
        results = []
        
        for item in self.items:
            # Name filter
            if name_pattern:
                if name_pattern.lower() not in item["name"].lower():
                    continue
            
            # Type filter
            if item_types:
                if item.get("type") not in item_types:
                    continue
            
            # Damage filter
            damage = item.get("damage", 0)
            if min_damage is not None and damage < min_damage:
                continue
            if max_damage is not None and damage > max_damage:
                continue
            
            # Defense filter
            defense = item.get("defense", 0)
            if min_defense is not None and defense < min_defense:
                continue
            if max_defense is not None and defense > max_defense:
                continue
            
            results.append(item)
        
        return results
    
    def get_random(
        self,
        item_type: str = None,
        count: int = 1,
        rarity_weights: dict[str, float] = None
    ) -> list[dict]:
        """
        Get random items.
        
        Args:
            item_type: Optional type filter.
            count: Number of items to return.
            rarity_weights: Optional rarity weighting.
            
        Returns:
            List of random items.
        """
        self.load()
        
        pool = self.items_by_type.get(item_type, []) if item_type else self.items
        
        if not pool:
            return []
        
        return random.choices(pool, k=min(count, len(pool)))
    
    def get_types(self) -> list[str]:
        """Get list of all item types."""
        self.load()
        return list(self.items_by_type.keys())
    
    def count(self) -> int:
        """Get total number of items."""
        self.load()
        return len(self.items)
    
    def display_all(self) -> str:
        """Get formatted display of all items."""
        self.load()
        lines = [f"{'─' * 40}", "ITEM DATABASE", f"{'─' * 40}"]
        
        for item_type, items in self.items_by_type.items():
            lines.append(f"\n[{item_type.upper()}]")
            for item in items:
                item_obj = Item.from_dict(item)
                lines.append(f"  {item_obj.rarity.color} {item['name']}")
                for key, val in item.items():
                    if key not in ["name", "type"]:
                        lines.append(f"      {key}: {val}")
        
        return "\n".join(lines)


# ============================================================================
# Convenience Functions (Backward Compatibility)
# ============================================================================

_default_database: Optional[ItemDatabase] = None


def get_item_database() -> ItemDatabase:
    """Get the default item database instance."""
    global _default_database
    if _default_database is None:
        _default_database = ItemDatabase()
    return _default_database


def load_items(file_path: str = None) -> list[dict]:
    """
    Load items from file (backward compatible).
    
    Args:
        file_path: Optional custom file path.
        
    Returns:
        List of item dictionaries.
    """
    if file_path:
        db = ItemDatabase(file_path)
    else:
        db = get_item_database()
    
    return db.load()


def get_item_by_name(name: str) -> Optional[dict]:
    """Get an item by name."""
    return get_item_database().get_by_name(name)


def get_items_by_type(item_type: str) -> list[dict]:
    """Get items by type."""
    return get_item_database().get_by_type(item_type)


def get_random_item(item_type: str = None) -> Optional[dict]:
    """Get a random item."""
    items = get_item_database().get_random(item_type, 1)
    return items[0] if items else None
