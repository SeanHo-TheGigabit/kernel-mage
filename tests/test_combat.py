"""Tests for combat system."""
import sys
sys.path.insert(0, '/home/user/kernel-mage')

from kernelmage.entities.player import create_player
from kernelmage.entities.enemy import create_bandit, create_swarm_minion
from kernelmage.combat.combat import create_encounter, CombatState
from kernelmage.magic.essences import EssenceType
from kernelmage.network.protocols import ProtocolType


def test_encounter_creation():
    """Test encounter creation."""
    player = create_player("TestMage")
    enemies = [create_bandit(), create_bandit()]

    encounter = create_encounter(player, enemies)

    assert encounter.player == player
    assert len(encounter.enemies) == 2
    assert encounter.state == CombatState.ACTIVE
    assert encounter.turn_number == 0

    print("✓ Encounter creation works")


def test_combat_spell_casting():
    """Test spell casting in combat."""
    player = create_player("TestMage")
    enemy = create_bandit()
    encounter = create_encounter(player, [enemy])

    # Cast spell
    result = encounter.player_cast_spell(
        target=enemy,
        essence_type=EssenceType.FIRE,
        protocol_type=ProtocolType.UDP
    )

    assert result.success
    assert len(encounter.combat_log) > 0

    print("✓ Combat spell casting works")


def test_multi_turn_spell():
    """Test multi-turn spell (TCP)."""
    player = create_player("TestMage")
    enemy = create_bandit()
    encounter = create_encounter(player, [enemy])

    # Cast TCP spell (3 turns)
    result = encounter.player_cast_spell(
        target=enemy,
        essence_type=EssenceType.FIRE,
        protocol_type=ProtocolType.TCP
    )

    assert result.success
    assert result.cast_time > 1

    # Should have pending spell
    assert len(encounter.pending_player_spells) > 0

    print("✓ Multi-turn spell works")


def test_pending_spell_resolution():
    """Test pending spell resolution."""
    player = create_player("TestMage")
    enemy = create_bandit()
    encounter = create_encounter(player, [enemy])

    # Cast TCP spell
    result = encounter.player_cast_spell(
        target=enemy,
        essence_type=EssenceType.LIGHTNING,
        protocol_type=ProtocolType.TCP
    )

    initial_pending = len(encounter.pending_player_spells)
    initial_hp = enemy.stats.current_hp

    # Advance turns until spell resolves
    for _ in range(3):
        encounter.process_pending_spells()

    # Spell should be resolved
    assert len(encounter.pending_player_spells) < initial_pending

    print("✓ Pending spell resolution works")


def test_victory_condition():
    """Test victory condition."""
    player = create_player("TestMage")
    enemy = create_swarm_minion()  # Weak enemy
    encounter = create_encounter(player, [enemy])

    # Kill enemy directly to test victory condition
    enemy.stats.current_hp = 0

    # Check for victory
    encounter.check_victory_conditions()

    assert not enemy.is_alive
    assert encounter.state == CombatState.VICTORY

    print("✓ Victory condition works")


def test_defeat_condition():
    """Test defeat condition."""
    player = create_player("TestMage")
    enemy = create_bandit()
    encounter = create_encounter(player, [enemy])

    # Kill player
    player.stats.current_hp = 0

    encounter.check_victory_conditions()

    assert not player.is_alive
    assert encounter.state == CombatState.DEFEAT

    print("✓ Defeat condition works")


def test_loot_awarding():
    """Test loot awarding."""
    player = create_player("TestMage")
    enemy = create_bandit()
    encounter = create_encounter(player, [enemy])

    initial_xp = player.experience
    initial_fire = player.essences[EssenceType.FIRE].quantity

    # Kill enemy and award loot
    encounter.state = CombatState.VICTORY
    encounter.award_loot()

    assert player.experience > initial_xp
    # Fire essence might increase (bandit drops fire)

    print("✓ Loot awarding works")


def test_enemy_turn():
    """Test enemy turn."""
    player = create_player("TestMage")
    enemy = create_bandit()
    encounter = create_encounter(player, [enemy])

    initial_hp = player.stats.current_hp

    # Enemy attacks
    encounter.enemy_turn(enemy)

    # Player might take damage (depending on RNG)
    # Just check the system doesn't crash
    assert player.stats.current_hp <= initial_hp

    print("✓ Enemy turn works")


def test_active_enemies():
    """Test active enemies tracking."""
    player = create_player("TestMage")
    enemies = [create_bandit(), create_bandit(), create_bandit()]
    encounter = create_encounter(player, enemies)

    assert len(encounter.active_enemies) == 3

    # Kill one enemy
    enemies[0].stats.current_hp = 0

    assert len(encounter.active_enemies) == 2

    print("✓ Active enemies tracking works")


if __name__ == "__main__":
    print("Running combat system tests...\n")

    test_encounter_creation()
    test_combat_spell_casting()
    test_multi_turn_spell()
    test_pending_spell_resolution()
    test_victory_condition()
    test_defeat_condition()
    test_loot_awarding()
    test_enemy_turn()
    test_active_enemies()

    print("\n✅ All combat tests passed!")
