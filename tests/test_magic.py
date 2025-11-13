"""Tests for magic system."""
import sys
sys.path.insert(0, '/home/user/kernel-mage')

from kernelmage.entities.player import create_player
from kernelmage.entities.enemy import create_bandit
from kernelmage.magic.essences import EssenceType, Essence
from kernelmage.magic.architectures import get_architecture, ArchitectureType
from kernelmage.magic.spells import SpellSystem
from kernelmage.network.protocols import ProtocolType


def test_essence_creation():
    """Test essence creation."""
    fire = Essence(EssenceType.FIRE, quantity=100, power_rating=80)

    assert fire.essence_type == EssenceType.FIRE
    assert fire.quantity == 100
    assert fire.power_rating == 80
    assert fire.color == "red"

    print("✓ Essence creation works")


def test_essence_effectiveness():
    """Test essence effectiveness."""
    fire = Essence(EssenceType.FIRE, quantity=50, power_rating=80)

    # Fire is strong against earth
    effectiveness = fire.get_effectiveness(EssenceType.EARTH)
    assert effectiveness > 1.0

    # Fire is weak against water
    effectiveness = fire.get_effectiveness(EssenceType.WATER)
    assert effectiveness < 1.0

    print("✓ Essence effectiveness works")


def test_architecture_modifiers():
    """Test architecture modifiers."""
    x86 = get_architecture(ArchitectureType.X86_CISC)
    arm = get_architecture(ArchitectureType.ARM_RISC)

    # x86 should have higher power
    x86_power = x86.get_spell_power(100)
    arm_power = arm.get_spell_power(100)
    assert x86_power > arm_power

    # ARM should have lower cost
    x86_cost = x86.get_spell_cost(100)
    arm_cost = arm.get_spell_cost(100)
    assert arm_cost < x86_cost

    print("✓ Architecture modifiers work")


def test_spell_casting():
    """Test spell casting."""
    player = create_player("TestMage")
    enemy = create_bandit()

    initial_mana = player.stats.current_mana
    initial_essence = player.essences[EssenceType.FIRE].quantity

    # Cast a UDP fire spell
    result = SpellSystem.cast_spell(
        caster=player,
        target=enemy,
        essence_type=EssenceType.FIRE,
        protocol_type=ProtocolType.UDP
    )

    assert result.success
    assert result.packet is not None
    assert result.damage > 0
    assert player.stats.current_mana < initial_mana  # Mana spent
    assert player.essences[EssenceType.FIRE].quantity < initial_essence  # Essence consumed

    print("✓ Spell casting works")


def test_tcp_vs_udp():
    """Test TCP vs UDP differences."""
    player = create_player("TestMage")
    enemy = create_bandit()

    # Cast TCP spell
    tcp_result = SpellSystem.cast_spell(
        player, enemy, EssenceType.FIRE, ProtocolType.TCP
    )

    # Reset player
    player = create_player("TestMage")

    # Cast UDP spell
    udp_result = SpellSystem.cast_spell(
        player, enemy, EssenceType.FIRE, ProtocolType.UDP
    )

    # TCP should cost more mana
    assert tcp_result.mana_cost > udp_result.mana_cost

    # TCP should take more turns
    assert tcp_result.cast_time > udp_result.cast_time

    print("✓ TCP vs UDP differences work")


def test_spell_resolution():
    """Test spell resolution."""
    player = create_player("TestMage")
    enemy = create_bandit()

    # Cast spell
    result = SpellSystem.cast_spell(
        player, enemy, EssenceType.FIRE, ProtocolType.TCP
    )

    assert result.success
    assert result.packet is not None

    initial_hp = enemy.stats.current_hp

    # Resolve spell - TCP has high accuracy but can still miss due to routing
    # Try multiple times to ensure it works
    hit_count = 0
    for _ in range(10):
        player_test = create_player("Test")
        enemy_test = create_bandit()
        test_result = SpellSystem.cast_spell(
            player_test, enemy_test, EssenceType.FIRE, ProtocolType.TCP
        )

        if test_result.success and test_result.packet:
            hit, damage, message = SpellSystem.resolve_spell(
                test_result.packet, enemy_test, ProtocolType.TCP
            )
            if hit:
                hit_count += 1

    # TCP should hit most of the time (at least 70%)
    assert hit_count >= 7, f"TCP only hit {hit_count}/10 times"

    print("✓ Spell resolution works")


def test_ping_spell():
    """Test ICMP ping."""
    player = create_player("TestMage")
    enemy = create_bandit()

    result = SpellSystem.cast_ping(player, enemy)

    assert result["success"]
    assert "info" in result
    assert result["info"]["name"] == "Bandit"
    assert result["info"]["hp"] > 0

    print("✓ Ping spell works")


if __name__ == "__main__":
    print("Running magic system tests...\n")

    test_essence_creation()
    test_essence_effectiveness()
    test_architecture_modifiers()
    test_spell_casting()
    test_tcp_vs_udp()
    test_spell_resolution()
    test_ping_spell()

    print("\n✅ All magic tests passed!")
