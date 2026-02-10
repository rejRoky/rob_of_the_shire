"""
Combat system module for Rob of the Shire game.

Provides a structured combat encounter system with turn-based mechanics,
action menus, and combat resolution. Handles the flow of battles between
player characters and enemies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum, auto
import random

from character import Character
from enemy import Enemy, EnemyRank, create_random_enemy
from config import config, CombatResult
from exceptions import (
    CombatException, NoCombatInProgressError, 
    CharacterDeadError, FleeFailedError
)
from logger import get_logger


class CombatPhase(Enum):
    """Phases of combat."""
    START = auto()
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    RESOLUTION = auto()
    END = auto()


@dataclass
class CombatLog:
    """
    Records combat events for display and history.
    
    Attributes:
        entries: List of combat log entries.
        max_entries: Maximum entries to keep.
    """
    entries: list[str] = field(default_factory=list)
    max_entries: int = 50
    
    def add(self, message: str) -> None:
        """Add a log entry."""
        self.entries.append(message)
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)
    
    def get_recent(self, count: int = 5) -> list[str]:
        """Get most recent log entries."""
        return self.entries[-count:]
    
    def clear(self) -> None:
        """Clear all log entries."""
        self.entries.clear()


@dataclass
class CombatStats:
    """
    Statistics for a combat encounter.
    
    Attributes:
        total_damage_dealt: Damage dealt by player.
        total_damage_taken: Damage taken by player.
        turns_elapsed: Number of turns in combat.
        items_used: Number of items used.
        abilities_used: Number of abilities used.
        critical_hits: Number of critical hits landed.
    """
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    turns_elapsed: int = 0
    items_used: int = 0
    abilities_used: int = 0
    critical_hits: int = 0
    dodges: int = 0
    
    def add_damage_dealt(self, amount: int, is_crit: bool = False) -> None:
        """Record damage dealt."""
        self.total_damage_dealt += amount
        if is_crit:
            self.critical_hits += 1
    
    def add_damage_taken(self, amount: int) -> None:
        """Record damage taken."""
        if amount == 0:
            self.dodges += 1
        else:
            self.total_damage_taken += amount
    
    def summary(self) -> str:
        """Get combat statistics summary."""
        return (
            f"\n{'═' * 40}\n"
            f"         COMBAT STATISTICS\n"
            f"{'═' * 40}\n"
            f"  Turns: {self.turns_elapsed}\n"
            f"  Damage Dealt: {self.total_damage_dealt}\n"
            f"  Damage Taken: {self.total_damage_taken}\n"
            f"  Critical Hits: {self.critical_hits}\n"
            f"  Dodges: {self.dodges}\n"
            f"  Items Used: {self.items_used}\n"
            f"{'═' * 40}"
        )


class CombatEncounter:
    """
    Manages a combat encounter between player and enemy.
    
    Handles turn order, action selection, combat resolution,
    and rewards distribution.
    
    Attributes:
        player: The player character.
        enemy: The enemy being fought.
        phase: Current combat phase.
        result: Combat outcome.
    """
    
    def __init__(
        self,
        player: Character,
        enemy: Enemy,
        allow_flee: bool = True
    ):
        """
        Initialize a combat encounter.
        
        Args:
            player: The player character.
            enemy: The enemy to fight.
            allow_flee: Whether the player can attempt to flee.
        """
        self.logger = get_logger()
        
        self.player = player
        self.enemy = enemy
        self.allow_flee = allow_flee
        
        self.phase = CombatPhase.START
        self.result: Optional[CombatResult] = None
        
        self.combat_log = CombatLog()
        self.stats = CombatStats()
        
        self.turn_number = 0
        self.is_active = True
        
        self.logger.info(
            f"Combat started: {player.name} vs {enemy.name}",
            player_hp=player.health,
            enemy_hp=enemy.health
        )
    
    # ========================================================================
    # Display Methods
    # ========================================================================
    
    def display_combat_status(self) -> None:
        """Display current combat status."""
        print("\n" + "═" * 50)
        print(f"  COMBAT - Turn {self.turn_number}")
        print("═" * 50)
        
        # Player status
        player_hp_pct = (self.player.health / self.player.max_health)
        player_bar = "█" * int(player_hp_pct * 20) + "░" * int((1 - player_hp_pct) * 20)
        print(f"\n  {self.player.name}")
        print(f"  HP: [{player_bar}] {self.player.health}/{self.player.max_health}")
        
        # Enemy status
        enemy_hp_pct = (self.enemy.health / self.enemy.max_health)
        enemy_bar = "█" * int(enemy_hp_pct * 20) + "░" * int((1 - enemy_hp_pct) * 20)
        print(f"\n  {self.enemy.name} ({self.enemy.rank.name})")
        print(f"  HP: [{enemy_bar}] {self.enemy.health}/{self.enemy.max_health}")
        
        print("\n" + "─" * 50)
    
    def display_action_menu(self) -> None:
        """Display available actions for player."""
        print("\n  Available Actions:")
        print("  1. Attack")
        print("  2. Use Item")
        print("  3. Defend")
        if self.allow_flee:
            print("  4. Flee")
        print("  5. Status")
    
    def display_weapons(self) -> list[dict]:
        """Display available weapons and return the list."""
        weapons = []
        
        # Equipped weapon
        if self.player.equipment.weapon:
            weapons.append(self.player.equipment.weapon)
        
        # Inventory weapons
        for item in self.player.inventory:
            if item.get("type") == "weapon" and item not in weapons:
                weapons.append(item)
        
        if not weapons:
            print("  No weapons available! Using fists.")
            return []
        
        print("\n  Select Weapon:")
        for i, weapon in enumerate(weapons, 1):
            damage = weapon.get("damage", 5)
            equipped = " (equipped)" if weapon == self.player.equipment.weapon else ""
            print(f"  {i}. {weapon['name']} - {damage} damage{equipped}")
        
        return weapons
    
    def display_usable_items(self) -> list[dict]:
        """Display usable items and return the list."""
        usable = []
        
        for item in self.player.inventory:
            if item.get("type") in ["potion", "consumable"]:
                usable.append(item)
        
        if not usable:
            print("  No usable items available!")
            return []
        
        print("\n  Select Item to Use:")
        for i, item in enumerate(usable, 1):
            effect = ""
            if "heal" in item:
                effect = f"+{item['heal']} HP"
            elif "mana" in item:
                effect = f"+{item['mana']} MP"
            print(f"  {i}. {item['name']} - {effect}")
        
        return usable
    
    # ========================================================================
    # Action Handlers
    # ========================================================================
    
    def handle_player_attack(self) -> bool:
        """
        Handle player attack action.
        
        Returns:
            True if action was completed.
        """
        weapons = self.display_weapons()
        
        if not weapons:
            # Unarmed attack
            damage = 5 + (self.player.stats.strength // 3)
            is_crit = random.random() < self.player.get_crit_chance()
            
            if is_crit:
                damage = int(damage * config.CRIT_DAMAGE_MULTIPLIER)
                print("\n  💥 CRITICAL HIT!")
            
            self.enemy.take_damage(damage)
            self.stats.add_damage_dealt(damage, is_crit)
            self.combat_log.add(f"{self.player.name} punched for {damage} damage")
            return True
        
        try:
            choice = input("\n  Choose weapon (number): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(weapons):
                weapon = weapons[idx]
                damage, is_crit = self.player.attack(weapon["name"], self.enemy)
                self.stats.add_damage_dealt(damage, is_crit)
                self.combat_log.add(
                    f"{self.player.name} attacked with {weapon['name']} for {damage} damage"
                )
                return True
            else:
                print("  Invalid choice.")
                return False
        except ValueError:
            print("  Invalid input.")
            return False
    
    def handle_player_item(self) -> bool:
        """
        Handle player item use action.
        
        Returns:
            True if action was completed.
        """
        usable = self.display_usable_items()
        
        if not usable:
            return False
        
        try:
            choice = input("\n  Choose item (number, or 0 to cancel): ").strip()
            idx = int(choice) - 1
            
            if idx == -1:
                return False
            
            if 0 <= idx < len(usable):
                item = usable[idx]
                self.player.use_item(item["name"])
                self.stats.items_used += 1
                self.combat_log.add(f"{self.player.name} used {item['name']}")
                return True
            else:
                print("  Invalid choice.")
                return False
        except ValueError:
            print("  Invalid input.")
            return False
    
    def handle_player_defend(self) -> bool:
        """Handle player defend action."""
        self.player.defend()
        self.combat_log.add(f"{self.player.name} took a defensive stance")
        return True
    
    def handle_player_flee(self) -> bool:
        """
        Handle player flee attempt.
        
        Returns:
            True if flee was attempted (successful or not).
        """
        flee_chance = config.FLEE_BASE_CHANCE + (self.player.stats.agility / 200)
        
        # Boss enemies are harder to flee from
        if self.enemy.rank in [EnemyRank.BOSS, EnemyRank.LEGENDARY]:
            flee_chance *= 0.5
        
        if random.random() < flee_chance:
            print(f"\n  💨 {self.player.name} successfully fled from battle!")
            self.result = CombatResult.FLED
            self.is_active = False
            self.combat_log.add(f"{self.player.name} fled from combat")
        else:
            print(f"\n  ❌ Failed to escape! {self.enemy.name} blocks the way!")
            self.combat_log.add(f"{self.player.name} failed to flee")
        
        return True
    
    # ========================================================================
    # Turn Management
    # ========================================================================
    
    def player_turn(self) -> None:
        """Execute player's turn."""
        self.phase = CombatPhase.PLAYER_TURN
        
        action_completed = False
        
        while not action_completed and self.is_active:
            self.display_action_menu()
            
            try:
                choice = input("\n  Choose action: ").strip()
                
                if choice == "1":
                    action_completed = self.handle_player_attack()
                elif choice == "2":
                    action_completed = self.handle_player_item()
                elif choice == "3":
                    action_completed = self.handle_player_defend()
                elif choice == "4" and self.allow_flee:
                    action_completed = self.handle_player_flee()
                elif choice == "5":
                    print(self.player.status_str())
                else:
                    print("  Invalid choice. Try again.")
            except Exception as e:
                self.logger.error(f"Error during player turn: {e}")
                print(f"  Error: {e}")
    
    def enemy_turn(self) -> None:
        """Execute enemy's turn."""
        if not self.is_active or not self.enemy.is_alive:
            return
        
        self.phase = CombatPhase.ENEMY_TURN
        
        action = self.enemy.execute_turn(self.player)
        
        if action == "attack":
            # Damage was handled in execute_turn, just record stats
            self.stats.add_damage_taken(0)  # Actual damage tracked separately
            self.combat_log.add(f"{self.enemy.name} attacked")
        elif action == "ability":
            self.combat_log.add(f"{self.enemy.name} used an ability")
        elif action == "defend":
            self.combat_log.add(f"{self.enemy.name} is defending")
        elif action == "flee":
            if not self.enemy.is_alive or random.random() < 0.3:
                print(f"\n  {self.enemy.name} fled from battle!")
                self.result = CombatResult.VICTORY  # Enemy fleeing counts as win
                self.is_active = False
    
    def check_combat_end(self) -> bool:
        """
        Check if combat has ended.
        
        Returns:
            True if combat has ended.
        """
        if not self.player.is_alive:
            self.result = CombatResult.DEFEAT
            self.is_active = False
            print(f"\n  💀 {self.player.name} has been defeated!")
            self.combat_log.add(f"{self.player.name} was defeated")
            return True
        
        if not self.enemy.is_alive:
            self.result = CombatResult.VICTORY
            self.is_active = False
            print(f"\n  🎉 Victory! {self.enemy.name} has been defeated!")
            self.combat_log.add(f"{self.enemy.name} was defeated")
            return True
        
        return False
    
    def award_victory_rewards(self) -> dict:
        """
        Award rewards for victory.
        
        Returns:
            Dictionary of rewards earned.
        """
        loot = self.enemy.get_loot()
        
        # Award XP
        levels_gained = self.player.gain_experience(loot["xp"])
        
        # Award gold
        self.player.gold += loot["gold"]
        
        # Award items
        for item in loot["items"]:
            try:
                self.player.add_item(item)
                print(f"  📦 Found: {item['name']}")
            except Exception:
                print(f"  Inventory full! Couldn't pick up {item['name']}")
        
        print(f"\n  Rewards:")
        print(f"  • {loot['xp']} XP")
        print(f"  • {loot['gold']} gold")
        
        if levels_gained:
            print(f"  • Leveled up {len(levels_gained)} time(s)!")
        
        return loot
    
    # ========================================================================
    # Main Combat Loop
    # ========================================================================
    
    def start(self) -> CombatResult:
        """
        Start and run the combat encounter.
        
        Returns:
            The combat result (VICTORY, DEFEAT, or FLED).
        """
        print("\n" + "╔" + "═" * 48 + "╗")
        print(f"║{'COMBAT BEGINS!':^48}║")
        print(f"║{f'{self.player.name} vs {self.enemy.name}':^48}║")
        print("╚" + "═" * 48 + "╝")
        
        self.combat_log.add(f"Combat started: {self.player.name} vs {self.enemy.name}")
        
        while self.is_active:
            self.turn_number += 1
            self.stats.turns_elapsed += 1
            
            self.display_combat_status()
            
            # Player turn
            self.player_turn()
            
            if self.check_combat_end():
                break
            
            # Enemy turn
            self.enemy_turn()
            
            if self.check_combat_end():
                break
        
        # Combat ended
        self.phase = CombatPhase.END
        
        if self.result == CombatResult.VICTORY:
            self.award_victory_rewards()
        
        print(self.stats.summary())
        
        self.logger.info(
            f"Combat ended: {self.result.name if self.result else 'UNKNOWN'}",
            turns=self.turn_number,
            player_hp=self.player.health
        )
        
        return self.result or CombatResult.ONGOING
    
    def get_result(self) -> Optional[CombatResult]:
        """Get the combat result."""
        return self.result


def start_combat(
    player: Character,
    enemy: Optional[Enemy] = None,
    enemy_level: int = 1,
    allow_flee: bool = True
) -> CombatResult:
    """
    Convenience function to start a combat encounter.
    
    Args:
        player: The player character.
        enemy: Optional specific enemy. If None, creates random enemy.
        enemy_level: Level for random enemy generation.
        allow_flee: Whether player can flee.
        
    Returns:
        The combat result.
    """
    if enemy is None:
        enemy = create_random_enemy(
            min_level=max(1, enemy_level - 1),
            max_level=enemy_level + 1
        )
    
    encounter = CombatEncounter(player, enemy, allow_flee)
    return encounter.start()


def start_boss_battle(player: Character, boss: Enemy) -> CombatResult:
    """
    Start a boss battle with special rules.
    
    Args:
        player: The player character.
        boss: The boss enemy.
        
    Returns:
        The combat result.
    """
    print("\n" + "🔥" * 25)
    print(f"   ⚔️  BOSS BATTLE: {boss.name.upper()}  ⚔️")
    print("🔥" * 25)
    
    # Boss battles don't allow fleeing
    encounter = CombatEncounter(player, boss, allow_flee=False)
    return encounter.start()
