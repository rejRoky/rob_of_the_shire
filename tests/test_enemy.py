"""
Unit tests for the Enemy and Combat system.

Tests enemy creation, behaviors, combat mechanics,
and combat encounters.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from enemy import (
    Enemy, EnemyBehavior, EnemyRank, LootTable, EnemyAbility,
    create_goblin, create_orc, create_skeleton, create_wolf,
    create_troll, create_dragon, create_random_enemy
)
from character import Character
from config import DifficultyLevel


class TestEnemyCreation:
    """Tests for enemy creation and initialization."""
    
    def test_create_basic_enemy(self):
        """Test creating an enemy with basic parameters."""
        enemy = Enemy(name="Goblin", health=50)
        
        assert enemy.name == "Goblin"
        assert enemy.max_health == 50
        assert enemy.is_alive
    
    def test_create_enemy_with_difficulty(self):
        """Test that difficulty affects enemy stats."""
        easy_enemy = Enemy(
            name="Goblin", health=50,
            difficulty=DifficultyLevel.EASY
        )
        hard_enemy = Enemy(
            name="Goblin", health=50,
            difficulty=DifficultyLevel.HARD
        )
        
        # Hard difficulty should have higher stats
        assert hard_enemy.max_health > easy_enemy.max_health
    
    def test_create_enemy_with_rank(self):
        """Test that rank affects enemy stats."""
        minion = Enemy(name="Goblin", health=50, rank=EnemyRank.MINION)
        boss = Enemy(name="Goblin", health=50, rank=EnemyRank.BOSS)
        
        assert boss.max_health > minion.max_health
        assert boss.xp_reward > minion.xp_reward


class TestEnemyBehavior:
    """Tests for enemy AI behavior."""
    
    def test_aggressive_behavior(self):
        """Test aggressive enemies prefer attacking."""
        enemy = Enemy(
            name="Aggressive", health=100,
            behavior=EnemyBehavior.AGGRESSIVE
        )
        target = Character(name="Target")
        
        # With aggressive behavior, should mostly attack
        actions = [enemy.choose_action(target) for _ in range(10)]
        attack_count = actions.count("attack")
        
        assert attack_count >= 5  # More than half should be attacks
    
    def test_defensive_behavior(self):
        """Test defensive enemies defend when low HP."""
        enemy = Enemy(
            name="Defensive", health=100,
            behavior=EnemyBehavior.DEFENSIVE
        )
        target = Character(name="Target")
        
        # Damage enemy to low HP
        enemy._health = 20
        
        # Should sometimes defend when low
        actions = [enemy.choose_action(target) for _ in range(20)]
        
        assert "defend" in actions
    
    def test_coward_behavior(self):
        """Test cowardly enemies may flee when low HP."""
        enemy = Enemy(
            name="Coward", health=100,
            behavior=EnemyBehavior.COWARD
        )
        target = Character(name="Target")
        
        # Damage enemy to very low HP
        enemy._health = 10
        
        # Should sometimes try to flee
        actions = [enemy.choose_action(target) for _ in range(30)]
        
        assert "flee" in actions


class TestEnemyCombat:
    """Tests for enemy combat actions."""
    
    def test_take_damage(self):
        """Test enemy taking damage."""
        enemy = Enemy(name="Test", health=100)
        
        damage = enemy.take_damage(30)
        
        assert damage > 0
        assert enemy.health < enemy.max_health
    
    def test_death(self):
        """Test enemy death when HP reaches 0."""
        enemy = Enemy(name="Test", health=50)
        
        enemy.take_damage(100)
        
        assert not enemy.is_alive
        assert enemy.health == 0
    
    def test_heal(self):
        """Test enemy healing."""
        enemy = Enemy(name="Test", health=100)
        enemy._health = 50
        
        healed = enemy.heal(30)
        
        assert enemy.health == 80
        assert healed == 30
    
    def test_heal_cap(self):
        """Test healing doesn't exceed max health."""
        enemy = Enemy(name="Test", health=100)
        enemy._health = 90
        
        healed = enemy.heal(30)
        
        assert enemy.health == enemy.max_health
        assert healed == 10
    
    def test_attack_target(self):
        """Test enemy attacking a character."""
        enemy = Enemy(name="Attacker", health=100, damage=20)
        target = Character(name="Target", health=100)
        
        damage = enemy.attack_target(target)
        
        assert damage > 0
        assert target.health < target.max_health
    
    def test_defend_action(self):
        """Test enemy defensive stance."""
        enemy = Enemy(name="Defender", health=100, defense=10)
        
        normal_defense = enemy.effective_defense
        enemy.defend_action()
        defending_defense = enemy.effective_defense
        
        assert defending_defense == normal_defense * 2


