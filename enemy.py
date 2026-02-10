"""
Enemy module for Rob of the Shire game.

Contains the Enemy class hierarchy with various enemy types, behaviors,
and combat mechanics. Supports different difficulty levels, loot drops,
and special abilities.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from enum import Enum, auto
from abc import ABC, abstractmethod
import random

from config import config, ENEMY_TYPES, DifficultyLevel
from logger import get_logger

if TYPE_CHECKING:
    from character import Character


class EnemyBehavior(Enum):
    """Defines how enemies act in combat."""
    AGGRESSIVE = auto()      # Always attacks
    DEFENSIVE = auto()       # Defends when low HP
    BALANCED = auto()        # Mix of attack and defense
    COWARD = auto()          # Flees when low HP
    BERSERKER = auto()       # Attack power increases at low HP
    TACTICAL = auto()        # Uses abilities strategically


class EnemyRank(Enum):
    """Enemy difficulty ranking."""
    MINION = 0.5       # Weak enemy
    NORMAL = 1.0       # Standard enemy
    ELITE = 1.5        # Stronger enemy
    BOSS = 2.5         # Boss enemy
    LEGENDARY = 5.0    # Extremely powerful


@dataclass
class LootTable:
    """
    Loot table for enemy drops.
    
    Attributes:
        gold_range: Tuple of (min, max) gold drop.
        xp_reward: Base XP reward for defeating enemy.
        items: List of possible item drops with drop chances.
    """
    gold_range: tuple[int, int] = (1, 10)
    xp_reward: int = 10
    items: list[dict] = field(default_factory=list)
    
    def roll_loot(self) -> dict:
        """
        Roll for loot drops.
        
        Returns:
            Dictionary with gold, xp, and items dropped.
        """
        loot = {
            "gold": random.randint(*self.gold_range),
            "xp": self.xp_reward,
            "items": []
        }
        
        for item_entry in self.items:
            if random.random() < item_entry.get("drop_chance", 0.1):
                loot["items"].append(item_entry["item"])
        
        return loot


@dataclass
class EnemyAbility:
    """
    Special ability that enemies can use.
    
    Attributes:
        name: Ability name.
        damage_multiplier: Damage scaling.
        effect: Special effect (status, heal, etc.).
        cooldown: Turns between uses.
        current_cooldown: Current cooldown counter.
    """
    name: str
    damage_multiplier: float = 1.0
    effect: Optional[str] = None
    cooldown: int = 3
    current_cooldown: int = 0
    
    @property
    def is_ready(self) -> bool:
        """Check if ability is ready to use."""
        return self.current_cooldown <= 0
    
    def use(self) -> None:
        """Use the ability, triggering cooldown."""
        self.current_cooldown = self.cooldown
    
    def tick(self) -> None:
        """Reduce cooldown by one turn."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


