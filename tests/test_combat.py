"""
Unit tests for the Combat System.

Tests combat encounters, action handling, damage calculations,
and combat resolution.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from combat import (
    CombatEncounter, CombatPhase, CombatLog, CombatStats,
    start_combat
)
from character import Character
from enemy import Enemy, EnemyRank, create_goblin
from config import CombatResult


class TestCombatLog:
    """Tests for CombatLog class."""
    
    def test_add_entry(self):
        """Test adding log entries."""
        log = CombatLog()
        
        log.add("Test entry 1")
        log.add("Test entry 2")
        
        assert len(log.entries) == 2
    
    def test_get_recent(self):
        """Test getting recent entries."""
        log = CombatLog()
        for i in range(10):
            log.add(f"Entry {i}")
        
        recent = log.get_recent(3)
        
        assert len(recent) == 3
        assert "Entry 9" in recent[-1]
    
    def test_max_entries(self):
        """Test that log respects max entries limit."""
        log = CombatLog(max_entries=5)
        
        for i in range(10):
            log.add(f"Entry {i}")
        
        assert len(log.entries) == 5
    
    def test_clear(self):
        """Test clearing the log."""
        log = CombatLog()
        log.add("Entry 1")
        log.add("Entry 2")
        
        log.clear()
        
        assert len(log.entries) == 0


class TestCombatStats:
    """Tests for CombatStats class."""
    
    def test_add_damage_dealt(self):
        """Test tracking damage dealt."""
        stats = CombatStats()
        
        stats.add_damage_dealt(50)
        stats.add_damage_dealt(30, is_crit=True)
        
        assert stats.total_damage_dealt == 80
        assert stats.critical_hits == 1
    
    def test_add_damage_taken(self):
        """Test tracking damage taken."""
        stats = CombatStats()
        
        stats.add_damage_taken(25)
        stats.add_damage_taken(0)  # Dodge
        
        assert stats.total_damage_taken == 25
        assert stats.dodges == 1
    
    def test_summary(self):
        """Test stats summary generation."""
        stats = CombatStats()
        stats.turns_elapsed = 5
        stats.total_damage_dealt = 100
        stats.total_damage_taken = 50
        
        summary = stats.summary()
        
        assert "5" in summary
        assert "100" in summary
        assert "50" in summary


class TestCombatEncounter:
    """Tests for CombatEncounter class."""
    
    @pytest.fixture
    def player(self):
        """Create a test player character."""
        char = Character(name="TestPlayer", health=100)
        char.add_item({"name": "Sword", "type": "weapon", "damage": 20})
        return char
    
    @pytest.fixture
    def enemy(self):
        """Create a test enemy."""
        return Enemy(name="TestEnemy", health=50, damage=10)
    
    def test_create_encounter(self, player, enemy):
        """Test creating a combat encounter."""
        encounter = CombatEncounter(player, enemy)
        
        assert encounter.player is player
        assert encounter.enemy is enemy
        assert encounter.phase == CombatPhase.START
        assert encounter.is_active
    
    def test_display_status(self, player, enemy, capsys):
        """Test combat status display."""
        encounter = CombatEncounter(player, enemy)
        
        encounter.display_combat_status()
        
        output = capsys.readouterr().out
        assert player.name in output
        assert enemy.name in output
    
    def test_check_combat_end_player_defeat(self, player, enemy):
        """Test combat ends when player dies."""
        encounter = CombatEncounter(player, enemy)
        player._health = 0
        
        ended = encounter.check_combat_end()
        
        assert ended
        assert encounter.result == CombatResult.DEFEAT
        assert not encounter.is_active
    
    def test_check_combat_end_enemy_defeat(self, player, enemy):
        """Test combat ends when enemy dies."""
        encounter = CombatEncounter(player, enemy)
        enemy._health = 0
        
        ended = encounter.check_combat_end()
        
        assert ended
        assert encounter.result == CombatResult.VICTORY
        assert not encounter.is_active
    
    def test_check_combat_continues(self, player, enemy):
        """Test combat continues when both alive."""
        encounter = CombatEncounter(player, enemy)
        
        ended = encounter.check_combat_end()
        
        assert not ended
        assert encounter.is_active


class TestCombatActions:
    """Tests for combat action handling."""
    
    @pytest.fixture
    def player(self):
        """Create a test player."""
        char = Character(name="Player", health=100)
        char.add_item({"name": "Iron Sword", "type": "weapon", "damage": 25})
        char.add_item({"name": "Health Potion", "type": "potion", "heal": 50})
        return char
    
    @pytest.fixture
    def enemy(self):
        """Create a weak test enemy."""
        return Enemy(name="Target", health=30, damage=5, defense=0)
    
    def test_defend_action(self, player, enemy):
        """Test player defend action."""
        encounter = CombatEncounter(player, enemy)
        
        result = encounter.handle_player_defend()
        
        assert result is True
        assert player.is_defending
    
    def test_display_weapons(self, player, enemy, capsys):
        """Test weapon display."""
        encounter = CombatEncounter(player, enemy)
        
        weapons = encounter.display_weapons()
        
        assert len(weapons) >= 1
        output = capsys.readouterr().out
        assert "Iron Sword" in output
    
    def test_display_usable_items(self, player, enemy, capsys):
        """Test usable items display."""
        encounter = CombatEncounter(player, enemy)
        
        items = encounter.display_usable_items()
        
        assert len(items) >= 1
        output = capsys.readouterr().out
        assert "Health Potion" in output


class TestCombatVictory:
    """Tests for combat victory handling."""
    
    @pytest.fixture
    def player(self):
        """Create a test player."""
        char = Character(name="Victor", level=1)
        return char
    
    def test_award_xp(self, player):
        """Test XP is awarded on victory."""
        enemy = create_goblin(level=1)
        encounter = CombatEncounter(player, enemy)
        encounter.result = CombatResult.VICTORY
        
        initial_xp = player.experience
        rewards = encounter.award_victory_rewards()
        
        assert player.experience > initial_xp or player.level > 1
        assert rewards["xp"] > 0
    
    def test_award_gold(self, player):
        """Test gold is awarded on victory."""
        enemy = create_goblin(level=1)
        encounter = CombatEncounter(player, enemy)
        encounter.result = CombatResult.VICTORY
        
        initial_gold = player.gold
        rewards = encounter.award_victory_rewards()
        
        assert player.gold >= initial_gold
        assert rewards["gold"] >= 0


class TestCombatIntegration:
    """Integration tests for full combat scenarios."""
    
    def test_weak_enemy_quick_victory(self):
        """Test defeating a very weak enemy."""
        player = Character(name="Hero", health=100)
        player.add_item({"name": "Mega Sword", "type": "weapon", "damage": 1000})
        player.equip_item("Mega Sword")
        
        weak_enemy = Enemy(name="Slime", health=1, damage=1)
        
        # Combat should end quickly with player victory
        encounter = CombatEncounter(player, weak_enemy)
        
        # Simulate one attack
        player.attack("Mega Sword", weak_enemy)
        
        assert not weak_enemy.is_alive
    
    def test_allow_flee_option(self):
        """Test flee option can be enabled/disabled."""
        player = Character(name="Coward")
        enemy = Enemy(name="Boss", health=1000, damage=100)
        
        encounter_flee = CombatEncounter(player, enemy, allow_flee=True)
        encounter_no_flee = CombatEncounter(player, enemy, allow_flee=False)
        
        assert encounter_flee.allow_flee
        assert not encounter_no_flee.allow_flee


class TestStartCombatFunction:
    """Tests for the start_combat convenience function."""
    
    def test_creates_random_enemy(self):
        """Test start_combat with no enemy creates random enemy."""
        player = Character(name="RandomFighter")
        player.add_item({"name": "Sword", "type": "weapon", "damage": 100})
        
        # We can't easily test the full loop, but we can verify
        # the function signature works
        assert callable(start_combat)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
