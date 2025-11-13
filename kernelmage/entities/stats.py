"""Entity stats and attributes."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Stats:
    """Base stats for entities (players and enemies)."""

    max_hp: int = 100
    current_hp: int = 100
    max_mana: int = 150  # Bandwidth
    current_mana: int = 150

    # Network characteristics
    bandwidth: int = 100  # Mbps - affects spell power
    packet_loss: float = 0.05  # 5% base miss chance
    latency: int = 1  # Turns delay for spell casting

    # Combat stats
    power: int = 10  # Base spell damage modifier
    defense: int = 5  # Firewall strength

    def take_damage(self, amount: int) -> int:
        """Apply damage and return actual damage taken."""
        actual_damage = max(0, amount - self.defense)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal HP and return actual healing."""
        actual_heal = min(amount, self.max_hp - self.current_hp)
        self.current_hp = min(self.max_hp, self.current_hp + actual_heal)
        return actual_heal

    def spend_mana(self, amount: int) -> bool:
        """Try to spend mana. Returns True if successful."""
        if self.current_mana >= amount:
            self.current_mana -= amount
            return True
        return False

    def restore_mana(self, amount: int) -> int:
        """Restore mana and return actual restoration."""
        actual_restore = min(amount, self.max_mana - self.current_mana)
        self.current_mana = min(self.max_mana, self.current_mana + actual_restore)
        return actual_restore

    @property
    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.current_hp > 0

    @property
    def hp_percentage(self) -> float:
        """Get HP as percentage."""
        return (self.current_hp / self.max_hp) * 100 if self.max_hp > 0 else 0

    @property
    def mana_percentage(self) -> float:
        """Get mana as percentage."""
        return (self.current_mana / self.max_mana) * 100 if self.max_mana > 0 else 0


@dataclass
class NetworkAddress:
    """Network address for targeting (DNS system)."""

    ip: str = ""  # e.g., "192.168.1.42" or "10.13.5.78"
    hostname: str = ""  # e.g., "village_guard_01"
    subnet: str = "0.0.0.0/0"  # Network location

    # DNS cache info
    is_cached: bool = False
    cache_ttl: int = 0  # Turns remaining in cache

    def __str__(self) -> str:
        """String representation of address."""
        if self.hostname:
            return f"{self.hostname} ({self.ip})"
        return self.ip if self.ip else "[Unknown]"

    @classmethod
    def generate(cls, subnet: str, host_id: int, hostname: str = "") -> 'NetworkAddress':
        """Generate a network address."""
        # Simple IP generation from subnet
        base = subnet.split('/')[0]
        parts = base.split('.')
        ip = f"{parts[0]}.{parts[1]}.{parts[2]}.{host_id}"

        return cls(
            ip=ip,
            hostname=hostname,
            subnet=subnet,
            is_cached=False,
            cache_ttl=0
        )
