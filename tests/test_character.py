"""
Unit tests for the Character class.

Tests character creation, stats, inventory management,
equipment, combat actions, and serialization.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from character import Character, Stats, Equipment
from config import CharacterClass, config
from exceptions import (
    ItemNotFoundError, InventoryFullError, 
    ItemNotUsableError, InvalidWeaponError
)


class TestCharacterCreation:
    """Tests for character creation and initialization."""
    
    def test_create_basic_character(self):
        """Test creating a character with default values."""
        char = Character(name="TestHero")
        
        assert char.name == "TestHero"
        assert char.level == 1
        assert char.experience == 0
        assert char.is_alive
        assert len(char.inventory) == 0
    
    def test_create_character_with_class(self):
        """Test creating characters with different classes."""
        warrior = Character(name="Warrior", character_class=CharacterClass.WARRIOR)
        mage = Character(name="Mage", character_class=CharacterClass.MAGE)
        
        assert warrior.character_class == CharacterClass.WARRIOR
        assert mage.character_class == CharacterClass.MAGE
        
        # Warriors should have more health
        assert warrior.max_health > mage.max_health
        # Mages should have more mana
        assert mage.max_mana > warrior.max_mana
    
    def test_character_health_bounds(self):
        """Test that health is bounded correctly."""
        char = Character(name="Test", health=100)
        
        # Health shouldn't exceed max
        char.health = 200
        assert char.health <= char.max_health
        
        # Health shouldn't go below 0
        char.health = -50
        assert char.health >= 0


class TestStats:
    """Tests for the Stats dataclass."""
    
    def test_stats_creation(self):
        """Test creating stats with values."""
        stats = Stats(strength=15, agility=12, intelligence=8)
        
        assert stats.strength == 15
        assert stats.agility == 12
        assert stats.intelligence == 8
    
    def test_stats_addition(self):
        """Test adding two Stats objects."""
        stats1 = Stats(strength=10, agility=10)
        stats2 = Stats(strength=5, agility=3)
        
        combined = stats1 + stats2
        
        assert combined.strength == 15
        assert combined.agility == 13
    
    def test_stats_serialization(self):
        """Test converting stats to dict and back."""
        original = Stats(strength=15, agility=12, intelligence=8, vitality=10, luck=7)
        
        data = original.to_dict()
        restored = Stats.from_dict(data)
        
        assert restored.strength == original.strength
        assert restored.agility == original.agility
        assert restored.luck == original.luck


class TestInventory:
    """Tests for inventory management."""
    
    def test_add_item(self):
        """Test adding items to inventory."""
        char = Character(name="Test")
        item = {"name": "Sword", "type": "weapon", "damage": 10}
        
        char.add_item(item)
        
        assert len(char.inventory) == 1
        assert char.inventory[0]["name"] == "Sword"
    
    def test_add_item_creates_copy(self):
        """Test that adding item creates a copy."""
        char = Character(name="Test")
        item = {"name": "Sword", "type": "weapon", "damage": 10}
        
        char.add_item(item)
        item["damage"] = 100  # Modify original
        
        # Inventory copy should be unchanged
        assert char.inventory[0]["damage"] == 10
    
    def test_remove_item(self):
        """Test removing items from inventory."""
        char = Character(name="Test")
        char.add_item({"name": "Sword", "type": "weapon"})
        char.add_item({"name": "Shield", "type": "weapon"})
        
        removed = char.remove_item("Sword")
        
        assert removed is not None
        assert removed["name"] == "Sword"
        assert len(char.inventory) == 1
    
    def test_remove_nonexistent_item(self):
        """Test removing an item that doesn't exist."""
        char = Character(name="Test")
        
        removed = char.remove_item("Nonexistent")
        
        assert removed is None
    
    def test_get_item(self):
        """Test getting an item without removing."""
        char = Character(name="Test")
        char.add_item({"name": "Sword", "type": "weapon", "damage": 10})
        
        item = char.get_item("Sword")
        
        assert item is not None
        assert item["name"] == "Sword"
        assert len(char.inventory) == 1  # Still in inventory
    
    def test_has_item(self):
        """Test checking if character has an item."""
        char = Character(name="Test")
        char.add_item({"name": "Sword", "type": "weapon"})
        
        assert char.has_item("Sword")
        assert char.has_item("sword")  # Case insensitive
        assert not char.has_item("Shield")


