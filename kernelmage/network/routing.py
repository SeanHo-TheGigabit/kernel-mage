"""Network routing and packet transmission."""
from dataclasses import dataclass
from typing import List
from kernelmage.core.entity import Entity
import random


@dataclass
class Route:
    """A route through the network."""

    source: str  # IP address
    destination: str  # IP address
    hops: List[str]  # Intermediate nodes
    ttl: int  # Time to live

    @property
    def hop_count(self) -> int:
        """Get number of hops in route."""
        return len(self.hops)

    @property
    def is_valid(self) -> bool:
        """Check if route is still valid (within TTL)."""
        return self.hop_count <= self.ttl

    def get_damage_multiplier(self) -> float:
        """Get damage multiplier based on hop count."""
        # Each hop reduces damage by 10%
        return max(0.3, 1.0 - (self.hop_count * 0.1))


class RoutingSystem:
    """Manages packet routing between entities."""

    @staticmethod
    def find_route(source: Entity, target: Entity,
                   direct: bool = True) -> Route:
        """
        Find route from source to target.

        Args:
            source: Source entity
            target: Target entity
            direct: If True, use direct route (1 hop)

        Returns:
            Route object
        """
        if direct:
            # Direct route (most common)
            return Route(
                source=source.network_address.ip,
                destination=target.network_address.ip,
                hops=[target.network_address.ip],
                ttl=5
            )
        else:
            # Indirect route with intermediate hops
            # Generate some intermediate nodes
            num_hops = random.randint(2, 4)
            hops = []

            for i in range(num_hops - 1):
                hop_ip = f"10.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
                hops.append(hop_ip)

            hops.append(target.network_address.ip)

            return Route(
                source=source.network_address.ip,
                destination=target.network_address.ip,
                hops=hops,
                ttl=10
            )

    @staticmethod
    def calculate_latency(route: Route, base_latency: int = 1) -> int:
        """Calculate total latency for route (in turns)."""
        return base_latency * route.hop_count

    @staticmethod
    def check_packet_loss(route: Route, base_loss: float) -> bool:
        """
        Check if packet is lost during transmission.

        Returns:
            True if packet is lost, False if delivered
        """
        # Packet loss increases with hop count
        total_loss = min(0.95, base_loss * (1 + route.hop_count * 0.1))
        return random.random() < total_loss
