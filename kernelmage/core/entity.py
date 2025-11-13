"""Base entity class for all game entities."""
from dataclasses import dataclass, field
from typing import Optional
from kernelmage.entities.stats import Stats, NetworkAddress


@dataclass
class Entity:
    """Base class for all entities (players, enemies, NPCs)."""

    name: str
    stats: Stats = field(default_factory=Stats)
    network_address: NetworkAddress = field(default_factory=NetworkAddress)

    # Visual representation
    symbol: str = "?"
    description: str = ""

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} ({self.stats.current_hp}/{self.stats.max_hp} HP)"

    @property
    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.stats.is_alive

    def take_damage(self, amount: int, source: Optional['Entity'] = None) -> int:
        """Take damage from a source."""
        actual_damage = self.stats.take_damage(amount)
        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal this entity."""
        return self.stats.heal(amount)