class TestEnemyAbilities:
    """Tests for enemy special abilities."""
    
    def test_ability_creation(self):
        """Test creating an ability."""
        ability = EnemyAbility(
            name="Power Strike",
            damage_multiplier=1.5,
            cooldown=3
        )
        
        assert ability.name == "Power Strike"
        assert ability.damage_multiplier == 1.5
        assert ability.is_ready
    
    def test_ability_cooldown(self):
        """Test ability cooldown mechanics."""
        ability = EnemyAbility(name="Test", cooldown=3)
        
        ability.use()
        assert not ability.is_ready
        assert ability.current_cooldown == 3
        
        ability.tick()
        assert ability.current_cooldown == 2
        
        ability.tick()
        ability.tick()
        assert ability.is_ready


class TestLootTable:
    """Tests for loot table system."""
    
    def test_roll_gold(self):
        """Test gold drops from loot table."""
        loot_table = LootTable(gold_range=(10, 20), xp_reward=50)
        
        loot = loot_table.roll_loot()
        
        assert 10 <= loot["gold"] <= 20
        assert loot["xp"] == 50
    
    def test_roll_items(self):
        """Test item drops with 100% chance."""
        loot_table = LootTable(
            gold_range=(1, 1),
            xp_reward=10,
            items=[
                {"item": {"name": "Guaranteed"}, "drop_chance": 1.0}
            ]
        )
        
        loot = loot_table.roll_loot()
        
        assert len(loot["items"]) == 1
        assert loot["items"][0]["name"] == "Guaranteed"


class TestEnemyFactories:
    """Tests for enemy factory functions."""
    
    def test_create_goblin(self):
        """Test goblin creation."""
        goblin = create_goblin(level=3)
        
        assert goblin.name == "Goblin"
        assert goblin.enemy_type == "goblin"
        assert goblin.level == 3
    
    def test_create_orc(self):
        """Test orc creation."""
        orc = create_orc(level=5)
        
        assert "Orc" in orc.name
        assert orc.enemy_type == "orc"
    
    def test_create_dragon(self):
        """Test dragon boss creation."""
        dragon = create_dragon(level=10)
        
        assert "Dragon" in dragon.name
        assert dragon.rank == EnemyRank.BOSS
    
    def test_create_random_enemy(self):
        """Test random enemy generation."""
        enemy = create_random_enemy(min_level=1, max_level=5)
        
        assert enemy is not None
        assert 1 <= enemy.level <= 5


class TestEnemyStringRepresentations:
    """Tests for enemy string representations."""
    
    def test_str(self):
        """Test __str__ method."""
        enemy = Enemy(name="TestEnemy", health=100, damage=20)
        
        result = str(enemy)
        
        assert "TestEnemy" in result
        assert "100" in result
    
    def test_repr(self):
        """Test __repr__ method."""
        enemy = Enemy(name="TestEnemy", health=50, rank=EnemyRank.ELITE)
        
        result = repr(enemy)
        
        assert "TestEnemy" in result
        assert "ELITE" in result
    
    def test_status_str(self):
        """Test status_str method."""
        enemy = Enemy(name="StatusTest", health=100)
        
        result = enemy.status_str()
        
        assert "StatusTest" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
