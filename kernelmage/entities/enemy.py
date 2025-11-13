"""Enemy classes and definitions."""
from dataclasses import dataclass, field
from typing import Optional
from kernelmage.core.entity import Entity
from kernelmage.entities.stats import Stats, NetworkAddress
from kernelmage.magic.essences import EssenceType


@dataclass
class Enemy(Entity):
    """Enemy entity."""

    # Loot
    essence_drop: Optional[EssenceType] = None
    essence_drop_amount: int = 10
    xp_reward: int = 25

    # AI behavior
    aggression: float = 0.7  # How likely to attack (0.0-1.0)
    preferred_essence: Optional[EssenceType] = None

    def __post_init__(self):
        """Initialize enemy defaults."""
        # Generate network address if not set
        if not self.network_address.ip:
            # Use a default hostile subnet
            import random
            host_id = random.randint(10, 250)
            self.network_address = NetworkAddress.generate(
                subnet="10.66.6.0/24",
                host_id=host_id,
                hostname=f"hostile_{self.name.lower().replace(' ', '_')}"
            )

    def get_loot(self) -> tuple[Optional[EssenceType], int]:
        """Get loot drops from this enemy."""
        return (self.essence_drop, self.essence_drop_amount)


# Enemy factory functions
def create_bandit() -> Enemy:
    """Create a bandit enemy."""
    stats = Stats(
        max_hp=50,
        current_hp=50,
        max_mana=40,
        current_mana=40,
        bandwidth=50,
        packet_loss=0.15,  # 15% miss chance
        power=5,
        defense=2,
    )

    return Enemy(
        name="Bandit",
        stats=stats,
        symbol="b",
        description="A highway robber using crude network magic",
        essence_drop=EssenceType.FIRE,
        essence_drop_amount=15,
        xp_reward=25,
        aggression=0.8,
        preferred_essence=EssenceType.FIRE,
    )


def create_corrupted_node() -> Enemy:
    """Create a corrupted network node enemy."""
    stats = Stats(
        max_hp=80,
        current_hp=80,
        max_mana=60,
        current_mana=60,
        bandwidth=75,
        packet_loss=0.10,
        power=8,
        defense=4,
    )

    return Enemy(
        name="Corrupted Node",
        stats=stats,
        symbol="N",
        description="A network node infected with malicious packets",
        essence_drop=EssenceType.SHADOW,
        essence_drop_amount=20,
        xp_reward=40,
        aggression=0.6,
        preferred_essence=EssenceType.SHADOW,
    )


def create_gateway_boss() -> Enemy:
    """Create a gateway boss enemy."""
    stats = Stats(
        max_hp=200,
        current_hp=200,
        max_mana=150,
        current_mana=150,
        bandwidth=150,
        packet_loss=0.05,  # Very accurate
        power=15,
        defense=8,
    )

    return Enemy(
        name="Gateway Boss",
        stats=stats,
        symbol="G",
        description="A powerful gateway controlling the entire subnet",
        essence_drop=EssenceType.LIGHTNING,
        essence_drop_amount=50,
        xp_reward=150,
        aggression=0.9,
        preferred_essence=EssenceType.LIGHTNING,
    )


def create_illusionist() -> Enemy:
    """Create an illusionist mage enemy."""
    stats = Stats(
        max_hp=60,
        current_hp=60,
        max_mana=100,
        current_mana=100,
        bandwidth=80,
        packet_loss=0.20,  # Uses deception
        power=7,
        defense=3,
    )

    return Enemy(
        name="Illusionist",
        stats=stats,
        symbol="I",
        description="A mage who corrupts DNS caches with illusions",
        essence_drop=EssenceType.SHADOW,
        essence_drop_amount=25,
        xp_reward=60,
        aggression=0.5,
        preferred_essence=EssenceType.SHADOW,
    )


def create_swarm_minion() -> Enemy:
    """Create a weak swarm minion."""
    stats = Stats(
        max_hp=20,
        current_hp=20,
        max_mana=10,
        current_mana=10,
        bandwidth=30,
        packet_loss=0.25,
        power=3,
        defense=1,
    )

    return Enemy(
        name="Swarm Minion",
        stats=stats,
        symbol="m",
        description="A weak creature, dangerous in numbers",
        essence_drop=EssenceType.WIND,
        essence_drop_amount=5,
        xp_reward=10,
        aggression=1.0,  # Always attacks
        preferred_essence=EssenceType.WIND,
    )
