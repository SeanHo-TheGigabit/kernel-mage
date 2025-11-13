"""DNS and targeting system."""
from dataclasses import dataclass
from typing import List, Optional
from kernelmage.core.entity import Entity
from kernelmage.entities.stats import NetworkAddress
import random


@dataclass
class DNSQuery:
    """A DNS query to resolve a target."""

    source: Entity
    target: Entity
    success_chance: float = 0.9  # 90% base success rate

    def resolve(self) -> Optional[NetworkAddress]:
        """Attempt to resolve the target's address."""
        # Check if query succeeds
        if random.random() < self.success_chance:
            # Successfully resolved
            address = self.target.network_address
            address.is_cached = False  # Not cached yet
            return address
        return None  # Query failed


@dataclass
class DNSPoisonEffect:
    """DNS poisoning effect that corrupts targeting."""

    duration: int  # Turns remaining
    corruption_chance: float = 0.5  # Chance to corrupt targeting

    def corrupt_address(self, address: NetworkAddress) -> NetworkAddress:
        """Corrupt an address with false information."""
        if random.random() < self.corruption_chance:
            # Generate fake IP
            fake_ip = f"10.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            corrupted = NetworkAddress(
                ip=fake_ip,
                hostname=f"illusion_{address.hostname}",
                subnet=address.subnet,
                is_cached=False,
                cache_ttl=0
            )
            return corrupted
        return address  # Not corrupted


class DNSSystem:
    """Manages DNS queries and targeting."""

    @staticmethod
    def query_target(source: Entity, target: Entity,
                     poison_effect: Optional[DNSPoisonEffect] = None) -> Optional[NetworkAddress]:
        """
        Query a target's network address.

        Args:
            source: The entity performing the query
            target: The entity being targeted
            poison_effect: Optional DNS poisoning effect

        Returns:
            NetworkAddress if successful, None if failed
        """
        query = DNSQuery(source, target)
        address = query.resolve()

        if address and poison_effect:
            # Apply DNS poisoning
            address = poison_effect.corrupt_address(address)

        return address

    @staticmethod
    def ping(source: Entity, target: Entity) -> dict:
        """
        ICMP ping - reveal target information.

        Returns:
            dict with target stats and network info
        """
        return {
            "name": target.name,
            "ip": target.network_address.ip,
            "hostname": target.network_address.hostname,
            "hp": target.stats.current_hp,
            "max_hp": target.stats.max_hp,
            "latency": target.stats.latency,
            "packet_loss": target.stats.packet_loss,
            "firewall": target.stats.defense,
        }

    @staticmethod
    def traceroute(source: Entity, target: Entity, hops: List[str]) -> dict:
        """
        ICMP traceroute - show route to target.

        Args:
            source: Source entity
            target: Target entity
            hops: List of intermediate nodes

        Returns:
            dict with route information
        """
        return {
            "source": source.network_address.ip,
            "destination": target.network_address.ip,
            "hops": hops,
            "hop_count": len(hops),
            "estimated_latency": len(hops) * target.stats.latency,
        }

    @staticmethod
    def flush_cache(entity: Entity):
        """Flush an entity's DNS cache (for players)."""
        if hasattr(entity, 'dns_cache'):
            entity.flush_dns_cache()
