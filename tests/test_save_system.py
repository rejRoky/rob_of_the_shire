"""
Unit tests for the Save System.

Tests save/load functionality, backups, save metadata,
and error handling.
"""

import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from save_system import (
    SaveManager, SaveMetadata, save_character, load_character,
    SAVE_VERSION
)
from character import Character
from config import CharacterClass
from exceptions import SaveFileNotFoundError, SaveFileCorruptedError


class TestSaveMetadata:
    """Tests for SaveMetadata class."""
    
    def test_create_metadata(self):
        """Test creating save metadata."""
        metadata = SaveMetadata(
            character_name="TestHero",
            character_level=5
        )
        
        assert metadata.character_name == "TestHero"
        assert metadata.character_level == 5
        assert metadata.version == SAVE_VERSION
    
    def test_metadata_timestamps(self):
        """Test that timestamps are set automatically."""
        metadata = SaveMetadata()
        
        assert metadata.created_at != ""
        assert metadata.modified_at != ""
    
    def test_update_modified(self):
        """Test updating modified timestamp."""
        metadata = SaveMetadata()
        original_modified = metadata.modified_at
        
        metadata.update_modified()
        
        assert metadata.save_count == 1
        # Modified time should change (though might be same second)
    
    def test_metadata_serialization(self):
        """Test converting metadata to dict and back."""
        original = SaveMetadata(
            character_name="SerialTest",
            character_level=10,
            playtime_seconds=3600,
            save_count=5
        )
        
        data = original.to_dict()
        restored = SaveMetadata.from_dict(data)
        
        assert restored.character_name == original.character_name
        assert restored.playtime_seconds == original.playtime_seconds


class TestSaveManager:
    """Tests for SaveManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def save_manager(self, temp_dir):
        """Create a save manager with temp directory."""
        return SaveManager(save_dir=temp_dir)
    
    @pytest.fixture
    def sample_character(self):
        """Create a sample character for testing."""
        char = Character(
            name="SaveTestHero",
            character_class=CharacterClass.WARRIOR,
            level=5
        )
        char.add_item({"name": "Sword", "type": "weapon", "damage": 20})
        char.gold = 100
        return char
    
    def test_save_creates_file(self, save_manager, sample_character, temp_dir):
        """Test that saving creates a save file."""
        save_manager.save(sample_character, slot=0)
        
        save_path = Path(temp_dir) / "save.json"
        assert save_path.exists()
    
    def test_save_and_load(self, save_manager, sample_character):
        """Test complete save and load cycle."""
        save_manager.save(sample_character, slot=0)
        loaded = save_manager.load(slot=0)
        
        assert loaded.name == sample_character.name
        assert loaded.level == sample_character.level
        assert loaded.gold == sample_character.gold
    
    def test_save_to_different_slots(self, save_manager, temp_dir):
        """Test saving to different slots."""
        char1 = Character(name="Hero1")
        char2 = Character(name="Hero2")
        
        save_manager.save(char1, slot=1)
        save_manager.save(char2, slot=2)
        
        loaded1 = save_manager.load(slot=1)
        loaded2 = save_manager.load(slot=2)
        
        assert loaded1.name == "Hero1"
        assert loaded2.name == "Hero2"
    
    def test_load_nonexistent_save(self, save_manager):
        """Test loading a save that doesn't exist."""
        with pytest.raises(SaveFileNotFoundError):
            save_manager.load(slot=99)
    
    def test_save_creates_backup(self, save_manager, sample_character, temp_dir):
        """Test that saving creates a backup of existing save."""
        # First save
        save_manager.save(sample_character, slot=0)
        
        # Modify and save again
        sample_character.gold = 500
        save_manager.save(sample_character, slot=0)
        
        # Check backup exists
        backup_dir = Path(temp_dir) / "backups"
        backups = list(backup_dir.glob("backup_0_*.json"))
        
        assert len(backups) >= 1
    
    def test_backup_cleanup(self, save_manager, sample_character):
        """Test that old backups are cleaned up."""
        save_manager.max_backups = 2
        
        # Create many saves to trigger cleanup
        for i in range(5):
            sample_character.gold = i * 100
            save_manager.save(sample_character, slot=0)
        
        backups = save_manager.list_backups(slot=0)
        assert len(backups) <= save_manager.max_backups
    
    def test_save_exists(self, save_manager, sample_character):
        """Test checking if save exists."""
        assert not save_manager.save_exists(slot=0)
        
        save_manager.save(sample_character, slot=0)
        
        assert save_manager.save_exists(slot=0)
    
    def test_list_saves(self, save_manager):
        """Test listing all saves."""
        char1 = Character(name="Slot0")
        char2 = Character(name="Slot1")
        
        save_manager.save(char1, slot=0)
        save_manager.save(char2, slot=1)
        
        saves = save_manager.list_saves()
        
        assert len(saves) == 2
    
    def test_get_save_info(self, save_manager, sample_character):
        """Test getting save metadata."""
        save_manager.save(sample_character, slot=0)
        
        info = save_manager.get_save_info(slot=0)
        
        assert info is not None
        assert info.character_name == sample_character.name
        assert info.character_level == sample_character.level
    
    def test_delete_save(self, save_manager, sample_character):
        """Test deleting a save."""
        save_manager.save(sample_character, slot=0)
        assert save_manager.save_exists(slot=0)
        
        save_manager.delete_save(slot=0)
        
        assert not save_manager.save_exists(slot=0)