class Enemy:
    """
    Enhanced Enemy class with combat AI and abilities.
    
    Represents hostile creatures the player can fight. Includes
    stats, behaviors, abilities, and loot mechanics.
    
    Attributes:
        name: Display name of the enemy.
        enemy_type: Type key for enemy stats.
        rank: Enemy difficulty ranking.
        behavior: Combat behavior pattern.
        level: Enemy level for scaling.
    """
    
    def __init__(
        self,
        name: str,
        health: int,
        damage: Optional[int] = None,
        defense: int = 0,
        enemy_type: str = "goblin",
        rank: EnemyRank = EnemyRank.NORMAL,
        behavior: EnemyBehavior = EnemyBehavior.BALANCED,
        level: int = 1,
        difficulty: DifficultyLevel = DifficultyLevel.NORMAL
    ):
        """
        Initialize an enemy.
        
        Args:
            name: Enemy's display name.
            health: Base health points.
            damage: Base damage (auto-calculated if None).
            defense: Defense rating.
            enemy_type: Type key from ENEMY_TYPES.
            rank: Difficulty ranking multiplier.
            behavior: Combat AI behavior.
            level: Level for scaling.
            difficulty: Game difficulty setting.
        """
        self.logger = get_logger()
        
        self.name = name
        self.enemy_type = enemy_type
        self.rank = rank
        self.behavior = behavior
        self.level = level
        self.difficulty = difficulty
        
        # Get base stats from enemy type
        type_data = ENEMY_TYPES.get(enemy_type.lower(), ENEMY_TYPES["goblin"])
        
        # Calculate scaled stats
        level_multiplier = 1 + ((level - 1) * 0.1)
        rank_multiplier = rank.value
        difficulty_multiplier = difficulty.value
        
        total_multiplier = level_multiplier * rank_multiplier * difficulty_multiplier
        
        # Stats
        self._max_health = int(health * total_multiplier)
        self._health = self._max_health
        
        base_damage = damage if damage is not None else type_data["base_damage"]
        self._damage = int(base_damage * total_multiplier)
        self._defense = int(defense * total_multiplier)
        
        # XP and loot
        base_xp = type_data["xp_reward"]
        self.xp_reward = int(base_xp * total_multiplier)
        
        self.loot_table = LootTable(
            gold_range=(int(5 * total_multiplier), int(20 * total_multiplier)),
            xp_reward=self.xp_reward
        )
        
        # Abilities
        self.abilities: list[EnemyAbility] = []
        self._setup_abilities()
        
        # Combat state
        self.is_defending = False
        self.status_effects: list[dict] = []
        self.turns_in_combat = 0
        
        self.logger.debug(
            f"Enemy created: {name}",
            health=self._max_health,
            damage=self._damage,
            rank=rank.name
        )
    
    def _setup_abilities(self) -> None:
        """Set up abilities based on enemy type and rank."""
        # Basic abilities for all enemies
        if self.rank in [EnemyRank.ELITE, EnemyRank.BOSS, EnemyRank.LEGENDARY]:
            self.abilities.append(EnemyAbility(
                name="Power Strike",
                damage_multiplier=1.5,
                cooldown=3
            ))
        
        if self.rank in [EnemyRank.BOSS, EnemyRank.LEGENDARY]:
            self.abilities.append(EnemyAbility(
                name="Crushing Blow",
                damage_multiplier=2.0,
                effect="stun",
                cooldown=5
            ))
        
        if self.rank == EnemyRank.LEGENDARY:
            self.abilities.append(EnemyAbility(
                name="Enrage",
                damage_multiplier=0.5,
                effect="self_buff",
                cooldown=7
            ))
    
    # ========================================================================
    # Properties
    # ========================================================================
    
    @property
    def health(self) -> int:
        """Current health points."""
        return self._health
    
    @property
    def max_health(self) -> int:
        """Maximum health points."""
        return self._max_health
    
    @property
    def is_alive(self) -> bool:
        """Check if enemy is alive."""
        return self._health > 0
    
    @property
    def health_percentage(self) -> float:
        """Get health as percentage."""
        return (self._health / self._max_health) * 100 if self._max_health > 0 else 0
    
    @property
    def damage(self) -> int:
        """Get current attack damage with modifiers."""
        base = self._damage
        
        # Berserker bonus at low HP
        if self.behavior == EnemyBehavior.BERSERKER and self.health_percentage < 30:
            base = int(base * 1.5)
        
        # Defense reduces damage output
        if self.is_defending:
            base = int(base * 0.5)
        
        return base
    
    @property
    def effective_defense(self) -> int:
        """Get defense with defensive stance bonus."""
        if self.is_defending:
            return self._defense * 2
        return self._defense
    
    # ========================================================================
    # Combat Methods
    # ========================================================================
    
    def take_damage(self, amount: int) -> int:
        """
        Take damage with defense calculation.
        
        Args:
            amount: Raw damage amount.
            
        Returns:
            Actual damage taken.
        """
        actual_damage = max(1, amount - self.effective_defense)
        self._health = max(0, self._health - actual_damage)
        
        if self.is_alive:
            self.logger.debug(
                f"{self.name} took {actual_damage} damage",
                remaining_health=self._health
            )
            print(f"{self.name} takes {actual_damage} damage! ({self._health}/{self._max_health} HP)")
        else:
            self.logger.info(f"{self.name} was defeated!")
            print(f"☠️ {self.name} has been defeated!")
        
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Heal the enemy.
        
        Args:
            amount: Amount to heal.
            
        Returns:
            Actual amount healed.
        """
        old_health = self._health
        self._health = min(self._max_health, self._health + amount)
        healed = self._health - old_health
        
        if healed > 0:
            print(f"{self.name} heals for {healed} HP!")
        
        return healed
    
    def choose_action(self, target: 'Character') -> str:
        """
        Decide what action to take based on behavior and state.
        
        Args:
            target: The player character target.
            
        Returns:
            Action string: 'attack', 'defend', 'ability', or 'flee'.
        """
        self.turns_in_combat += 1
        
        # Check for usable abilities
        ready_abilities = [a for a in self.abilities if a.is_ready]
        
        # Behavior-based decision making
        if self.behavior == EnemyBehavior.AGGRESSIVE:
            if ready_abilities and random.random() < 0.4:
                return "ability"
            return "attack"
        
        elif self.behavior == EnemyBehavior.DEFENSIVE:
            if self.health_percentage < 40:
                return "defend" if random.random() < 0.6 else "attack"
            return "attack"
        
        elif self.behavior == EnemyBehavior.COWARD:
            if self.health_percentage < 25:
                return "flee" if random.random() < 0.5 else "attack"
            return "attack"
        
        elif self.behavior == EnemyBehavior.BERSERKER:
            if ready_abilities and self.health_percentage < 30:
                return "ability"
            return "attack"
        
        elif self.behavior == EnemyBehavior.TACTICAL:
            if ready_abilities and random.random() < 0.3:
                return "ability"
            if self.health_percentage < 30 and random.random() < 0.4:
                return "defend"
            return "attack"
        
        else:  # BALANCED
            roll = random.random()
            if roll < 0.1 and self.health_percentage < 50:
                return "defend"
            if roll < 0.25 and ready_abilities:
                return "ability"
            return "attack"
    
    def attack_target(self, target: 'Character') -> int:
        """
        Attack the target character.
        
        Args:
            target: The character to attack.
            
        Returns:
            Damage dealt.
        """
        self.is_defending = False
        damage = self.damage
        
        # Small random variation
        damage = int(damage * random.uniform(0.9, 1.1))
        
        print(f"\n⚔️ {self.name} attacks {target.name}!")
        actual_damage = target.take_damage(damage)
        
        self.logger.log_combat_action(self.name, target.name, actual_damage, "natural attack")
        
        return actual_damage
    
    def use_ability(self, target: 'Character') -> Optional[EnemyAbility]:
        """
        Use a special ability.
        
        Args:
            target: The target character.
            
        Returns:
            The ability used, or None if none available.
        """
        ready_abilities = [a for a in self.abilities if a.is_ready]
        
        if not ready_abilities:
            return None
        
        ability = random.choice(ready_abilities)
        ability.use()
        
        damage = int(self.damage * ability.damage_multiplier)
        
        print(f"\n💫 {self.name} uses {ability.name}!")
        
        if ability.effect == "self_buff":
            self._damage = int(self._damage * 1.3)
            print(f"   {self.name}'s attack power increased!")
        else:
            actual_damage = target.take_damage(damage)
            
            if ability.effect == "stun":
                print(f"   {target.name} is stunned!")
        
        return ability
    
    def defend_action(self) -> None:
        """Take a defensive stance."""
        self.is_defending = True
        print(f"🛡️ {self.name} takes a defensive stance!")
    
    def tick_abilities(self) -> None:
        """Reduce cooldowns for all abilities."""
        for ability in self.abilities:
            ability.tick()
    
    def execute_turn(self, target: 'Character') -> str:
        """
        Execute a complete combat turn.
        
        Args:
            target: The player character.
            
        Returns:
            The action taken.
        """
        action = self.choose_action(target)
        
        if action == "attack":
            self.attack_target(target)
        elif action == "defend":
            self.defend_action()
        elif action == "ability":
            ability = self.use_ability(target)
            if ability is None:
                self.attack_target(target)
                action = "attack"
        elif action == "flee":
            print(f"💨 {self.name} tries to flee!")
            if random.random() < 0.3:
                print(f"   {self.name} escaped!")
        
        self.tick_abilities()
        return action
    
    def get_loot(self) -> dict:
        """
        Get loot drops from defeated enemy.
        
        Returns:
            Dictionary with gold, xp, and items.
        """
        return self.loot_table.roll_loot()
    
    # ========================================================================
    # Display Methods
    # ========================================================================
    
    def status_str(self) -> str:
        """Get formatted status string."""
        health_bar_width = 20
        filled = int((self.health_percentage / 100) * health_bar_width)
        bar = "█" * filled + "░" * (health_bar_width - filled)
        
        return (
            f"┌─ {self.name} ─────────────\n"
            f"│ HP: [{bar}] {self._health}/{self._max_health}\n"
            f"│ Rank: {self.rank.name} | Lvl: {self.level}\n"
            f"└────────────────────────────"
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} (HP: {self._health}/{self._max_health}, ATK: {self._damage})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"Enemy(name='{self.name}', type='{self.enemy_type}', "
            f"health={self._health}/{self._max_health}, rank={self.rank.name})"
        )


# ============================================================================
# Factory Functions for Common Enemy Types
# ============================================================================

def create_goblin(level: int = 1, rank: EnemyRank = EnemyRank.NORMAL) -> Enemy:
    """Create a goblin enemy."""
    return Enemy(
        name="Goblin",
        health=30,
        damage=8,
        defense=2,
        enemy_type="goblin",
        rank=rank,
        behavior=EnemyBehavior.COWARD,
        level=level
    )


def create_orc(level: int = 1, rank: EnemyRank = EnemyRank.NORMAL) -> Enemy:
    """Create an orc enemy."""
    return Enemy(
        name="Orc Warrior",
        health=60,
        damage=15,
        defense=5,
        enemy_type="orc",
        rank=rank,
        behavior=EnemyBehavior.AGGRESSIVE,
        level=level
    )


def create_skeleton(level: int = 1, rank: EnemyRank = EnemyRank.NORMAL) -> Enemy:
    """Create a skeleton enemy."""
    return Enemy(
        name="Skeleton",
        health=25,
        damage=10,
        defense=0,
        enemy_type="skeleton",
        rank=rank,
        behavior=EnemyBehavior.AGGRESSIVE,
        level=level
    )


def create_wolf(level: int = 1, rank: EnemyRank = EnemyRank.NORMAL) -> Enemy:
    """Create a wolf enemy."""
    return Enemy(
        name="Wild Wolf",
        health=35,
        damage=12,
        defense=2,
        enemy_type="wolf",
        rank=rank,
        behavior=EnemyBehavior.BERSERKER,
        level=level
    )


def create_troll(level: int = 1, rank: EnemyRank = EnemyRank.ELITE) -> Enemy:
    """Create a troll enemy."""
    return Enemy(
        name="Cave Troll",
        health=100,
        damage=25,
        defense=10,
        enemy_type="troll",
        rank=rank,
        behavior=EnemyBehavior.DEFENSIVE,
        level=level
    )


def create_dragon(level: int = 1) -> Enemy:
    """Create a dragon boss enemy."""
    return Enemy(
        name="Ancient Dragon",
        health=300,
        damage=50,
        defense=25,
        enemy_type="dragon",
        rank=EnemyRank.BOSS,
        behavior=EnemyBehavior.TACTICAL,
        level=level
    )


def create_random_enemy(
    min_level: int = 1,
    max_level: int = 5,
    allowed_ranks: Optional[list[EnemyRank]] = None
) -> Enemy:
    """
    Create a random enemy.
    
    Args:
        min_level: Minimum enemy level.
        max_level: Maximum enemy level.
        allowed_ranks: List of allowed enemy ranks.
        
    Returns:
        Random enemy instance.
    """
    if allowed_ranks is None:
        allowed_ranks = [EnemyRank.MINION, EnemyRank.NORMAL, EnemyRank.ELITE]
    
    level = random.randint(min_level, max_level)
    rank = random.choice(allowed_ranks)
    
    creators = [create_goblin, create_orc, create_skeleton, create_wolf]
    
    if rank in [EnemyRank.ELITE, EnemyRank.BOSS]:
        creators.append(create_troll)
    
    creator = random.choice(creators)
    return creator(level=level, rank=rank)