class TestEquipment:
    """Tests for equipment system."""
    
    def test_equip_weapon(self):
        """Test equipping a weapon."""
        char = Character(name="Test")
        weapon = {"name": "Sword", "type": "weapon", "damage": 20}
        char.add_item(weapon)
        
        char.equip_item("Sword")
        
        assert char.equipment.weapon is not None
        assert char.equipment.weapon["name"] == "Sword"
        assert not char.has_item("Sword")  # Removed from inventory
    
    def test_equip_replaces_existing(self):
        """Test that equipping replaces existing equipment."""
        char = Character(name="Test")
        char.add_item({"name": "Iron Sword", "type": "weapon", "damage": 15})
        char.add_item({"name": "Steel Sword", "type": "weapon", "damage": 25})
        
        char.equip_item("Iron Sword")
        char.equip_item("Steel Sword")
        
        assert char.equipment.weapon["name"] == "Steel Sword"
        assert char.has_item("Iron Sword")  # Old item back in inventory
    
    def test_unequip_item(self):
        """Test unequipping an item."""
        char = Character(name="Test")
        char.add_item({"name": "Sword", "type": "weapon", "damage": 20})
        char.equip_item("Sword")
        
        char.unequip_item("weapon")
        
        assert char.equipment.weapon is None
        assert char.has_item("Sword")


class TestItemUsage:
    """Tests for using items."""
    
    def test_use_healing_potion(self):
        """Test using a healing potion."""
        char = Character(name="Test", health=100)
        char.health = 50  # Damage the character
        char.add_item({"name": "Health Potion", "type": "potion", "heal": 30})
        
        char.use_item("Health Potion")
        
        assert char.health == 80
        assert not char.has_item("Health Potion")  # Consumed
    
    def test_use_mana_potion(self):
        """Test using a mana potion."""
        char = Character(name="Test")
        char.mana = 10
        char.add_item({"name": "Mana Potion", "type": "potion", "mana": 25})
        
        char.use_item("Mana Potion")
        
        assert char.mana == 35
    
    def test_use_item_not_found(self):
        """Test using an item that doesn't exist."""
        char = Character(name="Test")
        
        with pytest.raises(ItemNotFoundError):
            char.use_item("Nonexistent Potion")
    
    def test_use_unusable_item(self):
        """Test using an item that can't be used."""
        char = Character(name="Test")
        char.add_item({"name": "Key", "type": "quest"})
        
        with pytest.raises(ItemNotUsableError):
            char.use_item("Key")


class TestExperience:
    """Tests for experience and leveling."""
    
    def test_gain_experience(self):
        """Test gaining experience."""
        char = Character(name="Test")
        initial_xp = char.experience
        
        char.gain_experience(50)
        
        assert char.experience == initial_xp + 50
    
    def test_level_up(self):
        """Test leveling up when enough XP gained."""
        char = Character(name="Test")
        xp_needed = char.xp_to_next_level
        
        levels = char.gain_experience(xp_needed + 10)
        
        assert char.level == 2
        assert len(levels) == 1
        assert char.available_stat_points == config.STAT_POINTS_PER_LEVEL
    
    def test_multiple_level_ups(self):
        """Test gaining multiple levels at once."""
        char = Character(name="Test")
        
        # Give a lot of XP
        levels = char.gain_experience(10000)
        
        assert char.level > 1
        assert len(levels) > 1
    
    def test_allocate_stat_point(self):
        """Test allocating stat points."""
        char = Character(name="Test")
        char.available_stat_points = 5
        initial_strength = char.stats.strength
        
        char.allocate_stat_point("strength")
        
        assert char.stats.strength == initial_strength + 1
        assert char.available_stat_points == 4