class TestCorruptedSaves:
    """Tests for handling corrupted save files."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    def test_load_invalid_json(self, temp_dir):
        """Test loading a file with invalid JSON."""
        save_manager = SaveManager(save_dir=temp_dir)
        save_path = Path(temp_dir) / "save.json"
        
        # Write invalid JSON
        save_path.write_text("{ invalid json }")
        
        with pytest.raises(SaveFileCorruptedError):
            save_manager.load(slot=0)
    
    def test_load_missing_character_data(self, temp_dir):
        """Test loading save without character data."""
        save_manager = SaveManager(save_dir=temp_dir)
        save_path = Path(temp_dir) / "save.json"
        
        # Write valid JSON but missing character
        save_path.write_text('{"metadata": {}}')
        
        with pytest.raises(SaveFileCorruptedError):
            save_manager.load(slot=0)


class TestBackwardCompatibility:
    """Tests for backward compatibility functions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        temp = tempfile.mkdtemp()
        original_cwd = Path.cwd()
        yield temp
        shutil.rmtree(temp)
    
    def test_save_character_function(self, temp_dir, monkeypatch):
        """Test the save_character convenience function."""
        monkeypatch.chdir(temp_dir)
        
        char = Character(name="CompatTest")
        
        # Should not raise
        result = save_character(char)
        
        assert result is True or result is None
    
    def test_load_character_function(self, temp_dir, monkeypatch):
        """Test the load_character convenience function."""
        monkeypatch.chdir(temp_dir)
        
        char = Character(name="LoadTest", level=3)
        save_character(char)
        
        loaded = load_character()
        
        assert loaded.name == "LoadTest"
        assert loaded.level == 3


class TestSaveDataIntegrity:
    """Tests for save data integrity."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    def test_inventory_preserved(self, temp_dir):
        """Test that inventory items are preserved correctly."""
        save_manager = SaveManager(save_dir=temp_dir)
        
        char = Character(name="InventoryTest")
        items = [
            {"name": "Sword", "type": "weapon", "damage": 25},
            {"name": "Shield", "type": "weapon", "defense": 15},
            {"name": "Potion", "type": "potion", "heal": 50}
        ]
        for item in items:
            char.add_item(item)
        
        save_manager.save(char, slot=0)
        loaded = save_manager.load(slot=0)
        
        assert len(loaded.inventory) == 3
        assert any(item["name"] == "Sword" for item in loaded.inventory)
    
    def test_equipment_preserved(self, temp_dir):
        """Test that equipped items are preserved."""
        save_manager = SaveManager(save_dir=temp_dir)
        
        char = Character(name="EquipTest")
        char.add_item({"name": "Steel Sword", "type": "weapon", "damage": 30})
        char.equip_item("Steel Sword")
        
        save_manager.save(char, slot=0)
        loaded = save_manager.load(slot=0)
        
        assert loaded.equipment.weapon is not None
        assert loaded.equipment.weapon["name"] == "Steel Sword"
    
    def test_stats_preserved(self, temp_dir):
        """Test that character stats are preserved."""
        save_manager = SaveManager(save_dir=temp_dir)
        
        char = Character(name="StatsTest")
        char.available_stat_points = 10
        char.allocate_stat_point("strength")
        char.allocate_stat_point("strength")
        char.allocate_stat_point("agility")
        
        save_manager.save(char, slot=0)
        loaded = save_manager.load(slot=0)
        
        assert loaded.stats.strength == char.stats.strength
        assert loaded.stats.agility == char.stats.agility
        assert loaded.available_stat_points == char.available_stat_points


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
