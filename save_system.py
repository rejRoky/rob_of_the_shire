"""
Save system module for Rob of the Shire game.

Provides comprehensive save/load functionality with:
- JSON-based persistence
- Automatic backups
- Save file validation
- Multiple save slots
- Save metadata (timestamps, playtime)
"""

from __future__ import annotations
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field, asdict

from config import config
from exceptions import (
    SaveException, SaveFileNotFoundError, 
    SaveFileCorruptedError, SaveFailedError
)
from logger import get_logger, log_function_call

if TYPE_CHECKING:
    from character import Character


# Current save file format version
SAVE_VERSION = "2.0.0"


@dataclass
class SaveMetadata:
    """
    Metadata stored with each save file.
    
    Attributes:
        version: Save file format version.
        created_at: Timestamp when save was created.
        modified_at: Timestamp when save was last modified.
        playtime_seconds: Total playtime in seconds.
        save_count: Number of times this save has been saved.
        character_name: Name of the saved character.
        character_level: Level of the saved character.
    """
    version: str = SAVE_VERSION
    created_at: str = ""
    modified_at: str = ""
    playtime_seconds: int = 0
    save_count: int = 0
    character_name: str = ""
    character_level: int = 1
    
    def __post_init__(self):
        """Set timestamps if not provided."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.modified_at:
            self.modified_at = now
    
    def update_modified(self) -> None:
        """Update the modified timestamp."""
        self.modified_at = datetime.now().isoformat()
        self.save_count += 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SaveMetadata':
        """Create from dictionary."""
        return cls(
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            playtime_seconds=data.get("playtime_seconds", 0),
            save_count=data.get("save_count", 0),
            character_name=data.get("character_name", ""),
            character_level=data.get("character_level", 1)
        )
    
    def display(self) -> str:
        """Get formatted display string."""
        created = datetime.fromisoformat(self.created_at).strftime("%Y-%m-%d %H:%M")
        modified = datetime.fromisoformat(self.modified_at).strftime("%Y-%m-%d %H:%M")
        
        hours = self.playtime_seconds // 3600
        minutes = (self.playtime_seconds % 3600) // 60
        
        return (
            f"Character: {self.character_name} (Level {self.character_level})\n"
            f"Created: {created}\n"
            f"Last Saved: {modified}\n"
            f"Playtime: {hours}h {minutes}m\n"
            f"Save Count: {self.save_count}"
        )


class SaveManager:
    """
    Manages save and load operations for the game.
    
    Provides methods for saving, loading, backing up, and managing
    save files. Supports multiple save slots and automatic backups.
    
    Attributes:
        save_dir: Directory for save files.
        backup_dir: Directory for backup files.
        max_backups: Maximum number of backups to keep.
    """
    
    def __init__(
        self,
        save_dir: str = ".",
        backup_dir: Optional[str] = None,
        max_backups: int = 5
    ):
        """
        Initialize the save manager.
        
        Args:
            save_dir: Directory for save files.
            backup_dir: Directory for backups (defaults to save_dir/backups).
            max_backups: Maximum number of backup files to keep.
        """
        self.logger = get_logger()
        
        self.save_dir = Path(save_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else self.save_dir / config.BACKUP_DIR
        self.max_backups = max_backups
        
        # Ensure directories exist
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_save_path(self, slot: int = 0) -> Path:
        """Get path for a save slot."""
        if slot == 0:
            return self.save_dir / config.SAVE_FILE
        return self.save_dir / f"save_slot_{slot}.json"
    
    def _get_backup_path(self, slot: int = 0) -> Path:
        """Get path for a backup file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.backup_dir / f"backup_{slot}_{timestamp}.json"
    
    @log_function_call
    def save(
        self,
        character: 'Character',
        slot: int = 0,
        create_backup: bool = True
    ) -> bool:
        """
        Save a character to a save slot.
        
        Args:
            character: The character to save.
            slot: Save slot number (0 = default).
            create_backup: Whether to create a backup first.
            
        Returns:
            True if save was successful.
            
        Raises:
            SaveFailedError: If saving fails.
        """
        save_path = self._get_save_path(slot)
        
        try:
            # Create backup of existing save
            if create_backup and save_path.exists():
                self.create_backup(slot)
            
            # Load or create metadata
            if save_path.exists():
                try:
                    existing_data = self._load_raw(save_path)
                    metadata = SaveMetadata.from_dict(existing_data.get("metadata", {}))
                except Exception:
                    metadata = SaveMetadata()
            else:
                metadata = SaveMetadata()
            
            # Update metadata
            metadata.update_modified()
            metadata.character_name = character.name
            metadata.character_level = character.level
            metadata.version = SAVE_VERSION
            
            # Build save data
            save_data = {
                "metadata": metadata.to_dict(),
                "character": character.to_dict()
            }
            
            # Write to temp file first (atomic save)
            temp_path = save_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            
            # Move temp file to actual save (atomic on most systems)
            shutil.move(str(temp_path), str(save_path))
            
            self.logger.log_save_action("Saved", character.name, str(save_path))
            print(f"✅ Game saved successfully!")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to save: {e}")
            raise SaveFailedError(str(e))
    
    @log_function_call
    def load(self, slot: int = 0) -> 'Character':
        """
        Load a character from a save slot.
        
        Args:
            slot: Save slot number to load.
            
        Returns:
            The loaded Character instance.
            
        Raises:
            SaveFileNotFoundError: If save file doesn't exist.
            SaveFileCorruptedError: If save file is invalid.
        """
        # Import here to avoid circular imports
        from character import Character
        
        save_path = self._get_save_path(slot)
        
        if not save_path.exists():
            raise SaveFileNotFoundError(str(save_path))
        
        try:
            data = self._load_raw(save_path)
            
            # Validate save data
            self._validate_save_data(data)
            
            # Load character
            character = Character.from_dict(data["character"])
            
            self.logger.log_save_action("Loaded", character.name, str(save_path))
            print(f"✅ Loaded character '{character.name}' (Level {character.level})")
            
            return character
            
        except json.JSONDecodeError as e:
            raise SaveFileCorruptedError(str(save_path), f"Invalid JSON: {e}")
        except KeyError as e:
            raise SaveFileCorruptedError(str(save_path), f"Missing data: {e}")
        except Exception as e:
            raise SaveFileCorruptedError(str(save_path), str(e))
    
    def _load_raw(self, path: Path) -> dict:
        """Load raw JSON data from file."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _validate_save_data(self, data: dict) -> None:
        """
        Validate save data structure.
        
        Args:
            data: The loaded save data.
            
        Raises:
            SaveFileCorruptedError: If validation fails.
        """
        if "character" not in data:
            raise SaveFileCorruptedError("save", "Missing character data")
        
        char_data = data["character"]
        required_fields = ["name"]
        
        for field in required_fields:
            if field not in char_data:
                raise SaveFileCorruptedError("save", f"Missing field: {field}")
    
    def create_backup(self, slot: int = 0) -> bool:
        """
        Create a backup of a save slot.
        
        Args:
            slot: Save slot to backup.
            
        Returns:
            True if backup was created.
        """
        save_path = self._get_save_path(slot)
        
        if not save_path.exists():
            return False
        
        backup_path = self._get_backup_path(slot)
        
        try:
            shutil.copy2(str(save_path), str(backup_path))
            self.logger.debug(f"Created backup: {backup_path}")
            
            # Clean up old backups
            self._cleanup_old_backups(slot)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def _cleanup_old_backups(self, slot: int) -> None:
        """Remove old backup files beyond max_backups limit."""
        pattern = f"backup_{slot}_*.json"
        backups = sorted(self.backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
        
        while len(backups) > self.max_backups:
            old_backup = backups.pop(0)
            old_backup.unlink()
            self.logger.debug(f"Removed old backup: {old_backup}")
    
    def list_backups(self, slot: int = 0) -> list[dict]:
        """
        List available backups for a slot.
        
        Args:
            slot: Save slot to list backups for.
            
        Returns:
            List of backup info dictionaries.
        """
        pattern = f"backup_{slot}_*.json"
        backups = sorted(
            self.backup_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        result = []
        for backup_path in backups:
            try:
                data = self._load_raw(backup_path)
                metadata = SaveMetadata.from_dict(data.get("metadata", {}))
                result.append({
                    "path": str(backup_path),
                    "name": backup_path.name,
                    "modified": backup_path.stat().st_mtime,
                    "metadata": metadata
                })
            except Exception:
                result.append({
                    "path": str(backup_path),
                    "name": backup_path.name,
                    "modified": backup_path.stat().st_mtime,
                    "metadata": None
                })
        
        return result
    
    def restore_backup(self, backup_path: str, slot: int = 0) -> 'Character':
        """
        Restore a character from a backup.
        
        Args:
            backup_path: Path to backup file.
            slot: Slot to restore to.
            
        Returns:
            The restored Character instance.
        """
        from character import Character
        
        backup = Path(backup_path)
        
        if not backup.exists():
            raise SaveFileNotFoundError(backup_path)
        
        data = self._load_raw(backup)
        self._validate_save_data(data)
        
        character = Character.from_dict(data["character"])
        
        # Save to slot (overwrites current save)
        self.save(character, slot, create_backup=True)
        
        self.logger.info(f"Restored backup to slot {slot}")
        return character
    
    def delete_save(self, slot: int = 0, keep_backups: bool = True) -> bool:
        """
        Delete a save file.
        
        Args:
            slot: Save slot to delete.
            keep_backups: Whether to preserve backup files.
            
        Returns:
            True if save was deleted.
        """
        save_path = self._get_save_path(slot)
        
        if not save_path.exists():
            return False
        
        if not keep_backups:
            self.create_backup(slot)
        
        save_path.unlink()
        self.logger.info(f"Deleted save slot {slot}")
        
        return True
    
    def get_save_info(self, slot: int = 0) -> Optional[SaveMetadata]:
        """
        Get metadata for a save slot.
        
        Args:
            slot: Save slot to check.
            
        Returns:
            SaveMetadata if save exists, None otherwise.
        """
        save_path = self._get_save_path(slot)
        
        if not save_path.exists():
            return None
        
        try:
            data = self._load_raw(save_path)
            return SaveMetadata.from_dict(data.get("metadata", {}))
        except Exception:
            return None
    
    def list_saves(self) -> list[dict]:
        """
        List all save files.
        
        Returns:
            List of save info dictionaries.
        """
        saves = []
        
        # Check default save
        default_path = self._get_save_path(0)
        if default_path.exists():
            info = self.get_save_info(0)
            saves.append({
                "slot": 0,
                "path": str(default_path),
                "metadata": info
            })
        
        # Check numbered slots
        for slot in range(1, 10):
            path = self._get_save_path(slot)
            if path.exists():
                info = self.get_save_info(slot)
                saves.append({
                    "slot": slot,
                    "path": str(path),
                    "metadata": info
                })
        
        return saves
    
    def save_exists(self, slot: int = 0) -> bool:
        """Check if a save slot exists."""
        return self._get_save_path(slot).exists()


# ============================================================================
# Convenience Functions (Backward Compatibility)
# ============================================================================

_default_manager: Optional[SaveManager] = None


def get_save_manager() -> SaveManager:
    """Get the default save manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = SaveManager()
    return _default_manager


def save_character(character: 'Character', file_path: str = None) -> bool:
    """
    Save a character (backward compatible function).
    
    Args:
        character: Character to save.
        file_path: Optional custom file path (ignored, uses default).
        
    Returns:
        True if successful.
    """
    return get_save_manager().save(character, slot=0)


def load_character(file_path: str = None) -> 'Character':
    """
    Load a character (backward compatible function).
    
    Args:
        file_path: Optional custom file path (ignored, uses default).
        
    Returns:
        Loaded Character instance.
    """
    return get_save_manager().load(slot=0)


def quick_save(character: 'Character') -> bool:
    """Quick save to default slot."""
    return get_save_manager().save(character, slot=0)


def quick_load() -> 'Character':
    """Quick load from default slot."""
    return get_save_manager().load(slot=0)