class TestCombat:
    """Tests for combat-related methods."""
    
    def test_get_attack_damage(self):
        """Test calculating attack damage."""
        char = Character(name="Test")
        weapon = {"name": "Sword", "type": "weapon", "damage": 20}
        
        damage = char.get_attack_damage(weapon)
        
        assert damage > 0
        assert damage >= 20  # At least weapon damage
    
    def test_get_defense(self):
        """Test calculating defense."""
        char = Character(name="Test")
        
        defense = char.get_defense()
        
        assert defense >= 0
    
    def test_defend_doubles_defense(self):
        """Test that defending doubles defense."""
        char = Character(name="Test")
        normal_defense = char.get_defense()
        
        char.defend()
        defending_defense = char.get_defense()
        
        assert defending_defense == normal_defense * 2
    
    def test_take_damage(self):
        """Test taking damage."""
        char = Character(name="Test", health=100)
        initial_health = char.health
        
        damage_taken = char.take_damage(30)
        
        assert char.health < initial_health
        assert damage_taken > 0
    
    def test_death(self):
        """Test character death when health reaches 0."""
        char = Character(name="Test", health=100)
        
        char.take_damage(1000)  # Massive damage
        
        assert not char.is_alive
        assert char.health == 0


class TestSerialization:
    """Tests for character serialization."""
    
    def test_to_dict(self):
        """Test converting character to dictionary."""
        char = Character(name="TestHero", character_class=CharacterClass.MAGE)
        char.add_item({"name": "Staff", "type": "weapon", "damage": 15})
        char.gold = 100
        
        data = char.to_dict()
        
        assert data["name"] == "TestHero"
        assert data["character_class"] == "MAGE"
        assert data["gold"] == 100
        assert len(data["inventory"]) == 1
    
    def test_from_dict(self):
        """Test creating character from dictionary."""
        data = {
            "name": "LoadedHero",
            "character_class": "ROGUE",
            "level": 5,
            "experience": 250,
            "health": 80,
            "max_health": 120,
            "mana": 40,
            "max_mana": 70,
            "stamina": 100,
            "max_stamina": 100,
            "stats": {
                "strength": 15,
                "agility": 20,
                "intelligence": 10,
                "vitality": 12,
                "luck": 8
            },
            "inventory": [{"name": "Dagger", "type": "weapon"}],
            "gold": 500
        }
        
        char = Character.from_dict(data)
        
        assert char.name == "LoadedHero"
        assert char.level == 5
        assert char.stats.agility == 20
        assert char.gold == 500
    
    def test_roundtrip_serialization(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = Character(
            name="RoundtripHero",
            character_class=CharacterClass.RANGER,
            level=3
        )
        original.add_item({"name": "Bow", "type": "weapon", "damage": 25})
        original.gold = 150
        original.experience = 75
        
        data = original.to_dict()
        restored = Character.from_dict(data)
        
        assert restored.name == original.name
        assert restored.level == original.level
        assert restored.gold == original.gold
        assert len(restored.inventory) == len(original.inventory)


class TestStringRepresentations:
    """Tests for string representations."""
    
    def test_str(self):
        """Test __str__ method."""
        char = Character(name="StringTest", level=5)
        
        result = str(char)
        
        assert "StringTest" in result
        assert "5" in result
    
    def test_repr(self):
        """Test __repr__ method."""
        char = Character(name="ReprTest", health=80)
        
        result = repr(char)
        
        assert "ReprTest" in result
        assert "Character" in result
    
    def test_inventory_str(self):
        """Test inventory_str method."""
        char = Character(name="Test")
        char.add_item({"name": "Sword", "type": "weapon", "damage": 20})
        char.add_item({"name": "Potion", "type": "potion", "heal": 30})
        
        result = char.inventory_str()
        
        assert "Sword" in result
        assert "Potion" in result
    
    def test_inventory_str_with_filter(self):
        """Test inventory_str with type filter."""
        char = Character(name="Test")
        char.add_item({"name": "Sword", "type": "weapon"})
        char.add_item({"name": "Potion", "type": "potion"})
        
        result = char.inventory_str(type_filters=["weapon"])
        
        assert "Sword" in result
        assert "Potion" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
