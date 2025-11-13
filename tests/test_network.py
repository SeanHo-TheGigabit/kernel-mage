"""Tests for network system."""
import sys
sys.path.insert(0, '/home/user/kernel-mage')

from kernelmage.entities.player import create_player
from kernelmage.entities.enemy import create_bandit
from kernelmage.network.dns import DNSSystem, DNSQuery
from kernelmage.network.routing import RoutingSystem, Route
from kernelmage.network.protocols import get_protocol, ProtocolType
from kernelmage.network.packets import MagicalPacket, PacketHeader, PacketPayload
from kernelmage.magic.essences import EssenceType


def test_dns_query():
    """Test DNS querying."""
    player = create_player("TestMage")
    enemy = create_bandit()

    # Query target
    address = DNSSystem.query_target(player, enemy)

    assert address is not None
    assert address.ip != ""
    assert address.hostname != ""

    print("✓ DNS query works")


def test_dns_ping():
    """Test DNS ping."""
    player = create_player("TestMage")
    enemy = create_bandit()

    info = DNSSystem.ping(player, enemy)

    assert info["name"] == "Bandit"
    assert "ip" in info
    assert "hp" in info
    assert info["hp"] > 0

    print("✓ DNS ping works")


def test_routing_direct():
    """Test direct routing."""
    player = create_player("TestMage")
    enemy = create_bandit()

    route = RoutingSystem.find_route(player, enemy, direct=True)

    assert route.hop_count == 1
    assert route.is_valid
    assert route.source == player.network_address.ip
    assert route.destination == enemy.network_address.ip

    print("✓ Direct routing works")


def test_routing_indirect():
    """Test indirect routing."""
    player = create_player("TestMage")
    enemy = create_bandit()

    route = RoutingSystem.find_route(player, enemy, direct=False)

    assert route.hop_count > 1
    assert route.is_valid

    print("✓ Indirect routing works")


def test_route_damage_multiplier():
    """Test route damage multiplier."""
    player = create_player("TestMage")
    enemy = create_bandit()

    # Direct route
    direct_route = RoutingSystem.find_route(player, enemy, direct=True)
    direct_multiplier = direct_route.get_damage_multiplier()

    # Indirect route
    indirect_route = RoutingSystem.find_route(player, enemy, direct=False)
    indirect_multiplier = indirect_route.get_damage_multiplier()

    # Direct should do more damage
    assert direct_multiplier >= indirect_multiplier

    print("✓ Route damage multiplier works")


def test_protocol_configuration():
    """Test protocol configurations."""
    tcp = get_protocol(ProtocolType.TCP)
    udp = get_protocol(ProtocolType.UDP)

    # TCP should be slower but more accurate
    assert tcp.cast_time > udp.cast_time
    assert tcp.accuracy > udp.accuracy
    assert tcp.mana_cost_multiplier > udp.mana_cost_multiplier

    print("✓ Protocol configurations work")


def test_packet_creation():
    """Test packet creation."""
    player = create_player("TestMage")
    enemy = create_bandit()

    header = PacketHeader(
        source_ip=player.network_address.ip,
        destination_ip=enemy.network_address.ip,
        protocol=ProtocolType.UDP,
        ttl=5
    )

    payload = PacketPayload(
        essence_type=EssenceType.FIRE,
        power=50
    )

    packet = MagicalPacket(header=header, payload=payload)

    assert not packet.transmitted
    assert not packet.acknowledged

    # Transmit packet
    packet.transmit()
    assert packet.transmitted

    print("✓ Packet creation works")


def test_latency_calculation():
    """Test latency calculation."""
    player = create_player("TestMage")
    enemy = create_bandit()

    route = RoutingSystem.find_route(player, enemy, direct=True)
    latency = RoutingSystem.calculate_latency(route)

    assert latency >= route.hop_count

    print("✓ Latency calculation works")


if __name__ == "__main__":
    print("Running network system tests...\n")

    test_dns_query()
    test_dns_ping()
    test_routing_direct()
    test_routing_indirect()
    test_route_damage_multiplier()
    test_protocol_configuration()
    test_packet_creation()
    test_latency_calculation()

    print("\n✅ All network tests passed!")
