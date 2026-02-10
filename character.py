"""
Character module for Rob of the Shire game.

Contains the Character class with comprehensive RPG mechanics including:
- Stats system (health, mana, stamina, strength, agility, intelligence)
- Experience and leveling system
- Inventory management with equipment slots
- Combat capabilities
- Skill system
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
import random
import math

from config import (
    config, ItemType, CharacterClass, CLASS_STATS,
    ClassStats, DifficultyLevel
)
from exceptions import (
    ItemNotFoundError, InventoryFullError, ItemNotUsableError,
    ItemNotEquippableError, InsufficientStatsError, CharacterDeadError,
    MaxLevelReachedError, InvalidWeaponError
)
from logger import get_logger, log_function_call

if TYPE_CHECKING:
    from enemy import Enemy


@dataclass
class Stats:
    """
    Character statistics container.
    
    Attributes:
        strength: Physical power, affects melee damage.
        agility: Speed and reflexes, affects dodge and crit chance.
        intelligence: Mental acuity, affects magic damage and mana.
        vitality: Toughness, affects health and defense.
        luck: Fortune, affects critical hits and loot quality.
    """
    strength: int = 10
    agility: int = 10  
    intelligence: int = 10
    vitality: int = 10
    luck: int = 5
    
    def __add__(self, other: 'Stats') -> 'Stats':
        """Add two Stats objects together."""
        return Stats(
            strength=self.strength + other.strength,
            agility=self.agility + other.agility,
            intelligence=self.intelligence + other.intelligence,
            vitality=self.vitality + other.vitality,
            luck=self.luck + other.luck
        )
    
    def to_dict(self) -> dict:
        """Convert stats to dictionary for serialization."""
        return {
            "strength": self.strength,
            "agility": self.agility,
            "intelligence": self.intelligence,
            "vitality": self.vitality,
            "luck": self.luck
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Stats':
        """Create Stats from dictionary."""
        return cls(**data)


@dataclass
class Equipment:
    """
    Equipment slots for a character.
    
    Attributes:
        weapon: Currently equipped weapon item.
        armor: Currently equipped armor item.
        accessory: Currently equipped accessory item.
        shield: Currently equipped shield item.
    """
    weapon: Optional[dict] = None
    armor: Optional[dict] = None
    accessory: Optional[dict] = None
    shield: Optional[dict] = None
    
    def get_total_stats(self) -> dict[str, int]:
        """Calculate total stat bonuses from all equipment."""
        totals = {"damage": 0, "defense": 0, "health_bonus": 0, "mana_bonus": 0}
        
        for slot in [self.weapon, self.armor, self.accessory, self.shield]:
            if slot:
                for key in totals:
                    totals[key] += slot.get(key, 0)
        
        return totals
    
    def to_dict(self) -> dict:
        """Convert equipment to dictionary for serialization."""
        return {
            "weapon": self.weapon,
            "armor": self.armor,
            "accessory": self.accessory,
            "shield": self.shield
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Equipment':
        """Create Equipment from dictionary."""
        return cls(**data)


class Character:
    """
    Main character class with full RPG mechanics.
    
    Represents a player character with stats, inventory, equipment,
    and combat capabilities. Supports leveling, skills, and various
    RPG mechanics.
    
    Attributes:
        name: Character's display name.
        character_class: The character's class (Warrior, Mage, etc.).
        level: Current character level.
        experience: Current experience points.
        stats: Base character statistics.
        equipment: Currently equipped items.
        inventory: List of items in inventory.
        skills: List of learned skills.
        gold: Currency amount.
    """
    
    def __init__(
        self,
        name: str,
        character_class: CharacterClass = CharacterClass.WARRIOR,
        health: int = config.DEFAULT_HEALTH,
        mana: int = config.DEFAULT_MANA,
        stamina: int = config.DEFAULT_STAMINA,
        level: int = 1,
        experience: int = 0
    ):
        """
        Initialize a new character.
        
        Args:
            name: The character's name.
            character_class: The character's class type.
            health: Starting health points.
            mana: Starting mana points.
            stamina: Starting stamina points.
            level: Starting level.
            experience: Starting experience points.
        """
        self.logger = get_logger()
        
        # Basic attributes
        self.name = name
        self.character_class = character_class
        self.level = level
        self.experience = experience
        
        # Apply class bonuses
        class_stats = CLASS_STATS.get(character_class, CLASS_STATS[CharacterClass.WARRIOR])
        
        # Resource pools
        self._max_health = health + class_stats.health_bonus
        self._health = self._max_health
        self._max_mana = mana + class_stats.mana_bonus
        self._mana = self._max_mana
        self._max_stamina = stamina + class_stats.stamina_bonus
        self._stamina = self._max_stamina
        
        # Stats
        self.stats = Stats(
            strength=10 + class_stats.strength_bonus,
            agility=10 + class_stats.agility_bonus,
            intelligence=10 + class_stats.intelligence_bonus
        )
        
        # Progression
        self.available_stat_points = 0
        self.skill_points = 0
        
        # Equipment and inventory
        self.equipment = Equipment()
        self.inventory: list[dict] = []
        self.skills: list[str] = []
        
        # Economy
        self.gold = 0
        
        # Combat state
        self.status_effects: list[dict] = []
        self.is_defending = False
        
        self.logger.info(f"Character '{name}' created", char_class=character_class.name)
    
    # ========================================================================
    # Properties for resources with bounds checking
    # ========================================================================
    
    @property
    def health(self) -> int:
        """Current health points."""
        return self._health
    
    @health.setter
    def health(self, value: int) -> None:
        """Set health with bounds checking."""
        self._health = max(0, min(value, self._max_health))
    
    @property
    def max_health(self) -> int:
        """Maximum health including equipment bonuses."""
        bonus = self.equipment.get_total_stats().get("health_bonus", 0)
        return self._max_health + bonus
    
    @property
    def mana(self) -> int:
        """Current mana points."""
        return self._mana
    
    @mana.setter
    def mana(self, value: int) -> None:
        """Set mana with bounds checking."""
        self._mana = max(0, min(value, self._max_mana))
    
    @property
    def max_mana(self) -> int:
        """Maximum mana including equipment bonuses."""
        bonus = self.equipment.get_total_stats().get("mana_bonus", 0)
        return self._max_mana + bonus
    
    @property
    def stamina(self) -> int:
        """Current stamina points."""
        return self._stamina
    
    @stamina.setter
    def stamina(self, value: int) -> None:
        """Set stamina with bounds checking."""
        self._stamina = max(0, min(value, self._max_stamina))
    
    @property
    def max_stamina(self) -> int:
        """Maximum stamina."""
        return self._max_stamina
    
    @property
    def is_alive(self) -> bool:
        """Check if character is alive."""
        return self._health > 0
    
    @property
    def health_percentage(self) -> float:
        """Get health as percentage."""
        return (self._health / self.max_health) * 100
    
    # ========================================================================
    # Experience and Leveling
    # ========================================================================
    
    @property
    def xp_to_next_level(self) -> int:
        """Calculate XP needed for next level."""
        return int(config.BASE_XP_REQUIREMENT * (config.XP_SCALING_FACTOR ** (self.level - 1)))
    
    @property
    def xp_progress(self) -> float:
        """Get XP progress to next level as percentage."""
        return (self.experience / self.xp_to_next_level) * 100
    
    def gain_experience(self, amount: int) -> list[int]:
        """
        Add experience points and handle level ups.
        
        Args:
            amount: Amount of XP to add.
            
        Returns:
            List of levels gained (empty if none).
        """
        if amount <= 0:
            return []
        
        self.experience += amount
        levels_gained = []
        
        while self.experience >= self.xp_to_next_level and self.level < config.MAX_LEVEL:
            self.experience -= self.xp_to_next_level
            self._level_up()
            levels_gained.append(self.level)
        
        if levels_gained:
            self.logger.info(
                f"{self.name} gained {len(levels_gained)} level(s)!",
                new_level=self.level
            )
        
        return levels_gained
    
    def _level_up(self) -> None:
        """Handle level up logic."""
        old_level = self.level
        self.level += 1
        
        # Increase stat points
        self.available_stat_points += config.STAT_POINTS_PER_LEVEL
        self.skill_points += 1
        
        # Increase max resources
        self._max_health += 10 + (self.stats.vitality // 5)
        self._max_mana += 5 + (self.stats.intelligence // 5)
        self._max_stamina += 5 + (self.stats.agility // 5)
        
        # Restore resources
        self._health = self._max_health
        self._mana = self._max_mana
        self._stamina = self._max_stamina
        
        self.logger.log_level_up(self.name, old_level, self.level)
        print(f"\n🎉 LEVEL UP! {self.name} is now level {self.level}!")
        print(f"   +{config.STAT_POINTS_PER_LEVEL} stat points available")
    
    def allocate_stat_point(self, stat_name: str) -> bool:
        """
        Allocate a stat point to a specific stat.
        
        Args:
            stat_name: Name of stat to increase (strength, agility, etc.)
            
        Returns:
            True if successful, False otherwise.
        """
        if self.available_stat_points <= 0:
            print("No stat points available.")
            return False
        
        stat_name = stat_name.lower()
        valid_stats = ["strength", "agility", "intelligence", "vitality", "luck"]
        
        if stat_name not in valid_stats:
            print(f"Invalid stat. Choose from: {', '.join(valid_stats)}")
            return False
        
        current = getattr(self.stats, stat_name)
        setattr(self.stats, stat_name, current + 1)
        self.available_stat_points -= 1
        
        print(f"{stat_name.capitalize()} increased to {current + 1}!")
        return True
    
    # ========================================================================
    # Inventory Management
    # ========================================================================
    
    def add_item(self, item: dict) -> bool:
        """
        Add an item to inventory.
        
        Args:
            item: Item dictionary to add.
            
        Returns:
            True if item was added, False if inventory full.
            
        Raises:
            InventoryFullError: If inventory is at max capacity.
        """
        if len(self.inventory) >= config.MAX_INVENTORY_SIZE:
            raise InventoryFullError(config.MAX_INVENTORY_SIZE)
        
        self.inventory.append(item.copy())
        self.logger.log_item_action(self.name, "acquired", item["name"])
        return True
    
    def remove_item(self, item_name: str) -> Optional[dict]:
        """
        Remove an item from inventory.
        
        Args:
            item_name: Name of item to remove.
            
        Returns:
            The removed item, or None if not found.
        """
        for i, item in enumerate(self.inventory):
            if item["name"].lower() == item_name.lower():
                removed = self.inventory.pop(i)
                self.logger.log_item_action(self.name, "removed", item_name)
                return removed
        return None
    
    def get_item(self, item_name: str) -> Optional[dict]:
        """
        Get an item from inventory without removing it.
        
        Args:
            item_name: Name of item to find.
            
        Returns:
            The item dictionary, or None if not found.
        """
        for item in self.inventory:
            if item["name"].lower() == item_name.lower():
                return item
        return None
    
    def has_item(self, item_name: str) -> bool:
        """Check if character has an item."""
        return self.get_item(item_name) is not None
    
    def use_item(self, item_name: str) -> bool:
        """
        Use a consumable item from inventory.
        
        Args:
            item_name: Name of item to use.
            
        Returns:
            True if item was used successfully.
            
        Raises:
            ItemNotFoundError: If item not in inventory.
            ItemNotUsableError: If item cannot be used.
        """
        item = self.get_item(item_name)
        
        if not item:
            raise ItemNotFoundError(item_name)
        
        item_type = item.get("type", "")
        
        if item_type == ItemType.POTION.value or item_type == "potion":
            return self._use_potion(item)
        elif item_type == ItemType.CONSUMABLE.value or item_type == "consumable":
            return self._use_consumable(item)
        else:
            raise ItemNotUsableError(item_name, f"Items of type '{item_type}' cannot be used")
    
    def _use_potion(self, item: dict) -> bool:
        """Use a potion item."""
        effect_applied = False
        effects = []
        
        if "heal" in item:
            heal_amount = item["heal"]
            old_health = self._health
            self.health += heal_amount
            actual_heal = self._health - old_health
            effects.append(f"+{actual_heal} HP")
            effect_applied = True
        
        if "mana" in item:
            mana_amount = item["mana"]
            old_mana = self._mana
            self.mana += mana_amount
            actual_mana = self._mana - old_mana
            effects.append(f"+{actual_mana} MP")
            effect_applied = True
        
        if "stamina" in item:
            stamina_amount = item["stamina"]
            self.stamina += stamina_amount
            effects.append(f"+{stamina_amount} stamina")
            effect_applied = True
        
        if effect_applied:
            self.remove_item(item["name"])
            effect_str = ", ".join(effects)
            print(f"{self.name} used {item['name']}: {effect_str}")
            self.logger.log_item_action(self.name, "used", item["name"], effect_str)
            return True
        
        raise ItemNotUsableError(item["name"], "Potion has no effect")
    
    def _use_consumable(self, item: dict) -> bool:
        """Use a consumable item."""
        # Apply any temporary buffs
        if "buff" in item:
            buff_data = {
                "name": item["name"],
                "effect": item["buff"],
                "duration": item.get("duration", 3)
            }
            self.status_effects.append(buff_data)
            self.remove_item(item["name"])
            print(f"{self.name} used {item['name']}: {item['buff']} for {buff_data['duration']} turns")
            return True
        
        raise ItemNotUsableError(item["name"], "Consumable has no effect")
    
    def equip_item(self, item_name: str) -> bool:
        """
        Equip an item from inventory.
        
        Args:
            item_name: Name of item to equip.
            
        Returns:
            True if item was equipped successfully.
        """
        item = self.get_item(item_name)
        
        if not item:
            raise ItemNotFoundError(item_name)
        
        item_type = item.get("type", "")
        
        # Determine equipment slot
        if item_type in [ItemType.WEAPON.value, "weapon"]:
            old_item = self.equipment.weapon
            self.equipment.weapon = item
            slot = "weapon"
        elif item_type in [ItemType.ARMOR.value, "armor"]:
            old_item = self.equipment.armor
            self.equipment.armor = item
            slot = "armor"
        elif item_type in [ItemType.ACCESSORY.value, "accessory"]:
            old_item = self.equipment.accessory
            self.equipment.accessory = item
            slot = "accessory"
        elif item.get("subtype") == "shield":
            old_item = self.equipment.shield
            self.equipment.shield = item
            slot = "shield"
        else:
            raise ItemNotEquippableError(item_name, item_type)
        
        # Handle old equipment
        if old_item:
            self.inventory.append(old_item)
            print(f"Unequipped {old_item['name']}")
        
        self.remove_item(item_name)
        print(f"Equipped {item_name} in {slot} slot")
        self.logger.log_item_action(self.name, "equipped", item_name)
        return True
    
    def unequip_item(self, slot: str) -> bool:
        """
        Unequip item from a slot.
        
        Args:
            slot: Equipment slot name (weapon, armor, accessory, shield).
            
        Returns:
            True if item was unequipped.
        """
        slot = slot.lower()
        item = getattr(self.equipment, slot, None)
        
        if not item:
            print(f"Nothing equipped in {slot} slot.")
            return False
        
        if len(self.inventory) >= config.MAX_INVENTORY_SIZE:
            raise InventoryFullError(config.MAX_INVENTORY_SIZE)
        
        self.inventory.append(item)
        setattr(self.equipment, slot, None)
        print(f"Unequipped {item['name']} from {slot}")
        return True
    
    # ========================================================================
    # Combat
    # ========================================================================
    
    def get_attack_damage(self, weapon: Optional[dict] = None) -> int:
        """
        Calculate total attack damage.
        
        Args:
            weapon: Optional specific weapon to use, otherwise uses equipped.
            
        Returns:
            Total damage value.
        """
        if weapon is None:
            weapon = self.equipment.weapon
        
        base_damage = weapon.get("damage", 5) if weapon else 5
        strength_bonus = self.stats.strength // 2
        
        return base_damage + strength_bonus
    
    def get_defense(self) -> int:
        """Calculate total defense value."""
        equipment_defense = self.equipment.get_total_stats().get("defense", 0)
        vitality_bonus = self.stats.vitality // 3
        
        if self.is_defending:
            return (equipment_defense + vitality_bonus) * 2
        
        return equipment_defense + vitality_bonus
    
    def get_crit_chance(self) -> float:
        """Calculate critical hit chance."""
        return config.BASE_CRIT_CHANCE + (self.stats.luck / 100) + (self.stats.agility / 200)
    
    def get_dodge_chance(self) -> float:
        """Calculate dodge chance."""
        return config.DODGE_BASE_CHANCE + (self.stats.agility / 100)
    
    def attack(self, weapon_name: str, enemy: 'Enemy') -> tuple[int, bool]:
        """
        Attack an enemy with a weapon.
        
        Args:
            weapon_name: Name of weapon to use.
            enemy: Target enemy.
            
        Returns:
            Tuple of (damage dealt, is_critical).
            
        Raises:
            CharacterDeadError: If character is dead.
            InvalidWeaponError: If weapon not valid.
        """
        if not self.is_alive:
            raise CharacterDeadError(self.name)
        
        # Find weapon
        weapon = None
        for item in self.inventory:
            if item["name"].lower() == weapon_name.lower():
                if item.get("type") == "weapon":
                    weapon = item
                    break
        
        # Also check equipped weapon
        if not weapon and self.equipment.weapon:
            if self.equipment.weapon["name"].lower() == weapon_name.lower():
                weapon = self.equipment.weapon
        
        if not weapon:
            raise InvalidWeaponError(weapon_name)
        
        # Calculate damage
        base_damage = self.get_attack_damage(weapon)
        is_critical = random.random() < self.get_crit_chance()
        
        if is_critical:
            damage = int(base_damage * config.CRIT_DAMAGE_MULTIPLIER)
            print(f"💥 CRITICAL HIT!")
        else:
            damage = base_damage
        
        # Apply damage
        enemy.take_damage(damage)
        
        self.logger.log_combat_action(self.name, enemy.name, damage, weapon["name"])
        print(f"{self.name} attacked {enemy.name} with {weapon['name']} for {damage} damage!")
        
        self.is_defending = False
        return damage, is_critical
    
    def defend(self) -> None:
        """Enter defensive stance, doubling defense until next action."""
        self.is_defending = True
        print(f"{self.name} takes a defensive stance! (Defense doubled)")
    
    def take_damage(self, amount: int) -> int:
        """
        Take damage with defense calculation.
        
        Args:
            amount: Raw damage amount.
            
        Returns:
            Actual damage taken after defense.
        """
        defense = self.get_defense()
        actual_damage = max(1, amount - defense)
        
        # Check for dodge
        if random.random() < self.get_dodge_chance():
            print(f"{self.name} dodged the attack!")
            return 0
        
        self.health -= actual_damage
        
        if not self.is_alive:
            print(f"💀 {self.name} has been defeated!")
        else:
            print(f"{self.name} took {actual_damage} damage! ({self.health}/{self.max_health} HP)")
        
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Heal the character.
        
        Args:
            amount: Amount to heal.
            
        Returns:
            Actual amount healed.
        """
        old_health = self._health
        self.health += amount
        return self._health - old_health
    
    def restore_mana(self, amount: int) -> int:
        """Restore mana points."""
        old_mana = self._mana
        self.mana += amount
        return self._mana - old_mana
    
    def full_restore(self) -> None:
        """Fully restore all resources."""
        self._health = self.max_health
        self._mana = self.max_mana
        self._stamina = self.max_stamina
        self.status_effects.clear()
        print(f"{self.name} fully restored!")
    
    # ========================================================================
    # Inventory Display
    # ========================================================================
    
    def inventory_str(self, type_filters: Optional[list[str]] = None) -> str:
        """
        Get formatted inventory string.
        
        Args:
            type_filters: Optional list of item types to show.
            
        Returns:
            Formatted inventory string.
        """
        if not self.inventory:
            return "  (empty)"
        
        output_lines = []
        
        for item in self.inventory:
            item_type = item.get("type", "unknown")
            if type_filters is None or item_type in type_filters:
                # Item header
                output_lines.append(f"  • {item['name']} [{item_type}]")
                
                # Item properties
                for key, value in item.items():
                    if key not in ["name", "type"]:
                        output_lines.append(f"      {key}: {value}")
        
        return "\n".join(output_lines) if output_lines else "  (no matching items)"
    
    def equipment_str(self) -> str:
        """Get formatted equipment string."""
        lines = []
        
        slots = [
            ("Weapon", self.equipment.weapon),
            ("Armor", self.equipment.armor),
            ("Shield", self.equipment.shield),
            ("Accessory", self.equipment.accessory)
        ]
        
        for slot_name, item in slots:
            if item:
                stats = []
                for key, val in item.items():
                    if key not in ["name", "type"]:
                        stats.append(f"{key}: {val}")
                stat_str = f" ({', '.join(stats)})" if stats else ""
                lines.append(f"  {slot_name}: {item['name']}{stat_str}")
            else:
                lines.append(f"  {slot_name}: (empty)")
        
        return "\n".join(lines)
    
    def status_str(self) -> str:
        """Get formatted status string showing current state."""
        lines = [
            f"╔{'═' * 40}╗",
            f"║ {self.name:^38} ║",
            f"║ Level {self.level} {self.character_class.name:^30} ║",
            f"╠{'═' * 40}╣",
            f"║ HP: {self._health:>4}/{self.max_health:<4} {'█' * int(self.health_percentage / 5):10} ║",
            f"║ MP: {self._mana:>4}/{self.max_mana:<4} {'█' * int((self._mana / self.max_mana) * 20):10} ║",
            f"║ XP: {self.experience:>4}/{self.xp_to_next_level:<4} {'█' * int(self.xp_progress / 5):10} ║",
            f"╠{'═' * 40}╣",
            f"║ STR: {self.stats.strength:<3} AGI: {self.stats.agility:<3} INT: {self.stats.intelligence:<3} ║",
            f"║ VIT: {self.stats.vitality:<3} LCK: {self.stats.luck:<3} Gold: {self.gold:<6} ║",
            f"╚{'═' * 40}╝"
        ]
        return "\n".join(lines)
    
    def __str__(self) -> str:
        """String representation of character."""
        return (
            f"Character: {self.name}\n"
            f"Class: {self.character_class.name}\n"
            f"Level: {self.level}\n"
            f"Health: {self._health}/{self.max_health}\n"
            f"Mana: {self._mana}/{self.max_mana}\n"
            f"Experience: {self.experience}/{self.xp_to_next_level}\n"
            f"Inventory: {len(self.inventory)} items"
        )
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"Character(name='{self.name}', level={self.level}, health={self._health})"
    
    # ========================================================================
    # Serialization
    # ========================================================================
    
    def to_dict(self) -> dict:
        """
        Convert character to dictionary for saving.
        
        Returns:
            Dictionary representation of character.
        """
        return {
            "name": self.name,
            "character_class": self.character_class.name,
            "level": self.level,
            "experience": self.experience,
            "health": self._health,
            "max_health": self._max_health,
            "mana": self._mana,
            "max_mana": self._max_mana,
            "stamina": self._stamina,
            "max_stamina": self._max_stamina,
            "stats": self.stats.to_dict(),
            "available_stat_points": self.available_stat_points,
            "skill_points": self.skill_points,
            "equipment": self.equipment.to_dict(),
            "inventory": self.inventory.copy(),
            "skills": self.skills.copy(),
            "gold": self.gold,
            "status_effects": self.status_effects.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        """
        Create character from dictionary.
        
        Args:
            data: Dictionary containing character data.
            
        Returns:
            New Character instance.
        """
        # Get character class
        class_name = data.get("character_class", "WARRIOR")
        try:
            char_class = CharacterClass[class_name]
        except KeyError:
            char_class = CharacterClass.WARRIOR
        
        # Create character with basic stats
        char = cls(
            name=data["name"],
            character_class=char_class,
            level=data.get("level", 1),
            experience=data.get("experience", 0)
        )
        
        # Override resources
        char._health = data.get("health", char._health)
        char._max_health = data.get("max_health", char._max_health)
        char._mana = data.get("mana", char._mana)
        char._max_mana = data.get("max_mana", char._max_mana)
        char._stamina = data.get("stamina", char._stamina)
        char._max_stamina = data.get("max_stamina", char._max_stamina)
        
        # Load stats
        if "stats" in data:
            char.stats = Stats.from_dict(data["stats"])
        
        # Load other data
        char.available_stat_points = data.get("available_stat_points", 0)
        char.skill_points = data.get("skill_points", 0)
        char.gold = data.get("gold", 0)
        
        # Load equipment
        if "equipment" in data:
            char.equipment = Equipment.from_dict(data["equipment"])
        
        # Load inventory
        for item in data.get("inventory", []):
            char.inventory.append(item)
        
        # Load skills
        char.skills = data.get("skills", [])
        char.status_effects = data.get("status_effects", [])
        
        return char
