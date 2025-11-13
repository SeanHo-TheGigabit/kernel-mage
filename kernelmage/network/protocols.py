"""Network protocols for spell casting."""
from dataclasses import dataclass
from enum import Enum


class ProtocolType(Enum):
    """Network protocols that determine spell casting behavior."""

    TCP = "tcp"  # Reliable, slow, guaranteed hit
    UDP = "udp"  # Fast, unreliable, might miss
    ICMP = "icmp"  # Utility (ping, traceroute, echo)
    MULTICAST = "multicast"  # Area of effect


@dataclass
class Protocol:
    """Protocol configuration for spell casting."""

    protocol_type: ProtocolType
    cast_time: int  # Turns to cast
    mana_cost_multiplier: float  # Multiplier on base mana cost
    accuracy: float  # Hit chance (0.0 to 1.0)
    damage_multiplier: float  # Damage multiplier
    can_aoe: bool  # Can hit multiple targets
    description: str

    # Protocol descriptions
    DESCRIPTIONS = {
        ProtocolType.TCP: "Reliable three-way handshake. Guaranteed hit but slow.",
        ProtocolType.UDP: "Fire-and-forget. Fast but might miss.",
        ProtocolType.ICMP: "Utility protocol for reconnaissance and detection.",
        ProtocolType.MULTICAST: "Broadcast to area. Hits multiple targets.",
    }


# Predefined protocol configurations
TCP_PROTOCOL = Protocol(
    protocol_type=ProtocolType.TCP,
    cast_time=3,  # SYN, SYN-ACK, ACK+DATA
    mana_cost_multiplier=2.0,  # High overhead
    accuracy=1.0,  # Always hits
    damage_multiplier=1.0,  # Full damage
    can_aoe=False,
    description=Protocol.DESCRIPTIONS[ProtocolType.TCP],
)

UDP_PROTOCOL = Protocol(
    protocol_type=ProtocolType.UDP,
    cast_time=1,  # Instant
    mana_cost_multiplier=0.7,  # Low overhead
    accuracy=0.7,  # 70% hit chance
    damage_multiplier=0.8,  # Slightly less damage
    can_aoe=False,
    description=Protocol.DESCRIPTIONS[ProtocolType.UDP],
)

ICMP_PROTOCOL = Protocol(
    protocol_type=ProtocolType.ICMP,
    cast_time=1,
    mana_cost_multiplier=0.3,  # Very cheap
    accuracy=1.0,  # Utilities always work
    damage_multiplier=0.0,  # No damage, utility only
    can_aoe=True,
    description=Protocol.DESCRIPTIONS[ProtocolType.ICMP],
)

MULTICAST_PROTOCOL = Protocol(
    protocol_type=ProtocolType.MULTICAST,
    cast_time=2,  # Setup group, then send
    mana_cost_multiplier=2.5,  # Very expensive (packet replication)
    accuracy=0.85,  # Good but not perfect
    damage_multiplier=0.6,  # Damage split among targets
    can_aoe=True,
    description=Protocol.DESCRIPTIONS[ProtocolType.MULTICAST],
)

# Protocol registry
PROTOCOLS = {
    ProtocolType.TCP: TCP_PROTOCOL,
    ProtocolType.UDP: UDP_PROTOCOL,
    ProtocolType.ICMP: ICMP_PROTOCOL,
    ProtocolType.MULTICAST: MULTICAST_PROTOCOL,
}


def get_protocol(protocol_type: ProtocolType) -> Protocol:
    """Get protocol configuration by type."""
    return PROTOCOLS[protocol_type]
