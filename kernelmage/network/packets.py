"""Packet structure for magical spells."""
from dataclasses import dataclass
from typing import Optional
from kernelmage.magic.essences import EssenceType
from kernelmage.network.protocols import ProtocolType
from kernelmage.network.routing import Route


@dataclass
class PacketHeader:
    """Packet header information."""

    source_ip: str
    destination_ip: str
    protocol: ProtocolType
    ttl: int
    sequence_number: int = 0
    checksum: str = "0x0000"

    def __str__(self) -> str:
        """String representation of header."""
        return (
            f"From: {self.source_ip} → To: {self.destination_ip}\n"
            f"Protocol: {self.protocol.value.upper()} | TTL: {self.ttl}"
        )


@dataclass
class PacketPayload:
    """Packet payload (the actual spell data)."""

    essence_type: EssenceType
    power: int  # Damage/effect power
    shape: str = "projectile"  # Shape of spell
    effect: Optional[str] = None  # Additional effect (burn, freeze, etc.)

    def __str__(self) -> str:
        """String representation of payload."""
        base = f"Type: {self.essence_type.value.title()} | Power: {self.power}"
        if self.effect:
            base += f" | Effect: {self.effect}"
        return base


@dataclass
class MagicalPacket:
    """
    A complete magical packet (spell).

    This represents a spell as a network packet with header,
    payload, and routing information.
    """

    header: PacketHeader
    payload: PacketPayload
    route: Optional[Route] = None

    # Packet state
    transmitted: bool = False
    acknowledged: bool = False
    failed: bool = False

    def transmit(self):
        """Mark packet as transmitted."""
        self.transmitted = True

    def acknowledge(self):
        """Mark packet as acknowledged (TCP)."""
        self.acknowledged = True

    def fail(self):
        """Mark packet as failed."""
        self.failed = True

    @property
    def is_complete(self) -> bool:
        """Check if packet transmission is complete."""
        return self.transmitted and (self.acknowledged or self.failed)

    def __str__(self) -> str:
        """String representation of packet."""
        status = "TRANSMITTED" if self.transmitted else "PENDING"
        if self.acknowledged:
            status = "ACKNOWLEDGED"
        elif self.failed:
            status = "FAILED"

        return (
            f"╔════════════════════════════════╗\n"
            f"║     MAGICAL PACKET [{status}]     ║\n"
            f"╠════════════════════════════════╣\n"
            f"║ HEADER:                        ║\n"
            f"║ {self.header.source_ip:30} ║\n"
            f"║ → {self.header.destination_ip:28} ║\n"
            f"║ Protocol: {self.header.protocol.value.upper():19} ║\n"
            f"╠════════════════════════════════╣\n"
            f"║ PAYLOAD:                       ║\n"
            f"║ Essence: {self.payload.essence_type.value.title():20} ║\n"
            f"║ Power: {self.payload.power:23} ║\n"
            f"╚════════════════════════════════╝"
        )
