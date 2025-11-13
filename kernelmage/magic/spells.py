"""Spell casting system."""
from dataclasses import dataclass
from typing import Optional
from kernelmage.entities.player import Player
from kernelmage.core.entity import Entity
from kernelmage.magic.essences import EssenceType
from kernelmage.network.protocols import ProtocolType, get_protocol
from kernelmage.network.packets import MagicalPacket, PacketHeader, PacketPayload
from kernelmage.network.routing import RoutingSystem, Route
from kernelmage.network.dns import DNSSystem
import random


@dataclass
class SpellCastResult:
    """Result of a spell cast attempt."""

    success: bool
    packet: Optional[MagicalPacket]
    message: str
    damage: int = 0
    mana_cost: int = 0
    cast_time: int = 1  # Turns required


class SpellSystem:
    """Manages spell casting."""

    @staticmethod
    def calculate_mana_cost(
        essence_type: EssenceType,
        protocol_type: ProtocolType,
        player: Player,
        base_cost: int = 30
    ) -> int:
        """Calculate total mana cost for a spell."""
        protocol = get_protocol(protocol_type)

        # Base cost modified by protocol
        cost = base_cost * protocol.mana_cost_multiplier

        # Architecture modifies cost
        cost = player.current_architecture.get_spell_cost(int(cost))

        return int(cost)

    @staticmethod
    def calculate_damage(
        essence: 'Essence',
        protocol_type: ProtocolType,
        player: Player,
        route: Route
    ) -> int:
        """Calculate spell damage."""
        protocol = get_protocol(protocol_type)

        # Base damage from essence power and player stats
        base_damage = essence.power_rating + player.stats.power

        # Apply protocol multiplier
        damage = base_damage * protocol.damage_multiplier

        # Apply architecture multiplier
        damage = player.current_architecture.get_spell_power(int(damage))

        # Apply routing multiplier (damage decreases with hops)
        damage *= route.get_damage_multiplier()

        return max(1, int(damage))

    @staticmethod
    def cast_spell(
        caster: Player,
        target: Entity,
        essence_type: EssenceType,
        protocol_type: ProtocolType,
        direct_route: bool = True
    ) -> SpellCastResult:
        """
        Cast a spell from caster to target.

        Args:
            caster: The player casting the spell
            target: The target entity
            essence_type: Type of essence to use
            protocol_type: Network protocol to use
            direct_route: Use direct routing (True) or indirect (False)

        Returns:
            SpellCastResult with outcome
        """
        # Check if caster has the essence
        essence_amount = 5  # Base essence consumption
        if not caster.has_essence(essence_type, essence_amount):
            return SpellCastResult(
                success=False,
                packet=None,
                message=f"Not enough {essence_type.value} essence!",
                mana_cost=0
            )

        # Calculate mana cost
        mana_cost = SpellSystem.calculate_mana_cost(
            essence_type, protocol_type, caster
        )

        # Check if caster has enough mana
        if not caster.stats.spend_mana(mana_cost):
            return SpellCastResult(
                success=False,
                packet=None,
                message="Not enough mana!",
                mana_cost=0
            )

        # Consume essence
        caster.consume_essence(essence_type, essence_amount)

        # Get essence power
        essence = caster.essences[essence_type]

        # Find route to target
        route = RoutingSystem.find_route(caster, target, direct=direct_route)

        if not route.is_valid:
            return SpellCastResult(
                success=False,
                packet=None,
                message="Route TTL exceeded! Target too far.",
                mana_cost=mana_cost
            )

        # Calculate damage
        damage = SpellSystem.calculate_damage(
            essence, protocol_type, caster, route
        )

        # Create packet
        protocol = get_protocol(protocol_type)
        packet = MagicalPacket(
            header=PacketHeader(
                source_ip=caster.network_address.ip,
                destination_ip=target.network_address.ip,
                protocol=protocol_type,
                ttl=route.ttl,
                sequence_number=random.randint(1000, 9999),
                checksum=f"0x{random.randint(0x1000, 0xFFFF):04X}"
            ),
            payload=PacketPayload(
                essence_type=essence_type,
                power=damage,
                shape="projectile"
            ),
            route=route
        )

        # Get cast time from protocol and architecture
        cast_time = protocol.cast_time
        cast_time = caster.current_architecture.get_cast_time(cast_time)

        message = (
            f"Casting {essence_type.value} spell via {protocol_type.value.upper()}...\n"
            f"Cost: {mana_cost} mana | Cast time: {cast_time} turn(s)"
        )

        return SpellCastResult(
            success=True,
            packet=packet,
            message=message,
            damage=damage,
            mana_cost=mana_cost,
            cast_time=cast_time
        )

    @staticmethod
    def resolve_spell(
        packet: MagicalPacket,
        target: Entity,
        protocol_type: ProtocolType
    ) -> tuple[bool, int, str]:
        """
        Resolve a spell packet hitting the target.

        Returns:
            (hit: bool, damage: int, message: str)
        """
        protocol = get_protocol(protocol_type)

        # Check for packet loss (miss)
        packet_loss_check = target.stats.packet_loss * (1.0 - protocol.accuracy)
        if random.random() < packet_loss_check:
            packet.fail()
            return (False, 0, "Spell missed! (Packet loss)")

        # Check route packet loss
        if packet.route and RoutingSystem.check_packet_loss(
            packet.route, target.stats.packet_loss
        ):
            packet.fail()
            return (False, 0, "Spell lost in transmission!")

        # Hit! Apply damage
        packet.transmit()
        packet.acknowledge()

        damage = target.take_damage(packet.payload.power)

        message = (
            f"Hit! {damage} damage dealt "
            f"({packet.route.hop_count if packet.route else 1} hops)"
        )

        return (True, damage, message)

    @staticmethod
    def cast_ping(caster: Player, target: Entity) -> dict:
        """Cast ICMP Ping spell to reveal target info."""
        mana_cost = 10
        if not caster.stats.spend_mana(mana_cost):
            return {"success": False, "message": "Not enough mana!"}

        info = DNSSystem.ping(caster, target)
        caster.cache_target(target.network_address)

        return {
            "success": True,
            "info": info,
            "message": f"Pinged {target.name} successfully!",
            "mana_cost": mana_cost
        }
