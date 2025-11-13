"""Tests for entity system."""
import sys
sys.path.insert(0, '/home/user/kernel-mage')

from kernelmage.entities.player import create_player
from kernelmage.entities.enemy import create_bandit, create_gateway_boss
from kernelmage.magic.essences import EssenceType
from kernelmage.magic.architectures import ArchitectureType


def test_player_creation():
    """Test player creation."""
    player = create_player("TestMage")

    assert player.name == "TestMage"
    assert player.stats.current_hp == 100
    assert player.stats.current_mana == 150
    assert player.level == 1
    assert len(player.essences) > 0
    print("✓ Player creation works")


def test_player_essence_management():
    """Test essence consumption."""
    player = create_player("TestMage")

    # Check initial fire essence
    assert player.has_essence(EssenceType.FIRE, 5)

    # Consume essence
    success = player.consume_essence(EssenceType.FIRE, 5)
    assert success

    # Check quantity decreased
    assert player.essences[EssenceType.FIRE].quantity == 45  # Started with 50

    print("✓ Essence management works")


def test_player_architecture_switching():
    """Test architecture switching."""
    player = create_player("TestMage")

    # Initial architecture is x86
    assert player.current_architecture.arch_type == ArchitectureType.X86_CISC

    # Switch to ARM
    success = player.switch_architecture(ArchitectureType.ARM_RISC)
    assert success
    assert player.current_architecture.arch_type == ArchitectureType.ARM_RISC
    assert player.stats.current_mana == 130  # Lost 20 mana

    print("✓ Architecture switching works")


def test_player_leveling():
    """Test player leveling."""
    player = create_player("TestMage")

    initial_level = player.level
    initial_hp = player.stats.max_hp

    # Gain enough XP to level up
    player.gain_experience(100)

    assert player.level == initial_level + 1
    assert player.stats.max_hp > initial_hp

    print("✓ Leveling works")


def test_enemy_creation():
    """Test enemy creation."""
    bandit = create_bandit()

    assert bandit.name == "Bandit"
    assert bandit.stats.current_hp > 0
    assert bandit.is_alive
    assert bandit.xp_reward > 0

    print("✓ Enemy creation works")


def test_enemy_damage():
    """Test enemy taking damage."""
    enemy = create_gateway_boss()

    initial_hp = enemy.stats.current_hp

    damage = enemy.take_damage(50)

    assert damage > 0  # Some damage got through
    assert enemy.stats.current_hp < initial_hp
    assert enemy.is_alive  # Boss should survive 50 damage

    print("✓ Enemy damage works")


def test_enemy_loot():
    """Test enemy loot."""
    bandit = create_bandit()

    essence_type, amount = bandit.get_loot()

    assert essence_type is not None
    assert amount > 0

    print("✓ Enemy loot works")


if __name__ == "__main__":
    print("Running entity tests...\n")

    test_player_creation()
    test_player_essence_management()
    test_player_architecture_switching()
    test_player_leveling()
    test_enemy_creation()
    test_enemy_damage()
    test_enemy_loot()

    print("\n✅ All entity tests passed!")
