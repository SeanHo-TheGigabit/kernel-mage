"""Tests for simplified arena mode."""
import sys
sys.path.insert(0, '.')

from kernelmage.core.arena import ArenaGame
from kernelmage.entities.player import create_player
from kernelmage.magic.essences import EssenceType
from kernelmage.magic.architectures import ArchitectureType


def test_arena_initialization():
    """Test arena game initializes correctly."""
    print("\n[Test] Arena initialization...")

    arena = ArenaGame()

    assert arena.round_number == 0
    assert arena.running == True
    assert arena.player is None

    print("✓ Arena initializes correctly")


def test_generate_round_enemies():
    """Test enemy generation for different rounds."""
    print("\n[Test] Enemy generation...")

    arena = ArenaGame()
    arena.player = create_player("TestHero")

    # Round 1: Single bandit
    enemies_r1 = arena.generate_round_enemies(1)
    assert len(enemies_r1) == 1
    assert "Bandit" in enemies_r1[0].name
    print(f"✓ Round 1: {len(enemies_r1)} enemy (bandit)")

    # Round 2: Two bandits
    enemies_r2 = arena.generate_round_enemies(2)
    assert len(enemies_r2) == 2
    print(f"✓ Round 2: {len(enemies_r2)} enemies")

    # Round 3: Corrupted node
    enemies_r3 = arena.generate_round_enemies(3)
    assert len(enemies_r3) == 1
    assert "Corrupted" in enemies_r3[0].name
    print(f"✓ Round 3: {len(enemies_r3)} enemy (corrupted node)")

    # Round 4: Swarm
    enemies_r4 = arena.generate_round_enemies(4)
    assert len(enemies_r4) == 3
    print(f"✓ Round 4: {len(enemies_r4)} enemies (swarm)")

    # Round 8: Boss
    enemies_r8 = arena.generate_round_enemies(8)
    assert len(enemies_r8) == 1
    assert "Gateway" in enemies_r8[0].name
    print(f"✓ Round 8: {len(enemies_r8)} enemy (boss)")

    print("✓ Enemy generation works correctly")


def test_rest_between_rounds():
    """Test resting mechanic."""
    print("\n[Test] Rest between rounds...")

    arena = ArenaGame()
    arena.player = create_player("TestHero")

    # Damage the player
    arena.player.stats.current_hp = 50
    arena.player.stats.current_mana = 30

    old_hp = arena.player.stats.current_hp
    old_mana = arena.player.stats.current_mana

    # Rest
    arena.rest_between_rounds()

    # Should have restored some HP and mana
    assert arena.player.stats.current_hp > old_hp
    assert arena.player.stats.current_mana > old_mana

    print(f"✓ Rest restored HP: {old_hp} → {arena.player.stats.current_hp}")
    print(f"✓ Rest restored Mana: {old_mana} → {arena.player.stats.current_mana}")
    print("✓ Rest mechanic works")


def test_progressive_difficulty():
    """Test that difficulty increases with rounds."""
    print("\n[Test] Progressive difficulty...")

    arena = ArenaGame()
    arena.player = create_player("TestHero")

    # Check enemy counts increase
    rounds_to_check = [1, 2, 3, 4, 5, 6, 7, 8]
    total_hp_by_round = []

    for round_num in rounds_to_check:
        enemies = arena.generate_round_enemies(round_num)
        total_hp = sum(e.stats.max_hp for e in enemies)
        total_hp_by_round.append(total_hp)
        print(f"  Round {round_num}: {len(enemies)} enemies, {total_hp} total HP")

    # Early rounds should have less HP than later rounds
    assert total_hp_by_round[0] < total_hp_by_round[4]  # Round 1 < Round 5
    assert total_hp_by_round[2] < total_hp_by_round[7]  # Round 3 < Round 8

    print("✓ Difficulty increases progressively")


def test_arena_combat_flow():
    """Test a complete arena combat flow."""
    print("\n[Test] Arena combat flow...")

    arena = ArenaGame()
    arena.player = create_player("TestHero")
    arena.player.add_essence(EssenceType.FIRE, 50)
    arena.player.add_essence(EssenceType.WATER, 50)
    arena.player.switch_architecture(ArchitectureType.ARM_RISC)

    # Round 1
    arena.round_number = 1
    enemies = arena.generate_round_enemies(1)

    from kernelmage.combat.combat import create_encounter
    from kernelmage.network.protocols import ProtocolType

    encounter = create_encounter(arena.player, enemies)

    # Fight until victory or defeat
    max_turns = 20
    turns = 0

    while not encounter.is_over and turns < max_turns:
        # Player attacks first enemy
        target = encounter.active_enemies[0] if encounter.active_enemies else None

        if target:
            result = encounter.player_cast_spell(
                target,
                EssenceType.FIRE,
                ProtocolType.UDP
            )

            if result.success:
                encounter.next_turn()

        turns += 1

    # Should eventually win or lose
    assert encounter.is_over
    print(f"✓ Combat completed in {turns} turns")
    print(f"✓ Combat state: {encounter.state.value}")
    print(f"✓ Player alive: {arena.player.is_alive}")
    print("✓ Arena combat flow works")


if __name__ == "__main__":
    print("╔════════════════════════════════════════════╗")
    print("║   KernelMage - Arena Test Suite           ║")
    print("╚════════════════════════════════════════════╝")

    try:
        test_arena_initialization()
        test_generate_round_enemies()
        test_rest_between_rounds()
        test_progressive_difficulty()
        test_arena_combat_flow()

        print("\n" + "=" * 50)
        print("🎉 ALL ARENA TESTS PASSED!")
        print("=" * 50)
        print("\nArena systems verified:")
        print("  ✓ Arena initialization")
        print("  ✓ Enemy generation")
        print("  ✓ Rest mechanic")
        print("  ✓ Progressive difficulty")
        print("  ✓ Combat flow")
        print("\n✅ Arena mode is ready to play!")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
